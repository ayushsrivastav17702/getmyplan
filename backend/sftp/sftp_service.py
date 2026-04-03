"""
SFTP Service — Enhanced with connection pooling, retry with backoff, SSL/TLS verification,
file transfer with progress tracking, resume capability, duplicate detection,
malformed file handling, archival, and speed metrics.
"""
import paramiko
import os
import logging
import fnmatch
import re
import random
import hashlib
import time
import threading
import uuid
import pandas as pd
import io
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from collections import deque

logger = logging.getLogger(__name__)

FILE_PATTERNS = {
    'daily_sales': ['*sales*.csv', '*sales*.xlsx', '*transaction*.csv'],
    'store_inventory': ['*store*inv*.csv', '*store*stock*.csv', '*inventory*.csv'],
    'warehouse_inventory': ['*warehouse*.csv', '*wh_stock*.csv', '*wh_inv*.csv'],
}

DEMO_STORES = ['ST001', 'ST002', 'ST003', 'ST004', 'ST005',
               'ST006', 'ST007', 'ST008', 'ST009', 'ST010']
DEMO_WAREHOUSES = ['WH001', 'WH002']


class ConnectionPool:
    """Thread-safe SFTP connection pool with SSL/TLS verification."""

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self._pool: deque = deque()
        self._active = 0
        self._lock = threading.Lock()
        self._config: Dict = {}
        self._ssl_mode = 'auto'
        self._total_created = 0
        self._total_failed = 0

    def configure(self, config: Dict):
        self._config = config
        self._ssl_mode = config.get('ssl_mode', 'auto')

    @property
    def stats(self) -> Dict:
        with self._lock:
            return {
                'max_size': self.max_size,
                'available': len(self._pool),
                'active': self._active,
                'total_created': self._total_created,
                'total_failed': self._total_failed,
                'ssl_mode': self._ssl_mode,
            }

    def _create_connection(self) -> paramiko.SFTPClient:
        client = paramiko.SSHClient()
        if self._ssl_mode == 'strict':
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        elif self._ssl_mode == 'reject':
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kw = {
            'hostname': self._config['host'],
            'port': int(self._config.get('port', 22)),
            'username': self._config['username'],
            'timeout': int(self._config.get('timeout', 30)),
        }
        key_path = self._config.get('key_path')
        password = self._config.get('password')
        if key_path and os.path.exists(key_path):
            kw['pkey'] = paramiko.RSAKey.from_private_key_file(
                key_path, password=self._config.get('key_passphrase'))
        elif password:
            kw['password'] = password
        else:
            raise Exception("No SFTP auth method (key or password)")

        client.connect(**kw)
        transport = client.get_transport()
        if transport:
            transport.set_keepalive(60)
        sftp = client.open_sftp()
        sftp._ssh_client = client
        self._total_created += 1
        return sftp

    def acquire(self) -> Optional[paramiko.SFTPClient]:
        with self._lock:
            while self._pool:
                conn = self._pool.popleft()
                try:
                    conn.stat('.')
                    self._active += 1
                    return conn
                except Exception:
                    self._close_conn(conn)
            if self._active < self.max_size:
                try:
                    conn = self._create_connection()
                    self._active += 1
                    return conn
                except Exception:
                    self._total_failed += 1
                    raise
        return None

    def release(self, conn: paramiko.SFTPClient):
        with self._lock:
            self._active = max(0, self._active - 1)
            try:
                conn.stat('.')
                self._pool.append(conn)
            except Exception:
                self._close_conn(conn)

    def _close_conn(self, conn):
        try:
            client = getattr(conn, '_ssh_client', None)
            conn.close()
            if client:
                client.close()
        except Exception:
            pass

    def close_all(self):
        with self._lock:
            while self._pool:
                self._close_conn(self._pool.popleft())
            self._active = 0


