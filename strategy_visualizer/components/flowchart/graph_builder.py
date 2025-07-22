import networkx as nx
from utils.data_models import StrategyAnalysis
from utils.freqtrade_interfaces import FreqtradeInterfaceDefinitions

def create_strategy_graph(strategy: StrategyAnalysis) -> nx.DiGraph:
    """创建策略流程图的网络结构 - 覆盖所有freqtrade接口"""
    G = nx.DiGraph()
    
    # 获取所有freqtrade接口定义
    all_interfaces = FreqtradeInterfaceDefinitions.get_all_interfaces()
    
    # 添加核心流程节点
    core_nodes = [
        ('data_fetch', {
            'label': '数据获取', 
            'type': 'core_process', 
            'description': '从交易所获取OHLCV数据和信息对数据',
            'category': 'data_flow'
        }),
        ('strategy_init', {
            'label': '策略初始化', 
            'type': 'core_process', 
            'description': '初始化策略参数、ROI、止损等配置',
            'category': 'initialization'
        }),
        ('risk_management', {
            'label': '风险管理', 
            'type': 'core_process', 
            'description': '执行止损检查、仓位管理、风险控制',
            'category': 'risk_control'
        }),
        ('order_execution', {
            'label': '订单执行', 
            'type': 'core_process', 
            'description': '向交易所发送订单并跟踪执行状态',
            'category': 'execution'
        })
    ]
    
    # 添加所有策略接口节点
    strategy_nodes = []
    for interface_name, interface_def in all_interfaces.items():
        # 检查策略是否实现了这个接口
        strategy_interface = strategy.interfaces.get(interface_name)
        is_implemented = strategy_interface and strategy_interface.implemented
        
        # 创建节点信息
        node_info = {
            'label': interface_name,
            'type': 'strategy_interface',
            'category': interface_def['category'],
            'description': interface_def['description'],
            'is_implemented': is_implemented,
            'required': interface_def.get('required', False),
            'default_behavior': interface_def['default_behavior'],
            'default_pseudocode': interface_def['default_pseudocode'],
            'input_params': interface_def['input_params'],
            'output': interface_def['output']
        }
        
        # 如果策略实现了接口，添加策略特定信息
        if is_implemented:
            node_info.update({
                'strategy_description': strategy_interface.description,
                'strategy_pseudocode': strategy_interface.pseudocode,
                'strategy_logic': strategy_interface.logic_explanation,
                'strategy_params': strategy_interface.input_params
            })
        
        strategy_nodes.append((interface_name, node_info))
    
    # 合并所有节点
    all_nodes = core_nodes + strategy_nodes
    G.add_nodes_from(all_nodes)
    
    # 定义执行流程的边
    edges = create_execution_flow_edges(all_interfaces, strategy)
    G.add_edges_from(edges)
    
    return G

def create_execution_flow_edges(all_interfaces: dict, strategy: StrategyAnalysis) -> list:
    """创建执行流程的连接边"""
    edges = []
    
    # 基础流程
    edges.extend([
        ('data_fetch', 'informative_pairs'),
        ('informative_pairs', 'strategy_init'),
        ('strategy_init', 'bot_start'),
        ('bot_start', 'bot_loop_start'),
        ('bot_loop_start', 'populate_indicators'),
        ('populate_indicators', 'populate_buy_trend'),
        ('populate_indicators', 'populate_sell_trend'),
    ])
    
    # 买入流程
    edges.extend([
        ('populate_buy_trend', 'confirm_trade_entry'),
        ('confirm_trade_entry', 'leverage'),
        ('leverage', 'risk_management')
    ])
    
    # 卖出流程
    edges.extend([
        ('populate_sell_trend', 'custom_sell'),
        ('custom_sell', 'custom_exit'),
        ('custom_exit', 'confirm_trade_exit'),
        ('confirm_trade_exit', 'risk_management')
    ])
    
    # 风险管理流程
    edges.extend([
        ('risk_management', 'custom_stoploss'),
        ('custom_stoploss', 'adjust_trade_position'),
        ('adjust_trade_position', 'check_buy_timeout'),
        ('check_buy_timeout', 'check_sell_timeout'),
        ('check_sell_timeout', 'order_execution')
    ])
    
    return edges

