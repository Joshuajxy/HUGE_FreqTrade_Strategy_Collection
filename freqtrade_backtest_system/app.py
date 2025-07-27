import streamlit as st
from freqtrade_backtest_system.components.ui.main_layout import MainLayout
from freqtrade_backtest_system.components.visualization.advanced_charts import AdvancedCharts
from freqtrade_backtest_system.utils.data_models import BacktestResult, PerformanceMetrics, TradeRecord, BacktestConfig
from datetime import datetime, date
import pandas as pd

# Initialize layout
main_layout = MainLayout()
main_layout._setup_page_config()
main_layout._load_custom_css()

def main():
    main_layout.render_header()
    selected_page = main_layout.render_navigation()

    from freqtrade_backtest_system.components.strategy_manager.scanner import StrategyScanner
    scanner = StrategyScanner()
    available_strategies = scanner.scan_strategies()

    if selected_page == "Strategy Management":
        st.title("Strategy Management")
        st.write("This will be the strategy selection and management interface.")
        # Placeholder for StrategySelector
        # from freqtrade_backtest_system.components.strategy_manager.selector import StrategySelector
        # selector = StrategySelector()
        # selected_strategies = selector.render_strategy_selection(available_strategies)

    elif selected_page == "Backtest Configuration":
        st.title("Backtest Configuration")
        st.write("This will be the backtest parameter configuration interface.")
        # Placeholder for BacktestConfigPanel
        # from freqtrade_backtest_system.components.backtest_config.panel import BacktestConfigPanel
        # config_panel = BacktestConfigPanel()
        # config = config_panel.render_config_panel()

    elif selected_page == "Execution Monitoring":
        st.title("Execution Monitoring")
        st.write("This will be the real-time monitoring interface for backtesting and Dry Run.")

        from freqtrade_backtest_system.components.execution.dry_run_executor import DryRunExecutor
        from freqtrade_backtest_system.components.ui.dry_run_monitor_panel import DryRunMonitorPanel

        # Initialize DryRunExecutor in session state to maintain its state
        if 'dry_run_executor' not in st.session_state:
            st.session_state.dry_run_executor = DryRunExecutor()

        dry_run_executor = st.session_state.dry_run_executor
        dry_run_monitor_panel = DryRunMonitorPanel()

        # Get active dry runs
        active_dry_runs = dry_run_executor.get_active_dry_runs()
        dry_run_monitor_panel.render_dry_run_monitor(active_dry_runs)

        # Handle stop dry run request from the monitor panel
        if "stop_dry_run_id" in st.session_state and st.session_state["stop_dry_run_id"]:
            run_id_to_stop = st.session_state.pop("stop_dry_run_id")
            if dry_run_executor.stop_dry_run(run_id_to_stop):
                st.success(f"Dry Run {run_id_to_stop} stopped.")
            else:
                st.error(f"Failed to stop Dry Run {run_id_to_stop}.")
            st.rerun() # Rerun to update the UI after stopping

    elif selected_page == "Results Analysis":
        st.title("Results Analysis")
        st.write("This section will display detailed analysis and visualization charts of backtest results.")

        # Dummy data for demonstration
        dummy_config = BacktestConfig(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            timeframe="1h",
            pairs=["BTC/USDT"],
            initial_balance=1000,
            max_open_trades=3
        )

        dummy_trades_1 = [
            TradeRecord(pair="BTC/USDT", side="buy", timestamp=datetime(2023, 1, 5, 10, 0), price=20000, amount=0.01, profit=50, reason="entry"),
            TradeRecord(pair="BTC/USDT", side="sell", timestamp=datetime(2023, 1, 7, 15, 0), price=20500, amount=0.01, profit=50, reason="exit"),
            TradeRecord(pair="BTC/USDT", side="buy", timestamp=datetime(2023, 1, 10, 9, 0), price=21000, amount=0.01, profit=-20, reason="entry"),
            TradeRecord(pair="BTC/USDT", side="sell", timestamp=datetime(2023, 1, 12, 11, 0), price=20800, amount=0.01, profit=-20, reason="exit"),
            TradeRecord(pair="BTC/USDT", side="buy", timestamp=datetime(2023, 1, 15, 14, 0), price=22000, amount=0.01, profit=100, reason="entry"),
            TradeRecord(pair="BTC/USDT", side="sell", timestamp=datetime(2023, 1, 17, 16, 0), price=23000, amount=0.01, profit=100, reason="exit"),
        ]
        dummy_metrics_1 = PerformanceMetrics(total_return=130, total_return_pct=13, win_rate=66.67, max_drawdown=20, sharpe_ratio=0.8)
        dummy_result_1 = BacktestResult(strategy_name="StrategyA", config=dummy_config, metrics=dummy_metrics_1, trades=dummy_trades_1, timestamp=datetime.now())

        dummy_trades_2 = [
            TradeRecord(pair="BTC/USDT", side="buy", timestamp=datetime(2023, 1, 6, 11, 0), price=20100, amount=0.01, profit=30, reason="entry"),
            TradeRecord(pair="BTC/USDT", side="sell", timestamp=datetime(2023, 1, 8, 16, 0), price=20400, amount=0.01, profit=30, reason="exit"),
            TradeRecord(pair="BTC/USDT", side="buy", timestamp=datetime(2023, 1, 11, 10, 0), price=21100, amount=0.01, profit=80, reason="entry"),
            TradeRecord(pair="BTC/USDT", side="sell", timestamp=datetime(2023, 1, 13, 12, 0), price=21900, amount=0.01, profit=80, reason="exit"),
        ]
        dummy_metrics_2 = PerformanceMetrics(total_return=110, total_return_pct=11, win_rate=100, max_drawdown=0, sharpe_ratio=1.2)
        dummy_result_2 = BacktestResult(strategy_name="StrategyB", config=dummy_config, metrics=dummy_metrics_2, trades=dummy_trades_2, timestamp=datetime.now())

        results_to_display = [dummy_result_1, dummy_result_2]

        advanced_charts = AdvancedCharts()

        st.subheader("Cumulative Equity Curve")
        equity_curve_fig = advanced_charts.create_equity_curve(results_to_display)
        st.plotly_chart(equity_curve_fig, use_container_width=True)

        st.subheader("Drawdown Plot (StrategyA)")
        drawdown_fig_a = advanced_charts.create_drawdown_plot(dummy_result_1)
        st.plotly_chart(drawdown_fig_a, use_container_width=True)

        st.subheader("Drawdown Plot (StrategyB)")
        drawdown_fig_b = advanced_charts.create_drawdown_plot(dummy_result_2)
        st.plotly_chart(drawdown_fig_b, use_container_width=True)

        st.subheader("Trade Signal Markers (StrategyA)")
        # For trade markers, we need OHLCV data. Using dummy data for now.
        dummy_ohlcv = pd.DataFrame({
            'date': pd.to_datetime([datetime(2023, 1, 1), datetime(2023, 1, 5), datetime(2023, 1, 7), datetime(2023, 1, 10), datetime(2023, 1, 12), datetime(2023, 1, 15), datetime(2023, 1, 17), datetime(2023, 1, 20)]),
            'open': [20000, 20100, 20400, 20900, 20700, 21500, 22500, 22800],
            'high': [20200, 20300, 20600, 21200, 20900, 22200, 23200, 23500],
            'low': [19800, 19900, 20200, 20700, 20500, 21300, 22300, 22600],
            'close': [20100, 20200, 20500, 21000, 20800, 22000, 23000, 23300]
        })
        trade_markers_fig_a = advanced_charts.create_trade_markers_chart(dummy_result_1, dummy_ohlcv)
        st.plotly_chart(trade_markers_fig_a, use_container_width=True)


    elif selected_page == "Jupyter分析":
        st.title("Jupyter Notebook 深度分析")
        st.write("这里将是Jupyter Notebook集成界面。")
        # Placeholder for JupyterPanel
        # from freqtrade_backtest_system.components.jupyter_integration.jupyter_panel import JupyterPanel
        # jupyter_panel = JupyterPanel()
        # jupyter_panel.render_jupyter_panel(backtest_results)

    elif selected_page == "超参数优化":
        st.title("超参数优化")
        from freqtrade_backtest_system.components.ui.hyperopt_panel import HyperoptPanel
        hyperopt_panel = HyperoptPanel()
        hyperopt_panel.render_hyperopt_panel(available_strategies)

if __name__ == "__main__":
    main()
