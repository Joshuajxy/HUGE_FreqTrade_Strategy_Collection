#!/usr/bin/env python3
"""
滚轮缩放同步功能测试脚本
验证自定义组件的所有功能是否正常工作
"""

import streamlit as st
import json
import os
from utils.data_models import StrategyAnalysis
from components.flowchart import render_flowchart

def main():
    st.set_page_config(
        page_title="滚轮缩放同步功能测试",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 滚轮缩放同步功能测试")
    
    # 测试用例选择
    test_case = st.selectbox(
        "选择测试用例",
        [
            "简单策略 - 5个模块",
            "复杂策略 - 10个模块",
            "超复杂策略 - 15个模块"
        ]
    )
    
    # 生成测试数据
    if test_case == "简单策略 - 5个模块":
        strategy_data = create_simple_strategy()
    elif test_case == "复杂策略 - 10个模块":
        strategy_data = create_complex_strategy()
    else:
        strategy_data = create_super_complex_strategy()
    
    # 创建策略分析对象
    strategy = StrategyAnalysis.from_dict(strategy_data)
    
    # 功能测试区域
    st.header("🧪 功能测试")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("模块数量", len(strategy.modules))
    
    with col2:
        st.metric("连接数量", len(strategy.connections))
    
    with col3:
        if hasattr(st.session_state, 'flowchart_xrange'):
            x_range = st.session_state.flowchart_xrange[1] - st.session_state.flowchart_xrange[0]
            zoom_ratio = 2000 / x_range
            st.metric("当前缩放", f"{zoom_ratio:.1f}x")
        else:
            st.metric("当前缩放", "1.0x")
    
    # 测试说明
    st.info("""
    🔍 **测试说明**：
    1. 使用鼠标滚轮在流程图上进行缩放
    2. 观察左上角的缩放比例是否实时更新
    3. 观察字体大小是否随缩放比例变化
    4. 使用拖拽功能平移视图
    5. 检查缩放事件是否被正确捕获和显示
    """)
    
    # 渲染流程图
    st.header("📊 流程图测试区域")
    render_flowchart(strategy)
    
    # 显示测试结果
    st.header("📋 测试结果")
    
    # 检查会话状态
    if hasattr(st.session_state, 'flowchart_xrange'):
        st.success("✅ 坐标轴范围状态正常")
        st.write(f"X轴范围: {st.session_state.flowchart_xrange}")
        st.write(f"Y轴范围: {st.session_state.flowchart_yrange}")
    else:
        st.warning("⚠️ 坐标轴范围状态未初始化")
    
    # 组件状态检查
    try:
        from streamlit_plugins.plotly_zoom_sync import plotly_zoom_sync
        st.success("✅ 自定义组件导入成功")
    except Exception as e:
        st.error(f"❌ 自定义组件导入失败: {str(e)}")
    
    # 构建目录检查
    build_dir = os.path.join(os.path.dirname(__file__), "streamlit_plugins", "frontend", "build")
    if os.path.exists(build_dir):
        st.success("✅ 前端构建目录存在")
        files = os.listdir(build_dir)
        st.write(f"构建文件: {files}")
    else:
        st.error("❌ 前端构建目录不存在")

def create_simple_strategy():
    """创建简单测试策略"""
    return {
        "strategy_name": "SimpleTestStrategy",
        "description": "简单测试策略 - 5个模块",
        "modules": [
            {
                "name": "DataLoader",
                "type": "data_input",
                "description": "数据加载模块",
                "layer": 0,
                "position": 0,
                "parameters": {"timeframe": "1h"},
                "indicators": ["close", "volume"],
                "risk_level": "low"
            },
            {
                "name": "TechnicalIndicators",
                "type": "indicator",
                "description": "技术指标计算",
                "layer": 1,
                "position": 0,
                "parameters": {"sma_period": 20},
                "indicators": ["SMA"],
                "risk_level": "low"
            },
            {
                "name": "SignalGenerator",
                "type": "signal",
                "description": "信号生成模块",
                "layer": 2,
                "position": 0,
                "parameters": {"threshold": 0.5},
                "indicators": ["buy_signal"],
                "risk_level": "medium"
            },
            {
                "name": "RiskManager",
                "type": "risk_management",
                "description": "风险管理模块",
                "layer": 3,
                "position": 0,
                "parameters": {"stop_loss": 0.02},
                "indicators": ["position_size"],
                "risk_level": "high"
            },
            {
                "name": "OrderExecutor",
                "type": "execution",
                "description": "订单执行模块",
                "layer": 4,
                "position": 0,
                "parameters": {"order_type": "market"},
                "indicators": ["order_status"],
                "risk_level": "medium"
            }
        ],
        "connections": [
            {"from": "DataLoader", "to": "TechnicalIndicators", "data_flow": "price_data"},
            {"from": "TechnicalIndicators", "to": "SignalGenerator", "data_flow": "indicators"},
            {"from": "SignalGenerator", "to": "RiskManager", "data_flow": "signals"},
            {"from": "RiskManager", "to": "OrderExecutor", "data_flow": "risk_adjusted_signals"}
        ],
        "metadata": {
            "created_at": "2025-07-23T15:00:00Z",
            "version": "1.0.0",
            "complexity": "simple",
            "total_modules": 5
        }
    }

def create_complex_strategy():
    """创建复杂测试策略"""
    modules = []
    connections = []
    
    # 数据层 (Layer 0)
    modules.extend([
        {"name": "DataLoader1", "type": "data_input", "layer": 0, "position": 0, "description": "主要数据源", "parameters": {}, "indicators": [], "risk_level": "low"},
        {"name": "DataLoader2", "type": "data_input", "layer": 0, "position": 1, "description": "辅助数据源", "parameters": {}, "indicators": [], "risk_level": "low"}
    ])
    
    # 指标层 (Layer 1)
    modules.extend([
        {"name": "TechIndicator1", "type": "indicator", "layer": 1, "position": 0, "description": "趋势指标", "parameters": {}, "indicators": [], "risk_level": "low"},
        {"name": "TechIndicator2", "type": "indicator", "layer": 1, "position": 1, "description": "动量指标", "parameters": {}, "indicators": [], "risk_level": "low"},
        {"name": "TechIndicator3", "type": "indicator", "layer": 1, "position": 2, "description": "波动率指标", "parameters": {}, "indicators": [], "risk_level": "low"}
    ])
    
    # 信号层 (Layer 2)
    modules.extend([
        {"name": "SignalGen1", "type": "signal", "layer": 2, "position": 0, "description": "买入信号", "parameters": {}, "indicators": [], "risk_level": "medium"},
        {"name": "SignalGen2", "type": "signal", "layer": 2, "position": 1, "description": "卖出信号", "parameters": {}, "indicators": [], "risk_level": "medium"},
        {"name": "SignalFilter", "type": "signal", "layer": 2, "position": 2, "description": "信号过滤", "parameters": {}, "indicators": [], "risk_level": "medium"}
    ])
    
    # 风险管理层 (Layer 3)
    modules.extend([
        {"name": "RiskManager1", "type": "risk_management", "layer": 3, "position": 0, "description": "仓位管理", "parameters": {}, "indicators": [], "risk_level": "high"},
        {"name": "RiskManager2", "type": "risk_management", "layer": 3, "position": 1, "description": "止损管理", "parameters": {}, "indicators": [], "risk_level": "high"}
    ])
    
    # 执行层 (Layer 4)
    modules.append(
        {"name": "OrderExecutor", "type": "execution", "layer": 4, "position": 0, "description": "订单执行", "parameters": {}, "indicators": [], "risk_level": "medium"}
    )
    
    # 创建连接
    connections = [
        {"from": "DataLoader1", "to": "TechIndicator1", "data_flow": "price_data"},
        {"from": "DataLoader1", "to": "TechIndicator2", "data_flow": "price_data"},
        {"from": "DataLoader2", "to": "TechIndicator3", "data_flow": "volume_data"},
        {"from": "TechIndicator1", "to": "SignalGen1", "data_flow": "trend_data"},
        {"from": "TechIndicator2", "to": "SignalGen2", "data_flow": "momentum_data"},
        {"from": "TechIndicator3", "to": "SignalFilter", "data_flow": "volatility_data"},
        {"from": "SignalGen1", "to": "RiskManager1", "data_flow": "buy_signals"},
        {"from": "SignalGen2", "to": "RiskManager1", "data_flow": "sell_signals"},
        {"from": "SignalFilter", "to": "RiskManager2", "data_flow": "filtered_signals"},
        {"from": "RiskManager1", "to": "OrderExecutor", "data_flow": "position_signals"},
        {"from": "RiskManager2", "to": "OrderExecutor", "data_flow": "risk_signals"}
    ]
    
    return {
        "strategy_name": "ComplexTestStrategy",
        "description": "复杂测试策略 - 10个模块",
        "modules": modules,
        "connections": connections,
        "metadata": {
            "created_at": "2025-07-23T15:00:00Z",
            "version": "1.0.0",
            "complexity": "complex",
            "total_modules": len(modules)
        }
    }

def create_super_complex_strategy():
    """创建超复杂测试策略"""
    modules = []
    connections = []
    
    # 创建更多层级和模块来测试复杂布局
    for layer in range(5):
        layer_modules = 3 if layer < 4 else 1
        for pos in range(layer_modules):
            module_name = f"Module_L{layer}_P{pos}"
            modules.append({
                "name": module_name,
                "type": ["data_input", "indicator", "signal", "risk_management", "execution"][layer],
                "layer": layer,
                "position": pos,
                "description": f"Layer {layer} Module {pos}",
                "parameters": {},
                "indicators": [],
                "risk_level": ["low", "low", "medium", "high", "medium"][layer]
            })
    
    # 创建复杂的连接关系
    for i, module in enumerate(modules[:-3]):  # 除了最后一层
        next_layer_modules = [m for m in modules if m["layer"] == module["layer"] + 1]
        for next_module in next_layer_modules:
            connections.append({
                "from": module["name"],
                "to": next_module["name"],
                "data_flow": f"data_{i}"
            })
    
    return {
        "strategy_name": "SuperComplexTestStrategy",
        "description": "超复杂测试策略 - 15个模块",
        "modules": modules,
        "connections": connections,
        "metadata": {
            "created_at": "2025-07-23T15:00:00Z",
            "version": "1.0.0",
            "complexity": "super_complex",
            "total_modules": len(modules)
        }
    }

if __name__ == "__main__":
    main()
