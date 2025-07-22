#!/usr/bin/env python3
"""
测试应用启动是否正常
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_app_components():
    """测试应用的主要组件"""
    try:
        print("🔧 测试应用组件...")
        
        # 测试数据模型
        from utils.data_models import StrategyAnalysis
        print("✅ 数据模型导入成功")
        
        # 测试流程图组件
        from components.flowchart import render_flowchart
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.plotly_renderer import create_flowchart_figure
        print("✅ 流程图组件导入成功")
        
        # 测试策略详情组件
        from components.strategy_details import render_strategy_details
        print("✅ 策略详情组件导入成功")
        
        # 测试回测组件
        from components.backtest import render_backtest_panel
        print("✅ 回测组件导入成功")
        
        # 加载示例数据并测试完整流程
        sample_path = os.path.join(os.path.dirname(__file__), "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        G = create_strategy_graph(strategy)
        fig = create_flowchart_figure(G, strategy)
        
        print("✅ 完整流程测试成功")
        print(f"   策略名称: {strategy.strategy_name}")
        print(f"   节点数量: {len(G.nodes())}")
        print(f"   图形组件: {len(fig.data)} 个数据轨迹")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """检查依赖是否正确安装"""
    try:
        import streamlit
        import plotly
        import networkx
        import pandas
        import numpy
        
        print("✅ 所有依赖都已正确安装")
        print(f"   Streamlit: {streamlit.__version__}")
        print(f"   Plotly: {plotly.__version__}")
        print(f"   NetworkX: {networkx.__version__}")
        print(f"   Pandas: {pandas.__version__}")
        print(f"   NumPy: {numpy.__version__}")
        
        return True
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        return False

if __name__ == "__main__":
    print("🚀 测试应用启动准备...")
    print("=" * 50)
    
    deps_ok = check_dependencies()
    components_ok = test_app_components()
    
    print("\n" + "=" * 50)
    if deps_ok and components_ok:
        print("🎉 应用启动测试全部通过！")
        print("✅ 现在可以安全运行: python run.py")
        print("🌐 应用将在 http://localhost:8501 启动")
    else:
        print("❌ 应用启动测试失败")
        if not deps_ok:
            print("🔧 请安装缺失的依赖: pip install -r requirements.txt")
        if not components_ok:
            print("🔧 请检查组件代码是否有错误")