#!/usr/bin/env python3
"""
===============================================================================
Module      : cdr_writer.py
Description : Delivery Report CSV Writer
Version     : 1.0
===============================================================================
"""

import csv
import threading
from pathlib import Path
from datetime import datetime

from models import DeliveryReport


class CDRWriter:
    """
    Writes DeliveryReport objects to a daily CSV file.
    """

    HEADER = [
        "MESSAGE_ID",
        "MSISDN",
        "STATUS",
        "SUBMIT_TIME",
        "DELIVERY_TIME",
        "ERROR_CODE",
        "DESCRIPTION"
    ]

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger

        self.lock = threading.Lock()

        dlr_cfg = config["delivery_report"]
        path_cfg = config["paths"]

        self.directory = path_cfg["delivery_report_directory"]
        self.prefix = dlr_cfg.get("output_file_prefix", "DLR")
        self.delimiter = dlr_cfg.get("delimiter", ",")
        self.write_header = dlr_cfg.get("write_header", True)

        Path(self.directory).mkdir(
            parents=True,
            exist_ok=True
        )

    # =====================================================================
    # Public API
    # =====================================================================

    def write(self, report: DeliveryReport):

        if report is None:
            return

        with self.lock:

            output_file = self._output_file()

            new_file = not Path(output_file).exists()

            with open(
                output_file,
                "a",
                newline="",
                encoding="utf-8"
            ) as fp:

                writer = csv.writer(
                    fp,
                    delimiter=self.delimiter
                )

                if new_file and self.write_header:
                    writer.writerow(self.HEADER)

                writer.writerow([
                    report.message_id,
                    report.msisdn,
                    report.status,
                    report.submit_time,
                    report.done_time,
                    report.error_code,
                    report.description
                ])

                fp.flush()

        self.logger.info(
            "CDR written for Message ID=%s",
            report.message_id
        )

    # =====================================================================
    # Output File
    # =====================================================================

    def _output_file(self):

        filename = "{}_{}.csv".format(
            self.prefix,
            datetime.now().strftime("%Y%m%d")
        )

        return str(
            Path(self.directory) / filename
        )

    # =====================================================================
    # Statistics
    # =====================================================================

    def statistics(self):

        files = list(
            Path(self.directory).glob("*.csv")
        )

        return {
            "files": len(files),
            "directory": self.directory
        }

    # =====================================================================
    # Verify
    # =====================================================================

    def verify(self):

        Path(self.directory).mkdir(
            parents=True,
            exist_ok=True
        )

        self.logger.info(
            "CDR directory verified: %s",
            self.directory
        )


# ============================================================================
# Standalone Test
# ============================================================================

if __name__ == "__main__":

    from config_loader import ConfigLoader
    from logger import Logger

    config = ConfigLoader(
        "conf/config-uat.json"
    ).load()

    logger = Logger.get_logger(config)

    writer = CDRWriter(config, logger)

    report = DeliveryReport(
        message_id="123456789",
        msisdn="255712345678",
        status="DELIVRD",
        submit_time="2026-07-06 10:00:00",
        done_time="2026-07-06 10:00:05",
        error_code="000",
        description="Delivered"
    )

    writer.write(report)

    logger.info(writer.statistics())