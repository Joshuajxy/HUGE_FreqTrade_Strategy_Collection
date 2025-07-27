"""
Configuration manager
"""
import json
import streamlit as st
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from utils.data_models import BacktestConfig
from utils.error_handling import ErrorHandler, ConfigError, error_handler

class ConfigManager:
    """Configuration manager"""
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize configuration manager
        
        Args:
            config_dir: configuration file storage directory
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Ensure configuration directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        directories = [
            self.config_dir,
            self.config_dir / "backtest",
            self.config_dir / "templates"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    @error_handler(ConfigError, show_error=True, return_default=False)
    def save_config(self, config: BacktestConfig, name: str, description: str = "") -> bool:
        """
        Save configuration to file
        
        Args:
            config: backtest configuration object
            name: configuration name
            description: configuration description
            
        Returns:
            whether save was successful
        """
        try:
            # Validate configuration name
            if not self._validate_config_name(name):
                raise ConfigError(f"Invalid configuration name: {name}")
            
            # Create configuration data
            config_data = {
                'name': name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'config': config.to_dict()
            }
            
            # Save to file
            config_file = self.config_dir / "backtest" / f"{name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Configuration saved: {name}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to save configuration: {str(e)}")
            raise ConfigError(f"Failed to save configuration: {str(e)}")
    
    @error_handler(ConfigError, show_error=True, return_default=None)
    def load_config(self, name: str) -> Optional[BacktestConfig]:
        """
        Load configuration from file
        
        Args:
            name: configuration name
            
        Returns:
            backtest configuration object
        """
        try:
            config_file = self.config_dir / "backtest" / f"{name}.json"
            
            if not config_file.exists():
                raise ConfigError(f"Configuration file does not exist: {name}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate configuration data
            if 'config' not in config_data:
                raise ConfigError(f"Configuration file format error: {name}")
            
            config = BacktestConfig.from_dict(config_data['config'])
            ErrorHandler.log_info(f"Configuration loaded: {name}")
            
            return config
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to load configuration: {str(e)}")
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """
        List all saved configurations
        
        Returns:
            configuration information list
        """
        configs = []
        config_dir = self.config_dir / "backtest"
        
        try:
            for config_file in config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    configs.append({
                        'name': config_data.get('name', config_file.stem),
                        'description': config_data.get('description', ''),
                        'created_at': config_data.get('created_at', ''),
                        'file_path': str(config_file)
                    })
                
                except Exception as e:
                    ErrorHandler.log_warning(f"Cannot read configuration file {config_file}: {str(e)}")
                    continue
            
            # Sort by creation time
            configs.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            ErrorHandler.log_error(f"Failed to list configurations: {str(e)}")
        
        return configs
    
    @error_handler(ConfigError, show_error=True, return_default=False)
    def delete_config(self, name: str) -> bool:
        """
        Delete configuration
        
        Args:
            name: configuration name
            
        Returns:
            whether deletion was successful
        """
        try:
            config_file = self.config_dir / "backtest" / f"{name}.json"
            
            if not config_file.exists():
                raise ConfigError(f"Configuration file does not exist: {name}")
            
            config_file.unlink()
            ErrorHandler.log_info(f"Configuration deleted: {name}")
            
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to delete configuration: {str(e)}")
            raise ConfigError(f"Failed to delete configuration: {str(e)}")
    
    def _validate_config_name(self, name: str) -> bool:
        """Validate configuration name"""
        if not name or len(name.strip()) == 0:
            return False
        
        # Check invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False
        
        return True
    
    def render_config_manager(self) -> Optional[BacktestConfig]:
        """
        Render configuration management interface
        
        Returns:
            selected configuration object
        """
        st.subheader("💾 Configuration Management")
        
        # Get all configurations
        configs = self.list_configs()
        
        if not configs:
            st.info("📭 No saved configurations")
            return None
        
        # Configuration selection
        config_options = [f"{cfg['name']} - {cfg['description']}" for cfg in configs]
        
        selected_index = st.selectbox(
            "Select Configuration",
            range(len(config_options)),
            format_func=lambda x: config_options[x],
            help="Select configuration to load"
        )
        
        if selected_index is not None:
            selected_config = configs[selected_index]
            
            # Show configuration details
            self._render_config_details(selected_config)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Load Config", help="Load selected configuration"):
                    config = self.load_config(selected_config['name'])
                    if config:
                        st.success(f"✅ Configuration '{selected_config['name']}' loaded")
                        return config
            
            with col2:
                if st.button("🗑️ Delete Config", help="Delete selected configuration"):
                    if self.delete_config(selected_config['name']):
                        st.success(f"✅ Configuration '{selected_config['name']}' deleted")
                        st.rerun()
            
            with col3:
                # Export configuration
                config_json = self._export_config(selected_config['name'])
                if config_json:
                    st.download_button(
                        "📤 Export Config",
                        config_json,
                        file_name=f"{selected_config['name']}.json",
                        mime="application/json",
                        help="Export configuration file"
                    )
        
        return None
    
    def _render_config_details(self, config_info: Dict[str, Any]):
        """Render configuration details"""
        with st.expander("📋 Configuration Details", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {config_info['name']}")
                st.write(f"**Description:** {config_info['description'] or 'No description'}")
            
            with col2:
                if config_info['created_at']:
                    created_time = datetime.fromisoformat(config_info['created_at'])
                    st.write(f"**Created:** {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                st.write(f"**File Path:** {config_info['file_path']}")
    
    def render_save_config_dialog(self, config: BacktestConfig):
        """Render save configuration dialog"""
        st.subheader("💾 Save Current Configuration")
        
        with st.form("save_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                config_name = st.text_input(
                    "Configuration Name",
                    placeholder="Enter configuration name...",
                    help="Unique identifier for the configuration"
                )
            
            with col2:
                config_description = st.text_input(
                    "Configuration Description",
                    placeholder="Enter configuration description...",
                    help="Detailed description of the configuration"
                )
            
            # Show current configuration summary
            st.write("**Current Configuration Summary:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"- Time Range: {config.start_date} to {config.end_date}")
                st.write(f"- Timeframe: {config.timeframe}")
                st.write(f"- Pairs: {', '.join(config.pairs)}")
            
            with col2:
                st.write(f"- Initial Balance: {config.initial_balance:,.2f} USDT")
                st.write(f"- Max Open Trades: {config.max_open_trades}")
                st.write(f"- Fee Rate: {config.fee:.4f}")
            
            # Submit button
            submitted = st.form_submit_button("💾 Save Configuration")
            
            if submitted:
                if not config_name:
                    st.error("❌ Please enter configuration name")
                elif self._config_exists(config_name):
                    st.error(f"❌ Configuration name '{config_name}' already exists")
                else:
                    if self.save_config(config, config_name, config_description):
                        st.success(f"✅ Configuration '{config_name}' saved successfully")
                        st.rerun()
    
    def _config_exists(self, name: str) -> bool:
        """Check if configuration already exists"""
        config_file = self.config_dir / "backtest" / f"{name}.json"
        return config_file.exists()
    
    def _export_config(self, name: str) -> Optional[str]:
        """Export configuration as JSON string"""
        try:
            config_file = self.config_dir / "backtest" / f"{name}.json"
            
            if not config_file.exists():
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to export configuration: {str(e)}")
            return None
    
    def import_config(self, config_json: str, name: str) -> bool:
        """
        Import configuration
        
        Args:
            config_json: configuration JSON string
            name: configuration name
            
        Returns:
            whether import was successful
        """
        try:
            config_data = json.loads(config_json)
            
            # Validate configuration format
            if 'config' not in config_data:
                raise ConfigError("Configuration file format error")
            
            # Create configuration object for validation
            BacktestConfig.from_dict(config_data['config'])
            
            # Save configuration
            config_data['name'] = name
            config_data['created_at'] = datetime.now().isoformat()
            
            config_file = self.config_dir / "backtest" / f"{name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            ErrorHandler.log_info(f"Configuration imported: {name}")
            return True
        
        except Exception as e:
            ErrorHandler.log_error(f"Failed to import configuration: {str(e)}")
            return False
    
    def render_import_config_dialog(self):
        """Render import configuration dialog"""
        st.subheader("📥 Import Configuration")
        
        with st.form("import_config_form"):
            config_name = st.text_input(
                "Configuration Name",
                placeholder="Enter configuration name...",
                help="Name for the imported configuration"
            )
            
            config_json = st.text_area(
                "Configuration JSON",
                placeholder="Paste configuration JSON content...",
                height=200,
                help="Copy JSON content from exported configuration file"
            )
            
            submitted = st.form_submit_button("📥 Import Configuration")
            
            if submitted:
                if not config_name:
                    st.error("❌ Please enter configuration name")
                elif not config_json:
                    st.error("❌ Please enter configuration JSON content")
                elif self._config_exists(config_name):
                    st.error(f"❌ Configuration name '{config_name}' already exists")
                else:
                    if self.import_config(config_json, config_name):
                        st.success(f"✅ Configuration '{config_name}' imported successfully")
                        st.rerun()
                    else:
                        st.error("❌ Configuration import failed, please check JSON format")