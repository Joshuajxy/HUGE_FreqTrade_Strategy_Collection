"""
Freqtrade Backtest System Main Application
"""
import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from components.ui.main_layout import MainLayout
from components.strategy_manager.scanner import StrategyScanner
from components.strategy_manager.selector import StrategySelector
from components.backtest_config.panel import BacktestConfigPanel
from components.backtest_config.manager import ConfigManager
from components.results.comparator import ResultComparator
from utils.error_handling import ErrorHandler
from utils.data_models import BacktestResult
from components.execution.scheduler_singleton import get_scheduler

def initialize_session_state():
    """Initialize session state variables"""
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = True
        st.session_state.trigger_scan = False
        st.session_state.scan_path = ".."
        st.session_state.strategies = []
        st.session_state.selected_strategies = []
        st.session_state.backtest_config = None
        st.session_state.start_backtest = False
        st.session_state.task_ids = {}
        st.session_state.backtest_results = []
        st.session_state.selected_results_dir = None
        st.session_state.backtest_results_metadata = None
        st.session_state.latest_run_id = None
        st.session_state.results_need_refresh = False

def list_backtest_run_directories() -> list[Path]:
    """Return available backtest run directories sorted by modified time."""
    base_dir = Path("user_data/backtest_results")
    if not base_dir.exists():
        ErrorHandler.log_warning(f"回测结果基础目录不存在：{base_dir.resolve()}")
        return []

    try:
        run_dirs = [path for path in base_dir.iterdir() if path.is_dir()]
        ErrorHandler.log_info(
            f"共发现 {len(run_dirs)} 个回测目录：{', '.join(str(p.name) for p in run_dirs) if run_dirs else '无'}"
        )
        run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return run_dirs
    except Exception as exc:
        ErrorHandler.log_warning(f"读取回测目录列表失败：{exc}")
        return []


def load_backtest_results_from_directory(run_dir: Path) -> tuple[list[BacktestResult], dict | None]:
    """Load backtest results for a specific run directory."""
    results: list[BacktestResult] = []
    metadata: dict | None = None

    if not run_dir.exists() or not run_dir.is_dir():
        ErrorHandler.log_warning(f"指定的回测目录不存在：{run_dir}")
        return results, metadata

    metadata_path = run_dir / "run_metadata.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception as exc:
            ErrorHandler.log_warning(f"读取回测目录元数据失败：{metadata_path.name}：{exc}")

    results_dir = run_dir / "results"
    if results_dir.exists() and results_dir.is_dir():
        ErrorHandler.log_info(f"在目录 {run_dir.name} 中使用 results 子目录加载回测文件")
        search_dirs = [results_dir]
    else:
        search_dirs = [run_dir]
        ErrorHandler.log_warning(f"目录 {run_dir.name} 未找到 results 子目录，回退到根目录加载结果")

    # 优先加载主 results 目录中 `<strategy>_<timestamp>.json`
    for directory in search_dirs:
        candidate_files = sorted(directory.glob("*.json"))
        for file_path in candidate_files:
            if file_path.name.endswith(".meta.json") or file_path.name == "run_metadata.json":
                continue
            if "freqtrade_export" in file_path.parts:
                continue
            try:
                result = BacktestResult.load_from_file(file_path)
                if not result.source_file:
                    result.source_file = str(file_path)
                results.append(result)
            except Exception as exc:
                ErrorHandler.log_warning(f"无法加载回测结果文件 {file_path.name}：{exc}")

    # 若主目录没有结果，尝试 freqtrade_export 解析产物
    if not results:
        export_dir = results_dir / "freqtrade_export"
        if export_dir.exists():
            for summary_path in sorted(export_dir.glob("**/backtest-result-*.json")):
                try:
                    result = BacktestResult.load_from_file(summary_path)
                    if not result.source_file:
                        result.source_file = str(summary_path)
                    results.append(result)
                except Exception as exc:
                    ErrorHandler.log_warning(f"无法从 freqtrade_export 加载文件 {summary_path.name}：{exc}")

    if results:
        ErrorHandler.log_info(f"从目录 {run_dir.name} 加载 {len(results)} 条回测结果")
    else:
        ErrorHandler.log_warning(f"目录 {run_dir.name} 未加载到任何回测结果文件")

    return results, metadata


