#!/usr/bin/env python3
"""
演示增强的Freqtrade测试功能
展示详细的命令执行结果和日志分析
"""
import subprocess
import json
import time
from pathlib import Path

def demonstrate_enhanced_logging():
    """演示增强的日志记录功能"""
    print("🔥 FREQTRADE ENHANCED LOGGING DEMONSTRATION")
    print("=" * 60)

    # 检查freqtrade是否可用
    try:
        result = subprocess.run(["freqtrade", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Freqtrade detected: {result.stdout.split('Freqtrade Version:')[1].strip()}")
        else:
            print("❌ Freqtrade command failed")
            return
    except FileNotFoundError:
        print("❌ Freqtrade not found. Please install freqtrade first:")
        print("   pip install freqtrade")
        return

    # 演示不同的freqtrade命令
    demo_commands = [
        {
            "name": "Version Check",
            "cmd": ["freqtrade", "--version"],
            "description": "Check freqtrade version and system info"
        },
        {
            "name": "Help Command",
            "cmd": ["freqtrade", "--help"],
            "description": "Show freqtrade help information"
        },
        {
            "name": "Invalid Command",
            "cmd": ["freqtrade", "invalid-command"],
            "description": "Test error handling with invalid command"
        }
    ]

    for i, cmd_info in enumerate(demo_commands, 1):
        print(f"\n{'='*60}")
        print(f"🧪 DEMO {i}: {cmd_info['name']}")
        print(f"📝 {cmd_info['description']}")
        print(f"🔧 Command: {' '.join(cmd_info['cmd'])}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd_info['cmd'],
                capture_output=True,
                text=True,
                timeout=30
            )
            execution_time = time.time() - start_time

            print("\n🔍 EXECUTION RESULTS:")
            print(f"⏱️  Execution time: {execution_time:.3f} seconds")
            print(f"🔢 Return code: {result.returncode}")

            # 分析stdout
            if result.stdout:
                stdout_lines = result.stdout.split('\n')
                print(f"\n📄 STDOUT ({len(result.stdout)} chars, {len(stdout_lines)} lines):")

                # 显示前几行
                for j, line in enumerate(stdout_lines[:5]):
                    if line.strip():
                        print(f"   {j+1}: {line.strip()}")

                if len(stdout_lines) > 5:
                    print(f"   ... and {len(stdout_lines) - 5} more lines")

                # 统计日志级别
                log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                log_counts = {}
                for level in log_levels:
                    count = result.stdout.count(level)
                    if count > 0:
                        log_counts[level] = count

                if log_counts:
                    print(f"📋 Log levels found: {log_counts}")

            # 分析stderr
            if result.stderr:
                stderr_lines = result.stderr.split('\n')
                print(f"\n⚠️  STDERR ({len(result.stderr)} chars, {len(stderr_lines)} lines):")

                for j, line in enumerate(stderr_lines[:3]):
                    if line.strip():
                        print(f"   {j+1}: {line.strip()}")

                if len(stderr_lines) > 3:
                    print(f"   ... and {len(stderr_lines) - 3} more lines")

            # 返回码分析
            return_codes = {
                0: "✅ SUCCESS",
                1: "❌ GENERAL ERROR",
                2: "❌ USAGE ERROR",
                126: "❌ PERMISSION DENIED",
                127: "❌ COMMAND NOT FOUND"
            }

            meaning = return_codes.get(result.returncode, f"❓ UNKNOWN ({result.returncode})")
            print(f"\n📊 RESULT: {meaning}")

            # 性能统计
            total_chars = len(result.stdout) + len(result.stderr)
            print("\n📈 PERFORMANCE:")
            print(f"   Execution time: {execution_time:.3f} seconds")
            print(f"   Total output: {total_chars} characters")
            print(f"   Stdout: {len(result.stdout)} chars")
            print(f"   Stderr: {len(result.stderr)} chars")

        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT: Command took too long to execute")
        except Exception as e:
            print(f"💥 ERROR: {str(e)}")

    print(f"\n{'='*60}")
    print("🎉 Enhanced logging demonstration completed!")
    print("\n💡 Key features demonstrated:")
    print("   • Detailed execution timing")
    print("   • Comprehensive output analysis")
    print("   • Log level statistics")
    print("   • Error pattern recognition")
    print("   • Performance metrics")
    print("   • Return code interpretation")

if __name__ == "__main__":
    demonstrate_enhanced_logging()
