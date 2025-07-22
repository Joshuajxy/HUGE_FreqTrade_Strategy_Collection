import streamlit as st
from utils.data_models import StrategyAnalysis

def render_interface_details(strategy: StrategyAnalysis):
    """渲染接口实现详情"""
    
    st.subheader("🔧 接口实现")
    
    # 统计实现的接口数量
    implemented_count = sum(1 for info in strategy.interfaces.values() if info.implemented)
    total_count = len(strategy.interfaces)
    
    st.write(f"已实现接口: {implemented_count}/{total_count}")
    
    # 显示每个接口的详情
    for interface_name, interface_info in strategy.interfaces.items():
        if interface_info.implemented:
            with st.expander(f"✅ {interface_name}", expanded=False):
                st.write(f"**功能描述:** {interface_info.description}")
                
                if interface_info.logic_explanation:
                    st.write(f"**逻辑说明:** {interface_info.logic_explanation}")
                
                if interface_info.pseudocode:
                    st.write("**伪代码:**")
                    st.code(interface_info.pseudocode, language='python')
                
                if interface_info.input_params:
                    st.write("**输入参数:**")
                    for param in interface_info.input_params:
                        st.write(f"- **{param.name}** ({param.type}): {param.description}")
                
                if interface_info.output_description:
                    st.write(f"**输出:** {interface_info.output_description}")
        else:
            with st.expander(f"❌ {interface_name} (未实现)", expanded=False):
                st.write("该接口未在当前策略中实现")
                if interface_info.description:
                    st.write(f"**标准功能:** {interface_info.description}")