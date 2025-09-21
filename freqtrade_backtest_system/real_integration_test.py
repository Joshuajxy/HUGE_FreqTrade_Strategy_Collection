#!/usr/bin/env python3
"""
Complete integration test with real freqtrade execution
"""
import sys
from pathlib import Path
import subprocess
import json
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from components.execution.backtest_executor import BacktestExecutor
from utils.data_models import BacktestConfig
from utils.error_handling import ErrorHandler

def check_freqtrade_installation():
    """Check if freqtrade is properly installed"""
    print("🔍 检查 Freqtrade 安装...")

    try:
        result = subprocess.run([sys.executable, "-m", "freqtrade", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Freqtrade 已安装: {result.stdout.strip()}")
            return True
        else:
            print("❌ Freqtrade 命令执行失败")
            return False

    except FileNotFoundError:
        print("❌ Freqtrade 未找到，请先安装")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def download_backtest_data(config: BacktestConfig):
    """Download historical data needed for the backtest"""
    print("\n📥 下载回测数据...")
    try:
        cmd = [
            sys.executable, "-m", "freqtrade",
            "download-data",
            "--exchange", "binance",
            "-t", config.timeframe,
            "--pairs", *config.pairs,
            "--timerange", f"{config.start_date.strftime('%Y%m%d')}-{config.end_date.strftime('%Y%m%d')}"
        ]
        print(f"🔩 执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
        
        for line in iter(process.stdout.readline, ''):
            print(f"   {line.strip()}")
        
        process.wait() 
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, "下载脚本执行失败")

        print("✅ 数据下载成功。")
        ErrorHandler.log_info("Successfully downloaded backtest data.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据下载失败 (返回码: {e.returncode})")
        ErrorHandler.log_error(f"Failed to download data (return code: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ 数据下载时发生未知错误: {e}")
        ErrorHandler.log_error(f"An unknown error occurred during data download: {e}")
        return False

def run_real_backtest(strategy_name: str, config: BacktestConfig):
    """Run a real backtest with freqtrade"""
    print(f"\n🚀 执行真实回测: {strategy_name}...")

    try:
        print("📊 回测配置:")
        print(f"   时间范围: {config.start_date} 到 {config.end_date}")
        print(f"   时间框架: {config.timeframe}")
        print(f"   交易对: {config.pairs}")
        print(f"   初始资金: ${config.initial_balance}")

        # Initialize executor
        executor = BacktestExecutor()

        # Execute backtest
        print("\n⏳ 开始回测执行...")
        result = executor.execute_backtest(strategy_name, config)

        if result and result.status.name == "COMPLETED":
            print("✅ 回测成功完成!")
            print(f"   执行时间: {result.execution_time:.2f}秒")
            if hasattr(result, 'metrics'):
                print(f"   总收益率: {result.metrics.total_return_pct:.2f}%")
                print(f"   胜率: {result.metrics.win_rate:.2f}%")
                if hasattr(result.metrics, 'total_trades'):
                    print(f"   总交易数: {result.metrics.total_trades}")
            return True
        else:
            print(f"❌ 回测失败: {result.error_message if result else '未知错误'}")
            return False

    except Exception as e:
        print(f"❌ 回测执行异常: {e}")
        return False

def main():
    """Main integration test function"""
    print("🧪 开始完整集成测试...")
    print("=" * 60)

    # Step 1: Check freqtrade installation
    if not check_freqtrade_installation():
        print("\n❌ Freqtrade 未正确安装，无法进行完整测试")
        return False

    # Step 2: Define test strategy and config
    strategy_name = "ADX_15M_USDT"
    print(f"\n📝 使用指定的策略: {strategy_name}")
    config = BacktestConfig(
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
        timeframe="15m",
        pairs=["BTC/USDT", "ETH/USDT"],
        initial_balance=1000.0,
        max_open_trades=3,
        fee=0.001
    )

    # Step 3: Download data
    if not download_backtest_data(config):
        print("\n❌ 因数据下载失败，测试中止。\n")
        return False

    # Step 4: Run real backtest
    success = run_real_backtest(strategy_name, config)

    print("\n" + "=" * 60)
    if success:
        print("🎉 完整集成测试通过!")
        print("✅ 系统可以正常执行真实回测")
    else:
        print("❌ 集成测试失败")
        print("请检查系统配置和依赖")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)