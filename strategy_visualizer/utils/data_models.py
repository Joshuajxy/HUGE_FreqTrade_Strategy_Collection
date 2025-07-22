from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class NodeType(Enum):
    FREQTRADE_CORE = "freqtrade_core"
    STRATEGY_INTERFACE = "strategy_interface"
    DECISION = "decision"
    DATA_FLOW = "data_flow"

class ExecutionMode(Enum):
    IDLE = "idle"
    SIMULATION = "simulation"
    BACKTEST = "backtest"

@dataclass
class Parameter:
    name: str
    type: str
    description: str
    example: Optional[Any] = None

@dataclass
class InterfaceImplementation:
    implemented: bool
    description: str
    pseudocode: str
    input_params: List[Parameter]
    output_description: str
    logic_explanation: str

@dataclass
class StrategyAnalysis:
    strategy_name: str
    description: str
    interfaces: Dict[str, InterfaceImplementation]
    indicators: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    buy_conditions: List[Dict[str, Any]]
    sell_conditions: List[Dict[str, Any]]
    risk_management: Dict[str, Any]
    author: Optional[str] = None
    version: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyAnalysis':
        """从字典创建StrategyAnalysis对象"""
        interfaces = {}
        for key, value in data.get('interfaces', {}).items():
            interfaces[key] = InterfaceImplementation(
                implemented=value.get('implemented', False),
                description=value.get('description', ''),
                pseudocode=value.get('pseudocode', ''),
                input_params=[Parameter(**p) for p in value.get('input_params', [])],
                output_description=value.get('output_description', ''),
                logic_explanation=value.get('logic_explanation', '')
            )
        
        return cls(
            strategy_name=data['strategy_name'],
            description=data.get('description', ''),
            interfaces=interfaces,
            indicators=data.get('indicators', []),
            parameters=data.get('parameters', {}),
            buy_conditions=data.get('buy_conditions', []),
            sell_conditions=data.get('sell_conditions', []),
            risk_management=data.get('risk_management', {}),
            author=data.get('author'),
            version=data.get('version')
        )

@dataclass
class Trade:
    id: str
    pair: str
    side: str  # 'buy' or 'sell'
    timestamp: datetime
    price: float
    amount: float
    profit: Optional[float] = None
    reason: str = ""

@dataclass
class BacktestResult:
    strategy_name: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    price_data: Dict[str, List[Any]]  # OHLCV数据
    trades: List[Dict[str, Any]]
    performance: Dict[str, float]
    indicators: Dict[str, List[float]] = field(default_factory=dict)

@dataclass
class ExecutionStep:
    step_id: str
    node_id: str
    timestamp: datetime
    input_data: Any
    output_data: Any
    execution_time_ms: int
    status: str  # 'success' or 'error'

@dataclass
class ExecutionState:
    mode: ExecutionMode
    current_step: str
    execution_history: List[ExecutionStep] = field(default_factory=list)
    current_timestamp: Optional[datetime] = None
    backtest_progress: Optional[Dict[str, Any]] = None