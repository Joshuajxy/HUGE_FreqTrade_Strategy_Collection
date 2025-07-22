"""
增强的节点详情显示组件
专门用于显示策略接口函数的设计思路和伪代码
"""
import streamlit as st
from utils.data_models import StrategyAnalysis

def show_enhanced_node_details(node_id: str, strategy: StrategyAnalysis):
    """显示增强的节点详细信息，突出设计思路和伪代码"""
    
    # 节点基本信息映射
    node_info_map = {
        'data_fetch': {
            'name': '数据获取',
            'type': 'core',
            'description': '从交易所获取OHLCV历史数据和实时数据'
        },
        'strategy_init': {
            'name': '策略初始化',
            'type': 'core',
            'description': '初始化策略参数、ROI设置、止损设置等配置'
        },
        'populate_indicators': {
            'name': 'populate_indicators',
            'type': 'strategy',
            'description': '计算技术指标'
        },
        'populate_buy': {
            'name': 'populate_buy_trend',
            'type': 'strategy',
            'description': '生成买入信号'
        },
        'populate_sell': {
            'name': 'populate_sell_trend',
            'type': 'strategy',
            'description': '生成卖出信号'
        },
        'risk_management': {
            'name': '风险管理',
            'type': 'core',
            'description': '执行止损检查、仓位管理、风险控制'
        },
        'order_execution': {
            'name': '订单执行',
            'type': 'core',
            'description': '向交易所发送买入/卖出订单并跟踪执行状态'
        }
    }
    
    if node_id not in node_info_map:
        st.error("未知的节点ID")
        return
    
    node_info = node_info_map[node_id]
    
    # 显示节点标题
    st.markdown(f"# 📋 {node_info['name']}")
    
    if node_info['type'] == 'strategy':
        show_enhanced_strategy_interface_details(node_id, strategy)
    else:
        show_enhanced_core_node_details(node_info)

def show_enhanced_strategy_interface_details(node_id: str, strategy: StrategyAnalysis):
    """显示增强的策略接口节点详情，突出设计思路和伪代码"""
    
    # 映射节点ID到接口名称
    interface_mapping = {
        'populate_indicators': 'populate_indicators',
        'populate_buy': 'populate_buy_trend',
        'populate_sell': 'populate_sell_trend',
        'custom_stoploss': 'custom_stoploss',
        'custom_sell': 'custom_sell',
        'confirm_trade_entry': 'confirm_trade_entry',
        'confirm_trade_exit': 'confirm_trade_exit'
    }
    
    interface_name = interface_mapping.get(node_id)
    if not interface_name:
        st.error("未知的策略接口")
        return
    
    interface_info = strategy.interfaces.get(interface_name)
    
    if interface_info and interface_info.implemented:
        # 显示实现状态
        st.success(f"✅ **{interface_name}** - 已在当前策略中实现")
        
        # 主要内容区域
        st.markdown("---")
        
        # 设计思路 - 最重要的信息，放在最前面
        if interface_info.description:
            st.markdown("## 💡 设计思路")
            st.info(interface_info.description)
        
        # 伪代码 - 第二重要，单独突出显示
        if interface_info.pseudocode:
            st.markdown("## 💻 伪代码")
            st.code(interface_info.pseudocode, language='python')
        
        # 实现逻辑 - 详细说明
        if interface_info.logic_explanation:
            st.markdown("## 🧠 实现逻辑")
            st.write(interface_info.logic_explanation)
        
        # 创建标签页显示详细信息
        tab1, tab2, tab3 = st.tabs(["📥 输入参数", "📤 输出结果", "📊 相关信息"])
        
        with tab1:
            if interface_info.input_params:
                st.markdown("### 输入参数详情")
                for i, param in enumerate(interface_info.input_params, 1):
                    with st.expander(f"参数 {i}: {param.name}", expanded=True):
                        st.write(f"**类型**: `{param.type}`")
                        st.write(f"**描述**: {param.description}")
                        if param.example:
                            st.write("**示例**:")
                            st.code(str(param.example), language='python')
            else:
                st.info("该接口无特定输入参数信息")
        
        with tab2:
            if interface_info.output_description:
                st.markdown("### 输出结果")
                st.write(interface_info.output_description)
            else:
                st.info("无输出描述信息")
        
        with tab3:
            # 显示相关技术指标
            if hasattr(strategy, 'indicators') and strategy.indicators:
                st.markdown("### 📊 使用的技术指标")
                for indicator in strategy.indicators:
                    with st.expander(f"{indicator['name']}", expanded=False):
                        st.write(f"**描述**: {indicator.get('description', '无描述')}")
                        if 'parameters' in indicator:
                            st.write("**参数配置**:")
                            st.json(indicator['parameters'])
            
            # 显示买入/卖出条件
            if interface_name == 'populate_buy_trend' and hasattr(strategy, 'buy_conditions'):
                st.markdown("### 📈 买入条件")
                for i, condition in enumerate(strategy.buy_conditions, 1):
                    with st.expander(f"买入条件 {i}", expanded=False):
                        st.write(f"**描述**: {condition.get('description', '无描述')}")
                        if 'logic' in condition:
                            st.code(condition['logic'], language='python')
                        if 'indicators_used' in condition:
                            st.write(f"**使用指标**: {', '.join(condition['indicators_used'])}")
            
            if interface_name == 'populate_sell_trend' and hasattr(strategy, 'sell_conditions'):
                st.markdown("### 📉 卖出条件")
                for i, condition in enumerate(strategy.sell_conditions, 1):
                    with st.expander(f"卖出条件 {i}", expanded=False):
                        st.write(f"**描述**: {condition.get('description', '无描述')}")
                        if 'logic' in condition:
                            st.code(condition['logic'], language='python')
                        if 'indicators_used' in condition:
                            st.write(f"**使用指标**: {', '.join(condition['indicators_used'])}")
            
    else:
        # 未实现的接口 - 显示标准说明
        st.warning(f"❌ **{interface_name}** - 未在当前策略中实现")
        
        # 提供标准接口的详细说明
        standard_info = get_standard_interface_info(interface_name)
        
        if standard_info:
            st.markdown("---")
            st.markdown("## 📖 标准接口说明")
            st.info(standard_info['description'])
            
            st.markdown("## 💻 标准实现伪代码")
            st.code(standard_info['pseudocode'], language='python')
            
            if 'typical_usage' in standard_info:
                st.markdown("## 🔧 典型用法")
                st.write(standard_info['typical_usage'])

