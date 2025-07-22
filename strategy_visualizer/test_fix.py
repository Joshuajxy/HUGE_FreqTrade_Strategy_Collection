#!/usr/bin/env python3
"""
测试修复后的plotly_renderer
"""

import sys
import os
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_plotly_renderer():
    """测试plotly渲染器是否正常工作"""
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.plotly_renderer import create_flowchart_figure
        
        print("✅ 成功导入所有模块")
        
        # 加载示例策略
        sample_path = os.path.join(os.path.dirname(__file__), "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        print("✅ 成功加载示例数据")
        
        # 创建策略对象
        strategy = StrategyAnalysis.from_dict(sample_data)
        print(f"✅ 成功创建策略对象: {strategy.strategy_name}")
        
        # 创建图结构
        G = create_strategy_graph(strategy)
        print(f"✅ 成功创建图结构，节点数: {len(G.nodes())}")
        
        # 创建Plotly图形
        fig = create_flowchart_figure(G, strategy)
        print("✅ 成功创建Plotly图形")
        
        # 检查图形属性
        print(f"   - 数据轨迹数: {len(fig.data)}")
        print(f"   - 布局标题: {fig.layout.title.text}")
        print(f"   - 图形高度: {fig.layout.height}")
        print(f"   - 形状数量: {len(fig.layout.shapes) if fig.layout.shapes else 0}")
        print(f"   - 注释数量: {len(fig.layout.annotations) if fig.layout.annotations else 0}")
        
        print("\n🎉 所有测试通过！plotly_renderer修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 测试plotly_renderer修复...")
    print("=" * 50)
    
    success = test_plotly_renderer()
    
    if success:
        print("\n✅ 修复验证成功！应用现在应该可以正常运行")
        print("💡 请重新运行: python run.py")
    else:
        print("\n❌ 修复验证失败，需要进一步调试")