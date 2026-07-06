#!/usr/bin/env python3
"""
===============================================================================
Module      : dlr_parser.py
Description : SMPP Delivery Report Parser
Version     : 1.0
===============================================================================
"""

import re
from datetime import datetime

from models import DeliveryReport


class DLRParser:
    """
    Parses SMPP deliver_sm delivery reports into DeliveryReport objects.

    Supports common SMPP DLR formats such as:

    id:12345 sub:001 dlvrd:001 submit date:2507061030
    done date:2507061031 stat:DELIVRD err:000 text:Hello

    and vendor-specific key=value formats.
    """

    PATTERNS = {
        "id": r"id:([^\s]+)",
        "submit_date": r"submit date:([^\s]+)",
        "done_date": r"done date:([^\s]+)",
        "stat": r"stat:([^\s]+)",
        "err": r"err:([^\s]+)"
    }

    def __init__(self, logger=None):
        self.logger = logger

    # =====================================================================
    # Public API
    # =====================================================================

    def parse(self, pdu) -> DeliveryReport:

        short_message = ""

        if hasattr(pdu, "short_message"):

            value = pdu.short_message

            if isinstance(value, bytes):
                short_message = value.decode(
                    "utf-8",
                    errors="ignore"
                )
            else:
                short_message = str(value)

        message_id = self._extract("id", short_message)
        submit_date = self._extract("submit_date", short_message)
        done_date = self._extract("done_date", short_message)
        status = self._extract("stat", short_message)
        error_code = self._extract("err", short_message)

        msisdn = ""

        if hasattr(pdu, "source_addr"):
            msisdn = str(pdu.source_addr)

        report = DeliveryReport(
            message_id=message_id,
            msisdn=msisdn,
            status=status or "UNKNOWN",
            submit_time=self._format_date(submit_date),
            done_time=self._format_date(done_date),
            error_code=error_code or "000",
            description=self.status_description(status),
            raw_pdu=short_message
        )

        if self.logger:
            self.logger.info(
                "DLR Parsed - MessageID=%s Status=%s",
                report.message_id,
                report.status
            )

        return report

    # =====================================================================
    # Helpers
    # =====================================================================

    def _extract(self, key, text):

        pattern = self.PATTERNS.get(key)

        if not pattern:
            return ""

        match = re.search(pattern, text)

        if not match:
            return ""

        return match.group(1)

    def _format_date(self, value):

        if not value:
            return ""

        try:
            dt = datetime.strptime(value, "%y%m%d%H%M")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value

    @staticmethod
    def status_description(status):

        mapping = {
            "DELIVRD": "Delivered",
            "EXPIRED": "Expired",
            "UNDELIV": "Undelivered",
            "REJECTD": "Rejected",
            "ACCEPTD": "Accepted",
            "UNKNOWN": "Unknown",
            "ENROUTE": "Enroute"
        }

        return mapping.get(status, status or "Unknown")