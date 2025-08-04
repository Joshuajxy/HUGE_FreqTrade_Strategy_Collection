"""
Installation guide and setup helper
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from utils.error_handling import ErrorHandler

class InstallationGuide:
    """Installation guide and setup helper"""
    
    def __init__(self):
        """Initialize installation guide"""
        self.required_packages = [
            "freqtrade",
            "streamlit",
            "pandas",
            "numpy", 
            "plotly",
            "psutil"
        ]
        
        self.optional_packages = [
            "nbformat",
            "nbconvert", 
            "streamlit-option-menu",
            "papermill",
            "jupyter",
            "jupyterlab"
        ]
    
    def render_installation_guide(self):
        """Render installation guide in Streamlit"""
        st.header("🛠️ 系统安装指南")
        
        # System check
        st.subheader("📋 系统检查")
        self._render_system_check()
        
        # Installation instructions
        st.subheader("📦 安装说明")
        self._render_installation_instructions()
        
        # Freqtrade setup
        st.subheader("⚙️ Freqtrade 配置")
        self._render_freqtrade_setup()
        
        # Troubleshooting
        st.subheader("🔧 故障排除")
        self._render_troubleshooting()
    
    def _render_system_check(self):
        """Render system check section"""
        st.write("检查系统依赖和配置...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            st.success(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            st.error(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro} (需要 >= 3.8)")
        
        # Check required packages
        st.write("**必需包检查:**")
        missing_required = []
        
        for package in self.required_packages:
            try:
                __import__(package)
                st.success(f"✅ {package}")
            except ImportError:
                st.error(f"❌ {package} - 未安装")
                missing_required.append(package)
        
        # Check optional packages
        st.write("**可选包检查:**")
        missing_optional = []
        
        for package in self.optional_packages:
            try:
                __import__(package)
                st.success(f"✅ {package}")
            except ImportError:
                st.warning(f"⚠️ {package} - 未安装 (可选)")
                missing_optional.append(package)
        
        # Check freqtrade command
        st.write("**Freqtrade命令检查:**")
        if self._check_freqtrade_command():
            st.success("✅ freqtrade 命令可用")
        else:
            st.error("❌ freqtrade 命令不可用")
        
        # Summary
        if missing_required:
            st.error(f"⚠️ 缺少必需包: {', '.join(missing_required)}")
        else:
            st.success("🎉 所有必需包都已安装！")
    
    def _check_freqtrade_command(self) -> bool:
        """Check if freqtrade command is available"""
        try:
            result = subprocess.run(
                ["freqtrade", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _render_installation_instructions(self):
        """Render installation instructions"""
        tab1, tab2, tab3 = st.tabs(["快速安装", "详细安装", "Docker安装"])
        
        with tab1:
            st.write("### 🚀 快速安装")
            st.code("""
# 1. 安装必需包
pip install freqtrade streamlit pandas numpy plotly psutil

# 2. 安装可选包（推荐）
pip install nbformat nbconvert streamlit-option-menu papermill jupyter jupyterlab

# 3. 启动应用
streamlit run app.py
            """, language="bash")
            
            if st.button("📋 复制安装命令"):
                st.code("pip install freqtrade streamlit pandas numpy plotly psutil nbformat nbconvert streamlit-option-menu papermill jupyter jupyterlab")
        
        with tab2:
            st.write("### 📖 详细安装步骤")
            
            st.write("**步骤 1: 创建虚拟环境**")
            st.code("""
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\\Scripts\\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate
            """, language="bash")
            
            st.write("**步骤 2: 安装Freqtrade**")
            st.code("""
# 安装freqtrade
pip install freqtrade

# 验证安装
freqtrade --version
            """, language="bash")
            
            st.write("**步骤 3: 安装系统依赖**")
            st.code("""
# 从requirements.txt安装
pip install -r requirements.txt

# 或手动安装
pip install streamlit pandas numpy plotly psutil
            """, language="bash")
            
            st.write("**步骤 4: 安装可选依赖**")
            st.code("""
# Jupyter集成
pip install nbformat nbconvert papermill jupyter jupyterlab

# UI增强
pip install streamlit-option-menu
            """, language="bash")
        
        with tab3:
            st.write("### 🐳 Docker安装")
            st.code("""
# 构建Docker镜像
docker build -t freqtrade-backtest-system .

# 运行容器
docker run -p 8501:8501 freqtrade-backtest-system

# 使用docker-compose
docker-compose up -d
            """, language="bash")
            
            st.write("**Dockerfile示例:**")
            st.code("""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
            """, language="dockerfile")
    
    def _render_freqtrade_setup(self):
        """Render freqtrade setup section"""
        st.write("### ⚙️ Freqtrade配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本配置:**")
            st.code("""
# 创建freqtrade配置目录
mkdir freqtrade_config

# 生成示例配置
freqtrade create-userdir --userdir freqtrade_config

