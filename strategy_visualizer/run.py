#!/usr/bin/env python3
"""
Freqtrade策略可视化工具启动脚本
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    print("🚀 启动Freqtrade策略可视化工具...")
    print("📍 应用将在浏览器中打开: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    try:
        # 启动Streamlit应用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    main()