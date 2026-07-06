#!/usr/bin/env python3
"""
===============================================================================
Module      : send_sms.py
Description : SMS Sender Application Entry Point
Version     : 1.0
===============================================================================
"""

import argparse
import sys
import time

from archive import ArchiveManager
from cdr_writer import CDRWriter
from config_loader import ConfigLoader
from logger import Logger
from receiver import Receiver
from sender import Sender
from smpp_client import SMPPClient
from utils import Utils
from validator import Validator


class SMSSenderApplication:
    """
    Main application coordinator.

    Responsibilities:
        - Load configuration
        - Initialize modules
        - Execute SMS workflow
        - Gracefully shutdown
    """

    def __init__(self, config_file):

        #
        # Configuration
        #

        self.config = ConfigLoader(
            config_file
        ).load()

        #
        # Logger
        #

        self.logger = Logger.get_logger(
            self.config
        )

        Utils.print_banner(
            self.logger,
            self.config
        )

        #
        # Components
        #

        self.validator = Validator(
            self.config,
            self.logger
        )

        self.archive = ArchiveManager(
            self.config,
            self.logger
        )

        self.smpp_client = SMPPClient(
            self.config,
            self.logger
        )

        self.sender = Sender(
            self.config,
            self.logger,
            self.smpp_client
        )

        self.cdr_writer = CDRWriter(
            self.config,
            self.logger
        )

        self.receiver = Receiver(
            self.config,
            self.logger,
            self.smpp_client,
            self.sender,
            self.cdr_writer
        )

    # =========================================================================
    # Locate Input File
    # =========================================================================

    def find_input_file(self):

        input_directory = self.config["paths"][
            "input_directory"
        ]

        csv_files = Utils.get_csv_files(
            input_directory
        )

        if not csv_files:

            raise FileNotFoundError(
                f"No CSV files found in {input_directory}"
            )

        #
        # Process oldest file first
        #

        return csv_files[0]

    # =========================================================================
    # Initialize SMPP
    # =========================================================================

    def initialize(self):

        self.logger.info(
            "Initializing SMPP session..."
        )

        if not self.smpp_client.start():

            raise RuntimeError(
                "Unable to connect/bind to SMSC."
            )

        self.smpp_client.start_enquire_link_thread()

        self.receiver.start()

        self.logger.info(
            "Initialization completed."
        )

    # =========================================================================
    # Validate Input
    # =========================================================================

    def validate_input(
        self,
        input_file
    ):

        self.logger.info(
            "Validating input file: %s",
            input_file
        )

        result = self.validator.process(
            input_file
        )

        if not result.success:

            raise RuntimeError(
                "No valid SMS records found."
            )

        return result
        # =========================================================================
    # Send SMS Batch
    # =========================================================================

    def send_messages(
        self,
        validation_result
    ):

        self.logger.info(
            "Starting SMS submission..."
        )

        statistics = self.sender.send(
            validation_result.valid_records
        )

        self.logger.info(
            "SMS submission completed."
        )

        return statistics

    # =========================================================================
    # Wait For Delivery Reports
    # =========================================================================

    def wait_for_delivery_reports(self):

        if not self.config["delivery_report"]["enabled"]:

            self.logger.info(
                "Delivery Report processing disabled."
            )
            return

        timeout = self.config["delivery_report"].get(
            "wait_timeout_seconds",
            300
        )

        self.logger.info(
            "Waiting up to %d seconds for Delivery Reports...",
            timeout
        )

        self.receiver.wait_for_pending(timeout)

    # =========================================================================
    # Finalize Processing
    # =========================================================================

    def finalize(
        self,
        input_file,
        success
    ):

        self.archive.finalize(
            input_file,
            success
        )

    # =========================================================================
    # Main Workflow
    # =========================================================================

    def run(self):

        input_file = None
        success = False

        start_time = time.time()

        try:

            #
            # Locate input CSV
            #

            input_file = self.find_input_file()

            self.logger.info(
                "Input File : %s",
                input_file
            )

            #
            # Initialize SMPP
            #

            self.initialize()

            #
            # Validate CSV
            #

            validation_result = self.validate_input(
                input_file
            )

            #
            # Submit SMS
            #

            statistics = self.send_messages(
                validation_result
            )

            #
            # Wait for DLRs
            #

            self.wait_for_delivery_reports()

            #
            # Print sender summary
            #

            self.sender.print_summary()

            #
            # Print application summary
            #

            statistics.execution_time = (
                time.time() - start_time
            )

            Utils.print_summary(
                self.logger,
                statistics
            )

            success = True

            self.logger.info(
                "Application completed successfully."
            )

            return 0

        except Exception as ex:

            self.logger.exception(
                "Application failed: %s",
                ex
            )

            return 1

        finally:

            if input_file:

                self.finalize(
                    input_file,
                    success
                )

            self.shutdown()
        # =========================================================================
    # Shutdown
    # =========================================================================

    def shutdown(self):
        """
        Gracefully shutdown all components.
        """

        self.logger.info("Starting application shutdown...")

        #
        # Stop receiver first
        #

        try:
            self.receiver.shutdown()
        except Exception as ex:
            self.logger.warning(
                "Receiver shutdown error: %s",
                ex
            )

        #
        # Persist sender state
        #

        try:
            self.sender.shutdown()
        except Exception as ex:
            self.logger.warning(
                "Sender shutdown error: %s",
                ex
            )

        #
        # Stop SMPP
        #

        try:
            self.smpp_client.shutdown()
        except Exception as ex:
            self.logger.warning(
                "SMPP shutdown error: %s",
                ex
            )

        Logger.shutdown()


# =============================================================================
# Main
# =============================================================================

def main():

    parser = argparse.ArgumentParser(
        description="SMPP Batch SMS Sender"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Configuration JSON"
    )

    args = parser.parse_args()

    try:

        app = SMSSenderApplication(
            args.config
        )

        exit_code = app.run()

        return exit_code

    except KeyboardInterrupt:

        print("\nApplication interrupted by user.")

        return 130

    except Exception as ex:

        print(f"Fatal Error : {ex}")

        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":

    sys.exit(main())