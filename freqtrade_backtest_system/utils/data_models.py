"""
Core data model definitions
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
from pathlib import Path
import json
import pickle

class ExecutionStatus(Enum):
    """Execution status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class ExecutionMode(Enum):
    """Execution mode enumeration"""
    BACKTEST = "backtest"
    DRY_RUN = "dry_run"

@dataclass
class StrategyInfo:
    """Strategy information data class"""
    name: str
    file_path: Path
    description: str
    author: Optional[str] = None
    version: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    def __post_init__(self):
        """Post processing, ensure file_path is Path object"""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['file_path'] = str(self.file_path)
        if self.last_modified:
            data['last_modified'] = self.last_modified.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyInfo':
        """Create object from dictionary"""
        if 'last_modified' in data and data['last_modified']:
            data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        return cls(**data)

@dataclass
class BacktestConfig:
    """Backtest configuration data class"""
    start_date: date
    end_date: date
    timeframe: str
    pairs: List[str]
    initial_balance: float
    max_open_trades: int
    fee: float = 0.001
    enable_position_stacking: bool = False
    stake_amount: str = "unlimited"
    dry_run_wallet: float = 1000.0
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be earlier than end date")
        
        if self.initial_balance <= 0:
            raise ValueError("Initial balance must be greater than 0")
        
        if self.max_open_trades <= 0:
            raise ValueError("Max open trades must be greater than 0")
        
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
        if self.timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {self.timeframe}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """Create object from dictionary"""
        data['start_date'] = date.fromisoformat(data['start_date'])
        data['end_date'] = date.fromisoformat(data['end_date'])
        return cls(**data)
    
    def to_freqtrade_config(self, strategy_name: str) -> Dict[str, Any]:
        """Convert to freqtrade configuration format"""
        return {
            "strategy": strategy_name,
            "timeframe": self.timeframe,
            "timerange": f"{self.start_date.strftime('%Y%m%d')}-{self.end_date.strftime('%Y%m%d')}",
            "stake_currency": "USDT",
            "stake_amount": self.stake_amount,
            "dry_run": True,
            "dry_run_wallet": self.dry_run_wallet,
            "max_open_trades": self.max_open_trades,
            "exchange": {
                "name": "binance",
                "pair_whitelist": self.pairs,
                "ccxt_config": {},
                "ccxt_async_config": {}
            },
            "fee": self.fee,
            "enable_position_stacking": self.enable_position_stacking
        }

@dataclass
class TradeRecord:
    """Trade record data class"""
    pair: str
    side: str  # 'buy' or 'sell'
    timestamp: datetime
    price: float
    amount: float
    profit: Optional[float] = None
    profit_pct: Optional[float] = None
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeRecord':
        """Create object from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    total_return: float = 0.0
    total_return_pct: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_profit: float = 0.0
    avg_profit_pct: float = 0.0
    avg_duration: float = 0.0
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.max_drawdown != 0:
            self.calmar_ratio = self.total_return / abs(self.max_drawdown)

@dataclass
class BacktestResult:
    """Backtest result data class"""
    strategy_name: str
    config: BacktestConfig
    metrics: PerformanceMetrics
    trades: List[TradeRecord]
    timestamp: datetime
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    
    def __post_init__(self):
        """Post processing"""
        if isinstance(self.status, str):
            self.status = ExecutionStatus(self.status)
    
    def is_successful(self) -> bool:
        """Check if backtest was successful"""
        return self.status == ExecutionStatus.COMPLETED and self.error_message is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'strategy_name': self.strategy_name,
            'config': self.config.to_dict(),
            'metrics': asdict(self.metrics),
            'trades': [trade.to_dict() for trade in self.trades],
            'timestamp': self.timestamp.isoformat(),
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create object from dictionary"""
        return cls(
            strategy_name=data['strategy_name'],
            config=BacktestConfig.from_dict(data['config']),
            metrics=PerformanceMetrics(**data['metrics']),
            trades=[TradeRecord.from_dict(trade) for trade in data['trades']],
            timestamp=datetime.fromisoformat(data['timestamp']),
            execution_time=data.get('execution_time'),
            error_message=data.get('error_message'),
            status=ExecutionStatus(data['status'])
        )
    
    def save_to_file(self, file_path: Path):
        """Save to file"""
        if file_path.suffix == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        elif file_path.suffix == '.pkl':
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'BacktestResult':
        """Load from file"""
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls.from_dict(data)
        elif file_path.suffix == '.pkl':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

@dataclass
class ComparisonResult:
    """Comparison result data class"""
    strategies: List[str]
    metrics_comparison: Dict[str, List[float]]
    rankings: Dict[str, int]
    best_strategy: str
    comparison_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'strategies': self.strategies,
            'metrics_comparison': self.metrics_comparison,
            'rankings': self.rankings,
            'best_strategy': self.best_strategy,
            'comparison_timestamp': self.comparison_timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComparisonResult':
        """Create object from dictionary"""
        data['comparison_timestamp'] = datetime.fromisoformat(data['comparison_timestamp'])
        return cls(**data)

@dataclass
class DryRunStatus:
    """Dry Run status data class"""
    run_id: str
    strategy: str
    status: ExecutionStatus
    start_time: datetime
    last_update: datetime
    signals_count: int = 0
    current_balance: float = 0.0
    current_profit: float = 0.0
    open_trades: int = 0
    # New fields for real-time monitoring
    latest_log_line: str = ""
    trade_signals: List[Dict] = field(default_factory=list) # To store parsed trade signals
    balance_history: List[Dict] = field(default_factory=list) # To store balance snapshots
    # Add more fields as needed for detailed monitoring
    
    def __post_init__(self):
        """Post processing"""
        if isinstance(self.status, str):
            self.status = ExecutionStatus(self.status)
    
    def update_status(self, new_status: ExecutionStatus):
        """Update status"""
        self.status = new_status
        self.last_update = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'run_id': self.run_id,
            'strategy': self.strategy,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'last_update': self.last_update.isoformat(),
            'signals_count': self.signals_count,
            'current_balance': self.current_balance,
            'current_profit': self.current_profit,
            'open_trades': self.open_trades
        }

@dataclass
class NotebookTemplate:
    """Notebook template data class"""
    name: str
    description: str
    file_path: Path
    parameters: List[str]
    template_type: str  # 'single_strategy', 'comparison', 'custom'
    
    def __post_init__(self):
        """Post processing"""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'file_path': str(self.file_path),
            'parameters': self.parameters,
            'template_type': self.template_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotebookTemplate':
        """Create object from dictionary"""
        return cls(**data)

# Constants definition
DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
DEFAULT_PAIRS = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT"]
DEFAULT_STAKE_AMOUNTS = ["unlimited", "10", "50", "100", "500", "1000"]

# Performance metrics weight configuration
METRIC_WEIGHTS = {
    'total_return': 0.3,
    'win_rate': 0.2,
    'max_drawdown': 0.2,
    'sharpe_ratio': 0.15,
    'total_trades': 0.1,
    'avg_duration': 0.05
}