class TransferTracker:
    """Track file transfer progress in-memory."""

    def __init__(self):
        self._transfers: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start(self, transfer_id: str, filename: str, total_bytes: int, direction: str) -> Dict:
        with self._lock:
            entry = {
                'transfer_id': transfer_id,
                'filename': filename,
                'total_bytes': total_bytes,
                'transferred_bytes': 0,
                'direction': direction,
                'status': 'in_progress',
                'speed_bps': 0,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'completed_at': None,
                'error': None,
                'resumable': True,
                'resume_offset': 0,
            }
            self._transfers[transfer_id] = entry
            return entry.copy()

    def update(self, transfer_id: str, bytes_transferred: int, speed: float = 0):
        with self._lock:
            t = self._transfers.get(transfer_id)
            if t:
                t['transferred_bytes'] = bytes_transferred
                t['speed_bps'] = speed

    def complete(self, transfer_id: str):
        with self._lock:
            t = self._transfers.get(transfer_id)
            if t:
                t['status'] = 'completed'
                t['transferred_bytes'] = t['total_bytes']
                t['completed_at'] = datetime.now(timezone.utc).isoformat()

    def fail(self, transfer_id: str, error: str, resume_offset: int = 0):
        with self._lock:
            t = self._transfers.get(transfer_id)
            if t:
                t['status'] = 'failed'
                t['error'] = error
                t['resume_offset'] = resume_offset
                t['completed_at'] = datetime.now(timezone.utc).isoformat()

    def get(self, transfer_id: str) -> Optional[Dict]:
        with self._lock:
            t = self._transfers.get(transfer_id)
            return t.copy() if t else None

    def get_all(self) -> List[Dict]:
        with self._lock:
            return [t.copy() for t in self._transfers.values()]

    def get_speed_metrics(self) -> Dict:
        with self._lock:
            completed = [t for t in self._transfers.values() if t['status'] == 'completed']
            if not completed:
                return {'avg_speed_mbps': 0, 'max_speed_mbps': 0, 'total_transferred_mb': 0, 'total_transfers': 0}
            speeds = [t['speed_bps'] for t in completed if t['speed_bps'] > 0]
            total_bytes = sum(t['total_bytes'] for t in completed)
            return {
                'avg_speed_mbps': round(sum(speeds) / len(speeds) / 1_000_000, 2) if speeds else 0,
                'max_speed_mbps': round(max(speeds) / 1_000_000, 2) if speeds else 0,
                'total_transferred_mb': round(total_bytes / 1_000_000, 2),
                'total_transfers': len(completed),
            }


