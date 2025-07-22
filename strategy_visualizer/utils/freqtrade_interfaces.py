# freqtrade接口定义和默认实现
from typing import Dict, Any, List

class FreqtradeInterfaceDefinitions:
    """Freqtrade IStrategy基类的所有标准接口定义"""
    
    @staticmethod
    def get_all_interfaces() -> Dict[str, Dict[str, Any]]:
        """获取所有freqtrade标准接口的定义"""
        return {
            # 核心策略接口
            'populate_indicators': {
                'category': 'core',
                'description': '计算技术指标，为买入/卖出信号提供数据基础',
                'default_behavior': '返回原始DataFrame，不添加任何指标',
                'default_pseudocode': '''
def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    默认实现：直接返回原始数据框，不计算任何指标
    """
    return dataframe
                ''',
                'input_params': ['dataframe: DataFrame', 'metadata: dict'],
                'output': 'DataFrame with indicators',
                'required': True
            },
            
            'populate_buy_trend': {
                'category': 'core', 
                'description': '生成买入信号，标记何时应该买入',
                'default_behavior': '所有行的buy列设为0，即不产生任何买入信号',
                'default_pseudocode': '''
def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    默认实现：不产生任何买入信号
    """
    dataframe.loc[:, 'buy'] = 0
    return dataframe
                ''',
                'input_params': ['dataframe: DataFrame', 'metadata: dict'],
                'output': 'DataFrame with buy signals',
                'required': True
            },
            
            'populate_sell_trend': {
                'category': 'core',
                'description': '生成卖出信号，标记何时应该卖出',
                'default_behavior': '所有行的sell列设为0，即不产生任何卖出信号',
                'default_pseudocode': '''
def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    默认实现：不产生任何卖出信号
    """
    dataframe.loc[:, 'sell'] = 0
    return dataframe
                ''',
                'input_params': ['dataframe: DataFrame', 'metadata: dict'],
                'output': 'DataFrame with sell signals',
                'required': True
            },
            
            # 高级策略接口
            'custom_stoploss': {
                'category': 'advanced',
                'description': '自定义止损逻辑，可以实现动态止损',
                'default_behavior': '返回None，使用策略配置的固定止损',
                'default_pseudocode': '''
def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, 
                   current_rate: float, current_profit: float, **kwargs) -> float:
    """
    默认实现：不使用自定义止损，返回None使用固定止损
    """
    return None
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'current_time: datetime', 'current_rate: float', 'current_profit: float'],
                'output': 'float or None',
                'required': False
            },
            
            'custom_sell': {
                'category': 'advanced',
                'description': '自定义卖出逻辑，可以覆盖标准卖出信号',
                'default_behavior': '返回None，使用populate_sell_trend的信号',
                'default_pseudocode': '''
def custom_sell(self, pair: str, trade: Trade, current_time: datetime,
               current_rate: float, current_profit: float, **kwargs) -> Optional[str]:
    """
    默认实现：不使用自定义卖出，返回None
    """
    return None
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'current_time: datetime', 'current_rate: float', 'current_profit: float'],
                'output': 'Optional[str]',
                'required': False
            },
            
            'custom_exit': {
                'category': 'advanced',
                'description': '自定义退出逻辑，新版本替代custom_sell',
                'default_behavior': '返回None，使用标准退出逻辑',
                'default_pseudocode': '''
def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
               current_rate: float, current_profit: float, **kwargs) -> Optional[str]:
    """
    默认实现：不使用自定义退出，返回None
    """
    return None
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'current_time: datetime', 'current_rate: float', 'current_profit: float'],
                'output': 'Optional[str]',
                'required': False
            },
            
            # 确认接口
            'confirm_trade_entry': {
                'category': 'confirmation',
                'description': '确认交易入场，可以在最后时刻取消买入',
                'default_behavior': '返回True，确认所有买入信号',
                'default_pseudocode': '''
def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                       rate: float, time_in_force: str, current_time: datetime,
                       entry_tag: Optional[str], **kwargs) -> bool:
    """
    默认实现：确认所有交易入场
    """
    return True
                ''',
                'input_params': ['pair: str', 'order_type: str', 'amount: float', 'rate: float', 'time_in_force: str', 'current_time: datetime', 'entry_tag: Optional[str]'],
                'output': 'bool',
                'required': False
            },
            
            'confirm_trade_exit': {
                'category': 'confirmation',
                'description': '确认交易退出，可以在最后时刻取消卖出',
                'default_behavior': '返回True，确认所有卖出信号',
                'default_pseudocode': '''
