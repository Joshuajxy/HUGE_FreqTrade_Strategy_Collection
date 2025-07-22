import streamlit as st
from utils.data_models import StrategyAnalysis

def render_parameter_details(strategy: StrategyAnalysis):
    """渲染参数配置详情"""
    
    st.subheader("⚙️ 参数配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**基础参数:**")
        st.write(f"- 时间框架: {strategy.parameters.get('timeframe', 'N/A')}")
        st.write(f"- 止损: {strategy.parameters.get('stoploss', 'N/A')}")
        st.write(f"- 启动蜡烛数: {strategy.parameters.get('startup_candle_count', 'N/A')}")
    
    with col2:
        if 'roi' in strategy.parameters:
            st.write("**ROI配置:**")
            roi_data = strategy.parameters['roi']
            for time_key, roi_value in roi_data.items():
                if isinstance(roi_value, (int, float)):
                    st.write(f"- {time_key}分钟: {roi_value:.1%}")
    
    # 技术指标
    if strategy.indicators:
        st.subheader("📊 技术指标")
        for indicator in strategy.indicators:
            with st.expander(f"📈 {indicator['name']}", expanded=False):
                st.write(f"**描述:** {indicator['description']}")
                if 'parameters' in indicator:
                    st.write("**参数:**")
                    for param_name, param_value in indicator['parameters'].items():
                        st.write(f"- {param_name}: {param_value}")
    
    # 交易条件
    col1, col2 = st.columns(2)
    
    with col1:
        if strategy.buy_conditions:
            st.write("**买入条件:**")
            for i, condition in enumerate(strategy.buy_conditions, 1):
                st.write(f"{i}. {condition.get('description', 'N/A')}")
                if 'logic' in condition:
                    st.code(condition['logic'], language='python')
    
    with col2:
        if strategy.sell_conditions:
            st.write("**卖出条件:**")
            for i, condition in enumerate(strategy.sell_conditions, 1):
                st.write(f"{i}. {condition.get('description', 'N/A')}")
                if 'logic' in condition:
                    st.code(condition['logic'], language='python')
    
    # 风险管理
    if strategy.risk_management:
        st.subheader("🛡️ 风险管理")
        risk_mgmt = strategy.risk_management
        st.write(f"- 止损类型: {risk_mgmt.get('stoploss_type', 'N/A')}")
        st.write(f"- 追踪止损: {'是' if risk_mgmt.get('trailing_stop') else '否'}")
        st.write(f"- 自定义止损: {'是' if risk_mgmt.get('custom_stoploss') else '否'}")
        st.write(f"- 仓位管理: {risk_mgmt.get('position_sizing', 'N/A')}")