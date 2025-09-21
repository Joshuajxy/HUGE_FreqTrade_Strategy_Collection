"""
Installation guide component
"""
import streamlit as st
import subprocess
import sys
from pathlib import Path

def render_freqtrade_installation_guide():
    """Render freqtrade installation guide"""
    st.error("🚫 Freqtrade Not Found")
    
    st.markdown("""
    **Freqtrade is required to run backtests but was not found on your system.**
    
    Please follow one of the installation methods below:
    """)
    
    # Installation tabs
    tab1, tab2, tab3 = st.tabs(["🐍 Pip Install", "🔧 Manual Setup", "🐳 Docker"])
    
    with tab1:
        st.subheader("Install via Pip (Recommended)")
        
        st.code("pip install freqtrade", language="bash")
        
        if st.button("📦 Install Freqtrade Now", type="primary"):
            with st.spinner("Installing freqtrade..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "freqtrade"],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Freqtrade installed successfully!")
                        st.info("Please refresh the page to continue.")
                        if st.button("🔄 Refresh Page"):
                            st.rerun()
                    else:
                        st.error(f"❌ Installation failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    st.error("❌ Installation timeout. Please try manual installation.")
                except Exception as e:
                    st.error(f"❌ Installation error: {str(e)}")
    
    with tab2:
        st.subheader("Manual Installation")
        
        st.markdown("""
        **Step 1: Create virtual environment**
        ```bash
        python -m venv freqtrade-env
        ```
        
        **Step 2: Activate environment**
        
        Windows:
        ```bash
        freqtrade-env\\Scripts\\activate
        ```
        
        Linux/Mac:
        ```bash
        source freqtrade-env/bin/activate
        ```
        
        **Step 3: Install freqtrade**
        ```bash
        pip install freqtrade
        ```
        
        **Step 4: Verify installation**
        ```bash
        freqtrade --version
        ```
        """)
    
    with tab3:
        st.subheader("Docker Installation")
        
        st.markdown("""
        **Pull freqtrade Docker image:**
        ```bash
        docker pull freqtradeorg/freqtrade:stable
        ```
        
        **Run freqtrade in Docker:**
        ```bash
        docker run --rm -it freqtradeorg/freqtrade:stable --version
        ```
        
        **Note:** Docker setup requires additional configuration for this system.
        """)
    
    # Troubleshooting section
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Common Issues:**
        
        1. **Permission Error:**
           - Try: `pip install --user freqtrade`
           
        2. **Python Version:**
           - Freqtrade requires Python 3.8+
           - Check: `python --version`
           
        3. **Virtual Environment:**
           - Always use a virtual environment
           - Avoid system-wide installation
           
        4. **Dependencies:**
           - Install build tools if needed
           - Windows: Install Visual Studio Build Tools
           - Linux: `sudo apt-get install build-essential`
        """)
    
    # System check
    st.subheader("🔍 System Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            st.success(f"✅ Python {python_version}")
        else:
            st.error(f"❌ Python {python_version} (3.8+ required)")
    
    with col2:
        # Check pip
        try:
            import pip
            st.success("✅ Pip available")
        except ImportError:
            st.error("❌ Pip not available")
    
    # Check if freqtrade is available after potential installation
    if st.button("🔍 Check Freqtrade Status"):
        try:
            result = subprocess.run(
                ["freqtrade", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                st.success(f"✅ Freqtrade found: {result.stdout.strip()}")
                st.info("You can now use the backtest system!")
            else:
                st.error("❌ Freqtrade still not available")
                
        except FileNotFoundError:
            st.error("❌ Freqtrade command not found")
        except Exception as e:
            st.error(f"❌ Error checking freqtrade: {str(e)}")

def render_dependency_check():
    """Render dependency check component"""
    st.subheader("📋 Dependency Status")
    
    dependencies = [
        ("freqtrade", "freqtrade --version", True),
        ("pandas", "python -c 'import pandas; print(pandas.__version__)'", True),
        ("numpy", "python -c 'import numpy; print(numpy.__version__)'", True),
        ("plotly", "python -c 'import plotly; print(plotly.__version__)'", True),
        ("streamlit", "python -c 'import streamlit; print(streamlit.__version__)'", True),
        ("nbformat", "python -c 'import nbformat; print(nbformat.__version__)'", False),
        ("jupyterlab", "jupyter --version", False)
    ]
    
    for name, command, required in dependencies:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{name}**")
        
        with col2:
            if required:
                st.write("Required")
            else:
                st.write("Optional")
        
        with col3:
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    st.success("✅")
                else:
                    if required:
                        st.error("❌")
                    else:
                        st.warning("⚠️")
                        
            except (FileNotFoundError, subprocess.TimeoutExpired):
                if required:
                    st.error("❌")
                else:
                    st.warning("⚠️")
            except Exception:
                if required:
                    st.error("❌")
                else:
                    st.warning("⚠️")