def read_run_metadata(run_dir: Path) -> dict | None:
    """Read run metadata file if available."""
    metadata_path = run_dir / "run_metadata.json"
    if metadata_path.exists():
        try:
            return json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception as exc:
            ErrorHandler.log_warning(f"读取回测目录元数据失败：{metadata_path.name}：{exc}")
    return None

def main():
    """Main application function"""
    try:
        # Initialize session state
        initialize_session_state()

        # Initialize main layout
        layout = MainLayout()
        layout.render_header()
        
        # Render sidebar info
        layout.render_sidebar_info()

        tabs = st.tabs([
            "📋 Strategy Management",
            "⚙️ Backtest Config",
            "🔄 Execution Monitor",
            "📊 Results Analysis",
            "📓 Jupyter Analysis",
            "🚀 Performance Monitor",
        ])

        with tabs[0]:
            render_strategy_management()

        with tabs[1]:
            render_backtest_config()

        with tabs[2]:
            render_execution_monitor()

        with tabs[3]:
            render_results_analysis()

        with tabs[4]:
            render_jupyter_analysis()

        with tabs[5]:
            render_performance_monitor()
        
        # Render footer
        layout.render_footer()
            
    except Exception as e:
        ErrorHandler.handle_application_error(e)

def render_strategy_management():
    """Render strategy management page"""
    st.header("📋 Strategy Management")
    
    # Initialize components
    scanner = StrategyScanner([".."])  # Scan parent directory
    selector = StrategySelector()
    
    # Scan control panel
    st.subheader("🔍 Strategy Scanner")
    
    # Create three columns for the input and buttons
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown("**Scan Path**")
        scan_path = st.text_input(
            "Scan Path",
            value="..",
            help="Directory path containing strategy files",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**&nbsp;**", unsafe_allow_html=True)
        start_scan_clicked = st.button("🔍 Start Scan", type="primary")
    
    with col3:
        st.markdown("**&nbsp;**", unsafe_allow_html=True)
        clear_results_clicked = st.button("🗑️ Clear Results")

    if start_scan_clicked:
        st.session_state.trigger_scan = True
        st.session_state.scan_path = scan_path

    if clear_results_clicked:
        if 'strategies' in st.session_state:
            del st.session_state.strategies
        if 'selected_strategies' in st.session_state:
            del st.session_state.selected_strategies
        st.rerun()
    
    # Execute scan
    if st.session_state.get('trigger_scan', False):
        st.session_state.trigger_scan = False
        
        with st.spinner("Scanning strategy files..."):
            try:
                # Update scan path
                scanner = StrategyScanner([st.session_state.get('scan_path', '..')])
                strategies = scanner.scan_strategies()
                st.session_state.strategies = strategies
                
                if strategies:
                    st.success(f"✅ Scan completed! Found {len(strategies)} strategy files")
                else:
                    st.warning("⚠️ No strategy files found, please check scan path")
            except Exception as e:
                st.error(f"❌ Scan failed: {str(e)}")
    
    # Display scan results
    strategies = st.session_state.get('strategies', [])
    
    if strategies:
        st.divider()
        
        # Render strategy selection interface
        selected_strategies = selector.render_strategy_selection(strategies)
        
        # Save selected strategies to session state
        st.session_state.selected_strategies = selected_strategies
        
        if selected_strategies:
            st.success(f"✅ Selected {len(selected_strategies)} strategies, you can proceed to backtest configuration")
    else:
        st.info("Please click 'Start Scan' button to find strategy files")

def render_backtest_config():
    """Render backtest configuration page"""
    st.header("⚙️ Backtest Configuration")
    
    # Check if strategies are selected
    selected_strategies = st.session_state.get('selected_strategies', [])
    if not selected_strategies:
        st.warning("Please select strategies in Strategy Management page first")
        return
    
    st.info(f"Current selected strategies: {', '.join(s.name for s in selected_strategies)}")
    
    # Initialize components
    config_panel = BacktestConfigPanel()
    config_manager = ConfigManager()
    
    # Configuration management
    st.subheader("📁 Configuration Management")
    tab1, tab2 = st.tabs(["New Configuration", "Load Configuration"])
    
    with tab1:
        # Render configuration panel
        config = config_panel.render_config_panel()
        
        if config:
            # Save configuration option
            config_manager.render_save_config_dialog(config)
            
            # Save config to session state
            st.session_state.backtest_config = config
            
            # Estimate execution time
            estimated_time = config_panel.get_estimated_execution_time(config, len(selected_strategies))
            st.info(f"Estimated execution time: {estimated_time}")
            
            col_download, col_start = st.columns(2)

            with col_download:
                if st.button("📥 下载/更新数据", use_container_width=True):
                    from components.execution.executor_singleton import get_executor

                    executor = get_executor()
                    with st.spinner("正在下载历史数据..."):
                        ready, issues = executor.ensure_data_ready(config)

                    if ready:
                        st.success("历史数据已准备就绪，可进行回测。")
                    else:
                        st.error("历史数据检查失败，无法完成下载。")
                        for issue in issues:
                            st.warning(f"• {issue}")

            with col_start:
                if st.button("🚀 Start Backtest", type="primary", use_container_width=True):
                    from components.execution.executor_singleton import get_executor

                    executor = get_executor()
                    with st.spinner("正在检查历史数据..."):
                        ready, issues = executor.ensure_data_ready(config)

                    if ready:
                        st.session_state.start_backtest = True
                        st.success("回测配置已保存，请切换到上方的 🔄 Execution Monitor 标签查看进度")
                    else:
                        st.error("历史数据不足，无法启动回测。")
                        for issue in issues:
                            st.warning(f"• {issue}")
    
    with tab2:
        # Load saved configuration
        loaded_config = config_manager.render_config_manager()
        if loaded_config:
            st.session_state.backtest_config = loaded_config

def render_execution_monitor():
    """Render execution monitor page"""
    st.header("🔄 Execution Monitor")
    
    scheduler = get_scheduler()

    # Check if there's a pending backtest
    if st.session_state.get('start_backtest', False):
        selected_strategies = st.session_state.get('selected_strategies', [])
        config = st.session_state.get('backtest_config')
        
        if selected_strategies and config:
            # Start backtest execution
            if not st.session_state.get('task_ids'):
                from components.execution.executor_singleton import get_executor

                executor = get_executor()

                with st.spinner("正在准备历史数据..."):
                    ready, issues = executor.ensure_data_ready(config)

                if not ready:
                    st.session_state.start_backtest = False
                    st.session_state.task_ids = {}
                    st.error("历史数据校验失败，无法启动回测。")
                    for issue in issues:
                        st.warning(f"• {issue}")
                    st.info("请检查数据文件或调整回测参数后重试。")
                    return

                with st.spinner("正在启动回测任务..."):
                    task_ids = scheduler.submit_batch(selected_strategies, config)
                st.session_state.task_ids = task_ids
                st.session_state.start_backtest = False
            
            # Import and render execution monitoring panel
            from components.execution.monitoring_panel import ExecutionMonitoringPanel
            monitor_panel = ExecutionMonitoringPanel()
            
            # Display execution status with real-time logs
            task_ids = st.session_state.get('task_ids', {})
            if task_ids:
                monitor_panel.render_execution_monitor(scheduler, task_ids)
            else:
                st.info("No active executions to monitor")
        else:
            st.error("Missing backtest configuration or strategy selection")
    else:
        task_ids = st.session_state.get('task_ids', {})
        if task_ids:
            from components.execution.monitoring_panel import ExecutionMonitoringPanel
            monitor_panel = ExecutionMonitoringPanel()
            monitor_panel.render_execution_monitor(scheduler, task_ids)
        else:
            st.info("Please configure and start backtest in Backtest Config page first")

def render_execution_status(scheduler, task_ids):
    """Render execution status with enhanced monitoring"""
    # Import and render execution monitoring panel
    from components.execution.monitoring_panel import ExecutionMonitoringPanel
    monitor_panel = ExecutionMonitoringPanel()
    
    # Display execution status with real-time logs
    monitor_panel.render_execution_monitor(scheduler, task_ids)

def render_results_analysis():
    """Render results analysis page"""
    ErrorHandler.log_info("进入 Results Analysis 页面渲染流程")
    st.header("📊 回测结果分析")

    run_dirs = list_backtest_run_directories()
    if not run_dirs:
        ErrorHandler.log_warning("未发现回测结果目录，list_backtest_run_directories 返回空列表")
        st.info("暂无回测结果目录，请先执行回测任务。")
        st.session_state.backtest_results = []
        st.session_state.selected_results_dir = None
        st.session_state.backtest_results_metadata = None
        return

    run_options: list[tuple[str, Path, dict | None]] = []
    for run_dir in run_dirs:
        metadata_preview = read_run_metadata(run_dir) or {}
        status = metadata_preview.get("status", "unknown")
        strategy_count = len(metadata_preview.get("strategies", []))
        created_at = metadata_preview.get("created_at")
        created_display = ""
        if created_at:
            try:
                created_display = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
            except Exception:
                created_display = created_at

        label_parts = [run_dir.name, f"状态: {status}"]
        if strategy_count:
            label_parts.append(f"策略: {strategy_count}")
        if created_display:
            label_parts.append(f"开始: {created_display}")
        label = " | ".join(label_parts)
        run_options.append((label, run_dir, metadata_preview))
        ErrorHandler.log_info(f"发现回测目录: {run_dir} 状态={status} 策略数={strategy_count}")

    placeholder_label = "请选择回测目录"
    option_labels = [placeholder_label] + [item[0] for item in run_options]
    current_dir = st.session_state.get('selected_results_dir')

    if st.session_state.get('results_need_refresh'):
        latest_run_id = st.session_state.get('latest_run_id')
        if latest_run_id:
            expected_path = str(Path("user_data/backtest_results") / latest_run_id)
            st.session_state.selected_results_dir = expected_path
            current_dir = expected_path
            ErrorHandler.log_info(f"Results refresh triggered, defaulting to最新回测目录: {expected_path}")
        st.session_state.results_need_refresh = False

    default_index = 0
    if current_dir:
        for idx, (_, path, _) in enumerate(run_options, start=1):
            if str(path) == current_dir:
                default_index = idx
                break

    selected_label = st.selectbox("选择回测目录", option_labels, index=default_index)

    if selected_label == placeholder_label:
        if st.session_state.get('selected_results_dir'):
            st.session_state.selected_results_dir = None
            st.session_state.backtest_results = []
            st.session_state.backtest_results_metadata = None
        st.info("请选择回测目录以加载结果。")
        return

    selected_entry = next((entry for entry in run_options if entry[0] == selected_label), None)
    if not selected_entry:
        st.warning("所选回测目录不可用，请重试。")
        ErrorHandler.log_warning(f"所选目录标签 {selected_label} 未匹配到回测目录")
        return

    selected_run_dir, preview_metadata = selected_entry[1], selected_entry[2]
    prev_dir = st.session_state.get('selected_results_dir')
    ErrorHandler.log_info(
        f"选择回测目录: {selected_run_dir} (之前: {prev_dir}) 预览元数据键={list(preview_metadata.keys()) if preview_metadata else []}"
    )

    if prev_dir != str(selected_run_dir):
        results, metadata = load_backtest_results_from_directory(selected_run_dir)
        st.session_state.backtest_results = results
        st.session_state.backtest_results_metadata = metadata
        st.session_state.selected_results_dir = str(selected_run_dir)

        ErrorHandler.log_info(
            f"重新加载目录 {selected_run_dir.name}: 结果数={len(results)} 元数据键={list((metadata or {}).keys())}"
        )

        if results:
            st.success(f"已从目录 {selected_run_dir.name} 加载 {len(results)} 条回测结果。")
        else:
            st.warning(f"目录 {selected_run_dir.name} 中未找到可用的回测结果文件。")

    results = st.session_state.get('backtest_results', [])
    metadata = st.session_state.get('backtest_results_metadata') or preview_metadata or {}
    ErrorHandler.log_info(
        f"展示目录 {selected_run_dir.name}: 会话结果数={len(results)} 元数据状态={metadata.get('status')}"
    )

    st.markdown(f"**当前目录：** `{selected_run_dir}`")
    info_cols = st.columns(3)
    info_cols[0].markdown(f"**状态**：{metadata.get('status', 'unknown')}")
    info_cols[1].markdown(f"**策略数**：{len(metadata.get('strategies', []))}")
    created_at = metadata.get('created_at')
    created_display = created_at
    if created_at:
        try:
            created_display = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            created_display = created_at
    info_cols[2].markdown(f"**创建时间**：{created_display or '未知'}")

    if metadata.get('status') == 'completed' and metadata.get('completed_at'):
        try:
            completed_display = datetime.fromisoformat(metadata['completed_at']).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            completed_display = metadata['completed_at']
        st.caption(f"完成时间：{completed_display}")

    if not results:
        st.info("该目录下暂无回测结果，请稍后再试或选择其他目录。")
        return

    ErrorHandler.log_info(f"使用目录 {selected_run_dir.name} 的 {len(results)} 条回测结果进行分析")

    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["📈 性能总览", "🔗 可视化集成", "📋 策略明细"])

    with tab1:
        render_performance_analysis(results)
    
    with tab2:
        render_visualizer_integration(results)
    
    with tab3:
        render_strategy_details_tab(results)

