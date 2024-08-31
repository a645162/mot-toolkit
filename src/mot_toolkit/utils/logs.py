# -*- coding: utf-8 -*-

import os.path

import loguru

logger = loguru.logger

process_run_dir = os.getcwd()

if process_run_dir.endswith("src"):
    process_run_dir = os.path.dirname(process_run_dir)

log_directory_path = os.path.join(process_run_dir, "logs")

# Convert to an absolute path
log_directory_path = os.path.abspath(log_directory_path)

print("Log:\n" + log_directory_path)
log_file_name = "mot_toolkit_{time}.log"
log_path = os.path.join(log_directory_path, log_file_name)
logger.add(log_path, rotation='00:00', retention='60 days')


def get_logger() -> loguru.logger:
    return logger


if __name__ == "__main__":
    logger.info("mot-toolkit")
    logger.info("Test Log System")
