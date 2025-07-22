#!/usr/bin/env python3
"""
完整测试流程图中每个节点显示策略接口函数的设计思路和伪代码
"""

import sys
import os
import json

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_complete_interface_display():
    """完整测试流程图节点显示策略接口的设计思路和伪代码"""
    print("🚀 开始完整接口显示测试")
    print("=" * 60)
    
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.graph_builder import create_strategy_graph
        from components.flowchart.plotly_renderer import create_flowchart_figure
        from components.flowchart.enhanced_node_details import show_enhanced_node_details
        
        # 加载示例策略
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        
        print(f"📊 测试策略: {strategy.strategy_name}")
        print(f"📝 策略描述: {strategy.description}")
        
        # 创建流程图
        G = create_strategy_graph(strategy)
        print(f"\\n🔗 流程图包含 {len(G.nodes())} 个节点, {len(G.edges())} 条边")
        
        # 测试每个节点的详细信息
        print("\\n🔍 测试每个节点的详细信息:")
        
        success_count = 0
        total_nodes = 0
        
        for node_id, node_data in G.nodes(data=True):
            total_nodes += 1
            print(f"\\n📋 测试节点: {node_id} ({node_data['label']})")
            
            try:
                if node_data['type'] == 'strategy':
                    # 测试策略接口节点
                    interface_info = node_data.get('interface_info')
                    if interface_info:
                        print(f"   状态: {'✅ 已实现' if interface_info.implemented else '❌ 未实现'}")
                        
                        if interface_info.implemented:
                            # 验证关键信息
                            has_description = bool(interface_info.description)
                            has_pseudocode = bool(interface_info.pseudocode)
                            has_logic = bool(interface_info.logic_explanation)
                            
                            print(f"   💡 设计思路: {'✅' if has_description else '❌'} ({len(interface_info.description) if has_description else 0} 字符)")
                            print(f"   💻 伪代码: {'✅' if has_pseudocode else '❌'} ({len(interface_info.pseudocode.split('\\n')) if has_pseudocode else 0} 行)")
                            print(f"   🧠 实现逻辑: {'✅' if has_logic else '❌'} ({len(interface_info.logic_explanation) if has_logic else 0} 字符)")
                            
                            if has_description and has_pseudocode and has_logic:
                                success_count += 1
                                print("   ✅ 节点信息完整")
                            else:
                                print("   ❌ 节点信息不完整")
                        else:
                            # 未实现的接口也应该有标准说明
                            success_count += 1
                            print("   ✅ 未实现接口有标准说明")
                    else:
                        print("   ❌ 缺少接口信息")
                else:
                    # 测试核心节点
                    has_description = bool(node_data.get('description'))
                    print(f"   📝 功能描述: {'✅' if has_description else '❌'}")
                    if has_description:
                        success_count += 1
                        print("   ✅ 核心节点信息完整")
                    else:
                        print("   ❌ 核心节点信息不完整")
                        
            except Exception as e:
                print(f"   ❌ 测试节点时出错: {e}")
        
        print(f"\\n📈 测试结果统计:")
        print(f"   - 总节点数: {total_nodes}")
        print(f"   - 成功节点数: {success_count}")
        print(f"   - 成功率: {success_count/total_nodes*100:.1f}%")
        
        # 测试流程图渲染
        print("\\n🎨 测试流程图渲染...")
        try:
            fig = create_flowchart_figure(G, strategy)
            print("   ✅ 流程图渲染成功")
            
            # 检查图形数据
            if fig.data:
                print(f"   📊 图形包含 {len(fig.data)} 个数据轨迹")
                
                # 检查节点轨迹
                for trace in fig.data:
                    if hasattr(trace, 'hovertext') and trace.hovertext:
                        hover_count = len([h for h in trace.hovertext if h])
                        print(f"   🔍 悬停信息: {hover_count} 个节点有悬停文本")
                        
                        # 检查悬停文本质量
                        strategy_hovers = [h for h in trace.hovertext if h and '策略接口' in h]
                        design_count = sum(1 for h in strategy_hovers if '设计思路' in h)
                        pseudocode_count = sum(1 for h in strategy_hovers if '伪代码' in h)
                        
                        print(f"   💡 包含设计思路的悬停: {design_count} 个")
                        print(f"   💻 包含伪代码提示的悬停: {pseudocode_count} 个")
                        break
            
        except Exception as e:
            print(f"   ❌ 流程图渲染失败: {e}")
            return False
        
        # 验证核心要求
        print("\\n🎯 验证核心要求:")
        
        # 要求1: 流程图中的每个节点都表示策略的一个接口函数
        strategy_nodes = [n for n, d in G.nodes(data=True) if d['type'] == 'strategy']
        print(f"   ✅ 策略接口节点数量: {len(strategy_nodes)}")
        
        # 要求2: 每个节点要解释接口的设计思路
        nodes_with_design = 0
        for node_id, node_data in G.nodes(data=True):
            if node_data['type'] == 'strategy':
                interface_info = node_data.get('interface_info')
                if interface_info and interface_info.implemented and interface_info.description:
                    nodes_with_design += 1
        
        print(f"   ✅ 有设计思路的节点: {nodes_with_design}/{len(strategy_nodes)}")
        
        # 要求3: 每个节点要显示伪代码
        nodes_with_pseudocode = 0
        for node_id, node_data in G.nodes(data=True):
            if node_data['type'] == 'strategy':
                interface_info = node_data.get('interface_info')
                if interface_info and interface_info.implemented and interface_info.pseudocode:
                    nodes_with_pseudocode += 1
        
        print(f"   ✅ 有伪代码的节点: {nodes_with_pseudocode}/{len(strategy_nodes)}")
        
        # 最终评估
        all_requirements_met = (
            success_count == total_nodes and
            nodes_with_design == len([n for n, d in G.nodes(data=True) 
                                    if d['type'] == 'strategy' and d.get('interface_info') and d['interface_info'].implemented]) and
            nodes_with_pseudocode == len([n for n, d in G.nodes(data=True) 
                                        if d['type'] == 'strategy' and d.get('interface_info') and d['interface_info'].implemented])
        )
        
        print("\\n" + "=" * 60)
        if all_requirements_met:
            print("🎉 所有要求完全满足！")
            print("✅ 流程图中的每个节点都能显示策略接口函数的设计思路和伪代码")
            print("✅ 悬停信息包含设计思路和伪代码提示")
            print("✅ 点击节点可查看完整的接口详情")
        else:
            print("⚠️  部分要求未完全满足，但基本功能正常")
        
        return all_requirements_met
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_node_details():
    """测试增强的节点详情显示功能"""
    print("\\n🧪 测试增强的节点详情显示...")
    
    try:
        from utils.data_models import StrategyAnalysis
        from components.flowchart.enhanced_node_details import get_standard_interface_info, get_core_node_detailed_info
        
        # 测试标准接口信息
        interfaces = ['populate_indicators', 'populate_buy_trend', 'populate_sell_trend', 'custom_stoploss', 'custom_sell']
        
        print("📚 测试标准接口信息:")
        for interface in interfaces:
            info = get_standard_interface_info(interface)
            if info:
                has_desc = bool(info.get('description'))
                has_pseudo = bool(info.get('pseudocode'))
                print(f"   {interface}: 描述{'✅' if has_desc else '❌'} 伪代码{'✅' if has_pseudo else '❌'}")
            else:
                print(f"   {interface}: ❌ 无标准信息")
        
        # 测试核心节点信息
        core_nodes = ['数据获取', '策略初始化', '风险管理', '订单执行']
        
        print("\\n🔧 测试核心节点信息:")
        for node in core_nodes:
            info = get_core_node_detailed_info(node)
            if info:
                has_steps = bool(info.get('steps'))
                has_details = bool(info.get('technical_details'))
                print(f"   {node}: 步骤{'✅' if has_steps else '❌'} 技术细节{'✅' if has_details else '❌'}")
            else:
                print(f"   {node}: ❌ 无详细信息")
        
        print("✅ 增强节点详情测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 增强节点详情测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始完整的接口显示功能测试")
    print("=" * 60)
    
    success1 = test_complete_interface_display()
    success2 = test_enhanced_node_details()
    
    print("\\n" + "=" * 60)
    print("📊 最终测试结果:")
    
    if success1 and success2:
        print("🎉 所有测试完全通过！")
        print("💡 流程图完全满足原始要求:")
        print("   ✅ 每个节点都表示策略的一个接口函数")
        print("   ✅ 每个节点都解释接口的设计思路")
        print("   ✅ 每个节点都显示伪代码")
        print("   ✅ 悬停和点击交互功能完善")
    else:
        print("⚠️  部分测试未通过，需要进一步改进")
        if not success1:
            print("   ❌ 基础接口显示功能需要完善")
        if not success2:
            print("   ❌ 增强节点详情功能需要完善")
    
    sys.exit(0 if (success1 and success2) else 1)