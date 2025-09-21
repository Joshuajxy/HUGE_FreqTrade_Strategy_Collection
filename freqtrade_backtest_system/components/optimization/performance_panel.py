"""
Performance monitoring and optimization panel
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .performance_optimizer import (
    MemoryOptimizer, 
    ConcurrencyOptimizer, 
    CacheManager, 
    PerformanceProfiler,
    MemoryMonitor
)
from utils.error_handling import ErrorHandler

class PerformanceMonitoringPanel:
    """Performance monitoring and optimization panel"""
    
    def __init__(self):
        """Initialize performance panel"""
        self.memory_optimizer = MemoryOptimizer()
        self.concurrency_optimizer = ConcurrencyOptimizer()
        self.cache_manager = CacheManager()
        self.profiler = PerformanceProfiler()
        self.memory_monitor = MemoryMonitor()
        
        # Initialize session state
        if 'performance_monitoring' not in st.session_state:
            st.session_state.performance_monitoring = False
        if 'performance_data' not in st.session_state:
            st.session_state.performance_data = []
    
    def render(self):
        """Render performance monitoring panel"""
        st.header("⚡ 系统性能监控")
        
        # Create tabs for different monitoring aspects
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 实时监控", 
            "🔧 性能优化", 
            "💾 缓存管理", 
            "📈 历史分析"
        ])
        
        with tab1:
            self._render_real_time_monitoring()
        
        with tab2:
            self._render_performance_optimization()
        
        with tab3:
            self._render_cache_management()
        
        with tab4:
            self._render_historical_analysis()
    
    def _render_real_time_monitoring(self):
        """Render real-time monitoring tab"""
        st.subheader("📊 实时系统监控")
        
        # Monitoring control
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write("**监控状态:**")
            if st.session_state.performance_monitoring:
                st.success("✅ 监控运行中")
            else:
                st.info("⏸️ 监控已停止")
        
        with col2:
            if not st.session_state.performance_monitoring:
                if st.button("🚀 开始监控", type="primary"):
                    self.profiler.start_monitoring()
                    st.session_state.performance_monitoring = True
                    st.rerun()
            else:
                if st.button("⏹️ 停止监控"):
                    self.profiler.stop_monitoring()
                    st.session_state.performance_monitoring = False
                    st.rerun()
        
        with col3:
            if st.button("🔄 刷新数据"):
                st.rerun()
        
        # Current system metrics
        st.subheader("💻 当前系统状态")
        
        # Get current metrics
        memory_info = self.memory_monitor.get_memory_info()
        current_metrics = self.profiler.get_current_metrics()
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_usage = current_metrics.cpu_usage if current_metrics else 0
            st.metric(
                "CPU 使用率", 
                f"{cpu_usage:.1f}%",
                delta=None,
                delta_color="inverse"
            )
        
        with col2:
            memory_usage = memory_info['usage_percent']
            st.metric(
                "内存使用率", 
                f"{memory_usage:.1f}%",
                delta=None,
                delta_color="inverse"
            )
        
        with col3:
            available_memory = memory_info['available_mb']
            st.metric(
                "可用内存", 
                f"{available_memory:.0f} MB",
                delta=None
            )
        
        with col4:
            active_threads = current_metrics.active_threads if current_metrics else 0
            st.metric(
                "活跃线程", 
                str(active_threads),
                delta=None
            )
        
        # Memory usage breakdown
        st.subheader("💾 内存使用详情")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Memory usage pie chart
            memory_data = {
                '已使用': memory_info['used_mb'],
                '可用': memory_info['available_mb']
            }
            
            fig_memory = go.Figure(data=[go.Pie(
                labels=list(memory_data.keys()),
                values=list(memory_data.values()),
                hole=0.3
            )])
            
            fig_memory.update_layout(
                title="内存使用分布",
                height=300
            )
            
            st.plotly_chart(fig_memory, width='stretch')
        
        with col2:
            # Process memory info
            process_memory = memory_info['process_memory_mb']
            process_percent = memory_info['process_memory_percent']
            
            st.write("**进程内存使用:**")
            st.write(f"- 当前进程: {process_memory:.1f} MB ({process_percent:.1f}%)")
            st.write(f"- 系统总内存: {memory_info['total_mb']:.0f} MB")
            
            # Memory recommendations
            recommendations = self.memory_optimizer.get_memory_recommendations()
            if recommendations:
                st.write("**内存建议:**")
                for rec in recommendations:
                    st.warning(f"⚠️ {rec}")
        
        # Real-time performance chart
        if st.session_state.performance_monitoring and self.profiler.metrics_history:
            st.subheader("📈 实时性能图表")
            
            # Get recent metrics (last 50 data points)
            recent_metrics = self.profiler.metrics_history[-50:]
            
            if recent_metrics:
                # Create performance chart
                timestamps = [m.timestamp for m in recent_metrics]
                cpu_data = [m.cpu_usage for m in recent_metrics]
                memory_data = [m.memory_usage for m in recent_metrics]
                
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('CPU 使用率 (%)', '内存使用率 (%)'),
                    vertical_spacing=0.1
                )
                
                # CPU usage
                fig.add_trace(
                    go.Scatter(
                        x=timestamps, 
                        y=cpu_data,
                        mode='lines+markers',
                        name='CPU',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
                
                # Memory usage
                fig.add_trace(
                    go.Scatter(
                        x=timestamps, 
                        y=memory_data,
                        mode='lines+markers',
                        name='Memory',
                        line=dict(color='red')
                    ),
                    row=2, col=1
                )
                
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    title="系统性能实时监控"
                )
                
        st.plotly_chart(fig, width='stretch')
    
    def _render_performance_optimization(self):
        """Render performance optimization tab"""
        st.subheader("🔧 性能优化工具")
        
        # Memory optimization
        st.write("### 💾 内存优化")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧹 执行内存优化", type="primary"):
                with st.spinner("正在优化内存使用..."):
                    self.memory_optimizer.optimize_memory_usage()
                    st.success("内存优化完成！")
                    st.rerun()
        
        with col2:
            memory_usage = self.memory_monitor.get_memory_usage()
            if memory_usage > 0.8:
                st.error(f"⚠️ 高内存使用: {memory_usage:.1%}")
            elif memory_usage > 0.6:
                st.warning(f"⚠️ 中等内存使用: {memory_usage:.1%}")
            else:
                st.success(f"✅ 正常内存使用: {memory_usage:.1%}")
        
        # Concurrency optimization
        st.write("### ⚡ 并发优化")
        
        concurrency_recommendations = self.concurrency_optimizer.get_performance_recommendations()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**当前配置:**")
            st.write(f"- 最优工作线程数: {self.concurrency_optimizer.optimal_workers}")
            st.write(f"- CPU 核心数: {self.concurrency_optimizer.cpu_count}")
            
            if 'average_throughput' in concurrency_recommendations:
                st.write(f"- 平均吞吐量: {concurrency_recommendations['average_throughput']:.2f} tasks/s")
        
        with col2:
            st.write("**优化建议:**")
            recommendations = concurrency_recommendations.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    st.info(f"💡 {rec}")
            else:
                st.success("✅ 当前并发配置已优化")
        
        # System resource analysis
        st.write("### 📊 系统资源分析")
        
        # Get system info
        import psutil
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**CPU 信息:**")
            st.write(f"- 物理核心: {psutil.cpu_count(logical=False)}")
            st.write(f"- 逻辑核心: {psutil.cpu_count(logical=True)}")
            st.write(f"- 当前频率: {psutil.cpu_freq().current:.0f} MHz")
        
        with col2:
            st.write("**内存信息:**")
            memory_info = self.memory_monitor.get_memory_info()
            st.write(f"- 总内存: {memory_info['total_mb']:.0f} MB")
            st.write(f"- 可用内存: {memory_info['available_mb']:.0f} MB")
            st.write(f"- 使用率: {memory_info['usage_percent']:.1f}%")
        
        with col3:
            st.write("**磁盘信息:**")
            disk_usage = psutil.disk_usage('.')
            st.write(f"- 总空间: {disk_usage.total / (1024**3):.1f} GB")
            st.write(f"- 可用空间: {disk_usage.free / (1024**3):.1f} GB")
            st.write(f"- 使用率: {(disk_usage.used / disk_usage.total) * 100:.1f}%")
    
    def _render_cache_management(self):
        """Render cache management tab"""
        st.subheader("💾 缓存管理")
        
        # Get cache statistics
        cache_stats = self.cache_manager.get_cache_stats()
        
        # Cache statistics
        st.write("### 📊 缓存统计")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            hit_rate = cache_stats.get('hit_rate', 0)
            st.metric("缓存命中率", f"{hit_rate:.1%}")
        
        with col2:
            total_requests = cache_stats.get('total_requests', 0)
            st.metric("总请求数", str(total_requests))
        
        with col3:
            cache_files = cache_stats.get('cache_files', 0)
            st.metric("缓存文件数", str(cache_files))
        
        with col4:
            cache_size = cache_stats.get('total_size_mb', 0)
            st.metric("缓存大小", f"{cache_size:.1f} MB")
        
        # Cache performance chart
        if cache_stats.get('total_requests', 0) > 0:
            st.write("### 📈 缓存性能")
            
            hits = cache_stats.get('hits', 0)
            misses = cache_stats.get('misses', 0)
            
            fig = go.Figure(data=[
                go.Bar(name='命中', x=['缓存性能'], y=[hits], marker_color='green'),
                go.Bar(name='未命中', x=['缓存性能'], y=[misses], marker_color='red')
            ])
            
            fig.update_layout(
                barmode='stack',
                title='缓存命中/未命中统计',
                height=300
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # Cache management actions
        st.write("### 🔧 缓存操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ 清空缓存"):
                self.cache_manager.clear_cache()
                st.success("缓存已清空")
                st.rerun()
        
        with col2:
            if st.button("🧹 清理过期缓存"):
                # This is handled automatically, but we can trigger it manually
                self.cache_manager._cleanup_cache()
                st.success("过期缓存已清理")
                st.rerun()
        
        with col3:
            if st.button("📊 刷新统计"):
                st.rerun()
        
        # Cache configuration
        st.write("### ⚙️ 缓存配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_cache_size = st.number_input(
                "最大缓存大小 (MB)", 
                min_value=100, 
                max_value=2000, 
                value=500,
                help="设置缓存的最大大小限制"
            )
            
            if max_cache_size != self.cache_manager.max_cache_size / (1024 * 1024):
                self.cache_manager.max_cache_size = max_cache_size * 1024 * 1024
                st.success("缓存大小限制已更新")
        
        with col2:
            memory_cache_items = cache_stats.get('memory_cache_items', 0)
            st.write(f"**内存缓存项目:** {memory_cache_items}")
            st.write(f"**磁盘缓存文件:** {cache_files}")
            st.write(f"**缓存目录:** {self.cache_manager.cache_dir}")
    
    def _render_historical_analysis(self):
        """Render historical analysis tab"""
        st.subheader("📈 历史性能分析")
        
        # Get historical metrics
        if not self.profiler.metrics_history:
            st.info("暂无历史性能数据，请先启动性能监控")
            return
        
        # Time range selection
        col1, col2 = st.columns(2)
        
        with col1:
            hours_back = st.selectbox(
                "分析时间范围",
                [1, 6, 12, 24, 48],
                index=2,
                format_func=lambda x: f"过去 {x} 小时"
            )
        
        with col2:
            if st.button("📊 生成分析报告"):
                st.session_state.generate_report = True
        
        # Get metrics summary
        metrics_summary = self.profiler.get_metrics_summary(hours=hours_back)
        
        if not metrics_summary:
            st.warning(f"过去 {hours_back} 小时内没有性能数据")
            return
        
        # Display summary metrics
        st.write("### 📊 性能摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_cpu = metrics_summary.get('avg_cpu_usage', 0)
            max_cpu = metrics_summary.get('max_cpu_usage', 0)
            st.metric("平均 CPU", f"{avg_cpu:.1f}%", f"峰值: {max_cpu:.1f}%")
        
        with col2:
            avg_memory = metrics_summary.get('avg_memory_usage', 0)
            max_memory = metrics_summary.get('max_memory_usage', 0)
            st.metric("平均内存", f"{avg_memory:.1f}%", f"峰值: {max_memory:.1f}%")
        
        with col3:
            min_available = metrics_summary.get('min_memory_available', 0)
            st.metric("最少可用内存", f"{min_available:.0f} MB")
        
        with col4:
            avg_threads = metrics_summary.get('avg_active_threads', 0)
            max_threads = metrics_summary.get('max_active_threads', 0)
            st.metric("平均线程数", f"{avg_threads:.0f}", f"峰值: {max_threads}")
        
        # Historical performance charts
        st.write("### 📈 性能趋势图")
        
        # Filter metrics by time range
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        filtered_metrics = [
            m for m in self.profiler.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if filtered_metrics:
            # Create comprehensive performance chart
            timestamps = [m.timestamp for m in filtered_metrics]
            cpu_data = [m.cpu_usage for m in filtered_metrics]
            memory_data = [m.memory_usage for m in filtered_metrics]
            threads_data = [m.active_threads for m in filtered_metrics]
            
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('CPU 使用率 (%)', '内存使用率 (%)', '活跃线程数'),
                vertical_spacing=0.08
            )
            
            # CPU usage
            fig.add_trace(
                go.Scatter(
                    x=timestamps, 
                    y=cpu_data,
                    mode='lines',
                    name='CPU',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # Memory usage
            fig.add_trace(
                go.Scatter(
                    x=timestamps, 
                    y=memory_data,
                    mode='lines',
                    name='Memory',
                    line=dict(color='red', width=2)
                ),
                row=2, col=1
            )
            
            # Active threads
            fig.add_trace(
                go.Scatter(
                    x=timestamps, 
                    y=threads_data,
                    mode='lines',
                    name='Threads',
                    line=dict(color='green', width=2)
                ),
                row=3, col=1
            )
            
            fig.update_layout(
                height=600,
                showlegend=False,
                title=f"过去 {hours_back} 小时性能趋势"
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # Performance analysis insights
            st.write("### 🔍 性能分析洞察")
            
            insights = []
            
            # CPU analysis
            if max_cpu > 90:
                insights.append("⚠️ 检测到高CPU使用率峰值，可能影响系统响应")
            elif avg_cpu < 20:
                insights.append("✅ CPU使用率较低，系统资源充足")
            
            # Memory analysis
            if max_memory > 85:
                insights.append("⚠️ 内存使用率过高，建议优化内存使用")
            elif min_available < 500:
                insights.append("⚠️ 可用内存不足，可能导致系统不稳定")
            
            # Thread analysis
            if max_threads > 50:
                insights.append("⚠️ 线程数过多，可能存在资源竞争")
            
            if insights:
                for insight in insights:
                    if "⚠️" in insight:
                        st.warning(insight)
                    else:
                        st.success(insight)
            else:
                st.success("✅ 系统性能表现良好，未发现异常")
        
        # Export performance data
        st.write("### 📤 导出性能数据")
        
        if st.button("📊 导出 CSV 数据"):
            if filtered_metrics:
                # Convert to DataFrame
                data = []
                for m in filtered_metrics:
                    data.append({
                        'timestamp': m.timestamp,
                        'cpu_usage': m.cpu_usage,
                        'memory_usage': m.memory_usage,
                        'memory_available': m.memory_available,
                        'active_threads': m.active_threads
                    })
                
                df = pd.DataFrame(data)
                csv_data = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 下载性能数据",
                    data=csv_data,
                    file_name=f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("没有可导出的性能数据")