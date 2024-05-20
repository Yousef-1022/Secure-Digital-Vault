import pytest
from logger.logging import LogSession

def test_add_and_get_normal_logs():
    log_session = LogSession()
    log_session.add_normal_log("INFO: This is an info log.")
    log_session.add_normal_log("WARN: This is a warning log.")
    normal_logs = log_session.get_normal_logs()
    assert normal_logs == "INFO: This is an info log.\nWARN: This is a warning log.\n"

def test_add_and_get_error_logs():
    log_session = LogSession()
    log_session.add_error_log("ERROR: This is an error log.")
    log_session.add_error_log("ERROR: This is another error log.")
    error_logs = log_session.get_error_logs()
    assert error_logs == "ERROR: This is an error log.\nERROR: This is another error log.\n"

def test_empty_logs():
    log_session = LogSession()
    assert log_session.get_normal_logs() == ""
    assert log_session.get_error_logs() == ""
