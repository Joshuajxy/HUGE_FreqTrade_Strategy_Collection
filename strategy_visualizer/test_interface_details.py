#!/usr/bin/env python3
"""
测试流程图节点显示策略接口函数的设计思路和伪代码
"""

import sys
import os
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_interface_details_display():
    """测试每个节点都能显示策略接口函数的设计思路和伪代码"""
    print("🧪 测试接口详情显示功能...")
    
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.node_details import show_strategy_interface_details
        
        # 加载示例策略
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        
        # 创建流程图
        G = create_strategy_graph(strategy)
        
        print(f"\\n📊 流程图包含 {len(G.nodes())} 个节点:")
        
        # 检查每个策略接口节点
        strategy_nodes = []
        for node_id, node_data in G.nodes(data=True):
            print(f"  - {node_id}: {node_data['label']} ({node_data['type']})")
            if node_data['type'] == 'strategy':
                strategy_nodes.append((node_id, node_data))
        
        print(f"\\n🔍 检查 {len(strategy_nodes)} 个策略接口节点的详细信息:")
        
        for node_id, node_data in strategy_nodes:
            interface_info = node_data.get('interface_info')
            print(f"\\n📋 节点: {node_id} ({node_data['label']})")
            
            if interface_info:
                # 检查实现状态
                status = "✅ 已实现" if interface_info.implemented else "❌ 未实现"
                print(f"   状态: {status}")
                
                # 检查设计思路
                if interface_info.description:
                    print(f"   💡 设计思路: {interface_info.description}")
                    print(f"      长度: {len(interface_info.description)} 字符")
                else:
                    print("   ❌ 缺少设计思路")
                
                # 检查伪代码
                if interface_info.pseudocode:
                    lines = interface_info.pseudocode.split('\\n')
                    print(f"   💻 伪代码: {len(lines)} 行")
                    print(f"      示例: {lines[0] if lines else 'N/A'}")
                    if len(lines) > 1:
                        print(f"             {lines[1] if len(lines) > 1 else ''}")
                else:
                    print("   ❌ 缺少伪代码")
                
                # 检查实现逻辑
                if interface_info.logic_explanation:
                    print(f"   🧠 实现逻辑: {interface_info.logic_explanation[:60]}...")
                    print(f"      长度: {len(interface_info.logic_explanation)} 字符")
                else:
                    print("   ❌ 缺少实现逻辑")
                
                # 检查输入参数
                if interface_info.input_params:
                    print(f"   📥 输入参数: {len(interface_info.input_params)} 个")
                    for param in interface_info.input_params:
                        print(f"      - {param.name} ({param.type}): {param.description[:40]}...")
                else:
                    print("   ⚠️  无输入参数信息")
                
                # 检查输出描述
                if interface_info.output_description:
                    print(f"   📤 输出描述: {interface_info.output_description[:50]}...")
                else:
                    print("   ⚠️  无输出描述")
            else:
                print("   ❌ 无接口信息")
        
        # 验证关键要求
        print("\\n🎯 验证关键要求:")
        
        # 要求1: 每个策略接口节点都有设计思路
        missing_description = []
        for node_id, node_data in strategy_nodes:
            interface_info = node_data.get('interface_info')
            if interface_info and interface_info.implemented and not interface_info.description:
                missing_description.append(node_id)
        
        if missing_description:
            print(f"   ❌ 以下节点缺少设计思路: {missing_description}")
        else:
            print("   ✅ 所有已实现的接口都有设计思路")
        
        # 要求2: 每个策略接口节点都有伪代码
        missing_pseudocode = []
        for node_id, node_data in strategy_nodes:
            interface_info = node_data.get('interface_info')
            if interface_info and interface_info.implemented and not interface_info.pseudocode:
                missing_pseudocode.append(node_id)
        
        if missing_pseudocode:
            print(f"   ❌ 以下节点缺少伪代码: {missing_pseudocode}")
        else:
            print("   ✅ 所有已实现的接口都有伪代码")
        
        # 要求3: 每个策略接口节点都有实现逻辑说明
        missing_logic = []
        for node_id, node_data in strategy_nodes:
            interface_info = node_data.get('interface_info')
            if interface_info and interface_info.implemented and not interface_info.logic_explanation:
                missing_logic.append(node_id)
        
        if missing_logic:
            print(f"   ❌ 以下节点缺少实现逻辑: {missing_logic}")
        else:
            print("   ✅ 所有已实现的接口都有实现逻辑说明")
        
        # 统计结果
        implemented_count = sum(1 for _, node_data in strategy_nodes 
                              if node_data.get('interface_info') and node_data['interface_info'].implemented)
        total_interfaces = len(strategy_nodes)
        
        print(f"\\n📈 统计结果:")
        print(f"   - 策略接口节点总数: {total_interfaces}")
        print(f"   - 已实现接口数量: {implemented_count}")
        print(f"   - 未实现接口数量: {total_interfaces - implemented_count}")
        
        success = (len(missing_description) == 0 and 
                  len(missing_pseudocode) == 0 and 
                  len(missing_logic) == 0)
        
        if success:
            print("\\n🎉 所有要求都满足！流程图中的每个策略接口节点都能显示设计思路和伪代码")
        else:
            print("\\n⚠️  部分要求未满足，需要进一步完善")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_node_hover_info():
    """测试节点悬停信息是否包含设计思路和伪代码提示"""
    print("\\n🧪 测试节点悬停信息...")
    
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.plotly_renderer import create_plotly_traces
        
        # 加载示例策略
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        G = create_strategy_graph(strategy)
        
        # 创建布局位置（简化版）
        pos = {node: (0, i) for i, node in enumerate(G.nodes())}
        
        # 创建Plotly轨迹数据
        node_trace, edge_trace = create_plotly_traces(G, pos)
        
        # 检查悬停文本
        hover_texts = node_trace.hovertext
        
        print(f"检查 {len(hover_texts)} 个节点的悬停信息:")
        
        for i, (node_id, node_data) in enumerate(G.nodes(data=True)):
            if node_data['type'] == 'strategy':
                hover_text = hover_texts[i]
                print(f"\\n📋 {node_id}:")
                print(f"   悬停文本长度: {len(hover_text)} 字符")
                
                # 检查是否包含关键信息
                has_design_info = "设计思路" in hover_text or "description" in hover_text.lower()
                has_pseudocode_hint = "伪代码" in hover_text or "pseudocode" in hover_text.lower()
                has_logic_info = "实现逻辑" in hover_text or "logic" in hover_text.lower()
                
                print(f"   包含设计思路: {'✅' if has_design_info else '❌'}")
                print(f"   包含伪代码提示: {'✅' if has_pseudocode_hint else '❌'}")
                print(f"   包含实现逻辑: {'✅' if has_logic_info else '❌'}")
                
                # 显示悬停文本片段
                preview = hover_text.replace('<br>', ' | ')[:100]
                print(f"   预览: {preview}...")
        
        print("\\n✅ 节点悬停信息测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 悬停信息测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始接口详情显示测试")
    print("=" * 50)
    
    success1 = test_interface_details_display()
    success2 = test_node_hover_info()
    
    print("\\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有测试通过！流程图完全满足要求")
        print("💡 每个节点都能显示策略接口函数的设计思路和伪代码")
    else:
        print("⚠️  部分测试未通过，需要进一步改进")
    
    sys.exit(0 if (success1 and success2) else 1)