class SFTPService:
    """Manages SFTP with pooling, retry, SSL, progress, dedup, archive."""

    def __init__(self):
        self._config: Dict = {}
        self._pool = ConnectionPool()
        self._tracker = TransferTracker()
        self._retry_config = {'max_retries': 3, 'base_delay': 1.0, 'max_delay': 30.0}
        self._reconnect_attempts = 0
        self._last_connection_error = None
        self._file_hashes: Dict[str, str] = {}

    def load_config(self, config: Dict):
        self._config = config
        self._pool.max_size = int(config.get('pool_size', 5))
        self._pool.configure(config)
        self._retry_config = {
            'max_retries': int(config.get('max_retries', 3)),
            'base_delay': float(config.get('retry_base_delay', 1.0)),
            'max_delay': float(config.get('retry_max_delay', 30.0)),
        }

    @property
    def demo_mode(self) -> bool:
        return not self._config.get('host') or not self._config.get('username')

    @property
    def host(self):
        return self._config.get('host', '')

    @property
    def pool_stats(self) -> Dict:
        return self._pool.stats

    @property
    def transfer_tracker(self) -> TransferTracker:
        return self._tracker

    @property
    def retry_config(self) -> Dict:
        return self._retry_config.copy()

    @property
    def ssl_mode(self) -> str:
        return self._config.get('ssl_mode', 'auto')

    # ── Connection with retry + backoff ──────────────────────────

    def connect_with_retry(self) -> Dict:
        if self.demo_mode:
            return {'status': 'demo', 'message': 'Running in demo mode', 'retries': 0,
                    'ssl_mode': 'N/A', 'pool': self._pool.stats}

        max_retries = self._retry_config['max_retries']
        base_delay = self._retry_config['base_delay']
        max_delay = self._retry_config['max_delay']

        for attempt in range(max_retries + 1):
            try:
                conn = self._pool.acquire()
                if conn:
                    self._pool.release(conn)
                    self._reconnect_attempts = 0
                    self._last_connection_error = None
                    return {
                        'status': 'connected',
                        'host': self._config.get('host'),
                        'retries': attempt,
                        'ssl_mode': self.ssl_mode,
                        'pool': self._pool.stats,
                    }
            except paramiko.AuthenticationException as e:
                self._last_connection_error = f"Authentication failed: {e}"
                return {'status': 'auth_error', 'message': self._last_connection_error, 'retries': attempt}
            except paramiko.SSHException as e:
                err = str(e).lower()
                if 'permission' in err:
                    self._last_connection_error = f"Permission denied: {e}"
                    return {'status': 'permission_denied', 'message': self._last_connection_error, 'retries': attempt}
                self._last_connection_error = f"SSH error: {e}"
            except OSError as e:
                msg = str(e).lower()
                if 'timed out' in msg or 'timeout' in msg:
                    self._last_connection_error = f"Connection timed out ({self._config.get('timeout', 30)}s)"
                elif 'unreachable' in msg or 'no route' in msg:
                    self._last_connection_error = f"Host unreachable: {self._config.get('host')}"
                else:
                    self._last_connection_error = f"Network error: {e}"
            except Exception as e:
                self._last_connection_error = f"Connection failed: {e}"

            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning("SFTP attempt %d failed, retrying in %.1fs: %s", attempt + 1, delay, self._last_connection_error)
                time.sleep(delay)

        self._reconnect_attempts += 1
        return {
            'status': 'error',
            'message': self._last_connection_error or 'Connection failed after retries',
            'retries': max_retries,
            'reconnect_attempts': self._reconnect_attempts,
        }

    def test_connection(self) -> Dict:
        if self.demo_mode:
            return {
                'status': 'demo',
                'message': 'Running in demo mode — no SFTP server configured',
                'ssl_mode': 'N/A',
                'pool': {'max_size': self._pool.max_size, 'available': 0, 'active': 0},
            }
        return self.connect_with_retry()

    # ── File helpers ─────────────────────────────────────────────

    @staticmethod
    def _compute_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def detect_file_type(filename: str) -> Optional[str]:
        fl = filename.lower()
        for ftype, patterns in FILE_PATTERNS.items():
            for pat in patterns:
                if fnmatch.fnmatch(fl, pat):
                    return ftype
        return None

    @staticmethod
    def extract_store_code(filename: str) -> Optional[str]:
        m = re.search(r'(ST\d{3,})', filename, re.IGNORECASE)
        return m.group(1).upper() if m else None

    @staticmethod
    def extract_file_date(filename: str) -> Optional[str]:
        for pat, fmt in [(r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'), (r'(\d{8})', '%Y%m%d')]:
            m = re.search(pat, filename)
            if m:
                try:
                    return datetime.strptime(m.group(1), fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    def validate_file_content(self, data: bytes, filename: str) -> Dict:
        """Validate file structure — returns malformed info if bad."""
        result = {'valid': False, 'error': None, 'file_type': None, 'rows': 0, 'columns': []}
        try:
            result['file_type'] = self.detect_file_type(filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(io.BytesIO(data))
            elif ext in ('.xlsx', '.xls'):
                df = pd.read_excel(io.BytesIO(data))
            else:
                result['error'] = f'Unsupported file format: {ext}'
                return result
            if df.empty:
                result['error'] = 'File is empty (no data rows)'
                return result
            if len(df.columns) < 2:
                result['error'] = 'File has fewer than 2 columns — likely malformed'
                return result
            result['valid'] = True
            result['rows'] = len(df)
            result['columns'] = list(df.columns)
        except Exception as e:
            result['error'] = f'Failed to parse file: {str(e)}'
        return result

    def check_duplicate(self, data: bytes, filename: str) -> Dict:
        file_hash = self._compute_hash(data)
        key = f"{filename}:{file_hash}"
        is_dup = key in self._file_hashes
        if not is_dup:
            self._file_hashes[key] = datetime.now(timezone.utc).isoformat()
        return {'is_duplicate': is_dup, 'file_hash': file_hash,
                'original_processed_at': self._file_hashes.get(key) if is_dup else None}

    @staticmethod
    def get_archive_path(filename: str, status: str) -> str:
        folder = 'processed' if status == 'success' else 'failed'
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return f"/archive/{folder}/{date_str}/{filename}"

    # ── Real SFTP file operations ────────────────────────────────

    def _mkdir_p(self, conn, path):
        parts = path.split('/')
        current = ''
        for part in parts:
            if not part:
                current = '/'
                continue
            current = f"{current}/{part}" if current != '/' else f"/{part}"
            try:
                conn.stat(current)
            except FileNotFoundError:
                conn.mkdir(current)

    def upload_file(self, local_data: bytes, remote_path: str,
                    transfer_id: str, overwrite: bool = False) -> Dict:
        if self.demo_mode:
            return self._demo_upload(local_data, remote_path, transfer_id, overwrite)

        total = len(local_data)
        self._tracker.start(transfer_id, os.path.basename(remote_path), total, 'upload')
        start_time = time.time()
        try:
            conn = self._pool.acquire()
            if not conn:
                raise Exception("No connection available from pool")
            try:
                if not overwrite:
                    try:
                        conn.stat(remote_path)
                        base, ext = os.path.splitext(remote_path)
                        ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        remote_path = f"{base}_{ts}{ext}"
                    except FileNotFoundError:
                        pass
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    try:
                        conn.stat(remote_dir)
                    except FileNotFoundError:
                        self._mkdir_p(conn, remote_dir)
                chunk_size = 32768
                with conn.open(remote_path, 'wb') as f:
                    offset = 0
                    while offset < total:
                        chunk = local_data[offset:offset + chunk_size]
                        f.write(chunk)
                        offset += len(chunk)
                        elapsed = time.time() - start_time
                        speed = offset / elapsed if elapsed > 0 else 0
                        self._tracker.update(transfer_id, offset, speed)
                elapsed = time.time() - start_time
                speed = total / elapsed if elapsed > 0 else 0
                self._tracker.complete(transfer_id)
                return {
                    'status': 'success', 'transfer_id': transfer_id,
                    'remote_path': remote_path, 'bytes': total,
                    'speed_mbps': round(speed / 1_000_000, 2),
                    'duration_seconds': round(elapsed, 2),
                    'file_hash': self._compute_hash(local_data),
                    'overwrite_protected': False,
                }
            finally:
                self._pool.release(conn)
        except Exception as e:
            self._tracker.fail(transfer_id, str(e))
            return {'status': 'error', 'transfer_id': transfer_id, 'error': str(e)}

    def download_file(self, remote_path: str, transfer_id: str,
                      resume_offset: int = 0) -> Dict:
        if self.demo_mode:
            return self._demo_download(remote_path, transfer_id, resume_offset)
        try:
            conn = self._pool.acquire()
            if not conn:
                raise Exception("No connection available from pool")
            try:
                stat = conn.stat(remote_path)
                total = stat.st_size or 0
                self._tracker.start(transfer_id, os.path.basename(remote_path), total, 'download')
                start_time = time.time()
                buf = io.BytesIO()
                chunk_size = 32768
                with conn.open(remote_path, 'rb') as f:
                    if resume_offset > 0:
                        f.seek(resume_offset)
                    offset = resume_offset
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        buf.write(chunk)
                        offset += len(chunk)
                        elapsed = time.time() - start_time
                        speed = (offset - resume_offset) / elapsed if elapsed > 0 else 0
                        self._tracker.update(transfer_id, offset, speed)
                elapsed = time.time() - start_time
                net = offset - resume_offset
                speed = net / elapsed if elapsed > 0 else 0
                self._tracker.complete(transfer_id)
                data = buf.getvalue()
                return {
                    'status': 'success', 'transfer_id': transfer_id,
                    'remote_path': remote_path, 'bytes': len(data),
                    'speed_mbps': round(speed / 1_000_000, 2),
                    'duration_seconds': round(elapsed, 2),
                    'file_hash': self._compute_hash(data),
                    'resumed_from': resume_offset,
                }
            finally:
                self._pool.release(conn)
        except Exception as e:
            self._tracker.fail(transfer_id, str(e), resume_offset=resume_offset)
            return {'status': 'error', 'transfer_id': transfer_id, 'error': str(e), 'resume_offset': resume_offset}

    def batch_upload(self, files: List[Dict], base_remote_path: str) -> Dict:
        if self.demo_mode:
            return self._demo_batch_upload(files, base_remote_path)
        results = []
        for f in files:
            tid = f.get('transfer_id', str(uuid.uuid4())[:8])
            remote = f"{base_remote_path.rstrip('/')}/{f['filename']}"
            result = self.upload_file(f['data'], remote, tid, f.get('overwrite', False))
            results.append(result)
        return {
            'total': len(files),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results,
        }

    def archive_file(self, remote_path: str, archive_path: str) -> Dict:
        if self.demo_mode:
            return {'status': 'archived', 'archive_path': archive_path}
        try:
            conn = self._pool.acquire()
            if not conn:
                raise Exception("No connection available")
            try:
                parts = archive_path.rsplit('/', 1)
                if len(parts) == 2 and parts[0]:
                    try:
                        conn.stat(parts[0])
                    except FileNotFoundError:
                        self._mkdir_p(conn, parts[0])
                conn.rename(remote_path, archive_path)
                return {'status': 'archived', 'archive_path': archive_path}
            finally:
                self._pool.release(conn)
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    # ── Demo data generation ─────────────────────────────────────

    def _demo_upload(self, data, remote_path, transfer_id, overwrite):
        total = len(data)
        self._tracker.start(transfer_id, os.path.basename(remote_path), total, 'upload')
        speed = random.uniform(5_000_000, 25_000_000)
        duration = total / speed if speed > 0 else 0.1
        final_path = remote_path
        if not overwrite and random.random() < 0.3:
            base, ext = os.path.splitext(remote_path)
            ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            final_path = f"{base}_{ts}{ext}"
        self._tracker.update(transfer_id, total, speed)
        self._tracker.complete(transfer_id)
        return {
            'status': 'success', 'transfer_id': transfer_id,
            'remote_path': final_path, 'bytes': total,
            'speed_mbps': round(speed / 1_000_000, 2),
            'duration_seconds': round(duration, 2),
            'file_hash': self._compute_hash(data),
            'overwrite_protected': final_path != remote_path,
        }

    def _demo_download(self, remote_path, transfer_id, resume_offset):
        total = random.randint(50_000, 5_000_000)
        self._tracker.start(transfer_id, os.path.basename(remote_path), total, 'download')
        speed = random.uniform(5_000_000, 25_000_000)
        actual = total - resume_offset
        duration = actual / speed if speed > 0 else 0.1
        self._tracker.update(transfer_id, total, speed)
        self._tracker.complete(transfer_id)
        return {
            'status': 'success', 'transfer_id': transfer_id,
            'remote_path': remote_path, 'bytes': actual,
            'speed_mbps': round(speed / 1_000_000, 2),
            'duration_seconds': round(duration, 2),
            'file_hash': hashlib.sha256(os.urandom(32)).hexdigest(),
            'resumed_from': resume_offset,
        }

    def _demo_batch_upload(self, files, base_path):
        results = []
        for f in files:
            tid = f.get('transfer_id', str(random.randint(10000, 99999)))
            success = random.random() < 0.9
            size = len(f.get('data', b'')) or random.randint(10000, 500000)
            speed = random.uniform(5_000_000, 25_000_000)
            self._tracker.start(tid, f['filename'], size, 'upload')
            if success:
                self._tracker.complete(tid)
            else:
                self._tracker.fail(tid, 'Simulated upload error')
            results.append({
                'transfer_id': tid, 'filename': f['filename'],
                'status': 'success' if success else 'error',
                'bytes': size, 'speed_mbps': round(speed / 1_000_000, 2) if success else 0,
                'error': None if success else 'Simulated upload error',
            })
        return {
            'total': len(files),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results,
        }

    def generate_demo_cycle(self) -> List[Dict]:
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        results = []
        for store in DEMO_STORES:
            success = random.random() < 0.92
            rows = random.randint(800, 3500) if success else 0
            file_size = rows * random.randint(85, 120) if success else random.randint(500, 2000)
            speed = round(random.uniform(5, 25), 2) if success else 0
            dur = round(file_size / (speed * 1_000_000), 3) if speed > 0 else 0
            is_dup = random.random() < 0.05
            is_malformed = not success and random.random() < 0.4
            status = 'duplicate' if is_dup else ('malformed' if is_malformed else ('success' if success else 'error'))
            results.append({
                'filename': f'{store}_sales_{yesterday}.csv',
                'file_type': 'daily_sales', 'store_code': store,
                'file_date': yesterday, 'status': status,
                'rows_processed': rows,
                'rows_rejected': random.randint(0, 5) if success else 0,
                'file_size': file_size, 'speed_mbps': speed,
                'duration_seconds': dur,
                'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                'archive_path': f"/archive/{'processed' if success else 'failed'}/{yesterday}/{store}_sales_{yesterday}.csv",
                'error_message': None if success else (
                    'Duplicate file — skipped' if is_dup else
                    'Malformed CSV: unable to parse headers' if is_malformed else
                    random.choice(['Missing required column: quantity',
                                   'Date format mismatch in row 145',
                                   'File appears to be empty',
                                   'Duplicate records detected'])),
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })
        for store in DEMO_STORES:
            success = random.random() < 0.95
            rows = random.randint(1500, 6000) if success else 0
            file_size = rows * random.randint(60, 90) if success else 0
            speed = round(random.uniform(5, 25), 2) if success else 0
            dur = round(file_size / (speed * 1_000_000), 3) if speed > 0 else 0
            results.append({
                'filename': f'{store}_inventory_{yesterday}.csv',
                'file_type': 'store_inventory', 'store_code': store,
                'file_date': yesterday, 'status': 'success' if success else 'error',
                'rows_processed': rows,
                'rows_rejected': random.randint(0, 3) if success else 0,
                'file_size': file_size, 'speed_mbps': speed,
                'duration_seconds': dur,
                'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                'archive_path': f"/archive/{'processed' if success else 'failed'}/{yesterday}/{store}_inventory_{yesterday}.csv",
                'error_message': None if success else 'Connection timeout during processing',
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })
        for wh in DEMO_WAREHOUSES:
            rows = random.randint(4000, 12000)
            file_size = rows * random.randint(70, 100)
            speed = round(random.uniform(8, 30), 2)
            dur = round(file_size / (speed * 1_000_000), 3)
            results.append({
                'filename': f'{wh}_warehouse_inventory_{yesterday}.csv',
                'file_type': 'warehouse_inventory', 'store_code': None,
                'file_date': yesterday, 'status': 'success',
                'rows_processed': rows, 'rows_rejected': random.randint(0, 2),
                'file_size': file_size, 'speed_mbps': speed,
                'duration_seconds': dur,
                'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                'archive_path': f"/archive/processed/{yesterday}/{wh}_warehouse_inventory_{yesterday}.csv",
                'error_message': None,
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })
        return results

    def generate_demo_history(self, days: int = 7) -> List[Dict]:
        all_records = []
        now = datetime.now(timezone.utc)
        for d in range(days):
            day = now - timedelta(days=d)
            prev_day_str = (day - timedelta(days=1)).strftime('%Y-%m-%d')
            for store in DEMO_STORES:
                success = random.random() < 0.92
                rows = random.randint(800, 3500) if success else 0
                fs = rows * random.randint(85, 120) if success else random.randint(100, 2000)
                sp = round(random.uniform(5, 25), 2) if success else 0
                dur = round(fs / (sp * 1_000_000), 3) if sp > 0 else 0
                is_dup = random.random() < 0.03
                is_mal = not success and random.random() < 0.3
                status = 'duplicate' if is_dup else ('malformed' if is_mal else ('success' if success else 'error'))
                all_records.append({
                    'filename': f'{store}_sales_{prev_day_str}.csv',
                    'file_type': 'daily_sales', 'store_code': store,
                    'file_date': prev_day_str, 'status': status,
                    'rows_processed': rows,
                    'rows_rejected': random.randint(0, 5) if success else 0,
                    'file_size': fs, 'speed_mbps': sp, 'duration_seconds': dur,
                    'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                    'archive_path': f"/archive/{'processed' if success else 'failed'}/{prev_day_str}/{store}_sales_{prev_day_str}.csv",
                    'error_message': None if success else ('Duplicate' if is_dup else 'Malformed CSV' if is_mal else 'Column mismatch'),
                    'processed_at': day.replace(hour=random.randint(6, 9), minute=random.randint(0, 59)).isoformat(),
                })
            for store in DEMO_STORES:
                success = random.random() < 0.95
                rows = random.randint(1500, 6000) if success else 0
                fs = rows * random.randint(60, 90) if success else 0
                sp = round(random.uniform(5, 25), 2) if success else 0
                dur = round(fs / (sp * 1_000_000), 3) if sp > 0 else 0
                all_records.append({
                    'filename': f'{store}_inventory_{prev_day_str}.csv',
                    'file_type': 'store_inventory', 'store_code': store,
                    'file_date': prev_day_str, 'status': 'success' if success else 'error',
                    'rows_processed': rows, 'rows_rejected': random.randint(0, 3) if success else 0,
                    'file_size': fs, 'speed_mbps': sp, 'duration_seconds': dur,
                    'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                    'archive_path': f"/archive/{'processed' if success else 'failed'}/{prev_day_str}/{store}_inventory_{prev_day_str}.csv",
                    'error_message': None if success else 'Timeout',
                    'processed_at': day.replace(hour=random.randint(6, 9), minute=random.randint(0, 59)).isoformat(),
                })
            for wh in DEMO_WAREHOUSES:
                rows = random.randint(4000, 12000)
                fs = rows * random.randint(70, 100)
                sp = round(random.uniform(8, 30), 2)
                dur = round(fs / (sp * 1_000_000), 3)
                all_records.append({
                    'filename': f'{wh}_warehouse_inventory_{prev_day_str}.csv',
                    'file_type': 'warehouse_inventory', 'store_code': None,
                    'file_date': prev_day_str, 'status': 'success',
                    'rows_processed': rows, 'rows_rejected': random.randint(0, 2),
                    'file_size': fs, 'speed_mbps': sp, 'duration_seconds': dur,
                    'file_hash': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
                    'archive_path': f"/archive/processed/{prev_day_str}/{wh}_warehouse_inventory_{prev_day_str}.csv",
                    'error_message': None,
                    'processed_at': day.replace(hour=random.randint(6, 9), minute=random.randint(0, 59)).isoformat(),
                })
        all_records.sort(key=lambda x: x['processed_at'], reverse=True)
        return all_records


sftp_service = SFTPService()
