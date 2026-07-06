#!/usr/bin/env python3
"""
===============================================================================
Module      : archive.py
Description : Archive and File Management
Version     : 1.0
===============================================================================
"""

import os
import shutil
import time
from pathlib import Path

from utils import Utils


class ArchiveManager:
    """
    Handles processed and failed input files.
    """

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        paths = config["paths"]
        processing = config["processing"]

        self.archive_directory = paths["archive_directory"]
        self.failed_directory = paths["failed_directory"]

        self.archive_after_success = processing.get(
            "archive_after_success",
            True
        )

        self.delete_after_archive = processing.get(
            "delete_after_archive",
            False
        )

        self.move_to_failed_on_error = processing.get(
            "move_to_failed_on_error",
            True
        )

        Utils.create_directory(self.archive_directory)
        Utils.create_directory(self.failed_directory)

    # =========================================================================
    # Archive File
    # =========================================================================

    def archive(self, input_file: str):

        if not self.archive_after_success:

            self.logger.info(
                "Archive disabled. Skipping archive."
            )

            return None

        archived = Utils.archive_file(
            input_file,
            self.archive_directory
        )

        self.logger.info(
            "Archived file : %s",
            archived
        )

        if self.delete_after_archive:

            try:

                if os.path.exists(input_file):

                    os.remove(input_file)

            except Exception as ex:

                self.logger.warning(
                    "Unable to delete original file : %s",
                    ex
                )

        return archived

    # =========================================================================
    # Move Failed File
    # =========================================================================

    def move_failed(self, input_file: str):

        if not self.move_to_failed_on_error:

            self.logger.info(
                "Move-to-failed disabled."
            )

            return None

        failed = Utils.move_to_failed(
            input_file,
            self.failed_directory
        )

        self.logger.info(
            "Moved file to failed directory : %s",
            failed
        )

        return failed

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(
        self,
        directory: str,
        retention_days: int
    ):

        if retention_days <= 0:
            return

        cutoff = time.time() - (retention_days * 86400)

        removed = 0

        for item in Path(directory).iterdir():

            if not item.is_file():
                continue

            try:

                if item.stat().st_mtime < cutoff:

                    item.unlink()

                    removed += 1

            except Exception as ex:

                self.logger.warning(
                    "Unable to remove %s : %s",
                    item,
                    ex
                )

        self.logger.info(
            "Cleanup complete. Removed %d files from %s",
            removed,
            directory
        )

    # =========================================================================
    # Statistics
    # =========================================================================

    def statistics(self, directory: str):

        directory = Path(directory)

        if not directory.exists():

            return {
                "files": 0,
                "size_bytes": 0
            }

        total_files = 0
        total_size = 0

        for item in directory.iterdir():

            if item.is_file():

                total_files += 1
                total_size += item.stat().st_size

        return {
            "files": total_files,
            "size_bytes": total_size,
            "size_mb": Utils.bytes_to_mb(total_size)
        }

    # =========================================================================
    # Verify Directories
    # =========================================================================

    def verify(self):

        Utils.create_directory(self.archive_directory)
        Utils.create_directory(self.failed_directory)

        self.logger.info(
            "Archive directories verified."
        )

    # =========================================================================
    # Finalize Processing
    # =========================================================================

    def finalize(
        self,
        input_file: str,
        success: bool
    ):

        if success:

            return self.archive(input_file)

        return self.move_failed(input_file)


# =============================================================================
# Standalone Test
# =============================================================================

if __name__ == "__main__":

    import argparse

    from config_loader import ConfigLoader
    from logger import Logger

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        required=True
    )

    parser.add_argument(
        "--input",
        required=True
    )

    parser.add_argument(
        "--success",
        action="store_true"
    )

    args = parser.parse_args()

    config = ConfigLoader(
        args.config
    ).load()

    logger = Logger.get_logger(config)

    archive = ArchiveManager(
        config,
        logger
    )

    archive.verify()

    archive.finalize(
        args.input,
        args.success
    )

    Logger.shutdown()