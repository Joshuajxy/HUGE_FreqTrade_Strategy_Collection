"""
Freqtrade Backtest System Main Application
"""
import streamlit as st
from pathlib import Path
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
from components.execution.backtest_executor import BacktestExecutor
from components.results.parser import ResultParser
from components.results.comparator import ResultComparator
from utils.error_handling import ErrorHandler
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

def main():
    """Main application function"""
    try:
        # Initialize session state
        initialize_session_state()

        # Initialize main layout
        layout = MainLayout()
        layout.render_header()
        
        # Render navigation menu
        selected_page = layout.render_navigation()
        
        # Render sidebar info
        layout.render_sidebar_info()
        
        # Render content based on selected page
        if selected_page == "Strategy Management":
            render_strategy_management()
        elif selected_page == "Backtest Config":
            render_backtest_config()
        elif selected_page == "Execution Monitor":
            render_execution_monitor()
        elif selected_page == "Results Analysis":
            render_results_analysis()
        elif selected_page == "Jupyter Analysis":
            render_jupyter_analysis()
        elif selected_page == "Performance Monitor":
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
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_path = st.text_input(
            "Scan Path", 
            value="..", 
            help="Directory path containing strategy files"
        )
    
    with col2:
        if st.button("🔍 Start Scan", type="primary", width='stretch'):
            st.session_state.trigger_scan = True
            st.session_state.scan_path = scan_path
    
    with col3:
        if st.button("🗑️ Clear Results", width='stretch'):
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
            
            if st.button("🚀 Start Backtest", type="primary", width='stretch'):
                st.session_state.start_backtest = True
                st.success("Backtest configuration saved, please go to Execution Monitor page to view progress")
    
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
                with st.spinner("Starting backtest tasks..."):
                    # Submit tasks to scheduler
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
    st.header("📊 Results Analysis")
    
    # Check if there are backtest results
    results = st.session_state.get('backtest_results', [])
    if not results:
        st.info("No backtest results available, please run backtest first")
        return
    
    st.success(f"Found {len(results)} strategy backtest results")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["📈 Performance Analysis", "🔗 Visualizer Integration", "📋 Strategy Details"])
    
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
    st.subheader("🔧 Sort & Filter")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sort_options = comparator.sort_options
        sort_by = st.selectbox("Sort by", list(sort_options.keys()), index=0)
        sort_metric = sort_options[sort_by]
    
    with col2:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])
        ascending = sort_order == "Ascending"
    
    with col3:
        top_n = st.number_input("Top N", min_value=1, max_value=len(results), value=min(10, len(results)))
    
    with col4:
        apply_sort = st.button("Apply Sorting")
    
    # Apply sorting if requested
    if apply_sort:
        results = comparator.sort_results(results, sort_metric, ascending)
        results = results[:top_n]
        st.success(f"Sorted by {sort_by} ({sort_order}), showing top {top_n}")
    
    # Add filtering controls
    with st.expander("🔍 Advanced Filters"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            min_return = st.number_input("Min Return %", value=-100.0, step=1.0)
            min_return = min_return if st.checkbox("Apply Min Return", value=False) else None
        
        with col2:
            max_drawdown = st.number_input("Max Drawdown %", value=100.0, step=1.0)
            max_drawdown = max_drawdown if st.checkbox("Apply Max Drawdown", value=False) else None
        
        with col3:
            min_win_rate = st.number_input("Min Win Rate %", value=0.0, step=1.0, max_value=100.0)
            min_win_rate = min_win_rate if st.checkbox("Apply Min Win Rate", value=False) else None
        
        with col4:
            min_sharpe = st.number_input("Min Sharpe Ratio", value=-10.0, step=0.1)
            min_sharpe = min_sharpe if st.checkbox("Apply Min Sharpe", value=False) else None
        
        if st.button("Apply Filters"):
            results = comparator.filter_results(results, min_return, max_drawdown, min_win_rate, min_sharpe)
            st.success(f"Filtered results: {len(results)} strategies match criteria")
    
    # Strategy comparison
    if len(results) >= 2:
        st.subheader("📈 Strategy Comparison")
        
        with st.spinner("Analyzing strategy performance..."):
            comparison = comparator.compare_strategies(results)
        
        # Display best strategy
        st.success(f"🏆 Best Strategy: **{comparison.best_strategy}**")
        
        # Display rankings
        st.subheader("🏅 Strategy Rankings")
        ranking_data = []
        for strategy, rank in sorted(comparison.rankings.items(), key=lambda x: x[1]):
            ranking_data.append({"Rank": rank, "Strategy": strategy})
        
        st.table(pd.DataFrame(ranking_data))
        
        # Display performance matrix
        st.subheader("📋 Performance Matrix")
        matrix = comparator.create_enhanced_performance_matrix(results)
        if not matrix.empty:
            st.dataframe(matrix, width='stretch')
        
        # Risk-return analysis
        st.subheader("⚖️ Risk-Return Analysis")
        risk_analysis = comparator.analyze_risk_return(results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**High Return Low Risk Strategies:**")
            for strategy in risk_analysis['high_return_low_risk']:
                st.write(f"✅ {strategy}")
        
        with col2:
            st.write("**High Risk High Return Strategies:**")
            for strategy in risk_analysis['high_return_high_risk']:
                st.write(f"⚠️ {strategy}")
        
        # Top strategies by different metrics
        st.subheader("🏆 Top Strategies by Metric")
        top_metrics = ['sharpe_ratio', 'win_rate', 'total_return_pct', 'sortino_ratio']
        metric_names = ['Sharpe Ratio', 'Win Rate', 'Total Return %', 'Sortino Ratio']
        
        cols = st.columns(len(top_metrics))
        for i, (metric, name) in enumerate(zip(top_metrics, metric_names)):
            with cols[i]:
                top_strategies = comparator.get_top_strategies(results, 3, metric)
                st.write(f"**Top 3 by {name}:**")
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