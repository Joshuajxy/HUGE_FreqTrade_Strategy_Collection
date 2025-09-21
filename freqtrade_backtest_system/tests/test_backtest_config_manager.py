import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
from pathlib import Path
from datetime import datetime, date

from components.backtest_config.manager import ConfigManager
from utils.data_models import BacktestConfig
from utils.error_handling import ConfigError, ErrorHandler

# Mock Streamlit for UI components
@pytest.fixture(autouse=True)
def mock_streamlit():
    with patch('components.backtest_config.manager.st', autospec=True) as mock_st:
        # Mock st.columns to return a list of MagicMock objects based on the number of columns requested
        mock_st.columns.side_effect = lambda num_cols: [MagicMock() for _ in range(num_cols)]
        yield mock_st

# Mock ErrorHandler methods directly
@pytest.fixture(autouse=True)
def mock_error_handler_methods():
    with (
        patch('components.backtest_config.manager.ErrorHandler.log_info') as mock_log_info,
        patch('components.backtest_config.manager.ErrorHandler.log_error') as mock_log_error,
        patch('components.backtest_config.manager.ErrorHandler.log_warning') as mock_log_warning,
        patch('components.backtest_config.manager.ErrorHandler.handle_config_error') as mock_handle_config_error,
    ):
        yield mock_log_info, mock_log_error, mock_log_warning, mock_handle_config_error

@pytest.fixture
def mock_backtest_config():
    """Fixture for a sample BacktestConfig object."""
    return BacktestConfig(
        timeframe="5m",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31),
        pairs=["BTC/USDT", "ETH/USDT"],
        initial_balance=1000.0,
        max_open_trades=5,
        fee=0.001
    )

@pytest.fixture
def config_manager(tmp_path):
    """Fixture for ConfigManager with a temporary config directory."""
    return ConfigManager(config_dir=str(tmp_path / "configs"))

