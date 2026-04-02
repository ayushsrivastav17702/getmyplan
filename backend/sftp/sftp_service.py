"""
SFTP Service — handles connection, file listing, download, processing.
Operates in DEMO MODE when SFTP credentials are not configured,
generating realistic simulated data for the monitoring dashboard.
"""
import paramiko
import os
import logging
import fnmatch
import re
import random
import pandas as pd
import io
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# File type patterns for auto-detection
FILE_PATTERNS = {
    'daily_sales': ['*sales*.csv', '*sales*.xlsx', '*transaction*.csv'],
    'store_inventory': ['*store*inv*.csv', '*store*stock*.csv', '*inventory*.csv'],
    'warehouse_inventory': ['*warehouse*.csv', '*wh_stock*.csv', '*wh_inv*.csv'],
}

FILE_NAMING = {
    'daily_sales': '{store_code}_sales_{date}.csv',
    'store_inventory': '{store_code}_inventory_{date}.csv',
    'warehouse_inventory': 'warehouse_inventory_{date}.csv',
}

DEMO_STORES = ['ST001', 'ST002', 'ST003', 'ST004', 'ST005',
               'ST006', 'ST007', 'ST008', 'ST009', 'ST010']
DEMO_WAREHOUSES = ['WH001', 'WH002']


class SFTPService:
    """Manages SFTP connections and file operations. Falls back to demo mode."""

    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.is_connected = False
        self._config: Dict = {}

    # ── configuration ────────────────────────────────────────────

    def load_config(self, config: Dict):
        self._config = config

    @property
    def demo_mode(self) -> bool:
        return not self._config.get('host') or not self._config.get('username')

    @property
    def host(self):
        return self._config.get('host', '')

    # ── real SFTP connection ─────────────────────────────────────

    def connect(self) -> bool:
        if self.demo_mode:
            logger.info("SFTP running in DEMO MODE — no real server configured")
            return True
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kw = {
                'hostname': self._config['host'],
                'port': int(self._config.get('port', 22)),
                'username': self._config['username'],
                'timeout': 30,
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
            self.client.connect(**kw)
            self.sftp = self.client.open_sftp()
            self.is_connected = True
            logger.info(f"Connected to SFTP: {self._config['host']}")
            return True
        except Exception as e:
            logger.error(f"SFTP connect failed: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        self.is_connected = False

    def test_connection(self) -> Dict:
        if self.demo_mode:
            return {'status': 'demo', 'message': 'Running in demo mode — no SFTP server configured'}
        ok = self.connect()
        if ok:
            self.disconnect()
        return {
            'status': 'connected' if ok else 'error',
            'host': self._config.get('host'),
            'message': 'Connection successful' if ok else 'Connection failed',
        }

    # ── file detection helpers ───────────────────────────────────

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
        for pat, fmt in [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            (r'(\d{8})', '%Y%m%d'),
        ]:
            m = re.search(pat, filename)
            if m:
                try:
                    return datetime.strptime(m.group(1), fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    # ── demo data generation ─────────────────────────────────────

    def generate_demo_cycle(self) -> List[Dict]:
        """Simulate a processing cycle with realistic results."""
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        results = []

        # Daily sales — one per store
        for store in DEMO_STORES:
            success = random.random() < 0.92
            rows = random.randint(800, 3500) if success else 0
            results.append({
                'filename': f'{store}_sales_{yesterday}.csv',
                'file_type': 'daily_sales',
                'store_code': store,
                'file_date': yesterday,
                'status': 'success' if success else 'error',
                'rows_processed': rows,
                'rows_rejected': random.randint(0, 5) if success else 0,
                'file_size': rows * random.randint(85, 120) if success else random.randint(500, 2000),
                'error_message': None if success else random.choice([
                    'Missing required column: quantity',
                    'Date format mismatch in row 145',
                    'File appears to be empty',
                    'Duplicate records detected',
                ]),
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })

        # Store inventory — one per store
        for store in DEMO_STORES:
            success = random.random() < 0.95
            rows = random.randint(1500, 6000) if success else 0
            results.append({
                'filename': f'{store}_inventory_{yesterday}.csv',
                'file_type': 'store_inventory',
                'store_code': store,
                'file_date': yesterday,
                'status': 'success' if success else 'error',
                'rows_processed': rows,
                'rows_rejected': random.randint(0, 3) if success else 0,
                'file_size': rows * random.randint(60, 90) if success else 0,
                'error_message': None if success else 'Connection timeout during processing',
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })

        # Warehouse inventory
        for wh in DEMO_WAREHOUSES:
            rows = random.randint(4000, 12000)
            results.append({
                'filename': f'{wh}_warehouse_inventory_{yesterday}.csv',
                'file_type': 'warehouse_inventory',
                'store_code': None,
                'file_date': yesterday,
                'status': 'success',
                'rows_processed': rows,
                'rows_rejected': random.randint(0, 2),
                'file_size': rows * random.randint(70, 100),
                'error_message': None,
                'processed_at': (now - timedelta(minutes=random.randint(1, 55))).isoformat(),
            })

        return results

    def generate_demo_history(self, days: int = 7) -> List[Dict]:
        """Generate demo history spanning multiple days."""
        all_records = []
        now = datetime.now(timezone.utc)
        for d in range(days):
            day = now - timedelta(days=d)
            date_str = day.strftime('%Y-%m-%d')
            prev_day_str = (day - timedelta(days=1)).strftime('%Y-%m-%d')

            for store in DEMO_STORES:
                success = random.random() < 0.92
                rows = random.randint(800, 3500) if success else 0
                all_records.append({
                    'filename': f'{store}_sales_{prev_day_str}.csv',
                    'file_type': 'daily_sales',
                    'store_code': store,
                    'file_date': prev_day_str,
                    'status': 'success' if success else 'error',
                    'rows_processed': rows,
                    'rows_rejected': random.randint(0, 5) if success else 0,
                    'file_size': rows * random.randint(85, 120) if success else 0,
                    'error_message': None if success else 'Column mismatch',
                    'processed_at': day.replace(
                        hour=random.randint(6, 9),
                        minute=random.randint(0, 59),
                    ).isoformat(),
                })

            for store in DEMO_STORES:
                success = random.random() < 0.95
                rows = random.randint(1500, 6000) if success else 0
                all_records.append({
                    'filename': f'{store}_inventory_{prev_day_str}.csv',
                    'file_type': 'store_inventory',
                    'store_code': store,
                    'file_date': prev_day_str,
                    'status': 'success' if success else 'error',
                    'rows_processed': rows,
                    'rows_rejected': random.randint(0, 3) if success else 0,
                    'file_size': rows * random.randint(60, 90) if success else 0,
                    'error_message': None if success else 'Timeout',
                    'processed_at': day.replace(
                        hour=random.randint(6, 9),
                        minute=random.randint(0, 59),
                    ).isoformat(),
                })

            for wh in DEMO_WAREHOUSES:
                rows = random.randint(4000, 12000)
                all_records.append({
                    'filename': f'{wh}_warehouse_inventory_{prev_day_str}.csv',
                    'file_type': 'warehouse_inventory',
                    'store_code': None,
                    'file_date': prev_day_str,
                    'status': 'success',
                    'rows_processed': rows,
                    'rows_rejected': random.randint(0, 2),
                    'file_size': rows * random.randint(70, 100),
                    'error_message': None,
                    'processed_at': day.replace(
                        hour=random.randint(6, 9),
                        minute=random.randint(0, 59),
                    ).isoformat(),
                })

        all_records.sort(key=lambda x: x['processed_at'], reverse=True)
        return all_records


# Singleton
sftp_service = SFTPService()
