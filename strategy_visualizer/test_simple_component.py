#!/usr/bin/env python3
"""
测试最简单的自定义组件
验证 Streamlit 组件基础设施
"""

import streamlit as st
import streamlit.components.v1 as components
import os

# 创建一个内联的 HTML 组件来测试基础功能
def test_inline_component():
    st.title("🧪 内联组件测试")
    
    # 使用内联 HTML 创建简单的交互组件
    html_code = """
    <div style="padding: 20px; border: 2px solid #0066cc; border-radius: 10px; text-align: center;">
        <h3>🎯 简单交互测试</h3>
        <p id="status">等待点击...</p>
        <button onclick="handleClick()" style="
            padding: 10px 20px; 
            font-size: 16px;
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        ">点击测试</button>
        
        <script>
            let clickCount = 0;
            
            function handleClick() {
                clickCount++;
                document.getElementById('status').innerText = `已点击 ${clickCount} 次`;
                
                // 尝试与 Streamlit 通信
                if (window.parent && window.parent.postMessage) {
                    window.parent.postMessage({
                        type: 'streamlit:componentReady',
                        data: { clicks: clickCount }
                    }, '*');
                }
            }
            
            // 设置组件高度
            if (window.parent && window.parent.postMessage) {
                window.parent.postMessage({
                    type: 'streamlit:setFrameHeight',
                    data: { height: 200 }
                }, '*');
            }
        </script>
    </div>
    """
    
    # 使用 Streamlit 的内联 HTML 组件
    result = components.html(html_code, height=200)
    
    if result:
        st.write("📊 接收到的数据：", result)
    else:
        st.info("等待组件交互...")

def test_file_component():
    st.title("📁 文件组件测试")
    
    # 检查构建目录
    build_dir = os.path.join(os.path.dirname(__file__), "streamlit_plugins", "frontend", "build")
    st.write(f"构建目录: {build_dir}")
    st.write(f"目录存在: {os.path.exists(build_dir)}")
    
    if os.path.exists(build_dir):
        st.write("📂 构建目录内容:")
        for item in os.listdir(build_dir):
            item_path = os.path.join(build_dir, item)
            if os.path.isdir(item_path):
                st.write(f"  📁 {item}/")
            else:
                st.write(f"  📄 {item}")
    
    # 尝试加载文件组件
    try:
        from streamlit_plugins.plotly_zoom_sync import plotly_zoom_sync
        st.success("✅ 组件导入成功")
        
        # 测试简单数据
        test_data = [{"x": [1, 2, 3], "y": [1, 4, 2], "type": "scatter"}]
        test_layout = {"title": "测试图表"}
        
        result = plotly_zoom_sync(
            data=test_data,
            layout=test_layout,
            key="test_component"
        )
        
        if result:
            st.write("📊 组件返回数据：", result)
        else:
            st.info("等待组件事件...")
            
    except Exception as e:
        st.error(f"❌ 组件加载失败：{str(e)}")
        st.exception(e)

def main():
    st.set_page_config(page_title="组件测试", layout="wide")
    
    tab1, tab2 = st.tabs(["内联组件测试", "文件组件测试"])
    
    with tab1:
        test_inline_component()
    
    with tab2:
        test_file_component()

if __name__ == "__main__":
    main()
