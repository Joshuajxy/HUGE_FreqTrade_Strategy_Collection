#!/usr/bin/env python3
"""
简单的自定义组件测试
用于验证 Streamlit 组件基础设施是否正常工作
"""

import streamlit as st
from streamlit_plugins.plotly_zoom_sync import plotly_zoom_sync

def test_simple_component():
    st.title("🧪 自定义组件测试")
    
    st.write("测试自定义组件是否能正常加载...")
    
    # 创建简单的测试数据
    simple_data = [
        {
            "x": [1, 2, 3, 4],
            "y": [10, 11, 12, 13],
            "type": "scatter",
            "mode": "lines+markers",
            "name": "测试数据"
        }
    ]
    
    simple_layout = {
        "title": "简单测试图表",
        "xaxis": {"title": "X轴"},
        "yaxis": {"title": "Y轴"}
    }
    
    simple_config = {
        "displayModeBar": True,
        "scrollZoom": True
    }
    
    try:
        st.write("尝试加载自定义组件...")
        
        # 测试自定义组件
        event_data = plotly_zoom_sync(
            data=simple_data,
            layout=simple_layout,
            config=simple_config,
            key="test_component"
        )
        
        st.success("✅ 自定义组件加载成功！")
        
        if event_data:
            st.write("📊 接收到的事件数据：")
            st.json(event_data)
        else:
            st.info("等待缩放事件...")
            
    except Exception as e:
        st.error(f"❌ 自定义组件加载失败：{str(e)}")
        st.write("错误详情：")
        st.exception(e)

if __name__ == "__main__":
    test_simple_component()
