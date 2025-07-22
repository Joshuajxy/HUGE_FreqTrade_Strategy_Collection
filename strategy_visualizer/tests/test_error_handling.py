import pytest
import json
from io import StringIO
from utils.error_handling import FileLoadError, BacktestError, validate_strategy_analysis

def test_file_load_error():
    """测试FileLoadError异常"""
    error = FileLoadError("Test error", "test.json")
    
    assert error.message == "Test error"
    assert error.filename == "test.json"
    assert str(error) == "Test error: test.json"

def test_backtest_error():
    """测试BacktestError异常"""
    error = BacktestError("Test backtest error", "TEST_CODE")
    
    assert error.message == "Test backtest error"
    assert error.code == "TEST_CODE"

def test_validate_strategy_analysis_valid():
    """测试有效的策略分析数据验证"""
    valid_data = {
        'strategy_name': 'TestStrategy',
        'interfaces': {},
        'parameters': {}
    }
    
    # 应该不抛出异常
    validate_strategy_analysis(valid_data)

def test_validate_strategy_analysis_invalid():
    """测试无效的策略分析数据验证"""
    invalid_data = {
        'strategy_name': 'TestStrategy'
        # 缺少必要字段
    }
    
    with pytest.raises(KeyError):
        validate_strategy_analysis(invalid_data)