def show_enhanced_core_node_details(node_info: dict):
    """显示增强的核心流程节点详情"""
    
    st.info(f"🔧 这是freqtrade的核心执行流程节点")
    
    st.markdown("## 📝 功能说明")
    st.write(node_info['description'])
    
    # 获取详细的核心节点信息
    detailed_info = get_core_node_detailed_info(node_info['name'])
    
    if detailed_info:
        st.markdown("## 🔄 详细执行流程")
        for i, step in enumerate(detailed_info['steps'], 1):
            st.write(f"**{i}.** {step}")
        
        if 'technical_details' in detailed_info:
            with st.expander("🔧 技术细节", expanded=False):
                for detail in detailed_info['technical_details']:
                    st.write(f"• {detail}")

def get_standard_interface_info(interface_name: str) -> dict:
    """获取标准接口的详细信息"""
    
    standard_interfaces = {
        'populate_indicators': {
            'description': '计算策略所需的技术指标。这是策略的基础，所有后续的买入卖出决策都基于这些指标。',
            'pseudocode': '''def populate_indicators(self, dataframe, metadata):
    # 1. 导入所需的技术指标库 (如 TA-Lib, qtpylib)
    # 2. 计算各种技术指标
    dataframe['rsi'] = ta.RSI(dataframe['close'])
    dataframe['sma'] = ta.SMA(dataframe['close'], timeperiod=20)
    
    # 3. 计算复合指标
    bollinger = qtpylib.bollinger_bands(dataframe['close'], window=20, stds=2)
    dataframe['bb_lowerband'] = bollinger['lower']
    dataframe['bb_upperband'] = bollinger['upper']
    
    # 4. 返回包含所有指标的数据框
    return dataframe''',
            'typical_usage': '通常在这里计算RSI、MACD、布林带、移动平均线等技术指标，为后续的交易信号生成提供数据基础。'
        },
        'populate_buy_trend': {
            'description': '根据技术指标和市场条件生成买入信号。这个函数决定了策略何时进入市场。',
            'pseudocode': '''def populate_buy_trend(self, dataframe, metadata):
    # 1. 定义买入条件
    conditions = []
    
    # 2. 检查技术指标条件
    conditions.append(dataframe['rsi'] > 30)  # RSI不过度超卖
    conditions.append(dataframe['close'] < dataframe['bb_lowerband'])  # 价格触及下轨
    
    # 3. 组合所有条件
    if conditions:
        dataframe.loc[reduce(lambda x, y: x & y, conditions), 'buy'] = 1
    
    # 4. 返回包含买入信号的数据框
    return dataframe''',
            'typical_usage': '常见的买入条件包括：RSI超卖反弹、价格突破阻力位、多个指标共振等。'
        },
        'populate_sell_trend': {
            'description': '根据技术指标和市场条件生成卖出信号。这个函数决定了策略何时退出市场。',
            'pseudocode': '''def populate_sell_trend(self, dataframe, metadata):
    # 1. 定义卖出条件
    conditions = []
    
    # 2. 检查获利/止损条件
    conditions.append(dataframe['rsi'] > 70)  # RSI超买
    conditions.append(dataframe['close'] > dataframe['bb_upperband'])  # 价格突破上轨
    
    # 3. 组合所有条件
    if conditions:
        dataframe.loc[reduce(lambda x, y: x & y, conditions), 'sell'] = 1
    
    # 4. 返回包含卖出信号的数据框
    return dataframe''',
            'typical_usage': '常见的卖出条件包括：RSI超买、价格达到目标位、止损触发等。'
        },
        'custom_stoploss': {
            'description': '实现动态止损逻辑，可根据市场情况和持仓时间调整止损位，比固定止损更灵活。',
            'pseudocode': '''def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
    # 1. 获取交易信息
    trade_duration = (current_time - trade.open_date).total_seconds() / 3600  # 小时
    
    # 2. 根据持仓时间调整止损
    if trade_duration < 1:
        return -0.05  # 1小时内止损5%
    elif trade_duration < 6:
        return -0.03  # 6小时内止损3%
    else:
        return -0.01  # 长期持仓止损1%''',
            'typical_usage': '可以实现时间衰减止损、盈利保护止损、波动率自适应止损等高级止损策略。'
        },
        'custom_sell': {
            'description': '实现自定义卖出逻辑，补充标准卖出信号，提供更精细的退出控制。',
            'pseudocode': '''def custom_sell(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
    # 1. 检查盈利情况
    if current_profit > 0.20:  # 盈利超过20%
        return 'profit_target_reached'
    
    # 2. 检查持仓时间
    trade_duration = (current_time - trade.open_date).total_seconds() / 3600
    if trade_duration > 24 and current_profit < 0.05:  # 持仓超过24小时且盈利不足5%
        return 'timeout_exit'
    
    # 3. 其他自定义条件
    return None''',
            'typical_usage': '可以实现基于盈利目标、时间限制、市场条件变化的自定义退出逻辑。'
        }
    }
    
    return standard_interfaces.get(interface_name)

