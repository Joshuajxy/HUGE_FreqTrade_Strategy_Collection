# Freqtrade Backtest System

Professional freqtrade strategy backtesting and analysis platform, supporting multi-strategy parallel backtesting, real-time monitoring, result comparison, and Jupyter deep analysis.

## Features

- 🔍 **Automatic Strategy Discovery**: Automatically scan and identify strategy files
- 🚀 **Parallel Backtesting**: Support multiple strategies backtesting simultaneously for improved efficiency
- 📊 **Real-time Monitoring**: Continuous monitoring of strategy performance in dry run mode
- 📈 **Result Comparison**: Multi-dimensional strategy performance comparison and ranking
- 🎨 **Beautiful Interface**: Modern web interface with responsive design
- 📓 **Jupyter Integration**: Deep analysis and custom report generation

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application

```bash
streamlit run app.py
```

### 3. Access Application

Open browser and visit: http://localhost:8501

## Project Structure

```
freqtrade_backtest_system/
├── app.py                          # Main application entry
├── requirements.txt                # Dependencies list
├── README.md                       # Project documentation
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── components/                     # Functional components
│   ├── strategy_manager/           # Strategy management
│   ├── backtest_config/           # Backtest configuration
│   ├── execution/                 # Execution scheduling
│   ├── results/                   # Result processing
│   ├── visualization/             # Visualization
│   ├── jupyter_integration/       # Jupyter integration
│   └── ui/                        # UI components
├── utils/                         # Utility modules
├── data/                          # Data storage
├── configs/                       # Configuration files
├── notebook_templates/            # Jupyter templates
├── notebook_outputs/              # Analysis outputs
├── jupyter_exports/               # Data exports
└── tests/                         # Test files
```

## User Guide

### Strategy Management
1. System automatically scans strategy files in project directory
2. Support strategy search, filtering, and batch selection
3. Display strategy basic information and status

### Backtest Configuration
1. Set backtest time range (minimum 5-minute interval)
2. Select trading pairs and backtest parameters
3. Save and load common configurations

### Execution Monitoring
1. Real-time display of backtest execution status
2. Support parallel execution of multiple strategies
3. Provide detailed execution logs

### Result Analysis
1. Multi-dimensional strategy performance comparison
2. Interactive charts and data tables
3. Support result sorting and filtering

### Jupyter Analysis
1. Predefined analysis templates
2. Automated report generation
3. Support custom analysis scripts

## Development Guide

Please refer to the project spec documentation for detailed development standards and architecture design.

## License

MIT License