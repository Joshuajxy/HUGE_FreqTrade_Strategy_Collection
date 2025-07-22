import plotly.graph_objects as go
import networkx as nx
from typing import Dict, Tuple, List
from utils.data_models import StrategyAnalysis
from utils.freqtrade_interfaces import FreqtradeInterfaceDefinitions

def create_flowchart_figure(G: nx.DiGraph, strategy: StrategyAnalysis, x_range=None, y_range=None) -> go.Figure:
    """创建TensorBoard风格的大框图流程图"""
    # 使用层次化布局
    pos = create_hierarchical_layout(G)
    
    # 创建TensorBoard风格的节点和边
    shapes, annotations = create_tensorboard_nodes(G, pos, strategy)
    edge_shapes = create_curved_edges(G, pos)
    
    # 创建图形
    fig = go.Figure()
    
    # 添加一个空的散点图作为基础（用于交互）
    fig.add_trace(go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode='markers',
        marker=dict(size=1, opacity=0),  # 隐形标记点
        text=[node for node in G.nodes()],
        hoverinfo='text',
        showlegend=False
    ))
    
    # 更新布局，添加节点形状和连接线
    layout_config = create_tensorboard_layout()

    # 计算缩放比例（以x轴范围为主，初始范围[-1000, 1000]为100%）
    default_xrange = [-1000, 1000]
    default_yrange = [-200, 2200]
    cur_xrange = x_range if x_range else layout_config['xaxis']['range']
    cur_yrange = y_range if y_range else layout_config['yaxis']['range']
    x_zoom = (default_xrange[1] - default_xrange[0]) / (cur_xrange[1] - cur_xrange[0])
    y_zoom = (default_yrange[1] - default_yrange[0]) / (cur_yrange[1] - cur_yrange[0])
    zoom_ratio = min(x_zoom, y_zoom)
    zoom_percent = int(zoom_ratio * 100)
    print(f"[Zoom Debug] x_range={cur_xrange}, y_range={cur_yrange}, zoom_percent={zoom_percent}")

    # 缩放所有annotation字体
    def scale_font(font, base):
        f = dict(font) if font else {}
        f['size'] = int(f.get('size', base) * zoom_ratio)
        return f

    scaled_annotations = []
    for ann in annotations:
        ann2 = dict(ann)
        ann2['font'] = scale_font(ann.get('font'), 12)
        scaled_annotations.append(ann2)
    for ann in layout_config.get('annotations', []):
        ann2 = dict(ann)
        ann2['font'] = scale_font(ann.get('font'), 12)
        scaled_annotations.append(ann2)

    # 添加左上角缩放比例浮层
    scaled_annotations.append({
        'text': f'🔍 缩放: {zoom_percent}%',
        'showarrow': False,
        'xref': 'paper',
        'yref': 'paper',
        'x': 0.01,
        'y': 0.99,
        'xanchor': 'left',
        'yanchor': 'top',
        'font': {'color': '#1976D2', 'size': int(18 * zoom_ratio), 'family': 'monospace'},
        'bgcolor': 'rgba(255,255,255,0.7)',
        'bordercolor': '#1976D2',
        'borderpad': 4
    })

    layout_config['annotations'] = scaled_annotations
    layout_config['shapes'] = shapes + edge_shapes
    layout_config['xaxis']['range'] = cur_xrange
    layout_config['yaxis']['range'] = cur_yrange

    fig.update_layout(**layout_config)
    return fig

