import streamlit as st
from typing import List, Dict, Any
from freqtrade_backtest_system.utils.data_models import StrategyInfo, BacktestConfig
from freqtrade_backtest_system.components.execution.hyperopt_executor import HyperoptExecutor
from freqtrade_backtest_system.utils.error_handling import ErrorHandler
import pandas as pd

class HyperoptPanel:
    def __init__(self):
        self.hyperopt_executor = HyperoptExecutor()

    def render_hyperopt_panel(self, available_strategies: List[StrategyInfo]):
        st.subheader("🧪 Strategy Hyperparameter Optimization (Hyperopt)")

        if not available_strategies:
            st.info("Please scan and load strategy files first.")
            return

        selected_strategy_name = st.selectbox(
            "Select Strategy to Optimize",
            [s.name for s in available_strategies],
            key="hyperopt_strategy_select"
        )

        st.markdown("--- ")
        st.subheader("⚙️ Optimization Configuration")

        col1, col2 = st.columns(2)
        with col1:
            epochs = st.number_input("Optimization Epochs", min_value=1, value=100, step=10, key="hyperopt_epochs")
            loss_function = st.selectbox(
                "Loss Function",
                ["ShortTradeDurHyperoptLoss", "ProfitHyperoptLoss", "SharpeHyperoptLoss"], # Common Freqtrade loss functions
                key="hyperopt_loss_function"
            )
        with col2:
            timerange_start = st.date_input("Optimization Time Range - Start", value=pd.to_datetime("2023-01-01"), key="hyperopt_timerange_start")
            timerange_end = st.date_input("Optimization Time Range - End", value=pd.to_datetime("2023-03-31"), key="hyperopt_timerange_end")

        st.info("💡 Tip: Parameter range configuration currently requires manual modification of strategy files or Freqtrade configuration files. UI configuration will be supported in future versions.")

        if st.button("🚀 Start Hyperparameter Optimization", key="start_hyperopt_button"):
            with st.spinner("Starting hyperparameter optimization..."):
                try:
                    # Dummy BacktestConfig for hyperopt execution
                    # In a real scenario, this would come from a config panel
                    dummy_config = BacktestConfig(
                        start_date=timerange_start,
                        end_date=timerange_end,
                        timeframe="5m", # Default timeframe for hyperopt
                        pairs=["BTC/USDT"], # Default pair for hyperopt
                        initial_balance=1000,
                        max_open_trades=3
                    )

                    hyperopt_params = {
                        "epochs": epochs,
                        "loss": loss_function
                    }

                    result_file = self.hyperopt_executor.execute_hyperopt(
                        selected_strategy_name,
                        dummy_config,
                        hyperopt_params
                    )
                    st.session_state["hyperopt_result_file"] = result_file
                    st.session_state["hyperopt_strategy_name"] = selected_strategy_name
                    st.success(f"Hyperparameter optimization task started! Results will be saved to: {result_file}")
                except Exception as e:
                    ErrorHandler.handle_application_error(e)

        st.markdown("--- ")
        st.subheader("📊 Optimization Results")

        if "hyperopt_result_file" in st.session_state and st.session_state["hyperopt_result_file"]:
            result_file_path = st.session_state["hyperopt_result_file"]
            strategy_name = st.session_state["hyperopt_strategy_name"]
            st.write(f"**Strategy: {strategy_name}**")
            st.write(f"Result File: {result_file_path}")

            if st.button("🔄 Load and Display Results", key="load_hyperopt_results_button"):
                try:
                    results = self.hyperopt_executor.parse_hyperopt_results(result_file_path)
                    self._display_hyperopt_results(results)
                except Exception as e:
                    ErrorHandler.handle_application_error(e)
        else:
            st.info("No optimization results to display. Please start an optimization task first.")

    def _display_hyperopt_results(self, results: Dict[str, Any]):
        st.write("### Optimization Overview")
        st.json(results.get("results_metrics", {}))

        st.write("### Best Parameter Combination")
        st.json(results.get("best_params", {}))

        st.write("### Optimization History")
        # Display a subset of the optimization history for brevity
        history = results.get("hyperopt_results", [])
        if history:
            df_history = pd.DataFrame(history)
            st.dataframe(df_history.head(10)) # Show first 10 results
            if len(df_history) > 10:
                st.write(f"... (共 {len(df_history)} 条记录)")
        else:
            st.info("No optimization history found.")
