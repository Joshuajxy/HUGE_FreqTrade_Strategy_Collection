#!/usr/bin/env python3
"""
测试TensorBoard风格的流程图实现
"""

import streamlit as st
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_models import StrategyAnalysis, InterfaceImplementation, Parameter
from components.flowchart.main import render_flowchart

def create_test_strategy() -> StrategyAnalysis:
    """创建测试策略数据"""
    
    # 创建一些示例接口实现
    interfaces = {
        'populate_indicators': InterfaceImplementation(
            implemented=True,
            description='计算RSI、MACD、布林带等技术指标',
            pseudocode='''
def populate_indicators(self, dataframe, metadata):
    # 计算RSI指标
    dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
    
    # 计算MACD指标
    macd, macdsignal, macdhist = ta.MACD(dataframe)
    dataframe['macd'] = macd
    dataframe['macdsignal'] = macdsignal
    
    # 计算布林带
    dataframe['bb_upper'], dataframe['bb_middle'], dataframe['bb_lower'] = ta.BBANDS(dataframe)
    
    return dataframe
            ''',
            input_params=[
                Parameter('dataframe', 'DataFrame', 'OHLCV数据框'),
                Parameter('metadata', 'dict', '交易对元数据')
            ],
            output_description='包含技术指标的DataFrame',
            logic_explanation='使用TA-Lib库计算多种技术指标，为买卖信号提供数据基础'
        ),
        
        'populate_buy_trend': InterfaceImplementation(
            implemented=True,
            description='基于RSI超卖和布林带下轨突破生成买入信号',
            pseudocode='''
def populate_buy_trend(self, dataframe, metadata):
    dataframe.loc[
        (dataframe['rsi'] < 30) &  # RSI超卖
        (dataframe['close'] < dataframe['bb_lower']) &  # 价格低于布林带下轨
        (dataframe['volume'] > dataframe['volume'].rolling(20).mean()),  # 成交量放大
        'buy'] = 1
    
    return dataframe
            ''',
            input_params=[
                Parameter('dataframe', 'DataFrame', '包含指标的数据框'),
                Parameter('metadata', 'dict', '交易对元数据')
            ],
            output_description='包含买入信号的DataFrame',
            logic_explanation='当RSI指标显示超卖且价格跌破布林带下轨时，结合成交量确认，生成买入信号'
        ),
        
        'populate_sell_trend': InterfaceImplementation(
            implemented=True,
            description='基于RSI超买和MACD背离生成卖出信号',
            pseudocode='''
def populate_sell_trend(self, dataframe, metadata):
    dataframe.loc[
        (dataframe['rsi'] > 70) &  # RSI超买
        (dataframe['macd'] < dataframe['macdsignal']) &  # MACD死叉
        (dataframe['close'] > dataframe['bb_upper']),  # 价格高于布林带上轨
        'sell'] = 1
    
    return dataframe
            ''',
            input_params=[
                Parameter('dataframe', 'DataFrame', '包含指标的数据框'),
                Parameter('metadata', 'dict', '交易对元数据')
            ],
            output_description='包含卖出信号的DataFrame',
            logic_explanation='当RSI指标显示超买且MACD出现死叉时，结合布林带上轨突破，生成卖出信号'
        ),
        
        'custom_stoploss': InterfaceImplementation(
            implemented=True,
            description='实现动态追踪止损，根据盈利情况调整止损位',
            pseudocode='''
def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
    if current_profit > 0.20:  # 盈利超过20%
        return -0.05  # 设置5%止损
    elif current_profit > 0.10:  # 盈利超过10%
        return -0.02  # 设置2%止损
    
    return self.stoploss  # 使用默认止损
            ''',
            input_params=[
                Parameter('pair', 'str', '交易对'),
                Parameter('trade', 'Trade', '交易对象'),
                Parameter('current_rate', 'float', '当前价格'),
                Parameter('current_profit', 'float', '当前盈利率')
            ],
            output_description='动态止损百分比',
            logic_explanation='根据当前盈利情况动态调整止损位，实现追踪止损效果'
        )
    }
    
    # 创建策略分析对象
    strategy = StrategyAnalysis(
        strategy_name='TestTensorBoardStrategy',
        description='用于测试TensorBoard风格流程图的示例策略',
        interfaces=interfaces,
        indicators=[
            {'name': 'RSI', 'description': '相对强弱指标'},
            {'name': 'MACD', 'description': '指数平滑移动平均线'},
            {'name': 'Bollinger Bands', 'description': '布林带指标'}
        ],
        parameters={
            'roi': {'0': 0.10, '40': 0.04, '100': 0.02, '180': 0},
            'stoploss': -0.10,
            'timeframe': '5m'
        },
        buy_conditions=[
            {
                'description': 'RSI超卖买入',
                'logic': 'RSI < 30 AND 价格 < 布林带下轨',
                'indicators_used': ['RSI', 'Bollinger Bands']
            }
        ],
        sell_conditions=[
            {
                'description': 'RSI超买卖出',
                'logic': 'RSI > 70 AND MACD死叉',
                'indicators_used': ['RSI', 'MACD']
            }
        ],
        risk_management={
            'stoploss_type': 'dynamic',
            'trailing_stop': True,
            'custom_stoploss': True
        }
    )
    
    return strategy

def main():
    """主测试函数"""
    st.set_page_config(
        page_title="TensorBoard风格流程图测试",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 TensorBoard风格流程图测试")
    st.write("测试新的大框图设计、粗箭头曲线连接和默认信息显示")
    
    # 创建测试策略
    test_strategy = create_test_strategy()
    
    # 显示策略信息
    with st.expander("📋 测试策略信息", expanded=False):
        st.write(f"**策略名称:** {test_strategy.strategy_name}")
        st.write(f"**策略描述:** {test_strategy.description}")
        st.write(f"**已实现接口数:** {len([i for i in test_strategy.interfaces.values() if i.implemented])}")
        st.write(f"**总接口数:** {len(test_strategy.interfaces)}")
    
    # 渲染TensorBoard风格流程图
    st.header("🚀 TensorBoard风格流程图")
    render_flowchart(test_strategy)
    
    # 显示改进说明
    with st.expander("✨ 新功能特性", expanded=True):
        st.write("""
        **🎯 TensorBoard风格改进:**
        
        1. **大框图设计** - 每个节点使用280x120像素的大框图，信息更丰富
        2. **默认信息显示** - 节点内直接显示关键信息，无需悬停
        3. **粗箭头曲线** - 使用4像素宽的曲线连接，带有箭头指示
        4. **完整接口覆盖** - 显示所有freqtrade标准接口，包括未实现的
        5. **默认实现说明** - 未实现的接口显示父类默认行为
        
        **🎨 视觉改进:**
        - ✅ 绿色：已实现的策略接口
        - 🔧 橙色：使用默认实现的接口
        - ⚙️ 蓝色：freqtrade核心流程
        
        **🔍 交互改进:**
        - 点击任意节点查看详细信息
        - 已实现接口显示策略特定逻辑
        - 未实现接口显示默认行为和实现建议
        """)

if __name__ == "__main__":
    main()