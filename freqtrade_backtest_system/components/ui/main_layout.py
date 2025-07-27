"""
Main interface layout component
"""
import streamlit as st
from streamlit_option_menu import option_menu

class MainLayout:
    """Main interface layout manager"""
    
    def __init__(self):
        """Initialize layout"""
        self._setup_page_config()
        self._load_custom_css()
    
    def _setup_page_config(self):
        """Configure basic page settings"""
        st.set_page_config(
            page_title="Freqtrade Backtest System",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo/help',
                'Report a bug': 'https://github.com/your-repo/issues',
                'About': "# Freqtrade Backtest System\nProfessional strategy backtesting and analysis platform"
            }
        )
    
    def _load_custom_css(self):
        """Load custom CSS styles"""
        css = """
        <style>
        /* Theme colors */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --success-color: #2ca02c;
            --warning-color: #d62728;
            --info-color: #17a2b8;
            --light-bg: #f8f9fa;
            --dark-bg: #343a40;
        }
        
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom container styles */
        .main-container {
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .metric-container {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
            margin-bottom: 1rem;
        }
        
        .strategy-card {
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .strategy-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        .strategy-card.selected {
            border-color: var(--primary-color);
            background: #f0f8ff;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-running { background-color: var(--warning-color); }
        .status-completed { background-color: var(--success-color); }
        .status-failed { background-color: var(--warning-color); }
        .status-idle { background-color: #6c757d; }
        
        /* Progress bar styles */
        .progress-container {
            background: #e9ecef;
            border-radius: 4px;
            height: 8px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            height: 100%;
            transition: width 0.3s ease;
        }
        
        /* Table styles */
        .dataframe {
            border: none !important;
        }
        
        .dataframe th {
            background: var(--primary-color) !important;
            color: white !important;
            font-weight: 600 !important;
            text-align: center !important;
        }
        
        .dataframe td {
            text-align: center !important;
            padding: 0.75rem !important;
        }
        
        .dataframe tr:nth-child(even) {
            background: #f8f9fa !important;
        }
        
        /* Button styles */
        .stButton > button {
            background: linear-gradient(90deg, var(--primary-color), #1565c0);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3);
        }
        
        /* Sidebar styles */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        /* Chart container */
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-container {
                padding: 0.5rem;
            }
            
            .metric-container {
                padding: 1rem;
            }
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def render_header(self):
        """Render page header"""
        st.markdown("""
        <div class="main-container">
            <h1 style="color: white; text-align: center; margin: 0;">
                📈 Freqtrade Strategy Backtest System
            </h1>
            <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">
                Professional Multi-Strategy Parallel Backtesting & Analysis Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_navigation(self) -> str:
        """Render navigation menu"""
        selected = option_menu(
            menu_title=None,
            options=["Strategy Management", "Backtest Configuration", "Execution Monitoring", "Results Analysis", "Jupyter Analysis", "Hyperparameter Optimization"],
            icons=["folder", "gear", "play-circle", "bar-chart", "journal-code", "speedometer2"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#1f77b4", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
        return selected
    
    def render_sidebar_info(self):
        """Render sidebar information"""
        with st.sidebar:
            st.markdown("### 📊 System Status")
            
            # System status indicators
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", "Normal", delta="✅")
            with col2:
                st.metric("Active Tasks", "0", delta="0")
            
            st.markdown("### 🔧 Quick Actions")
            
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
            
            if st.button("📋 View Logs", use_container_width=True):
                self._show_logs()
            
            st.markdown("### 📚 Help Information")
            
            with st.expander("💡 Usage Tips"):
                st.markdown("""
                **Strategy Management:**
                - Auto scan strategy files
                - Support batch selection
                
                **Backtest Config:**
                - Minimum 5-minute interval
                - Support config saving
                
                **Execution Monitor:**
                - Real-time status display
                - Parallel execution support
                
                **Results Analysis:**
                - Multi-dimensional comparison
                - Interactive charts
                """)
    
    def _show_logs(self):
        """Show system logs"""
        try:
            from pathlib import Path
            log_file = Path("logs/app.log")
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = f.readlines()
                
                # Show recent logs
                recent_logs = logs[-50:] if len(logs) > 50 else logs
                
                st.text_area(
                    "System Logs",
                    value="".join(recent_logs),
                    height=300,
                    disabled=True
                )
            else:
                st.info("No log file available")
        
        except Exception as e:
            st.error(f"Failed to read logs: {str(e)}")
    
    def render_footer(self):
        """Render page footer"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📈 Freqtrade Backtest System**")
            st.caption("Version 1.0.0")
        
        with col2:
            st.markdown("**🔗 Related Links**")
            st.markdown("[Freqtrade Documentation](https://www.freqtrade.io/)")
        
        with col3:
            st.markdown("**💬 Technical Support**")
            st.caption("Please check help documentation for issues")
    
    def show_loading(self, message: str = "Processing..."):
        """Show loading status"""
        return st.spinner(message)
    
    def show_success(self, message: str):
        """Show success message"""
        st.success(f"✅ {message}")
    
    def show_error(self, message: str):
        """Show error message"""
        st.error(f"❌ {message}")
    
    def show_warning(self, message: str):
        """Show warning message"""
        st.warning(f"⚠️ {message}")
    
    def show_info(self, message: str):
        """Show info message"""
        st.info(f"ℹ️ {message}")