class TestConfigManager:

    def test_init_creates_directories(self, tmp_path):
        config_dir = tmp_path / "configs"
        manager = ConfigManager(config_dir=str(config_dir))
        assert config_dir.exists()
        assert (config_dir / "backtest").exists()
        assert (config_dir / "templates").exists()

    @pytest.mark.parametrize("name, expected", [
        ("ValidName", True),
        ("Name With Spaces", True),
        ("name-with-hyphens", True),
        ("name_with_underscores", True),
        ("", False),
        ("  ", False),
        ("Name/With/Slash", False),
        ("Name\\With\\Backslash", False),
        ("Name:With:Colon", False),
        ("Name*With*Asterisk", False),
        ("Name?With?Question", False),
        ("Name\"With\"Quote", False),
        ("Name<With<Less", False),
        ("Name>With>Greater", False),
        ("Name|With|Pipe", False),
    ])
    def test_validate_config_name(self, config_manager, name, expected):
        assert config_manager._validate_config_name(name) == expected

    @patch('components.backtest_config.manager.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('components.backtest_config.manager.datetime')
    def test_save_config_success(self, mock_dt, mock_file_open, mock_json_dump, config_manager, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        mock_dt.now.isoformat.return_value = "2023-01-01T10:00:00"

        result = config_manager.save_config(mock_backtest_config, "MyConfig", "A test config")
        assert result is True
        mock_file_open.assert_called_once_with(
            config_manager.config_dir / "backtest" / "MyConfig.json", 'w', encoding='utf-8'
        )
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        saved_data = args[0]
        assert saved_data['name'] == "MyConfig"
        assert saved_data['description'] == "A test config"
        assert saved_data['created_at'] == "2023-01-01T10:00:00"
        assert saved_data['config'] == mock_backtest_config.to_dict()
        mock_log_info.assert_called_once_with("Configuration saved: MyConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.ErrorHandler.handle_config_error')
    def test_save_config_invalid_name(self, mock_handle_config_error, config_manager, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, _ = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Invalid configuration name: Invalid/Name"):
            config_manager.save_config.__wrapped__(config_manager, mock_backtest_config, "Invalid/Name")
        mock_log_error.assert_called_once_with("Failed to save configuration: Invalid configuration name: Invalid/Name")
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('components.backtest_config.manager.datetime')
    def test_save_config_io_error(self, mock_dt, mock_file_open, mock_json_dump, config_manager, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        mock_dt.now.isoformat.return_value = "2023-01-01T10:00:00"
        mock_json_dump.side_effect = IOError("Disk full") # Apply side_effect to json.dump
        with pytest.raises(ConfigError, match="Failed to save configuration: Disk full"):
            config_manager.save_config.__wrapped__(config_manager, mock_backtest_config, "MyConfig")
        mock_log_error.assert_called_once_with("Failed to save configuration: Disk full")
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('components.backtest_config.manager.BacktestConfig.from_dict')
    def test_load_config_success(self, mock_from_dict, mock_exists, mock_file_open, mock_json_load, config_manager, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_json_load.return_value = {
            'name': 'MyConfig',
            'description': 'A test config',
            'created_at': '2023-01-01T10:00:00',
            'config': mock_backtest_config.to_dict()
        }
        mock_from_dict.return_value = mock_backtest_config

        loaded_config = config_manager.load_config("MyConfig") # Corrected call: removed config_manager as first arg
        assert loaded_config == mock_backtest_config
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once_with(
            config_manager.config_dir / "backtest" / "MyConfig.json", 'r', encoding='utf-8'
        )
        mock_json_load.assert_called_once()
        mock_from_dict.assert_called_once_with(mock_backtest_config.to_dict())
        mock_log_info.assert_called_once_with("Configuration loaded: MyConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_config_not_found(self, mock_exists, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Configuration file does not exist: NonExistentConfig"):
            config_manager.load_config.__wrapped__(config_manager, "NonExistentConfig")
        mock_exists.assert_called_once()
        mock_log_error.assert_called_once_with("Failed to load configuration: Configuration file does not exist: NonExistentConfig")
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "{}", 0))
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_config_invalid_json(self, mock_exists, mock_file_open, mock_json_load, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Failed to load configuration"):
            config_manager.load_config.__wrapped__(config_manager, "MyConfig")
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
        mock_json_load.assert_called_once()
        mock_log_error.assert_called_once_with("Failed to load configuration: Invalid JSON: line 1 column 1 (char 0)")
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.load', return_value={'name': 'MyConfig'})
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_config_missing_config_key(self, mock_exists, mock_file_open, mock_json_load, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Configuration file format error: MyConfig"):
            config_manager.load_config.__wrapped__(config_manager, "MyConfig")
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
        mock_json_load.assert_called_once()
        mock_log_error.assert_called_once_with("Failed to load configuration: Configuration file format error: MyConfig")
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.glob')
    @patch('components.backtest_config.manager.json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_list_configs_success(self, mock_file_open, mock_json_load, mock_glob, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _ , mock_handle_config_error = mock_error_handler_methods
        # Mock two config files
        mock_file1 = MagicMock()
        mock_file1.stem = "ConfigA"
        mock_file1.__str__.return_value = "/tmp/configs/backtest/ConfigA.json"
        mock_file2 = MagicMock()
        mock_file2.stem = "ConfigB"
        mock_file2.__str__.return_value = "/tmp/configs/backtest/ConfigB.json"
        mock_glob.return_value = [mock_file1, mock_file2]

        mock_json_load.side_effect = [
            {
                'name': 'ConfigA',
                'description': 'Desc A',
                'created_at': '2023-01-02T10:00:00',
                'config': {}
            },
            {
                'name': 'ConfigB',
                'description': 'Desc B',
                'created_at': '2023-01-01T10:00:00',
                'config': {}
            }
        ]

        configs = config_manager.list_configs()
        assert len(configs) == 2
        assert configs[0]['name'] == "ConfigA" # Sorted by created_at DESC
        assert configs[1]['name'] == "ConfigB"
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.glob', return_value=[])
    def test_list_configs_no_configs(self, mock_glob, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        configs = config_manager.list_configs()
        assert len(configs) == 0
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.glob')
    @patch('components.backtest_config.manager.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "{}", 0))
    @patch('builtins.open', new_callable=mock_open)
    def test_list_configs_with_invalid_file(self, mock_file_open, mock_json_load, mock_glob, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, mock_log_warning, mock_handle_config_error = mock_error_handler_methods
        mock_file1 = MagicMock()
        mock_file1.stem = "ConfigA"
        mock_file1.__str__.return_value = "/tmp/configs/backtest/ConfigA.json"
        mock_glob.return_value = [mock_file1]

        configs = config_manager.list_configs()
        assert len(configs) == 0
        mock_log_warning.assert_called_once()
        mock_log_warning.assert_called_once_with(f"Cannot read configuration file {mock_file1}: Invalid JSON: line 1 column 1 (char 0)")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists', return_value=True)
    def test_delete_config_success(self, mock_exists, mock_unlink, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        result = config_manager.delete_config("MyConfig")
        assert result is True
        mock_exists.assert_called_once()
        mock_unlink.assert_called_once()
        mock_log_info.assert_called_once_with("Configuration deleted: MyConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.exists', return_value=False)
    def test_delete_config_not_found(self, mock_exists, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Configuration file does not exist: NonExistentConfig"):
            config_manager.delete_config.__wrapped__(config_manager, "NonExistentConfig")
        mock_exists.assert_called_once()
        mock_log_error.assert_called_once_with("Failed to delete configuration: Configuration file does not exist: NonExistentConfig")
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.unlink', side_effect=IOError("Permission denied"))
    @patch('pathlib.Path.exists', return_value=True)
    def test_delete_config_io_error(self, mock_exists, mock_unlink, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        with pytest.raises(ConfigError, match="Failed to delete configuration: Permission denied"):
            config_manager.delete_config.__wrapped__(config_manager, "MyConfig")
        mock_exists.assert_called_once()
        mock_unlink.assert_called_once()
        mock_log_error.assert_called_once_with("Failed to delete configuration: Permission denied")
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.exists', side_effect=[True, False]) # First call True, second False
    def test_config_exists(self, mock_exists, config_manager):
        assert config_manager._config_exists("ExistingConfig") is True
        assert config_manager._config_exists("NonExistingConfig") is False
        assert mock_exists.call_count == 2

    @patch('builtins.open', new_callable=mock_open, read_data='{"config": {}}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_export_config_success(self, mock_exists, mock_file_open, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        exported_json = config_manager._export_config("MyConfig")
        assert exported_json == '{"config": {}}'
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('pathlib.Path.exists', return_value=False)
    def test_export_config_not_found(self, mock_exists, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        exported_json = config_manager._export_config("NonExistentConfig")
        assert exported_json is None
        mock_exists.assert_called_once()
        mock_log_error.assert_not_called() # No error logged for not found
        mock_handle_config_error.assert_not_called()

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_export_config_io_error(self, mock_exists, mock_file_open, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_file_open.side_effect = IOError("Read error") # Apply side_effect to the mock file handle
        exported_json = config_manager._export_config("MyConfig")
        assert exported_json is None
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
        mock_log_error.assert_called_once()
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.loads')
    @patch('components.backtest_config.manager.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('components.backtest_config.manager.BacktestConfig.from_dict')
    @patch('components.backtest_config.manager.datetime')
    def test_import_config_success(self, mock_dt, mock_from_dict, mock_file_open, mock_json_dump, mock_json_loads, config_manager, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_json_loads.return_value = {
            'description': 'Imported config',
            'config': mock_backtest_config.to_dict()
        }
        mock_from_dict.return_value = mock_backtest_config
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        mock_dt.now.isoformat.return_value = "2023-01-01T10:00:00"

        config_json_str = json.dumps({'config': mock_backtest_config.to_dict()})
        result = config_manager.import_config(config_json_str, "ImportedConfig")
        assert result is True
        mock_json_loads.assert_called_once_with(config_json_str)
        mock_from_dict.assert_called_once_with(mock_backtest_config.to_dict())
        mock_file_open.assert_called_once_with(
            config_manager.config_dir / "backtest" / "ImportedConfig.json", 'w', encoding='utf-8'
        )
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        saved_data = args[0]
        assert saved_data['name'] == "ImportedConfig"
        assert saved_data['created_at'] == "2023-01-01T10:00:00"
        assert saved_data['config'] == mock_backtest_config.to_dict()
        mock_log_info.assert_called_once_with("Configuration imported: ImportedConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.loads', side_effect=json.JSONDecodeError("Invalid JSON", "{}", 0))
    def test_import_config_invalid_json(self, mock_json_loads, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        result = config_manager.import_config("invalid json", "ImportedConfig")
        assert result is False
        mock_log_error.assert_called_once()
        mock_handle_config_error.assert_not_called()

    @patch('components.backtest_config.manager.json.loads', return_value={'description': 'Imported config'})
    def test_import_config_missing_config_key(self, mock_json_loads, config_manager, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        result = config_manager.import_config("{}", "ImportedConfig")
        assert result is False
        mock_json_loads.assert_called_once_with("{}")
        mock_log_error.assert_called_once()
        mock_handle_config_error.assert_not_called()

    # Test Streamlit UI methods - focusing on calls to st functions
    def test_render_config_manager_no_configs(self, config_manager, mock_streamlit, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        config_manager.list_configs = MagicMock(return_value=[])
        result = config_manager.render_config_manager()
        assert result is None
        config_manager.list_configs.assert_called_once()
        mock_streamlit.subheader.assert_called_once_with("💾 Configuration Management")
        mock_streamlit.info.assert_called_once_with("📭 No saved configurations")
        mock_log_info.assert_not_called()
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_config_manager_with_configs_load_button(self, config_manager, mock_streamlit, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.selectbox.return_value = 0
        mock_streamlit.button.side_effect = [True, False, False] # Load button clicked
        config_manager.list_configs = MagicMock(return_value=[
            {'name': 'ConfigA', 'description': 'Desc A', 'created_at': '2023-01-02T10:00:00', 'file_path': '/path/to/ConfigA.json'}
        ])
        # Mock load_config to also call log_info
        def mock_load_config_side_effect(name):
            mock_log_info("Configuration loaded: " + name)
            return mock_backtest_config
        config_manager.load_config = MagicMock(side_effect=mock_load_config_side_effect)
        config_manager._render_config_details = MagicMock()

        result = config_manager.render_config_manager()
        assert result == mock_backtest_config
        mock_streamlit.selectbox.assert_called_once()
        mock_streamlit.button.assert_any_call("📥 Load Config", help="Load selected configuration")
        config_manager.load_config.assert_called_once_with('ConfigA')
        mock_streamlit.success.assert_called_once_with("✅ Configuration 'ConfigA' loaded")
        mock_log_info.assert_called_once_with("Configuration loaded: ConfigA")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_config_manager_with_configs_delete_button(self, config_manager, mock_streamlit, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.selectbox.return_value = 0
        mock_streamlit.button.side_effect = [False, True, False] # Delete button clicked
        config_manager.list_configs = MagicMock(return_value=[
            {'name': 'ConfigA', 'description': 'Desc A', 'created_at': '2023-01-02T10:00:00', 'file_path': '/path/to/ConfigA.json'}
        ])
        # Mock delete_config to also call log_info
        def mock_delete_config_side_effect(name):
            mock_log_info("Configuration deleted: " + name)
            return True
        config_manager.delete_config = MagicMock(side_effect=mock_delete_config_side_effect)
        config_manager._render_config_details = MagicMock()

        config_manager.render_config_manager()
        mock_streamlit.button.assert_any_call("🗑️ Delete Config", help="Delete selected configuration")
        config_manager.delete_config.assert_called_once_with('ConfigA')
        mock_streamlit.success.assert_called_once_with("✅ Configuration 'ConfigA' deleted")
        mock_streamlit.rerun.assert_called_once()
        mock_log_info.assert_called_once_with("Configuration deleted: ConfigA")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_save_config_dialog_success(self, config_manager, mock_streamlit, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.form.return_value.__enter__.return_value = None
        mock_streamlit.text_input.side_effect = ["NewConfig", "Description for new config"]
        mock_streamlit.form_submit_button.return_value = True
        config_manager._config_exists = MagicMock(return_value=False)
        # Mock save_config to also call log_info
        def mock_save_config_side_effect(config, name, description):
            mock_log_info("Configuration saved: " + name)
            return True
        config_manager.save_config = MagicMock(side_effect=mock_save_config_side_effect)

        config_manager.render_save_config_dialog(mock_backtest_config)
        mock_streamlit.text_input.assert_any_call("Configuration Name", placeholder="Enter configuration name...", help="Unique identifier for the configuration")
        mock_streamlit.text_input.assert_any_call("Configuration Description", placeholder="Enter configuration description...", help="Detailed description of the configuration")
        mock_streamlit.columns.assert_called_with(2) # Ensure st.columns(2) was called
        config_manager._config_exists.assert_called_once_with("NewConfig")
        config_manager.save_config.assert_called_once_with(mock_backtest_config, "NewConfig", "Description for new config")
        mock_streamlit.success.assert_called_once_with("✅ Configuration 'NewConfig' saved successfully")
        mock_streamlit.rerun.assert_called_once()
        mock_log_info.assert_called_once_with("Configuration saved: NewConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_save_config_dialog_name_exists(self, config_manager, mock_streamlit, mock_backtest_config, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.form.return_value.__enter__.return_value = None
        mock_streamlit.text_input.side_effect = ["ExistingConfig", "Description"]
        mock_streamlit.form_submit_button.return_value = True
        config_manager._config_exists = MagicMock(return_value=True)
        config_manager.save_config = MagicMock() # Explicitly mock save_config

        config_manager.render_save_config_dialog(mock_backtest_config)
        mock_streamlit.columns.assert_called_with(2) # Ensure st.columns(2) was called
        config_manager._config_exists.assert_called_once_with("ExistingConfig")
        mock_streamlit.error.assert_called_once_with("❌ Configuration name 'ExistingConfig' already exists")
        config_manager.save_config.assert_not_called()
        mock_log_info.assert_not_called()
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_import_config_dialog_success(self, config_manager, mock_streamlit, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.form.return_value.__enter__.return_value = None
        mock_streamlit.text_input.return_value = "ImportedConfig"
        mock_streamlit.text_area.return_value = '{"config": {"timeframe": "1h", "start_date": "2023-01-01", "end_date": "2023-01-02", "pairs": ["BTC/USDT"], "initial_balance": 1000, "max_open_trades": 1, "fee": 0.001}}'
        mock_streamlit.form_submit_button.return_value = True
        config_manager._config_exists = MagicMock(return_value=False)
        # Mock import_config to also call log_info
        def mock_import_config_side_effect(config_json, name):
            mock_log_info("Configuration imported: " + name)
            return True
        config_manager.import_config = MagicMock(side_effect=mock_import_config_side_effect)

        config_manager.render_import_config_dialog()
        mock_streamlit.text_input.assert_called_once_with("Configuration Name", placeholder="Enter configuration name...", help="Name for the imported configuration")
        mock_streamlit.text_area.assert_called_once()
        config_manager._config_exists.assert_called_once_with("ImportedConfig")
        config_manager.import_config.assert_called_once_with(
            '{"config": {"timeframe": "1h", "start_date": "2023-01-01", "end_date": "2023-01-02", "pairs": ["BTC/USDT"], "initial_balance": 1000, "max_open_trades": 1, "fee": 0.001}}',
            "ImportedConfig"
        )
        mock_streamlit.success.assert_called_once_with("✅ Configuration 'ImportedConfig' imported successfully")
        mock_streamlit.rerun.assert_called_once()
        mock_log_info.assert_called_once_with("Configuration imported: ImportedConfig")
        mock_log_error.assert_not_called()
        mock_handle_config_error.assert_not_called()

    def test_render_import_config_dialog_invalid_json(self, config_manager, mock_streamlit, mock_error_handler_methods):
        mock_log_info, mock_log_error, _, mock_handle_config_error = mock_error_handler_methods
        mock_streamlit.form.return_value.__enter__.return_value = None
        mock_streamlit.text_input.return_value = "ImportedConfig"
        mock_streamlit.text_area.return_value = 'invalid json'
        mock_streamlit.form_submit_button.return_value = True
        config_manager._config_exists = MagicMock(return_value=False)
        # Mock import_config to simulate failure and call log_error and handle_config_error
        def mock_import_config_side_effect(config_json, name):
            mock_log_error("Failed to import configuration: Invalid JSON")
            mock_handle_config_error(ConfigError("Invalid JSON"))
            return False
        config_manager.import_config = MagicMock(side_effect=mock_import_config_side_effect)

        config_manager.render_import_config_dialog()
        config_manager.import_config.assert_called_once_with('invalid json', "ImportedConfig")
        mock_streamlit.error.assert_called_once_with("❌ Configuration import failed, please check JSON format")
        mock_log_info.assert_not_called()
        mock_log_error.assert_called_once_with("Failed to import configuration: Invalid JSON")
        mock_handle_config_error.assert_called_once()