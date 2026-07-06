#!/usr/bin/env python3
"""
===============================================================================
Module      : utils.py
Description : Common Utility Functions
Version     : 1.0
===============================================================================
"""

import os
import csv
import time
import socket
import shutil
import hashlib
import fcntl
from pathlib import Path
from datetime import datetime
from typing import List


class Utils:
    """
    Common utility methods used across the application.
    """

    # =========================================================================
    # Date & Time
    # =========================================================================

    @staticmethod
    def current_datetime() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def current_timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def current_date() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    # =========================================================================
    # Host Information
    # =========================================================================

    @staticmethod
    def hostname() -> str:
        return socket.gethostname()

    @staticmethod
    def process_id() -> int:
        return os.getpid()

    # =========================================================================
    # Directory Operations
    # =========================================================================

    @staticmethod
    def create_directory(path: str):

        Path(path).mkdir(
            parents=True,
            exist_ok=True
        )

    @staticmethod
    def ensure_directories(config):

        paths = config["paths"]

        Utils.create_directory(paths["input_directory"])
        Utils.create_directory(paths["archive_directory"])
        Utils.create_directory(paths["failed_directory"])
        Utils.create_directory(paths["delivery_report_directory"])
        Utils.create_directory(paths["log_directory"])

    # =========================================================================
    # File Operations
    # =========================================================================

    @staticmethod
    def file_exists(file_path: str) -> bool:

        return Path(file_path).is_file()

    @staticmethod
    def directory_exists(directory: str) -> bool:

        return Path(directory).is_dir()

    @staticmethod
    def is_file_empty(file_path: str) -> bool:

        return os.path.getsize(file_path) == 0

    @staticmethod
    def file_size(file_path: str) -> int:

        return os.path.getsize(file_path)

    @staticmethod
    def bytes_to_mb(size: int) -> float:

        return round(size / (1024 * 1024), 2)

    @staticmethod
    def unique_filename(filename: str) -> str:

        return "{}_{}_{}_{}".format(
            Utils.current_timestamp(),
            Utils.hostname(),
            Utils.process_id(),
            filename
        )

    # =========================================================================
    # Atomic File Move
    # =========================================================================

    @staticmethod
    def atomic_move(source: str, destination: str):

        destination = Path(destination)

        Utils.create_directory(destination.parent)

        os.replace(source, destination)

        return str(destination)

    # =========================================================================
    # File Locking (Linux)
    # =========================================================================

    @staticmethod
    def lock_file(file_handle):

        fcntl.flock(
            file_handle,
            fcntl.LOCK_EX
        )

    @staticmethod
    def unlock_file(file_handle):

        fcntl.flock(
            file_handle,
            fcntl.LOCK_UN
        )

    # =========================================================================
    # CSV Discovery
    # =========================================================================

    @staticmethod
    def get_csv_files(directory: str) -> List[str]:

        directory = Path(directory)

        if not directory.exists():
            return []

        files = list(directory.glob("*.csv"))

        files.sort(
            key=lambda f: f.stat().st_mtime
        )

        return [str(f) for f in files]

    @staticmethod
    def csv_record_count(file_path: str) -> int:

        count = 0

        with open(file_path, newline="", encoding="utf-8") as fp:

            reader = csv.reader(fp)

            next(reader, None)

            for _ in reader:
                count += 1

        return count
            # =========================================================================
    # SHA256
    # =========================================================================

    @staticmethod
    def sha256(file_path: str) -> str:

        sha = hashlib.sha256()

        with open(file_path, "rb") as fp:

            while True:

                chunk = fp.read(8192)

                if not chunk:
                    break

                sha.update(chunk)

        return sha.hexdigest()

    # =========================================================================
    # Archive Helpers
    # =========================================================================

    @staticmethod
    def archive_file(source_file: str, archive_directory: str) -> str:

        Utils.create_directory(archive_directory)

        filename = Utils.unique_filename(
            Path(source_file).name
        )

        destination = Path(archive_directory) / filename

        return Utils.atomic_move(
            source_file,
            str(destination)
        )

    @staticmethod
    def move_to_failed(source_file: str,
                       failed_directory: str) -> str:

        Utils.create_directory(failed_directory)

        filename = Utils.unique_filename(
            Path(source_file).name
        )

        destination = Path(failed_directory) / filename

        return Utils.atomic_move(
            source_file,
            str(destination)
        )

    @staticmethod
    def copy_file(source: str,
                  destination_directory: str) -> str:

        Utils.create_directory(destination_directory)

        filename = Utils.unique_filename(
            Path(source).name
        )

        destination = Path(destination_directory) / filename

        shutil.copy2(source, destination)

        return str(destination)

    @staticmethod
    def delete_file(file_path: str):

        if Path(file_path).exists():

            Path(file_path).unlink()

    # =========================================================================
    # Disk Usage
    # =========================================================================

    @staticmethod
    def disk_usage(path: str):

        usage = shutil.disk_usage(path)

        return {

            "total": usage.total,

            "used": usage.used,

            "free": usage.free
        }

    @staticmethod
    def free_disk_space_mb(path: str):

        usage = shutil.disk_usage(path)

        return round(
            usage.free / (1024 * 1024),
            2
        )

    # =========================================================================
    # Timer
    # =========================================================================

    @staticmethod
    def execution_time(start_time: float) -> float:

        return round(
            time.time() - start_time,
            2
        )

    @staticmethod
    def wait(seconds: int):

        time.sleep(seconds)

    # =========================================================================
    # File Information
    # =========================================================================

    @staticmethod
    def file_extension(file_path: str) -> str:

        return Path(file_path).suffix

    @staticmethod
    def file_name(file_path: str) -> str:

        return Path(file_path).name

    @staticmethod
    def absolute_path(file_path: str) -> str:

        return str(
            Path(file_path).resolve()
        )

    # =========================================================================
    # CSV Utilities
    # =========================================================================

    @staticmethod
    def write_csv(file_path,
                  header,
                  rows):

        Utils.create_directory(
            Path(file_path).parent
        )

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as fp:

            writer = csv.writer(fp)

            writer.writerow(header)

            writer.writerows(rows)

    @staticmethod
    def append_csv(file_path,
                   row):

        file_exists = Path(file_path).exists()

        with open(
            file_path,
            "a",
            newline="",
            encoding="utf-8"
        ) as fp:

            writer = csv.writer(fp)

            if not file_exists:
                pass

            writer.writerow(row)
            # =========================================================================
    # Application Banner
    # =========================================================================

    @staticmethod
    def print_banner(logger, config):

        app = config["application"]

        logger.info("=" * 80)
        logger.info("Application : %s", app["name"])
        logger.info("Version     : %s", app["version"])
        logger.info("Environment : %s", app["environment"])
        logger.info("Hostname    : %s", Utils.hostname())
        logger.info("Process ID  : %s", Utils.process_id())
        logger.info("Start Time  : %s", Utils.current_datetime())
        logger.info("=" * 80)

    # =========================================================================
    # Execution Summary
    # =========================================================================

    @staticmethod
    def print_summary(logger, statistics):

        logger.info("=" * 80)
        logger.info("Execution Summary")
        logger.info("=" * 80)
        logger.info("Total Records      : %d", statistics.total_records)
        logger.info("Submitted          : %d", statistics.submitted_records)
        logger.info("Delivered          : %d", statistics.delivered_records)
        logger.info("Failed             : %d", statistics.failed_records)
        logger.info("Invalid            : %d", statistics.invalid_records)
        logger.info("SMS Parts          : %d", statistics.total_sms_parts)
        logger.info("Execution Time     : %.2f Seconds", statistics.execution_time)
        logger.info("=" * 80)

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    @staticmethod
    def separator(length: int = 80,
                  character: str = "-") -> str:

        return character * length

    @staticmethod
    def safe_str(value) -> str:

        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def is_blank(value) -> bool:

        return Utils.safe_str(value) == ""

    # =========================================================================
    # Retry Helper
    # =========================================================================

    @staticmethod
    def retry(operation,
              retries=3,
              delay=1,
              logger=None):

        last_exception = None

        for attempt in range(1, retries + 1):

            try:

                return operation()

            except Exception as ex:

                last_exception = ex

                if logger:

                    logger.warning(
                        "Retry %d/%d failed : %s",
                        attempt,
                        retries,
                        ex
                    )

                if attempt < retries:

                    time.sleep(delay)

        raise last_exception

    # =========================================================================
    # Environment
    # =========================================================================

    @staticmethod
    def environment(config):

        return config["application"]["environment"]

    @staticmethod
    def application_name(config):

        return config["application"]["name"]

    # =========================================================================
    # Cleanup
    # =========================================================================

    @staticmethod
    def cleanup_old_files(directory,
                          retention_days):

        if retention_days <= 0:
            return

        cutoff = time.time() - (retention_days * 86400)

        directory = Path(directory)

        if not directory.exists():
            return

        for item in directory.iterdir():

            if item.is_file():

                try:

                    if item.stat().st_mtime < cutoff:

                        item.unlink()

                except Exception:
                    pass