import pytest
from logger.logging import Logger

def test_singleton_instance():
    logger1 = Logger()
    logger2 = Logger()
    assert logger1 is logger2, "Logger is not following singleton pattern"

def test_info_logging():
    Logger.delete_instance()
    logger = Logger()
    logger.info("This is an info log.")
    assert "INFO" in logger.get_all_normal_logs()
    assert "This is an info log." in logger.get_all_normal_logs()

def test_warn_logging():
    Logger.delete_instance()
    logger = Logger()
    logger.warn("This is a warning log.")
    assert "WARNING" in logger.get_all_normal_logs()
    assert "This is a warning log." in logger.get_all_normal_logs()

def test_error_logging():
    Logger.delete_instance()
    logger = Logger()
    logger.error("This is an error log.")
    assert "ERROR" in logger.get_all_error_logs()
    assert "This is an error log." in logger.get_all_error_logs()

def test_attention_logging():
    Logger.delete_instance()
    logger = Logger()
    log_message = logger.attention("This is an attention log.", no_session=True)
    assert "ATTENTION" in log_message
    assert "This is an attention log." in log_message

def test_get_all_normal_logs():
    Logger.delete_instance()
    logger = Logger()
    logger.info("First info log.")
    logger.info("Second info log.")
    normal_logs = logger.get_all_normal_logs()
    assert "First info log." in normal_logs
    assert "Second info log." in normal_logs

def test_get_all_error_logs():
    Logger.delete_instance()
    logger = Logger()
    logger.error("First error log.")
    logger.error("Second error log.")
    error_logs = logger.get_all_error_logs()
    assert "First error log." in error_logs
    assert "Second error log." in error_logs

def test_form_log_message():
    log_message = Logger.form_log_message("Test message", "TEST")
    assert "TEST" in log_message
    assert "Test message" in log_message

def test_get_current_time():
    current_time = Logger.get_current_time()
    assert isinstance(current_time, int)
    assert current_time > 0

def test_singleton_reset():
    logger1 = Logger()
    Logger.delete_instance()
    logger2 = Logger()
    assert logger1 is not logger2, "Singleton instance was not reset properly"
