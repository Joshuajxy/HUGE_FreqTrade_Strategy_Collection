import streamlit as st
import streamlit.components.v1 as components
import os

# Declare the custom component (frontend/build must exist after npm build)
_component_dir = os.path.dirname(os.path.abspath(__file__))
_build_dir = os.path.join(_component_dir, "frontend", "build")

# Debug: print the build directory path
print(f"[Component Debug] Build directory: {_build_dir}")
print(f"[Component Debug] Build directory exists: {os.path.exists(_build_dir)}")

_plotly_zoom_sync = components.declare_component(
    "plotly_zoom_sync",
    path=_build_dir
)

def plotly_zoom_sync(data, layout, config=None, key=None):
    """
    显示支持缩放同步的Plotly图。
    返回前端relayout事件数据（如x/y轴范围），可用于自动调整流程图。
    """
    event_data = _plotly_zoom_sync(
        args=dict(data=data, layout=layout, config=config or {}),
        key=key,
        default=None
    )
    return event_data
