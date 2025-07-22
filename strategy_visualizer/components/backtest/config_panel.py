import streamlit as st
from datetime import datetime, timedelta

def render_backtest_config() -> dict:
    """渲染回测配置面板"""
    with st.expander("⚙️ 回测配置", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_date = st.date_input(
                "开始日期", 
                datetime.now() - timedelta(days=30),
                help="回测开始日期"
            )
            timeframe = st.selectbox(
                "时间框架", 
                ["1m", "5m", "15m", "1h", "4h", "1d"],
                index=3,
                help="K线时间间隔"
            )
        
        with col2:
            end_date = st.date_input(
                "结束日期", 
                datetime.now(),
                help="回测结束日期"
            )
            pair = st.text_input(
                "交易对", 
                "BTC/USDT",
                help="要回测的交易对"
            )
        
        with col3:
            initial_balance = st.number_input(
                "初始资金", 
                value=1000.0,
                min_value=100.0,
                help="回测初始资金（USDT）"
            )
            max_open_trades = st.number_input(
                "最大持仓", 
                value=3,
                min_value=1,
                max_value=10,
                help="同时持有的最大交易数量"
            )
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'timeframe': timeframe,
        'pair': pair,
        'initial_balance': initial_balance,
        'max_open_trades': max_open_trades
    }