import streamlit as st
from utils.data_models import StrategyAnalysis
from utils.freqtrade_interfaces import FreqtradeInterfaceDefinitions

def show_node_details(node_name: str, strategy: StrategyAnalysis):
    """显示节点详细信息 - 支持所有freqtrade接口"""
    
    # 获取所有接口定义
    all_interfaces = FreqtradeInterfaceDefinitions.get_all_interfaces()
    
    with st.expander(f"📋 {node_name} 详细信息", expanded=True):
        if node_name in all_interfaces:
            show_strategy_interface_details(node_name, strategy, all_interfaces[node_name])
        else:
            show_core_process_details(node_name)

def show_strategy_interface_details(node_name: str, strategy: StrategyAnalysis, interface_def: dict):
    """显示策略接口节点详情 - 包括默认实现"""
    
    # 检查策略是否实现了这个接口
    strategy_interface = strategy.interfaces.get(node_name)
    is_implemented = strategy_interface and strategy_interface.implemented
    
    # 显示接口基本信息
    st.write("**接口名称:**", node_name)
    st.write("**接口分类:**", interface_def['category'].upper())
    st.write("**是否必需:**", "✅ 是" if interface_def.get('required', False) else "❌ 否")
    
    # 显示实现状态
    if is_implemented:
        st.success("✅ 该接口已在当前策略中实现")
        
        # 显示策略特定实现
        st.write("**策略实现描述:**")
        st.write(strategy_interface.description or "无描述")
        
        if strategy_interface.logic_explanation:
            st.write("**实现逻辑:**")
            st.write(strategy_interface.logic_explanation)
        
        if strategy_interface.pseudocode:
            st.write("**策略伪代码:**")
            st.code(strategy_interface.pseudocode, language='python')
        
        # 显示输入参数
        if strategy_interface.input_params:
            st.write("**输入参数:**")
            for param in strategy_interface.input_params:
                st.write(f"- **{param.name}** ({param.type}): {param.description}")
    
    else:
        st.warning("🔧 该接口未实现，使用freqtrade默认行为")
        
        # 显示默认实现信息
        st.write("**默认行为:**")
        st.write(interface_def['default_behavior'])
        
        st.write("**默认实现伪代码:**")
        st.code(interface_def['default_pseudocode'], language='python')
    
    # 显示接口通用信息
    st.write("**接口描述:**")
    st.write(interface_def['description'])
    
    st.write("**标准输入参数:**")
    for param in interface_def['input_params']:
        st.write(f"- {param}")
    
    st.write("**返回值:**")
    st.write(interface_def['output'])
    
    # 显示使用建议
    if not is_implemented:
        st.info("💡 **实现建议:** 如果需要自定义此接口的行为，可以在策略类中重写此方法。")

def show_core_process_details(node_name: str):
    """显示核心流程节点详情"""
    core_processes = {
        'data_fetch': {
            'description': '从交易所获取OHLCV历史数据和实时数据',
            'details': '''
            这是freqtrade的核心数据获取流程：
            1. 连接到配置的交易所API
            2. 获取指定交易对的OHLCV数据
            3. 获取informative_pairs定义的额外数据
            4. 数据预处理和格式化
            5. 传递给策略进行分析
            ''',
            'responsibility': 'Freqtrade核心引擎负责'
        },
        'strategy_init': {
            'description': '初始化策略参数、ROI设置、止损设置等',
            'details': '''
            策略初始化流程：
            1. 加载策略配置参数
            2. 设置ROI（投资回报率）表
            3. 配置止损参数
            4. 初始化技术指标参数
            5. 调用bot_start()生命周期方法
            ''',
            'responsibility': 'Freqtrade核心引擎 + 策略配置'
        },
        'risk_management': {
            'description': '执行止损检查、仓位管理、风险控制',
            'details': '''
            风险管理流程：
            1. 检查固定止损条件
            2. 调用custom_stoploss()（如果实现）
            3. 检查ROI止盈条件
            4. 验证最大持仓数量
            5. 计算仓位大小
            6. 执行风险控制规则
            ''',
            'responsibility': 'Freqtrade核心引擎'
        },
        'order_execution': {
            'description': '向交易所发送买入/卖出订单并跟踪执行状态',
            'details': '''
            订单执行流程：
            1. 验证交易信号有效性
            2. 计算订单数量和价格
            3. 调用confirm_trade_entry/exit()确认
            4. 向交易所发送订单
            5. 跟踪订单执行状态
            6. 处理部分成交和失败情况
            ''',
            'responsibility': 'Freqtrade核心引擎'
        }
    }
    
    process_info = core_processes.get(node_name, {
        'description': '核心流程节点',
        'details': '这是freqtrade的核心执行流程之一。',
        'responsibility': 'Freqtrade核心引擎'
    })
    
    st.write("**流程描述:**")
    st.write(process_info['description'])
    
    st.write("**详细流程:**")
    st.write(process_info['details'])
    
    st.write("**负责模块:**")
    st.write(process_info['responsibility'])
    
    st.info("💡 这是freqtrade的核心流程，不需要在策略中实现，由freqtrade引擎自动处理。")