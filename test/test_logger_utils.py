import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentium.utils.logger_utils import LoggerUtils, LoggerConfig

def test_logger_utils():
    print("=== Testing LoggerUtils ===")
    
    # 1. Configuration
    config = LoggerConfig(level="INFO", enable_console=True)
    LoggerUtils.configure(config)
    
    logger = LoggerUtils.get_logger("AgentiumTestLogger")
    logger.info("Test logging message at INFO level")
    logger.warning("Test logging message at WARNING level")
    
    # 2. Test @log_operation decorator
    @LoggerUtils.log_operation("test_timed_op")
    def dummy_timed_operation(x, y):
        return x + y
        
    calc_res = dummy_timed_operation(15, 27)
    print("Calculation Result with @log_operation:", calc_res)
    assert calc_res == 42, "Decorator interfered with function result"

    print("Result: PASS\n")

if __name__ == "__main__":
    test_logger_utils()
