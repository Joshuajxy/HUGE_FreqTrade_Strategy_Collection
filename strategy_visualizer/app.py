import streamlit as st
import json
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.data_models import StrategyAnalysis
from utils.error_handling import handle_file_load, FileLoadError
from components.strategy_details import render_strategy_details

def main():
    st.set_page_config(
        page_title="Freqtrade策略可视化工具",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("🚀 Freqtrade策略可视化分析工具")
    
    # 页面顶部 - 文件上传和配置
    st.markdown("<div style='margin-bottom: 1.2em'></div>", unsafe_allow_html=True)
    with st.container():
        st.header("📁 策略文件")
        uploaded_file = st.file_uploader(
            "上传策略分析文件", 
            type=['json'],
            help="请上传经过LM处理的标准化策略分析JSON文件",
            key="top_file_uploader"
        )
        if uploaded_file:
            try:
                strategy_data = load_strategy_file(uploaded_file)
                if strategy_data:
                    st.session_state.current_strategy = strategy_data
                    st.success(f"已加载策略: {strategy_data.strategy_name}")
            except FileLoadError as e:
                st.error(f"文件加载失败: {e.message}")
            except Exception as e:
                st.error(f"未知错误: {str(e)}")

    # 主界面布局
    if 'current_strategy' in st.session_state:
        # 右侧信息面板是否显示
        if 'show_info_panel' not in st.session_state:
            st.session_state.show_info_panel = True
        col1, col2 = st.columns([4, 0.01] if not st.session_state.show_info_panel else [2, 1])
        
        with col1:
            st.header("📊 策略执行流程图")
            from components.flowchart import render_flowchart
            render_flowchart(st.session_state.current_strategy)
        
        def toggle_info_panel():
            st.session_state.show_info_panel = not st.session_state.show_info_panel

        with col2:
            st.button(
                "隐藏详情面板" if st.session_state.show_info_panel else "显示详情面板",
                key="toggle_info_panel",
                help="点击隐藏/显示右侧详情信息，最大化流程图区域",
                on_click=toggle_info_panel
            )
            if st.session_state.show_info_panel:
                st.header("📋 策略详情")
                from components.strategy_details import render_strategy_details
                render_strategy_details(st.session_state.current_strategy)

        
        # 回测面板
        st.header("🔄 回测分析")
        from components.backtest import render_backtest_panel
        render_backtest_panel(st.session_state.current_strategy)
    else:
        st.info("👆 请在页面上方上传策略分析文件开始使用")
        
        # 显示示例文件信息
        st.subheader("📖 使用说明")
        st.write("1. 使用LM工具分析freqtrade策略代码")
        st.write("2. 生成标准化的JSON分析文件")
        st.write("3. 上传JSON文件查看可视化分析结果")
        
        # 提供示例文件下载
        render_sample_file_download(current_dir)

def load_strategy_file(uploaded_file) -> StrategyAnalysis:
    """加载并验证策略文件"""
    data = handle_file_load(uploaded_file)
    return StrategyAnalysis.from_dict(data)

def render_sample_file_download(current_dir: str):
    """渲染示例文件下载功能"""
    try:
        example_path = os.path.join(current_dir, "prompts", "examples", "sample_analysis.json")
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                sample_data = f.read()
            
            st.download_button(
                label="📥 下载示例分析文件",
                data=sample_data,
                file_name="sample_analysis.json",
                mime="application/json"
            )
        else:
            st.info("💡 示例文件不可用，请直接上传您的策略分析文件")
            
            # 显示示例JSON格式
            with st.expander("📋 查看示例JSON格式", expanded=False):
                sample_json = {
                    "strategy_name": "YourStrategy",
                    "description": "策略描述",
                    "interfaces": {
                        "populate_indicators": {
                            "implemented": True,
                            "description": "计算技术指标",
                            "pseudocode": "计算RSI、布林带等指标",
                            "input_params": [],
                            "output_description": "返回包含指标的DataFrame",
                            "logic_explanation": "详细逻辑说明"
                        }
                    },
                    "parameters": {
                        "roi": {"0": 0.1},
                        "stoploss": -0.1,
                        "timeframe": "5m"
                    }
                }
                st.json(sample_json)
                
    except Exception as e:
        st.warning(f"示例文件处理出错: {str(e)}")
        st.info("您可以直接上传策略分析JSON文件开始使用")

if __name__ == "__main__":
    main()