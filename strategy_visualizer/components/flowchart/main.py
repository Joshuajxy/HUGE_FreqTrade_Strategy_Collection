import streamlit as st
# from streamlit_plugins.plotly_zoom_sync import plotly_zoom_sync  # 暂时禁用
from .graph_builder import create_strategy_graph
from .plotly_renderer import create_flowchart_figure, create_legend_info, get_plotly_config
from .event_handler import get_selected_node
# from .event_handler import handle_node_selection  # 暂时未使用
from utils.data_models import StrategyAnalysis

def render_flowchart(strategy: StrategyAnalysis):
    """渲染交互式流程图主组件"""
    
    # 创建控制面板
    render_flowchart_controls()
    
    # 创建网络图
    G = create_strategy_graph(strategy)
    
    # 记录当前缩放/平移的坐标轴范围
    if 'flowchart_xrange' not in st.session_state:
        st.session_state.flowchart_xrange = [-1000, 1000]
    if 'flowchart_yrange' not in st.session_state:
        st.session_state.flowchart_yrange = [-200, 2200]

    # 创建Plotly图形，传递当前坐标轴范围
    fig = create_flowchart_figure(
        G, strategy,
        x_range=st.session_state.flowchart_xrange,
        y_range=st.session_state.flowchart_yrange
    )

    # 临时禁用自定义组件，使用标准 Plotly 图表确保正常显示
    st.info("🖱️ **流程图显示**：使用鼠标滚轮缩放 | 拖拽平移 | 双击重置视图")
    
    # 使用标准 Plotly 图表显示
    st.plotly_chart(
        fig,
        config=get_plotly_config(),
        key="strategy_flowchart",
        use_container_width=True
    )
    
    # 显示缩放说明（标准 Plotly 图表无法获取实时缩放状态）
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("缩放功能", "内置支持")
        st.caption("使用鼠标滚轮或工具栏")
    with col2:
        st.info("💡 **提示**：图表支持内置的缩放和平移功能，使用鼠标滚轮或右上角工具栏进行操作")
        st.warning("⚠️ **注意**：当前使用标准图表，无法显示实时缩放比例。如需实时缩放同步，请等待自定义组件修复。")
    
    # 暂时禁用事件数据处理
    event_data = None

    # 监听缩放/平移事件，自动更新坐标轴范围（实时同步）
    if event_data:
        updated = False
        if 'xaxis.range[0]' in event_data and 'xaxis.range[1]' in event_data:
            st.session_state.flowchart_xrange = [event_data['xaxis.range[0]'], event_data['xaxis.range[1]']]
            updated = True
        if 'yaxis.range[0]' in event_data and 'yaxis.range[1]' in event_data:
            st.session_state.flowchart_yrange = [event_data['yaxis.range[0]'], event_data['yaxis.range[1]']]
            updated = True
        if updated:
            st.rerun()

    # 显示图例
    render_flowchart_legend()

    # 显示选中节点的详细信息
    selected_node = get_selected_node()
    if selected_node:
        st.write(f"当前选中节点: **{selected_node}**")

def render_flowchart_controls():
    """渲染流程图控制面板"""
    with st.expander("🎛️ 流程图控制", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 刷新图表"):
                st.rerun()
        
        with col2:
            show_legend = st.checkbox("显示图例", value=True)
            st.session_state.show_flowchart_legend = show_legend
        
        with col3:
            auto_layout = st.checkbox("自动布局", value=True)
            st.session_state.auto_layout = auto_layout

def render_flowchart_legend():
    """渲染流程图图例"""
    if st.session_state.get('show_flowchart_legend', True):
        with st.expander("🏷️ 图例说明", expanded=False):
            legend_items = create_legend_info()
            
            st.write("**节点类型:**")
            cols = st.columns(3)
            
            for i, item in enumerate(legend_items):
                col_idx = i % 3
                with cols[col_idx]:
                    st.markdown(
                        f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
                        f'<div style="width: 20px; height: 20px; background-color: {item["color"]}; '
                        f'border-radius: 50%; margin-right: 10px;"></div>'
                        f'<span>{item["label"]}</span></div>',
                        unsafe_allow_html=True
                    )
            
            st.write("**交互说明:**")
            st.write("- 🖱️ 点击节点查看详细信息")
            st.write("- 🔍 悬停节点查看简要描述")
            st.write("- 🎯 绿色节点表示已实现的策略接口")
            st.write("- 🟡 黄色节点表示未实现的策略接口")

def render_node_statistics(strategy: StrategyAnalysis):
    """渲染节点统计信息"""
    st.subheader("📊 接口实现统计")
    
    # 统计接口实现情况
    total_interfaces = len(strategy.interfaces)
    implemented_interfaces = sum(1 for info in strategy.interfaces.values() if info.implemented)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总接口数", total_interfaces)
    
    with col2:
        st.metric("已实现", implemented_interfaces)
    
    with col3:
        implementation_rate = (implemented_interfaces / total_interfaces * 100) if total_interfaces > 0 else 0
        st.metric("实现率", f"{implementation_rate:.1f}%")
    
    # 显示未实现的接口
    unimplemented = [name for name, info in strategy.interfaces.items() if not info.implemented]
    if unimplemented:
        st.write("**未实现的接口:**")
        for interface in unimplemented:
            st.write(f"- {interface}")

def render_execution_flow_info():
    """渲染执行流程说明"""
    with st.expander("ℹ️ 执行流程说明", expanded=False):
        st.write("""
        **Freqtrade策略执行流程:**
        
        1. **数据获取** - 从交易所获取OHLCV数据
        2. **策略初始化** - 加载策略参数和配置
        3. **指标计算** - 执行populate_indicators计算技术指标
        4. **信号生成** - 并行执行populate_buy_trend和populate_sell_trend
        5. **风险管理** - 检查止损、仓位管理等风险控制
        6. **订单执行** - 向交易所发送交易订单
        
        **策略接口说明:**
        - 绿色节点：已在当前策略中实现的接口
        - 黄色节点：freqtrade标准接口但当前策略未实现
        - 蓝色节点：freqtrade核心执行流程（不需要策略实现）
        """)