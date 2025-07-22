import streamlit as st
from typing import Dict, Any
from utils.data_models import StrategyAnalysis
from utils.freqtrade_interfaces import FreqtradeInterfaceDefinitions
from .node_details import show_node_details

def handle_node_selection(selection: Dict[str, Any], strategy: StrategyAnalysis):
    """处理节点选择事件 - 支持所有freqtrade接口"""
    if not selection or not selection.get('points'):
        return
    
    # 获取选中的节点信息
    point = selection['points'][0]
    
    # 从点击的坐标推断节点
    if 'x' in point and 'y' in point:
        clicked_x = point['x']
        clicked_y = point['y']
        
        # 根据坐标映射到节点
        node_id = map_coordinates_to_node(clicked_x, clicked_y)
        
        if node_id:
            # 存储选中的节点
            st.session_state.selected_node = node_id
            show_node_details(node_id, strategy)
    
    # 如果有pointIndex，也尝试使用
    elif 'pointIndex' in point:
        node_index = point['pointIndex']
        all_interfaces = FreqtradeInterfaceDefinitions.get_all_interfaces()
        all_nodes = ['data_fetch', 'informative_pairs', 'strategy_init', 'bot_start', 
                    'bot_loop_start', 'populate_indicators', 'populate_buy_trend', 
                    'populate_sell_trend', 'confirm_trade_entry', 'custom_sell', 
                    'custom_exit', 'confirm_trade_exit', 'leverage', 'risk_management',
                    'custom_stoploss', 'adjust_trade_position', 'check_buy_timeout',
                    'check_sell_timeout', 'order_execution']
        
        if 0 <= node_index < len(all_nodes):
            node_id = all_nodes[node_index]
            st.session_state.selected_node = node_id
            show_node_details(node_id, strategy)

def map_coordinates_to_node(x: float, y: float) -> str:
    """根据坐标映射到节点ID - 支持所有接口节点"""
    # 定义节点位置映射（与plotly_renderer中的布局对应）
    node_positions = {
        'data_fetch': (0, 0),
        'informative_pairs': (0, 120),
        'strategy_init': (-200, 240),
        'bot_start': (200, 240),
        'bot_loop_start': (0, 360),
        'populate_indicators': (0, 480),
        'populate_buy_trend': (-200, 600),
        'populate_sell_trend': (200, 600),
        'confirm_trade_entry': (-400, 720),
        'custom_sell': (-133, 720),
        'custom_exit': (133, 720),
        'confirm_trade_exit': (400, 720),
        'leverage': (-100, 840),
        'risk_management': (100, 840),
        'custom_stoploss': (-100, 960),
        'adjust_trade_position': (100, 960),
        'check_buy_timeout': (-100, 1080),
        'check_sell_timeout': (100, 1080),
        'order_execution': (0, 1200)
    }
    
    # 找到最接近的节点
    min_distance = float('inf')
    closest_node = None
    
    for node_id, (node_x, node_y) in node_positions.items():
        distance = ((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_node = node_id
    
    # 如果距离太远，认为没有点击到节点
    if min_distance > 150:  # 增加容错范围
        return None
    
    return closest_node

def handle_node_click(node_id: str, strategy: StrategyAnalysis):
    """处理节点点击事件"""
    # 存储当前选中的节点
    st.session_state.selected_node = node_id
    
    # 显示节点详情
    show_node_details(node_id, strategy)

def get_selected_node() -> str:
    """获取当前选中的节点"""
    return st.session_state.get('selected_node', None)

def clear_selection():
    """清除节点选择"""
    if 'selected_node' in st.session_state:
        del st.session_state.selected_node