def create_hierarchical_layout(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    """创建层次化布局 - 适配所有freqtrade接口"""
    # 定义更详细的层次结构
    layers = {
        0: ['data_fetch'],
        1: ['informative_pairs'],
        2: ['strategy_init', 'bot_start'],
        3: ['bot_loop_start'],
        4: ['populate_indicators'],
        5: ['populate_buy_trend', 'populate_sell_trend'],
        6: ['confirm_trade_entry', 'custom_sell', 'custom_exit', 'confirm_trade_exit'],
        7: ['leverage', 'risk_management'],
        8: ['custom_stoploss', 'adjust_trade_position'],
        9: ['check_buy_timeout', 'check_sell_timeout'],
        10: ['order_execution']
    }
    
    pos = {}
    layer_height = 180  # 显著增加层间距以避免重叠
    layer_width = 1200  # 显著增加层宽度以适应更多节点
    
    for layer_idx, nodes in layers.items():
        y = layer_idx * layer_height
        
        # 过滤出实际存在的节点
        existing_nodes = [node for node in nodes if node in G.nodes()]
        
        if not existing_nodes:
            continue
            
        # 计算节点在该层的x坐标
        if len(existing_nodes) == 1:
            pos[existing_nodes[0]] = (0, y)
        else:
            # 为多个节点分配x坐标，确保足够的间距
            total_width = layer_width
            
            # 根据节点数量动态调整间距
            if len(existing_nodes) > 3:
                # 对于多节点层，增加总宽度以确保足够间距
                total_width = layer_width * (len(existing_nodes) / 3)
            
            node_spacing = total_width / (len(existing_nodes) + 1)
            
            for i, node in enumerate(existing_nodes):
                x = -total_width/2 + (i + 1) * node_spacing
                pos[node] = (x, y)
    
    return pos

def create_tensorboard_nodes(G: nx.DiGraph, pos: Dict, strategy: StrategyAnalysis) -> Tuple[List, List]:
    """创建TensorBoard风格的大框图节点"""
    shapes = []
    annotations = []
    
    # 获取接口分类信息
    categories = FreqtradeInterfaceDefinitions.get_interface_categories()
    
    for node in G.nodes():
        x, y = pos[node]
        node_info = G.nodes[node]
        
        # 节点尺寸 - TensorBoard风格的大框图
        width = 280
        height = 120
        
        # 根据节点类型确定颜色和样式
        if node_info['type'] == 'strategy_interface':
            # 策略接口节点
            if node_info.get('is_implemented'):
                fill_color = '#E8F5E8'  # 浅绿色背景
                border_color = '#4CAF50'  # 绿色边框
                status_text = '✅ 已实现'
                status_color = '#2E7D32'
            else:
                fill_color = '#FFF8E1'  # 浅黄色背景
                border_color = '#FF9800'  # 橙色边框
                status_text = '🔧 使用默认'
                status_color = '#F57C00'
        else:
            # 核心流程节点
            fill_color = '#E3F2FD'  # 浅蓝色背景
            border_color = '#2196F3'  # 蓝色边框
            status_text = '⚙️ 核心流程'
            status_color = '#1976D2'
        
        # 创建节点矩形
        shapes.append({
            'type': 'rect',
            'x0': x - width/2,
            'y0': y - height/2,
            'x1': x + width/2,
            'y1': y + height/2,
            'fillcolor': fill_color,
            'line': {
                'color': border_color,
                'width': 3
            },
            'layer': 'below'
        })
        
        # 创建节点标题
        title_text = node_info['label']
        if len(title_text) > 20:
            title_text = title_text[:17] + '...'
        
        annotations.append({
            'x': x,
            'y': y + 35,
            'text': f'<b>{title_text}</b>',
            'showarrow': False,
            'font': {'size': 14, 'color': '#333'},
            'align': 'center'
        })
        
        # 创建状态标识
        annotations.append({
            'x': x,
            'y': y + 15,
            'text': status_text,
            'showarrow': False,
            'font': {'size': 11, 'color': status_color},
            'align': 'center'
        })
        
        # 创建描述文本（默认显示在节点内）
        description = node_info.get('description', '')
        if len(description) > 60:
            description = description[:57] + '...'
        
        annotations.append({
            'x': x,
            'y': y - 5,
            'text': description,
            'showarrow': False,
            'font': {'size': 10, 'color': '#666'},
            'align': 'center'
        })
        
        # 为策略接口添加额外信息
        if node_info['type'] == 'strategy_interface':
            if node_info.get('is_implemented'):
                # 显示策略特定信息
                strategy_interface = strategy.interfaces.get(node)
                if strategy_interface and strategy_interface.logic_explanation:
                    logic_preview = strategy_interface.logic_explanation[:40]
                    if len(strategy_interface.logic_explanation) > 40:
                        logic_preview += '...'
                    
                    annotations.append({
                        'x': x,
                        'y': y - 25,
                        'text': f'💡 {logic_preview}',
                        'showarrow': False,
                        'font': {'size': 9, 'color': '#4CAF50'},
                        'align': 'center'
                    })
            else:
                # 显示默认行为
                default_behavior = node_info.get('default_behavior', '')
                if len(default_behavior) > 35:
                    default_behavior = default_behavior[:32] + '...'
                
                annotations.append({
                    'x': x,
                    'y': y - 25,
                    'text': f'🔧 {default_behavior}',
                    'showarrow': False,
                    'font': {'size': 9, 'color': '#FF9800'},
                    'align': 'center'
                })
        
        # 添加分类标签
        category = node_info.get('category', 'core')
        category_info = categories.get(category, {'name': '其他'})
        
        annotations.append({
            'x': x,
            'y': y - 45,
            'text': f'📂 {category_info["name"]}',
            'showarrow': False,
            'font': {'size': 8, 'color': '#999'},
            'align': 'center'
        })
    
    return shapes, annotations

def create_legend_info():
    """创建图例信息"""
    categories = FreqtradeInterfaceDefinitions.get_interface_categories()
    legend_items = []
    
    for category, info in categories.items():
        legend_items.append({
            'color': info['color'],
            'label': info['name']
        })
    
    # 添加节点状态图例
    legend_items.extend([
        {'color': '#4CAF50', 'label': '✅ 已实现接口'},
        {'color': '#FF9800', 'label': '🔧 使用默认实现'},
        {'color': '#2196F3', 'label': '⚙️ 核心流程'}
    ])
    
    return legend_items

def create_curved_edges(G: nx.DiGraph, pos: Dict) -> List:
    """创建粗箭头曲线连接"""
    edge_shapes = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # 计算控制点以创建曲线
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        
        # 添加更大的曲率以避免穿过节点
        if abs(x1 - x0) > abs(y1 - y0):
            # 水平方向的连接，添加垂直曲率
            # 增加曲率以避免穿过节点
            curve_factor = 60  # 增加曲率因子
            control_y = mid_y + curve_factor if y1 > y0 else mid_y - curve_factor
            control_x = mid_x
        else:
            # 垂直方向的连接，添加水平曲率
            # 增加曲率以避免穿过节点
            curve_factor = 100  # 增加曲率因子
            control_x = mid_x + curve_factor if x1 > x0 else mid_x - curve_factor
            control_y = mid_y
        
        # 创建SVG路径字符串用于曲线
        path = f'M {x0},{y0} Q {control_x},{control_y} {x1},{y1}'
        
        # 添加曲线，确保在节点下方
        edge_shapes.append({
            'type': 'path',
            'path': path,
            'line': {
                'color': '#666',
                'width': 3  # 稍微减小线条宽度以减少视觉干扰
            },
            'layer': 'below',  # 确保线条在节点下方
            'opacity': 0.8     # 稍微降低不透明度以减少视觉干扰
        })
        
        # 添加箭头
        # 计算箭头方向
        dx = x1 - control_x
        dy = y1 - control_y
        length = (dx**2 + dy**2)**0.5
        
        if length > 0:
            # 标准化方向向量
            dx_norm = dx / length
            dy_norm = dy / length
            
            # 箭头大小
            arrow_size = 12  # 稍微减小箭头大小
            
            # 计算箭头的三个点
            # 将箭头向后移动更多，确保不会覆盖节点
            arrow_tip_x = x1 - 30 * dx_norm  # 箭头尖端更向后
            arrow_tip_y = y1 - 30 * dy_norm
            
            # 箭头的两个翼
            arrow_left_x = arrow_tip_x - arrow_size * dx_norm - arrow_size * dy_norm
            arrow_left_y = arrow_tip_y - arrow_size * dy_norm + arrow_size * dx_norm
            
            arrow_right_x = arrow_tip_x - arrow_size * dx_norm + arrow_size * dy_norm
            arrow_right_y = arrow_tip_y - arrow_size * dy_norm - arrow_size * dx_norm
            
            # 创建箭头形状
            arrow_path = f'M {arrow_left_x},{arrow_left_y} L {arrow_tip_x},{arrow_tip_y} L {arrow_right_x},{arrow_right_y} Z'  # 闭合路径
            
            # 注意：这里箭头连接到arrow_tip而不是节点本身(x1,y1)，避免覆盖节点
            edge_shapes.append({
                'type': 'path',
                'path': arrow_path,
                'line': {
                    'color': '#666',
                    'width': 3
                },
                'fillcolor': '#666',  # 填充箭头
                'layer': 'below',     # 确保箭头在节点下方
                'opacity': 0.8        # 稍微降低不透明度
            })
    
    return edge_shapes

def create_tensorboard_layout() -> Dict:
    """创建TensorBoard风格的布局"""
    return {
        'title': {
            'text': '🚀 Freqtrade策略执行流程图 - TensorBoard风格',
            'x': 0.5,
            'font': {'size': 20, 'color': '#333'}
        },
        'showlegend': False,
        'hovermode': 'closest',
        'margin': dict(b=50, l=50, r=50, t=80),
        'xaxis': {
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False,
            'range': [-1000, 1000],  # 显著增加范围以适应更宽的布局和缩放空间
            'scaleanchor': 'y',  # 保持x和y轴的比例一致
            'constrain': 'domain',  # 确保缩放时保持比例
            'fixedrange': False,   # 允许轴缩放
        },
        'yaxis': {
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False,
            'range': [-200, 2200],  # 显著增加范围以适应更高的布局和缩放空间
            'constrain': 'domain',  # 确保缩放时保持比例
            'fixedrange': False,    # 允许轴缩放
        },
        'height': 1600,  # 增加高度以适应更多节点
        'autosize': True,  # 自动调整大小
        'plot_bgcolor': '#FAFAFA',  # TensorBoard风格的背景色
        'paper_bgcolor': '#FFFFFF',
        'dragmode': 'zoom',  # 启用拖动缩放
        'modebar': {
            'orientation': 'v',
            'bgcolor': 'rgba(255, 255, 255, 0.7)',
            'color': '#333',
            'activecolor': '#2196F3'
        },
        'annotations': [
            {
                'text': '💡 点击节点查看详细信息 | 🔍 绿色=已实现 | 🟡 黄色=使用默认 | 🟦 蓝色=核心流程',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.02,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'color': '#666', 'size': 12}
            },
            {
                'text': '👛️ 使用滚轮缩放 | 🔍 双击重置视图 | ⬅️⬆️⬇️➡️ 拖动平移',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.04,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'color': '#666', 'size': 12}
            }
        ],
        'updatemenus': [
            {
                'buttons': [
                    {
                        'args': [{'xaxis.autorange': True, 'yaxis.autorange': True}],
                        'label': '🔍 重置视图',
                        'method': 'relayout'
                    },
                    {
                        'args': [{'width': 1200, 'height': 1600}],
                        'label': '📷 适应屏幕',
                        'method': 'relayout'
                    }
                ],
                'direction': 'down',
                'pad': {'r': 10, 't': 10},
                'showactive': True,
                'type': 'buttons',
                'x': 0.05,
                'xanchor': 'left',
                'y': 1.02,
                'yanchor': 'bottom',
                'bgcolor': 'rgba(255, 255, 255, 0.8)',
                'bordercolor': '#2196F3',
                'font': {'color': '#333'}
            }
        ]
    }


def get_plotly_config() -> Dict:
    """获取Plotly的配置选项，需要在Streamlit中单独传递"""
    return {
        'scrollZoom': True,     # 启用滚轮缩放
        'displayModeBar': True, # 始终显示模式栏
        'modeBarButtonsToAdd': [
            'zoom2d',
            'pan2d',
            'zoomIn2d',
            'zoomOut2d',
            'resetScale2d'
        ],
        'doubleClick': 'reset'   # 双击重置视图
    }