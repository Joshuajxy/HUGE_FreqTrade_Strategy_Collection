import streamlit as st
import json
from typing import Any, Dict

class FileLoadError(Exception):
    """文件加载错误"""
    def __init__(self, message: str, filename: str):
        self.message = message
        self.filename = filename
        super().__init__(f"{message}: {filename}")

class BacktestError(Exception):
    """回测执行错误"""
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)

def handle_file_load(uploaded_file) -> Dict[str, Any]:
    """安全地加载和验证策略文件"""
    try:
        content = json.load(uploaded_file)
        validate_strategy_analysis(content)
        return content
    except json.JSONDecodeError:
        raise FileLoadError("文件格式不正确，请确保是有效的JSON文件", uploaded_file.name)
    except KeyError as e:
        raise FileLoadError(f"缺少必要字段: {str(e)}", uploaded_file.name)
    except Exception as e:
        raise FileLoadError(f"文件加载失败: {str(e)}", uploaded_file.name)

def validate_strategy_analysis(data: Dict[str, Any]) -> None:
    """验证策略分析数据格式"""
    required_fields = ['strategy_name', 'interfaces', 'parameters']
    for field in required_fields:
        if field not in data:
            raise KeyError(field)

def handle_backtest_error(error: Exception) -> BacktestError:
    """处理回测执行错误"""
    error_msg = str(error)
    
    if "strategy" in error_msg.lower() and "not found" in error_msg.lower():
        return BacktestError("策略文件未找到或无效", "INVALID_STRATEGY")
    elif "data" in error_msg.lower() and ("not found" in error_msg.lower() or "insufficient" in error_msg.lower()):
        return BacktestError("历史数据不足或无法获取", "DATA_NOT_FOUND")
    elif "permission" in error_msg.lower():
        return BacktestError("权限不足，无法执行回测", "PERMISSION_ERROR")
    else:
        return BacktestError(f"回测执行失败: {error_msg}", "EXECUTION_ERROR")

def safe_execute(func, error_message: str = "操作失败"):
    """安全执行函数并处理错误"""
    try:
        return func()
    except Exception as e:
        st.error(f"{error_message}: {str(e)}")
        return None