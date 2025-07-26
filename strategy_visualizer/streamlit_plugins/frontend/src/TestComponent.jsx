import React from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

class TestComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = { clickCount: 0 };
  }

  componentDidMount() {
    Streamlit.setFrameHeight(200);
  }

  handleClick = () => {
    const newCount = this.state.clickCount + 1;
    this.setState({ clickCount: newCount });
    Streamlit.setComponentValue({ clicked: newCount });
  }

  render() {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <h3>🧪 组件测试</h3>
        <p>点击次数: {this.state.clickCount}</p>
        <button onClick={this.handleClick} style={{ 
          padding: "10px 20px", 
          fontSize: "16px",
          backgroundColor: "#0066cc",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer"
        }}>
          点击测试
        </button>
      </div>
    );
  }
}

export default withStreamlitConnection(TestComponent);
