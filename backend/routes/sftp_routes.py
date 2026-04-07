"""SFTP Enhanced Routes — upload, download, batch, progress, speed, error log, daily summary."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import csv
import io
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/sftp", tags=["SFTP"])

_get_db = None
_sftp = None
_notify = None


def init_sftp_routes(get_db_func, sftp_svc):
    global _get_db, _sftp, _notify
    _get_db = get_db_func
    _sftp = sftp_svc
    # Lazy-import notification helpers
    try:
        from routes.notification_routes import (
            alert_upload_failure, alert_processing_error, alert_malformed_file
        )
        _notify = {
            "upload_failure": alert_upload_failure,
            "processing_error": alert_processing_error,
            "malformed": alert_malformed_file,
        }
    except ImportError:
        _notify = None


def get_db():
    return _get_db()


# ── Upload / Download / Batch ────────────────────────────────────

@router.post("/upload")
async def upload_file_to_sftp(
    file: UploadFile = File(...),
    remote_path: str = Form("/incoming"),
    overwrite: bool = Form(False),
):
    """Upload a file to SFTP with malformed detection, duplicate check, overwrite protection."""
    data = await file.read()
    transfer_id = str(uuid.uuid4())[:8]
    full_path = f"{remote_path.rstrip('/')}/{file.filename}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Validate content — malformed detection
    validation = _sftp.validate_file_content(data, file.filename)
    if not validation['valid']:
        archive = _sftp.get_archive_path(file.filename, 'failed')
        await get_db().sftp_logs.insert_one({
            'filename': file.filename, 'file_type': validation.get('file_type'),
            'status': 'malformed', 'error_message': validation['error'],
            'file_size': len(data), 'archive_path': archive,
            'processed_at': now_iso, 'transfer_id': transfer_id,
        })
        # Trigger malformed file alert
        if _notify:
            try:
                await _notify["malformed"](file.filename, validation['error'])
            except Exception as e:
                logger.error(f"Notification error: {e}")
        return {'status': 'malformed', 'transfer_id': transfer_id,
                'error': validation['error'], 'archive_path': archive}

    # Duplicate check
    dup = _sftp.check_duplicate(data, file.filename)
    if dup['is_duplicate']:
        await get_db().sftp_logs.insert_one({
            'filename': file.filename, 'file_type': validation.get('file_type'),
            'status': 'duplicate', 'error_message': 'Duplicate file detected — skipped',
            'file_size': len(data), 'file_hash': dup['file_hash'],
            'processed_at': now_iso, 'transfer_id': transfer_id,
        })
        return {'status': 'duplicate', 'transfer_id': transfer_id,
                'file_hash': dup['file_hash'], 'message': 'File already processed — skipped'}

    # Upload with overwrite protection
    result = _sftp.upload_file(data, full_path, transfer_id, overwrite)
    archive = _sftp.get_archive_path(file.filename, result.get('status', 'error'))
    await get_db().sftp_logs.insert_one({
        'filename': file.filename,
        'file_type': validation.get('file_type'),
        'store_code': _sftp.extract_store_code(file.filename),
        'file_date': _sftp.extract_file_date(file.filename),
        'status': result.get('status', 'error'),
        'rows_processed': validation.get('rows', 0) if result.get('status') == 'success' else 0,
        'file_size': len(data),
        'speed_mbps': result.get('speed_mbps', 0),
        'duration_seconds': result.get('duration_seconds', 0),
        'file_hash': result.get('file_hash', ''),
        'archive_path': archive,
        'error_message': result.get('error'),
        'processed_at': now_iso, 'transfer_id': transfer_id,
    })
    # Trigger upload failure alert if error
    if result.get('status') == 'error' and _notify:
        try:
            await _notify["upload_failure"](file.filename, result.get('error', 'Unknown'), transfer_id)
        except Exception as e:
            logger.error(f"Notification error: {e}")
    return result


@router.post("/download")
async def download_from_sftp(
    remote_path: str = Form(...),
    resume_offset: int = Form(0),
):
    """Download a file from SFTP with resume capability."""
    transfer_id = str(uuid.uuid4())[:8]
    result = _sftp.download_file(remote_path, transfer_id, resume_offset)
    response = {k: v for k, v in result.items() if k != 'data'}

    await get_db().sftp_logs.insert_one({
        'filename': remote_path.rsplit('/', 1)[-1],
        'direction': 'download', 'status': result['status'],
        'file_size': result.get('bytes', 0),
        'speed_mbps': result.get('speed_mbps', 0),
        'duration_seconds': result.get('duration_seconds', 0),
        'file_hash': result.get('file_hash', ''),
        'resumed_from': resume_offset,
        'error_message': result.get('error'),
        'processed_at': datetime.now(timezone.utc).isoformat(),
        'transfer_id': transfer_id,
    })
    return response


@router.post("/batch-upload")
async def batch_upload(files: List[UploadFile] = File(...)):
    """Upload multiple files in one request."""
    file_list = []
    validations = []
    for f in files:
        data = await f.read()
        v = _sftp.validate_file_content(data, f.filename)
        validations.append(v)
        file_list.append({
            'filename': f.filename, 'data': data,
            'transfer_id': str(uuid.uuid4())[:8], 'overwrite': False,
        })

    valid = [(fl, v) for fl, v in zip(file_list, validations) if v['valid']]
    malformed_items = [(fl, v) for fl, v in zip(file_list, validations) if not v['valid']]

    unique, dup_items = [], []
    for fl, v in valid:
        d = _sftp.check_duplicate(fl['data'], fl['filename'])
        if d['is_duplicate']:
            dup_items.append(fl)
        else:
            unique.append(fl)

    batch_result = _sftp.batch_upload(unique, '/incoming')
    now_iso = datetime.now(timezone.utc).isoformat()

    # Log malformed
    for fl, v in malformed_items:
        await get_db().sftp_logs.insert_one({
            'filename': fl['filename'], 'file_type': v.get('file_type'),
            'status': 'malformed', 'error_message': v.get('error'),
            'file_size': len(fl['data']), 'archive_path': _sftp.get_archive_path(fl['filename'], 'failed'),
            'processed_at': now_iso, 'transfer_id': fl['transfer_id'],
        })

    # Log duplicates
    for fl in dup_items:
        await get_db().sftp_logs.insert_one({
            'filename': fl['filename'], 'status': 'duplicate',
            'error_message': 'Duplicate file — skipped',
            'file_size': len(fl['data']), 'processed_at': now_iso,
            'transfer_id': fl['transfer_id'],
        })

    # Log uploaded
    for r in batch_result.get('results', []):
        matching_fl = next((fl for fl in unique if fl['filename'] == r.get('filename')), None)
        matching_v = next((v for fl, v in valid if fl['filename'] == r.get('filename')), None)
        await get_db().sftp_logs.insert_one({
            'filename': r.get('filename', ''),
            'file_type': matching_v.get('file_type') if matching_v else None,
            'store_code': _sftp.extract_store_code(r.get('filename', '')),
            'status': r.get('status', 'error'),
            'rows_processed': matching_v.get('rows', 0) if matching_v and r.get('status') == 'success' else 0,
            'file_size': r.get('bytes', 0),
            'speed_mbps': r.get('speed_mbps', 0),
            'error_message': r.get('error'),
            'archive_path': _sftp.get_archive_path(r.get('filename', ''), r.get('status', 'error')),
            'processed_at': now_iso,
            'transfer_id': matching_fl['transfer_id'] if matching_fl else '',
        })

    return {
        'total': len(file_list),
        'uploaded': batch_result.get('success', 0),
        'failed': batch_result.get('failed', 0),
        'malformed': len(malformed_items),
        'duplicates': len(dup_items),
        'results': batch_result.get('results', []),
    }


# ── Transfer Progress & Resume ───────────────────────────────────

@router.get("/transfer-progress/{transfer_id}")
async def get_transfer_progress(transfer_id: str):
    progress = _sftp.transfer_tracker.get(transfer_id)
    if not progress:
        raise HTTPException(404, "Transfer not found")
    return progress


@router.get("/transfers")
async def get_all_transfers():
    return _sftp.transfer_tracker.get_all()


@router.post("/resume/{transfer_id}")
async def resume_transfer(transfer_id: str):
    progress = _sftp.transfer_tracker.get(transfer_id)
    if not progress:
        raise HTTPException(404, "Transfer not found")
    if progress['status'] != 'failed':
        return {'message': 'Transfer not in failed state', 'current_status': progress['status']}
    if progress['direction'] == 'download':
        result = _sftp.download_file(progress['filename'], f"{transfer_id}_r", progress.get('resume_offset', 0))
        return {k: v for k, v in result.items() if k != 'data'}
    return {'message': 'Upload resume requires re-uploading the file'}


# ── Speed Metrics ────────────────────────────────────────────────

@router.get("/speed-metrics")
async def get_speed_metrics():
    session = _sftp.transfer_tracker.get_speed_metrics()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    logs = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": week_ago}, "speed_mbps": {"$exists": True, "$gt": 0}},
        {"_id": 0, "speed_mbps": 1, "file_size": 1, "duration_seconds": 1, "processed_at": 1}
    ).to_list(2000)

    if not logs:
        return {'avg_speed_mbps': 0, 'max_speed_mbps': 0, 'min_speed_mbps': 0,
                'total_transferred_mb': 0, 'total_duration_seconds': 0,
                'total_transfers': 0, 'daily_metrics': [], 'session_metrics': session}

    speeds = [l['speed_mbps'] for l in logs if l.get('speed_mbps')]
    total_size = sum(l.get('file_size', 0) for l in logs)
    total_dur = sum(l.get('duration_seconds', 0) for l in logs)

    by_day: Dict[str, Dict] = {}
    for l in logs:
        d = l.get('processed_at', '')[:10]
        if d not in by_day:
            by_day[d] = {'date': d, 'speeds': [], 'total_mb': 0}
        if l.get('speed_mbps'):
            by_day[d]['speeds'].append(l['speed_mbps'])
        by_day[d]['total_mb'] += l.get('file_size', 0) / 1_000_000

    daily = []
    for dd in sorted(by_day.values(), key=lambda x: x['date']):
        daily.append({
            'date': dd['date'],
            'avg_speed_mbps': round(sum(dd['speeds']) / len(dd['speeds']), 2) if dd['speeds'] else 0,
            'total_mb': round(dd['total_mb'], 2),
        })

    return {
        'avg_speed_mbps': round(sum(speeds) / len(speeds), 2) if speeds else 0,
        'max_speed_mbps': round(max(speeds), 2) if speeds else 0,
        'min_speed_mbps': round(min(speeds), 2) if speeds else 0,
        'total_transferred_mb': round(total_size / 1_000_000, 2),
        'total_duration_seconds': round(total_dur, 2),
        'total_transfers': len(logs),
        'daily_metrics': daily,
        'session_metrics': session,
    }


# ── Connection Pool Status ───────────────────────────────────────

@router.get("/connection-pool")
async def get_connection_pool_status():
    return {
        'pool': _sftp.pool_stats,
        'retry_config': _sftp.retry_config,
        'ssl_mode': _sftp.ssl_mode,
        'demo_mode': _sftp.demo_mode,
    }


# ── Error Log Download ───────────────────────────────────────────

@router.get("/error-log/download")
async def download_error_log(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: int = 7,
):
    """Download error log as CSV file."""
    query: Dict[str, Any] = {"status": {"$in": ["error", "malformed"]}}
    if start_date:
        ts_q: Dict[str, str] = {"$gte": start_date}
        if end_date:
            ts_q["$lte"] = end_date + "T23:59:59"
        query["processed_at"] = ts_q
    else:
        query["processed_at"] = {"$gte": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()}

    logs = await get_db().sftp_logs.find(query, {"_id": 0}).sort("processed_at", -1).to_list(5000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Filename', 'File Type', 'Store', 'Status',
                     'Error Message', 'File Size (KB)', 'Archive Path'])
    for log in logs:
        writer.writerow([
            log.get('processed_at', ''), log.get('filename', ''),
            log.get('file_type', ''), log.get('store_code', ''),
            log.get('status', ''), log.get('error_message', ''),
            round(log.get('file_size', 0) / 1024, 1),
            log.get('archive_path', ''),
        ])
    output.seek(0)
    ds = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sftp_errors_{ds}.csv"})


# ── Daily Summary ────────────────────────────────────────────────

@router.get("/daily-summary")
async def get_daily_summary(date: Optional[str] = None):
    if not date:
        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    logs = await get_db().sftp_logs.find(
        {"processed_at": {"$regex": f"^{date}"}}, {"_id": 0}
    ).to_list(2000)
    if not logs:
        logs = await get_db().sftp_logs.find({"file_date": date}, {"_id": 0}).to_list(2000)

    total = len(logs)
    success = sum(1 for l in logs if l.get('status') == 'success')
    failed = sum(1 for l in logs if l.get('status') == 'error')
    malformed = sum(1 for l in logs if l.get('status') == 'malformed')
    duplicates = sum(1 for l in logs if l.get('status') == 'duplicate')
    total_rows = sum(l.get('rows_processed', 0) for l in logs)
    total_size = sum(l.get('file_size', 0) for l in logs)
    speeds = [l.get('speed_mbps', 0) for l in logs if l.get('speed_mbps', 0) > 0]

    by_type: Dict[str, Dict] = {}
    for l in logs:
        ft = l.get('file_type', 'unknown')
        if ft not in by_type:
            by_type[ft] = {'total': 0, 'success': 0, 'failed': 0, 'rows': 0, 'size_mb': 0}
        by_type[ft]['total'] += 1
        if l.get('status') == 'success':
            by_type[ft]['success'] += 1
        elif l.get('status') in ('error', 'malformed'):
            by_type[ft]['failed'] += 1
        by_type[ft]['rows'] += l.get('rows_processed', 0)
        by_type[ft]['size_mb'] += l.get('file_size', 0) / 1_000_000
    for v in by_type.values():
        v['size_mb'] = round(v['size_mb'], 2)

    stores_seen = set(l.get('store_code') for l in logs if l.get('store_code'))
    expected = {'ST001', 'ST002', 'ST003', 'ST004', 'ST005', 'ST006', 'ST007', 'ST008', 'ST009', 'ST010'}
    missing = sorted(expected - stores_seen)

    errors: Dict[str, int] = {}
    for l in logs:
        err = l.get('error_message')
        if err:
            errors[err] = errors.get(err, 0) + 1
    top_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'date': date,
        'total_files': total, 'success': success, 'failed': failed,
        'malformed': malformed, 'duplicates': duplicates,
        'success_rate': round((success / max(total, 1)) * 100, 1),
        'total_rows': total_rows,
        'total_size_mb': round(total_size / 1_000_000, 2),
        'avg_speed_mbps': round(sum(speeds) / len(speeds), 2) if speeds else 0,
        'by_type': by_type,
        'store_coverage': {
            'total_expected': len(expected),
            'total_received': len(stores_seen),
            'missing_stores': missing,
        },
        'top_errors': [{'error': e, 'count': c} for e, c in top_errors],
    }


@router.get("/daily-summary/download")
async def download_daily_summary(date: Optional[str] = None):
    summary = await get_daily_summary(date)
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow([f"SFTP Daily Summary - {summary['date']}"])
    w.writerow([])
    w.writerow(['Metric', 'Value'])
    for k in ['total_files', 'success', 'failed', 'malformed', 'duplicates']:
        w.writerow([k.replace('_', ' ').title(), summary[k]])
    w.writerow(['Success Rate', f"{summary['success_rate']}%"])
    w.writerow(['Total Rows', summary['total_rows']])
    w.writerow(['Total Size MB', summary['total_size_mb']])
    w.writerow(['Avg Speed MB/s', summary['avg_speed_mbps']])
    w.writerow([])
    w.writerow(['Missing Stores', ', '.join(summary['store_coverage']['missing_stores'])])
    w.writerow([])
    w.writerow(['Top Errors', 'Count'])
    for e in summary['top_errors']:
        w.writerow([e['error'], e['count']])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sftp_summary_{summary['date']}.csv"})
