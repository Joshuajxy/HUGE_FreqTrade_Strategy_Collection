import streamlit as st
from .graph_builder import create_strategy_graph
from .plotly_renderer import create_flowchart_figure, create_legend_info, get_plotly_config
from .event_handler import handle_node_selection, get_selected_node
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

    # 使用 streamlit-plotly-events 捕获 zoom/pan 事件
    # ⚠️ streamlit-plotly-events 不支持 zoom/pan/relayout 事件，无法实现滚轮缩放实时同步
    # 恢复 st.plotly_chart 用于缩放/平移，config 参数可用，但仅在刷新/按钮等事件后同步
    chart_event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="strategy_flowchart",
        config=get_plotly_config()
    )

    # 监听缩放/平移事件，自动更新坐标轴范围（仅在 Streamlit 触发 rerun 时有效）
    if hasattr(chart_event, 'relayoutData') and isinstance(chart_event.relayoutData, dict) and chart_event.relayoutData:
        relayout = chart_event.relayoutData
        updated = False
        if 'xaxis.range[0]' in relayout and 'xaxis.range[1]' in relayout:
            st.session_state.flowchart_xrange = [relayout['xaxis.range[0]'], relayout['xaxis.range[1]']]
            updated = True
        if 'yaxis.range[0]' in relayout and 'yaxis.range[1]' in relayout:
            st.session_state.flowchart_yrange = [relayout['yaxis.range[0]'], relayout['yaxis.range[1]']]
            updated = True
        if updated:
            st.experimental_rerun()

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