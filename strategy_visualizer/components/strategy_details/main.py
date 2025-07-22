import streamlit as st
from utils.data_models import StrategyAnalysis
from .interface_viewer import render_interface_details
from .parameter_viewer import render_parameter_details

def render_strategy_details(strategy: StrategyAnalysis):
    """渲染策略详情主面板"""
    
    # 基本信息
    st.subheader("📋 基本信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**策略名称:** {strategy.strategy_name}")
        st.write(f"**描述:** {strategy.description}")
    
    with col2:
        if strategy.author:
            st.write(f"**作者:** {strategy.author}")
        if strategy.version:
            st.write(f"**版本:** {strategy.version}")
    
    # 参数配置
    render_parameter_details(strategy)
    
    # 接口实现详情
    render_interface_details(strategy)