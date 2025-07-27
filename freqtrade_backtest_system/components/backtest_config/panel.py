"""
Backtest configuration panel component
"""
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from utils.data_models import BacktestConfig, DEFAULT_TIMEFRAMES, DEFAULT_PAIRS, DEFAULT_STAKE_AMOUNTS
from utils.error_handling import ErrorHandler, ConfigError, error_handler

class BacktestConfigPanel:
    """Backtest configuration panel"""
    
    def __init__(self):
        """Initialize configuration panel"""
        self.config = None
    
    def render_config_panel(self) -> Optional[BacktestConfig]:
        """
        Render backtest configuration panel
        
        Returns:
            Backtest configuration object
        """
        st.subheader("⚙️ Backtest Configuration")
        
        try:
            # Basic configuration
            config_data = self._render_basic_config()
            
            # Advanced configuration
            advanced_config = self._render_advanced_config()
            
            # Merge configurations
            config_data.update(advanced_config)
            
            # Validate configuration
            if self._validate_config(config_data):
                self.config = BacktestConfig(**config_data)
                return self.config
            
            return None
        
        except Exception as e:
            ErrorHandler.handle_config_error(e)
            return None
    
    def _render_basic_config(self) -> Dict[str, Any]:
        """Render basic configuration"""
        with st.expander("📅 Basic Configuration", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Time Settings**")
                
                # Default time range
                default_end = date.today()
                default_start = default_end - timedelta(days=30)
                
                start_date = st.date_input(
                    "Start Date",
                    value=default_start,
                    max_value=default_end,
                    help="Backtest start date"
                )
                
                end_date = st.date_input(
                    "End Date",
                    value=default_end,
                    min_value=start_date,
                    max_value=default_end,
                    help="Backtest end date"
                )
                
                timeframe = st.selectbox(
                    "Timeframe",
                    DEFAULT_TIMEFRAMES,
                    index=DEFAULT_TIMEFRAMES.index("1h"),
                    help="Candlestick time interval, minimum 5 minutes supported"
                )
            
            with col2:
                st.markdown("**Trading Settings**")
                
                pairs = st.multiselect(
                    "Trading Pairs",
                    DEFAULT_PAIRS,
                    default=["BTC/USDT"],
                    help="Select trading pairs for backtesting"
                )
                
                initial_balance = st.number_input(
                    "Initial Balance (USDT)",
                    min_value=100.0,
                    max_value=1000000.0,
                    value=1000.0,
                    step=100.0,
                    help="Initial balance for backtesting"
                )
                
                max_open_trades = st.number_input(
                    "Max Open Trades",
                    min_value=1,
                    max_value=20,
                    value=3,
                    help="Maximum number of concurrent trades"
                )
            
            with col3:
                st.markdown("**Risk Settings**")
                
                stake_amount = st.selectbox(
                    "Stake Amount",
                    DEFAULT_STAKE_AMOUNTS,
                    index=0,
                    help="Amount to invest per trade"
                )
                
                fee = st.number_input(
                    "Fee Rate",
                    min_value=0.0,
                    max_value=0.01,
                    value=0.001,
                    step=0.0001,
                    format="%.4f",
                    help="Trading fee rate"
                )
                
                dry_run_wallet = st.number_input(
                    "Dry Run Wallet (USDT)",
                    min_value=100.0,
                    max_value=1000000.0,
                    value=1000.0,
                    step=100.0,
                    help="Virtual funds for dry run mode"
                )
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'timeframe': timeframe,
            'pairs': pairs,
            'initial_balance': initial_balance,
            'max_open_trades': max_open_trades,
            'stake_amount': stake_amount,
            'fee': fee,
            'dry_run_wallet': dry_run_wallet
        }
    
    def _render_advanced_config(self) -> Dict[str, Any]:
        """Render advanced configuration"""
        with st.expander("🔧 Advanced Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Trading Strategy**")
                
                enable_position_stacking = st.checkbox(
                    "Enable Position Stacking",
                    value=False,
                    help="Allow multiple positions on the same trading pair"
                )
                
                st.markdown("**Data Source Settings**")
                
                data_source = st.selectbox(
                    "Data Source",
                    ["binance", "okx", "huobi", "kraken"],
                    index=0,
                    help="Select historical data source"
                )
            
            with col2:
                st.markdown("**Performance Optimization**")
                
                enable_protections = st.checkbox(
                    "Enable Protections",
                    value=True,
                    help="Enable freqtrade built-in protection mechanisms"
                )
                
                process_only_new_candles = st.checkbox(
                    "Process Only New Candles",
                    value=True,
                    help="Improve backtest performance"
                )
        
        return {
            'enable_position_stacking': enable_position_stacking
        }
    
    def _validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration parameters"""
        try:
            # Date validation
            if config_data['start_date'] >= config_data['end_date']:
                st.error("❌ Start date must be earlier than end date")
                return False
            
            # Trading pairs validation
            if not config_data['pairs']:
                st.error("❌ Please select at least one trading pair")
                return False
            
            # Balance validation
            if config_data['initial_balance'] <= 0:
                st.error("❌ Initial balance must be greater than 0")
                return False
            
            # Time range validation
            date_diff = (config_data['end_date'] - config_data['start_date']).days
            if date_diff < 1:
                st.error("❌ Backtest time range must be at least 1 day")
                return False
            
            if date_diff > 365:
                st.warning("⚠️ Backtest time range exceeds 1 year, may take longer time")
            
            # Display configuration summary
            self._show_config_summary(config_data)
            
            return True
        
        except Exception as e:
            ErrorHandler.handle_config_error(e)
            return False
    
    def _show_config_summary(self, config_data: Dict[str, Any]):
        """Display configuration summary"""
        st.success("✅ Configuration validation passed")
        
        with st.expander("📋 Configuration Summary", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Time Settings:**")
                st.write(f"- Start Date: {config_data['start_date']}")
                st.write(f"- End Date: {config_data['end_date']}")
                st.write(f"- Timeframe: {config_data['timeframe']}")
                
                days = (config_data['end_date'] - config_data['start_date']).days
                st.write(f"- Backtest Days: {days} days")
            
            with col2:
                st.write("**Trading Settings:**")
                st.write(f"- Trading Pairs: {', '.join(config_data['pairs'])}")
                st.write(f"- Initial Balance: {config_data['initial_balance']:,.2f} USDT")
                st.write(f"- Max Open Trades: {config_data['max_open_trades']}")
                st.write(f"- Stake Amount: {config_data['stake_amount']}")
                st.write(f"- Fee Rate: {config_data['fee']:.4f}")
    
    def render_quick_configs(self):
        """Render quick configuration options"""
        st.subheader("⚡ Quick Configurations")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📅 Last 7 Days", help="Set last 7 days backtest"):
                self._apply_quick_config("7days")
        
        with col2:
            if st.button("📅 Last 30 Days", help="Set last 30 days backtest"):
                self._apply_quick_config("30days")
        
        with col3:
            if st.button("📅 Last 90 Days", help="Set last 90 days backtest"):
                self._apply_quick_config("90days")
        
        with col4:
            if st.button("📅 Last 1 Year", help="Set last 1 year backtest"):
                self._apply_quick_config("1year")
    
    def _apply_quick_config(self, config_type: str):
        """Apply quick configuration"""
        today = date.today()
        
        config_map = {
            "7days": today - timedelta(days=7),
            "30days": today - timedelta(days=30),
            "90days": today - timedelta(days=90),
            "1year": today - timedelta(days=365)
        }
        
        if config_type in config_map:
            st.session_state.quick_start_date = config_map[config_type]
            st.session_state.quick_end_date = today
            st.rerun()
    
    def render_config_validation_info(self):
        """Render configuration validation information"""
        st.info("""
        **Configuration Requirements:**
        - Start date must be earlier than end date
        - At least one trading pair must be selected
        - Initial balance must be greater than 0
        - Minimum timeframe supported is 5 minutes
        - Recommended backtest time should not exceed 1 year
        """)
    
    def get_estimated_execution_time(self, config: BacktestConfig, strategy_count: int) -> str:
        """Estimate execution time"""
        try:
            # Estimate based on empirical formula
            days = (config.end_date - config.start_date).days
            pairs_count = len(config.pairs)
            
            # Timeframe weights
            timeframe_weights = {
                "1m": 10, "5m": 8, "15m": 6, "30m": 4,
                "1h": 3, "2h": 2, "4h": 1.5, "1d": 1
            }
            
            weight = timeframe_weights.get(config.timeframe, 3)
            
            # Estimate single strategy execution time (seconds)
            base_time = days * pairs_count * weight * 0.1
            
            # Consider parallel execution
            parallel_factor = min(strategy_count, 4)  # Assume max 4 parallel
            total_time = (base_time * strategy_count) / parallel_factor
            
            if total_time < 60:
                return f"About {int(total_time)} seconds"
            elif total_time < 3600:
                return f"About {int(total_time / 60)} minutes"
            else:
                return f"About {int(total_time / 3600)} hours"
        
        except Exception:
            return "Cannot estimate"