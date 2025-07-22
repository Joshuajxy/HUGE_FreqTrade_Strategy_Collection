#!/usr/bin/env python3
"""
应用功能测试脚本
"""

import sys
import os
import json
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_imports():
    """测试所有模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from utils.data_models import StrategyAnalysis
        print("✅ utils.data_models 导入成功")
        
        from utils.error_handling import handle_file_load, FileLoadError
        print("✅ utils.error_handling 导入成功")
        
        from components.flowchart import render_flowchart
        print("✅ components.flowchart 导入成功")
        
        from components.backtest import render_backtest_panel
        print("✅ components.backtest 导入成功")
        
        from components.strategy_details import render_strategy_details
        print("✅ components.strategy_details 导入成功")
        
        import app
        print("✅ app 主模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n🧪 测试数据模型...")
    
    try:
        from utils.data_models import StrategyAnalysis
        
        # 测试示例数据
        sample_data = {
            "strategy_name": "TestStrategy",
            "description": "测试策略",
            "interfaces": {
                "populate_indicators": {
                    "implemented": True,
                    "description": "计算指标",
                    "pseudocode": "计算RSI",
                    "input_params": [],
                    "output_description": "返回DataFrame",
                    "logic_explanation": "计算技术指标"
                }
            },
            "indicators": [],
            "parameters": {"roi": {"0": 0.1}, "stoploss": -0.1},
            "buy_conditions": [],
            "sell_conditions": [],
            "risk_management": {}
        }
        
        strategy = StrategyAnalysis.from_dict(sample_data)
        print(f"✅ 策略对象创建成功: {strategy.strategy_name}")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_sample_file():
    """测试示例文件"""
    print("\n🧪 测试示例文件...")
    
    try:
        sample_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            from utils.data_models import StrategyAnalysis
            strategy = StrategyAnalysis.from_dict(sample_data)
            
            print(f"✅ 示例文件加载成功: {strategy.strategy_name}")
            print(f"   - 接口数量: {len(strategy.interfaces)}")
            print(f"   - 已实现接口: {sum(1 for info in strategy.interfaces.values() if info.implemented)}")
            
            return True
        else:
            print(f"⚠️  示例文件不存在: {sample_path}")
            return True  # 不是致命错误
            
    except Exception as e:
        print(f"❌ 示例文件测试失败: {e}")
        return False

def test_components():
    """测试组件功能"""
    print("\n🧪 测试组件功能...")
    
    try:
        from components.flowchart.graph_builder import create_strategy_graph
        from utils.data_models import StrategyAnalysis
        
        # 创建测试策略
        test_data = {
            "strategy_name": "TestStrategy",
            "description": "测试策略",
            "interfaces": {
                "populate_indicators": {
                    "implemented": True,
                    "description": "计算指标",
                    "pseudocode": "计算RSI",
                    "input_params": [],
                    "output_description": "返回DataFrame",
                    "logic_explanation": "计算技术指标"
                }
            },
            "indicators": [],
            "parameters": {"roi": {"0": 0.1}, "stoploss": -0.1},
            "buy_conditions": [],
            "sell_conditions": [],
            "risk_management": {}
        }
        
        strategy = StrategyAnalysis.from_dict(test_data)
        
        # 测试图结构构建
        G = create_strategy_graph(strategy)
        print(f"✅ 流程图构建成功: {len(G.nodes())} 个节点, {len(G.edges())} 条边")
        
        return True
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始应用功能测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_data_models,
        test_sample_file,
        test_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用可以正常运行")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)