def render_performance_analysis(results):
    """Render performance analysis tab"""
    # Initialize comparator
    comparator = ResultComparator()
    
    # Add sorting and filtering controls
    st.subheader("🔧 排序与筛选")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sort_options = comparator.sort_options
        sort_by = st.selectbox("排序字段", list(sort_options.keys()), index=0)
        sort_metric = sort_options[sort_by]
    
    with col2:
        sort_order = st.selectbox("排序顺序", ["降序", "升序"])
        ascending = sort_order == "升序"
    
    with col3:
        top_n = st.number_input("展示前 N 项", min_value=1, max_value=len(results), value=min(10, len(results)))
    
    with col4:
        apply_sort = st.button("应用排序")
    
    # Apply sorting if requested
    if apply_sort:
        results = comparator.sort_results(results, sort_metric, ascending)
        results = results[:top_n]
        st.success(f"已按 {sort_by}（{sort_order}）排序，显示前 {top_n} 项")
    
    # Add filtering controls
    with st.expander("🔍 高级筛选"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            min_return = st.number_input("最低收益率 %", value=-100.0, step=1.0)
            min_return = min_return if st.checkbox("启用最低收益率", value=False) else None
        
        with col2:
            max_drawdown = st.number_input("最大回撤 %", value=100.0, step=1.0)
            max_drawdown = max_drawdown if st.checkbox("启用最大回撤", value=False) else None
        
        with col3:
            min_win_rate = st.number_input("最低胜率 %", value=0.0, step=1.0, max_value=100.0)
            min_win_rate = min_win_rate if st.checkbox("启用最低胜率", value=False) else None
        
        with col4:
            min_sharpe = st.number_input("最低夏普比", value=-10.0, step=0.1)
            min_sharpe = min_sharpe if st.checkbox("启用最低夏普比", value=False) else None

        if st.button("应用筛选"):
            results = comparator.filter_results(results, min_return, max_drawdown, min_win_rate, min_sharpe)
            st.success(f"筛选后共有 {len(results)} 条结果符合条件")
    
    # Strategy comparison
    if len(results) >= 2:
        st.subheader("📈 策略对比")
        
        with st.spinner("Analyzing strategy performance..."):
            comparison = comparator.compare_strategies(results)
        
        # Display best strategy
        st.success(f"🏆 最佳策略：**{comparison.best_strategy}**")
        
        # Display rankings
        st.subheader("🏅 策略排名")
        ranking_data = []
        for strategy, rank in sorted(comparison.rankings.items(), key=lambda x: x[1]):
            ranking_data.append({"Rank": rank, "Strategy": strategy})
        
        st.table(pd.DataFrame(ranking_data))
        
        # Display performance matrix
        st.subheader("📋 性能矩阵")
        matrix = comparator.create_enhanced_performance_matrix(results)
        if not matrix.empty:
            st.dataframe(matrix, width='stretch')
        
        # Risk-return analysis
        st.subheader("⚖️ 风险-收益分析")
        risk_analysis = comparator.analyze_risk_return(results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**高收益低风险策略：**")
            for strategy in risk_analysis['high_return_low_risk']:
                st.write(f"✅ {strategy}")
        
        with col2:
            st.write("**高风险高收益策略：**")
            for strategy in risk_analysis['high_return_high_risk']:
                st.write(f"⚠️ {strategy}")
        
        # Top strategies by different metrics
        st.subheader("🏆 指标表现最佳的策略")
        top_metrics = ['sharpe_ratio', 'win_rate', 'total_return_pct', 'sortino_ratio']
        metric_names = ['Sharpe Ratio', 'Win Rate', 'Total Return %', 'Sortino Ratio']
        
        cols = st.columns(len(top_metrics))
        for i, (metric, name) in enumerate(zip(top_metrics, metric_names)):
            with cols[i]:
                top_strategies = comparator.get_top_strategies(results, 3, metric)
                st.write(f"**{name} 前三名：**")
                for j, strategy in enumerate(top_strategies, 1):
                    value = getattr(strategy.metrics, metric, 0)
                    if isinstance(value, float):
                        st.write(f"{j}. {strategy.strategy_name} ({value:.3f})")
                    else:
                        st.write(f"{j}. {strategy.strategy_name} ({value})")

def render_visualizer_integration(results):
    """Render visualizer integration tab"""
    from components.integration.visualizer_bridge import VisualizerIntegrationPanel
    
    # Get strategies from session state
    strategies = st.session_state.get('strategies', [])
    
    # Initialize and render integration panel
    integration_panel = VisualizerIntegrationPanel()
    integration_panel.render(strategies, results)

def render_strategy_details_tab(results):
    """Render strategy details tab"""
    st.subheader("📋 Strategy Details")
    selected_strategy = st.selectbox(
        "Select strategy to view details",
        [result.strategy_name for result in results]
    )
    
    if selected_strategy:
        selected_result = next(r for r in results if r.strategy_name == selected_strategy)
        render_strategy_details(selected_result)

def render_strategy_details(result):
    """Render strategy details"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Return %", f"{result.metrics.total_return_pct:.2f}%")
        st.metric("Win Rate %", f"{result.metrics.win_rate:.2f}%")
    
    with col2:
        st.metric("Max Drawdown %", f"{result.metrics.max_drawdown_pct:.2f}%")
        st.metric("Sharpe Ratio", f"{result.metrics.sharpe_ratio:.3f}")
    
    with col3:
        st.metric("Total Trades", result.metrics.total_trades)
        st.metric("Avg Profit", f"{result.metrics.avg_profit:.2f}")
    
    # Display configuration info
    with st.expander("📋 Backtest Configuration"):
        st.write(f"**Time Range:** {result.config.start_date} to {result.config.end_date}")
        st.write(f"**Timeframe:** {result.config.timeframe}")
        st.write(f"**Trading Pairs:** {', '.join(result.config.pairs)}")
        st.write(f"**Initial Balance:** {result.config.initial_balance:,.2f} USDT")

def render_jupyter_analysis():
    """Render Jupyter analysis page"""
    st.header("📊 Jupyter Analysis")
    
    try:
        from components.jupyter_integration.jupyter_panel import JupyterAnalysisPanel
        
        # Initialize Jupyter panel
        jupyter_panel = JupyterAnalysisPanel()
        
        # Get backtest results
        results = st.session_state.get('backtest_results', [])
        
        # Render Jupyter analysis panel
        jupyter_panel.render(results)
        
    except ImportError as e:
        st.warning("⚠️ Jupyter integration is not fully available")
        st.info("Some Jupyter features may be limited due to missing dependencies")
        
        # Show basic info about available results
        results = st.session_state.get('backtest_results', [])
        if results:
            st.success(f"Found {len(results)} strategy results available for analysis")
            
            # Simple results display
            for result in results:
                with st.expander(f"📊 {result.strategy_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Return", f"{result.metrics.total_return_pct:.2f}%")
                    with col2:
                        st.metric("Win Rate", f"{result.metrics.win_rate:.2f}%")
                    with col3:
                        st.metric("Max Drawdown", f"{result.metrics.max_drawdown_pct:.2f}%")
        else:
            st.info("No backtest results available. Please run a backtest first.")
    
    except Exception as e:
        st.error(f"Error loading Jupyter analysis: {str(e)}")
        st.info("Please check the system logs for more details")

def render_performance_monitor():
    """Render performance monitoring page"""
    from components.optimization.performance_panel import PerformanceMonitoringPanel
    
    # Initialize performance panel
    performance_panel = PerformanceMonitoringPanel()
    
    # Render performance monitoring panel
    performance_panel.render()

if __name__ == "__main__":
    main()