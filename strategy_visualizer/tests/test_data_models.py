import pytest
from utils.data_models import StrategyAnalysis, Parameter, InterfaceImplementation

def test_parameter_creation():
    """测试Parameter数据模型"""
    param = Parameter(
        name="dataframe",
        type="DataFrame",
        description="OHLCV price data"
    )
    
    assert param.name == "dataframe"
    assert param.type == "DataFrame"
    assert param.description == "OHLCV price data"
    assert param.example is None

def test_interface_implementation():
    """测试InterfaceImplementation数据模型"""
    interface = InterfaceImplementation(
        implemented=True,
        description="Test interface",
        pseudocode="test code",
        input_params=[],
        output_description="test output",
        logic_explanation="test logic"
    )
    
    assert interface.implemented is True
    assert interface.description == "Test interface"

def test_strategy_analysis_from_dict():
    """测试StrategyAnalysis.from_dict方法"""
    data = {
        'strategy_name': 'TestStrategy',
        'description': 'Test strategy',
        'interfaces': {
            'populate_indicators': {
                'implemented': True,
                'description': 'Test description',
                'pseudocode': 'test code',
                'input_params': [],
                'output_description': 'test output',
                'logic_explanation': 'test logic'
            }
        },
        'indicators': [],
        'parameters': {'roi': {'0': 0.1}},
        'buy_conditions': [],
        'sell_conditions': [],
        'risk_management': {}
    }
    
    strategy = StrategyAnalysis.from_dict(data)
    
    assert strategy.strategy_name == 'TestStrategy'
    assert 'populate_indicators' in strategy.interfaces
    assert strategy.interfaces['populate_indicators'].implemented is True