# 下载示例策略
freqtrade download-data --pairs BTC/USDT ETH/USDT --timeframes 5m 1h --days 30
            """, language="bash")
        
        with col2:
            st.write("**数据下载:**")
            st.code("""
# 下载历史数据
freqtrade download-data \\
    --exchange binance \\
    --pairs BTC/USDT ETH/USDT \\
    --timeframes 5m 15m 1h \\
    --days 90
            """, language="bash")
        
        st.write("**配置文件示例:**")
        with st.expander("查看config.json示例"):
            st.code("""
{
    "max_open_trades": 3,
    "stake_currency": "USDT",
    "stake_amount": 100,
    "tradable_balance_ratio": 0.99,
    "fiat_display_currency": "USD",
    "dry_run": true,
    "cancel_open_orders_on_exit": false,
    "trading_mode": "spot",
    "margin_mode": "",
    "unfilledtimeout": {
        "entry": 10,
        "exit": 10,
        "exit_timeout_count": 0,
        "unit": "minutes"
    },
    "entry_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1,
        "price_last_balance": 0.0,
        "check_depth_of_market": {
            "enabled": false,
            "bids_to_ask_delta": 1
        }
    },
    "exit_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1
    },
    "exchange": {
        "name": "binance",
        "key": "",
        "secret": "",
        "ccxt_config": {},
        "ccxt_async_config": {},
        "pair_whitelist": [
            "BTC/USDT",
            "ETH/USDT"
        ],
        "pair_blacklist": []
    },
    "pairlists": [
        {"method": "StaticPairList"}
    ],
    "edge": {
        "enabled": false
    },
    "telegram": {
        "enabled": false
    },
    "api_server": {
        "enabled": false
    },
    "bot_name": "freqtrade",
    "initial_state": "running",
    "force_entry_enable": false,
    "internals": {
        "process_throttle_secs": 5
    }
}
            """, language="json")
    
    def _render_troubleshooting(self):
        """Render troubleshooting section"""
        st.write("### 🔧 常见问题解决")
        
        problems = [
            {
                "title": "freqtrade命令未找到",
                "symptoms": ["FileNotFoundError", "freqtrade: command not found"],
                "solutions": [
                    "确保已安装freqtrade: `pip install freqtrade`",
                    "检查PATH环境变量",
                    "尝试使用完整路径: `python -m freqtrade`",
                    "重新激活虚拟环境"
                ]
            },
            {
                "title": "依赖包冲突",
                "symptoms": ["ImportError", "ModuleNotFoundError", "版本冲突"],
                "solutions": [
                    "创建新的虚拟环境",
                    "使用pip freeze检查已安装包",
                    "逐个安装依赖包",
                    "使用pip install --upgrade升级包"
                ]
            },
            {
                "title": "Streamlit启动失败",
                "symptoms": ["端口占用", "权限错误", "配置错误"],
                "solutions": [
                    "更改端口: `streamlit run app.py --server.port 8502`",
                    "检查防火墙设置",
                    "以管理员权限运行",
                    "清除streamlit缓存: `streamlit cache clear`"
                ]
            },
            {
                "title": "数据下载失败",
                "symptoms": ["网络错误", "API限制", "交易所连接失败"],
                "solutions": [
                    "检查网络连接",
                    "使用VPN或代理",
                    "更换数据源交易所",
                    "减少下载的数据量"
                ]
            }
        ]
        
        for i, problem in enumerate(problems):
            with st.expander(f"❓ {problem['title']}"):
                st.write("**症状:**")
                for symptom in problem['symptoms']:
                    st.write(f"- {symptom}")
                
                st.write("**解决方案:**")
                for solution in problem['solutions']:
                    st.write(f"- {solution}")
        
        # Contact support
        st.write("### 📞 获取帮助")
        st.info("""
        如果以上解决方案都无法解决问题，请：
        
        1. 查看系统日志文件 `logs/app.log`
        2. 运行调试脚本 `python debug_test.py`
        3. 检查GitHub Issues页面
        4. 联系技术支持
        """)
    
    def check_installation_status(self) -> Dict[str, bool]:
        """Check installation status of all components"""
        status = {}
        
        # Check required packages
        for package in self.required_packages:
            try:
                __import__(package)
                status[package] = True
            except ImportError:
                status[package] = False
        
        # Check optional packages
        for package in self.optional_packages:
            try:
                __import__(package)
                status[f"{package}_optional"] = True
            except ImportError:
                status[f"{package}_optional"] = False
        
        # Check freqtrade command
        status['freqtrade_command'] = self._check_freqtrade_command()
        
        return status
    
    def get_installation_commands(self) -> List[str]:
        """Get list of installation commands"""
        commands = [
            "pip install freqtrade",
            "pip install streamlit pandas numpy plotly psutil",
            "pip install nbformat nbconvert streamlit-option-menu",
            "pip install papermill jupyter jupyterlab"
        ]
        return commands