def get_core_node_detailed_info(node_name: str) -> dict:
    """获取核心节点的详细信息"""
    
    core_nodes_info = {
        '数据获取': {
            'steps': [
                '连接到配置的交易所API',
                '获取指定交易对的历史OHLCV数据',
                '获取实时价格数据用于交易决策',
                '处理数据质量检查和缺失值填充',
                '确保数据时间戳的一致性和完整性'
            ],
            'technical_details': [
                '支持多种交易所：Binance、Kraken、Bittrex等',
                '数据缓存机制减少API调用',
                '自动处理网络异常和重连',
                '数据格式标准化处理'
            ]
        },
        '策略初始化': {
            'steps': [
                '加载策略配置文件和参数',
                '初始化ROI（投资回报率）设置',
                '设置止损和止盈参数',
                '配置交易对和时间框架',
                '初始化技术指标计算所需的历史数据',
                '验证策略参数的有效性'
            ],
            'technical_details': [
                '参数验证和类型检查',
                '默认值设置和覆盖机制',
                '策略版本兼容性检查',
                '内存和计算资源预分配'
            ]
        },
        '风险管理': {
            'steps': [
                '检查当前持仓状态和可用资金',
                '执行止损和止盈检查',
                '计算合适的仓位大小',
                '验证交易信号的风险水平',
                '应用资金管理规则',
                '记录风险指标和统计数据'
            ],
            'technical_details': [
                '凯利公式仓位计算',
                '最大回撤控制',
                '相关性风险管理',
                '流动性风险评估'
            ]
        },
        '订单执行': {
            'steps': [
                '验证交易信号和市场条件',
                '计算最终的订单数量和价格',
                '向交易所发送买入/卖出订单',
                '监控订单执行状态',
                '处理部分成交和订单取消',
                '更新持仓和资金状态',
                '记录交易日志和统计信息'
            ],
            'technical_details': [
                '市价单和限价单支持',
                '滑点控制和价格保护',
                '订单超时和重试机制',
                '交易费用计算和优化'
            ]
        }
    }
    
    return core_nodes_info.get(node_name)