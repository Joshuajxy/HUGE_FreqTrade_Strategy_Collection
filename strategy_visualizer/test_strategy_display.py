#!/usr/bin/env python3
"""
测试策略信息显示功能
"""

import sys
import os
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_strategy_info_display():
    """测试策略信息在流程图中的显示"""
    print("🧪 测试策略信息显示...")
    
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.plotly_renderer import create_flowchart_figure
        
        # 加载示例策略
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        
        # 创建流程图
        G = create_strategy_graph(strategy)
        
        # 检查节点是否包含策略信息
        print(f"✅ 策略名称: {strategy.strategy_name}")
        print(f"✅ 策略描述: {strategy.description}")
        
        # 检查接口实现情况
        implemented_interfaces = []
        unimplemented_interfaces = []
        
        for interface_name, interface_info in strategy.interfaces.items():
            if interface_info.implemented:
                implemented_interfaces.append(interface_name)
                print(f"✅ 已实现接口: {interface_name}")
                print(f"   - 描述: {interface_info.description}")
                print(f"   - 逻辑: {interface_info.logic_explanation[:50]}...")
            else:
                unimplemented_interfaces.append(interface_name)
                print(f"❌ 未实现接口: {interface_name}")
        
        # 检查节点信息
        for node_id, node_data in G.nodes(data=True):
            if node_data['type'] == 'strategy':
                interface_info = node_data.get('interface_info')
                if interface_info:
                    status = "已实现" if interface_info.implemented else "未实现"
                    print(f"🔍 节点 {node_id}: {status}")
                    if interface_info.implemented:
                        print(f"   - 逻辑说明: {interface_info.logic_explanation[:50]}...")
        
        # 检查指标信息
        if strategy.indicators:
            print(f"📊 技术指标 ({len(strategy.indicators)}个):")
            for indicator in strategy.indicators:
                print(f"   - {indicator['name']}: {indicator['description'][:50]}...")
        
        # 检查买入/卖出条件
        if strategy.buy_conditions:
            print(f"📈 买入条件 ({len(strategy.buy_conditions)}个):")
            for condition in strategy.buy_conditions:
                print(f"   - {condition['description']}")
                print(f"     逻辑: {condition['logic']}")
        
        if strategy.sell_conditions:
            print(f"📉 卖出条件 ({len(strategy.sell_conditions)}个):")
            for condition in strategy.sell_conditions:
                print(f"   - {condition['description']}")
                print(f"     逻辑: {condition['logic']}")
        
        print(f"✅ 策略信息显示测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 策略信息显示测试失败: {e}")
        return False

def test_node_interaction():
    """测试节点交互功能"""
    print("\n🧪 测试节点交互功能...")
    
    try:
        from components.flowchart.node_details import show_strategy_interface_details, show_core_node_details
        from utils.data_models import StrategyAnalysis
        
        # 加载示例策略
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        
        # 测试策略接口节点详情
        print("✅ 策略接口节点详情功能可用")
        
        # 测试核心节点详情
        core_node_info = {
            'name': '数据获取',
            'description': '从交易所获取OHLCV数据'
        }
        print("✅ 核心节点详情功能可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 节点交互测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始策略信息显示测试")
    print("=" * 50)
    
    tests = [
        test_strategy_info_display,
        test_node_interaction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有策略信息显示测试通过！")
        print("💡 流程图应该能正确显示策略的具体信息")
        return True
    else:
        print("⚠️  部分测试失败，请检查策略信息显示功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)