def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str,
                      amount: float, rate: float, time_in_force: str,
                      exit_reason: str, current_time: datetime, **kwargs) -> bool:
    """
    默认实现：确认所有交易退出
    """
    return True
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'order_type: str', 'amount: float', 'rate: float', 'time_in_force: str', 'exit_reason: str', 'current_time: datetime'],
                'output': 'bool',
                'required': False
            },
            
            # 杠杆和仓位管理
            'leverage': {
                'category': 'position',
                'description': '设置交易杠杆倍数',
                'default_behavior': '返回1.0，不使用杠杆',
                'default_pseudocode': '''
def leverage(self, pair: str, current_time: datetime, current_rate: float,
            proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
    """
    默认实现：不使用杠杆，返回1.0
    """
    return 1.0
                ''',
                'input_params': ['pair: str', 'current_time: datetime', 'current_rate: float', 'proposed_leverage: float', 'max_leverage: float', 'side: str'],
                'output': 'float',
                'required': False
            },
            
            'adjust_trade_position': {
                'category': 'position',
                'description': '调整现有交易仓位，实现加仓或减仓',
                'default_behavior': '返回None，不调整仓位',
                'default_pseudocode': '''
def adjust_trade_position(self, trade: Trade, current_time: datetime,
                         current_rate: float, current_profit: float,
                         min_stake: Optional[float], max_stake: float, **kwargs) -> Optional[float]:
    """
    默认实现：不调整交易仓位
    """
    return None
                ''',
                'input_params': ['trade: Trade', 'current_time: datetime', 'current_rate: float', 'current_profit: float', 'min_stake: Optional[float]', 'max_stake: float'],
                'output': 'Optional[float]',
                'required': False
            },
            
            # 信息获取接口
            'informative_pairs': {
                'category': 'data',
                'description': '定义需要额外获取的信息对数据',
                'default_behavior': '返回空列表，不获取额外数据',
                'default_pseudocode': '''
def informative_pairs(self) -> List[Tuple[str, str]]:
    """
    默认实现：不获取额外的信息对数据
    """
    return []
                ''',
                'input_params': [],
                'output': 'List[Tuple[str, str]]',
                'required': False
            },
            
            # 生命周期接口
            'bot_start': {
                'category': 'lifecycle',
                'description': '机器人启动时调用，用于初始化',
                'default_behavior': '什么都不做',
                'default_pseudocode': '''
def bot_start(self, **kwargs) -> None:
    """
    默认实现：机器人启动时不执行任何操作
    """
    pass
                ''',
                'input_params': [],
                'output': 'None',
                'required': False
            },
            
            'bot_loop_start': {
                'category': 'lifecycle',
                'description': '每个交易循环开始时调用',
                'default_behavior': '什么都不做',
                'default_pseudocode': '''
def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
    """
    默认实现：每个循环开始时不执行任何操作
    """
    pass
                ''',
                'input_params': ['current_time: datetime'],
                'output': 'None',
                'required': False
            },
            
            # 超时检查接口
            'check_buy_timeout': {
                'category': 'timeout',
                'description': '检查买入订单是否超时',
                'default_behavior': '返回False，不取消超时订单',
                'default_pseudocode': '''
def check_buy_timeout(self, pair: str, trade: Trade, order: dict,
                     current_time: datetime, **kwargs) -> bool:
    """
    默认实现：不取消超时的买入订单
    """
    return False
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'order: dict', 'current_time: datetime'],
                'output': 'bool',
                'required': False
            },
            
            'check_sell_timeout': {
                'category': 'timeout',
                'description': '检查卖出订单是否超时',
                'default_behavior': '返回False，不取消超时订单',
                'default_pseudocode': '''
def check_sell_timeout(self, pair: str, trade: Trade, order: dict,
                      current_time: datetime, **kwargs) -> bool:
    """
    默认实现：不取消超时的卖出订单
    """
    return False
                ''',
                'input_params': ['pair: str', 'trade: Trade', 'order: dict', 'current_time: datetime'],
                'output': 'bool',
                'required': False
            }
        }
    
    @staticmethod
    def get_interface_categories() -> Dict[str, Dict[str, str]]:
        """获取接口分类信息"""
        return {
            'core': {
                'name': '核心接口',
                'color': '#4CAF50',
                'description': '策略必须实现的核心接口'
            },
            'advanced': {
                'name': '高级接口', 
                'color': '#FF9800',
                'description': '可选的高级功能接口'
            },
            'confirmation': {
                'name': '确认接口',
                'color': '#2196F3', 
                'description': '交易确认相关接口'
            },
            'position': {
                'name': '仓位管理',
                'color': '#9C27B0',
                'description': '杠杆和仓位调整接口'
            },
            'data': {
                'name': '数据获取',
                'color': '#00BCD4',
                'description': '数据获取相关接口'
            },
            'lifecycle': {
                'name': '生命周期',
                'color': '#795548',
                'description': '机器人生命周期接口'
            },
            'timeout': {
                'name': '超时处理',
                'color': '#F44336',
                'description': '订单超时处理接口'
            }
        }