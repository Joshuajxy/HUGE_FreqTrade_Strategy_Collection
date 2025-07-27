import streamlit as st
from typing import Dict, Any
from freqtrade_backtest_system.utils.data_models import DryRunStatus, ExecutionStatus
import plotly.graph_objects as go
from datetime import datetime

class DryRunMonitorPanel:
    def render_dry_run_monitor(self, dry_run_status: Dict[str, DryRunStatus]):
        st.subheader("📊 Real-time Dry Run Monitoring")

        if not dry_run_status:
            st.info("No running Dry Run tasks.")
            return

        for run_id, status in dry_run_status.items():
            with st.expander(f"**Strategy: {status.strategy} (ID: {run_id})** - Status: {status.status.value.upper()}", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Run Time", str(datetime.now() - status.start_time).split('.')[0])
                with col2:
                    st.metric("Last Update", status.last_update.strftime("%H:%M:%S"))
                with col3:
                    st.metric("Signals Count", status.signals_count)
                with col4:
                    st.metric("Open Trades", status.open_trades)

                st.markdown("--- ")
                st.subheader("Equity Curve")
                if status.balance_history:
                    df_balance = pd.DataFrame(status.balance_history)
                    df_balance['timestamp'] = pd.to_datetime(df_balance['timestamp'])
                    fig = go.Figure(data=go.Scatter(x=df_balance['timestamp'], y=df_balance['balance'], mode='lines'))
                    fig.update_layout(title='Real-time Equity Curve', xaxis_title='Time', yaxis_title='Balance')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No equity curve data available.")

                st.subheader("Trade Signals")
                if status.trade_signals:
                    df_signals = pd.DataFrame(status.trade_signals)
                    st.dataframe(df_signals)
                else:
                    st.info("No trade signal data available.")

                st.subheader("Latest Log")
                st.code(status.latest_log_line if status.latest_log_line else "Waiting for log output...")

                if st.button(f"Stop {status.strategy}", key=f"stop_dry_run_{run_id}"):
                    # This button will trigger the stop_dry_run method in the main app logic
                    st.session_state["stop_dry_run_id"] = run_id
                    st.warning(f"Request to stop {status.strategy} sent...")

