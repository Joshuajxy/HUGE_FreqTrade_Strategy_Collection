#!/usr/bin/env python3
"""
Freqtrade策略可视化工具启动脚本
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import streamlit
        import plotly
        import networkx
        import pandas
        import numpy
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_virtual_env():
    """检查是否在虚拟环境中"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def main():
    """主启动函数"""
    print("🚀 启动Freqtrade策略可视化工具")
    print("=" * 50)
    
    # 检查虚拟环境
    if not check_virtual_env():
        print("⚠️  建议在虚拟环境中运行此应用")
        print("创建虚拟环境: python -m venv venv")
        print("激活虚拟环境: venv\\Scripts\\activate (Windows) 或 source venv/bin/activate (Linux/Mac)")
        print()
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")
    
    print("✅ 依赖检查通过")
    print("🌐 启动Web应用...")
    print("📍 应用将在浏览器中打开: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    try:
        # 启动Streamlit应用
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", "8501",
            "--server.address", "localhost"
        ]
        
        # 启动应用
        process = subprocess.Popen(cmd)
        
        # 等待几秒后打开浏览器
        time.sleep(3)
        try:
            webbrowser.open("http://localhost:8501")
        except:
            pass  # 如果无法打开浏览器，用户可以手动打开
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\\n👋 应用已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("按回车键退出...")
    sys.exit(0 if success else 1)