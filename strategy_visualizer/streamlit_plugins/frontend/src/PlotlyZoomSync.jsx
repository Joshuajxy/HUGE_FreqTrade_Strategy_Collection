import React from "react";
import Plot from "react-plotly.js";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

class PlotlyZoomSync extends React.Component {
  constructor(props) {
    super(props);
    this.handleRelayout = this.handleRelayout.bind(this);
  }

  handleRelayout(eventData) {
    // 打印坐标轴范围到浏览器控制台
    console.log('Plotly relayout eventData (坐标范围):', eventData);
    // 只推送有用的坐标轴范围
    Streamlit.setComponentValue(eventData);
  }

  render() {
    const { args } = this.props;
    
    // 添加调试信息
    console.log('PlotlyZoomSync render called with args:', args);
    
    if (!args) {
      console.error('No args provided to PlotlyZoomSync');
      return <div style={{padding: '20px', color: 'red'}}>错误：没有接收到数据</div>;
    }
    
    const { data, layout, config } = args;
    
    if (!data || !layout) {
      console.error('Missing data or layout:', { data, layout });
      return <div style={{padding: '20px', color: 'red'}}>错误：缺少图表数据或布局</div>;
    }
    
    console.log('Rendering Plot with:', { dataLength: data?.length, layout: layout?.title });
    
    try {
      return (
        <div style={{ width: "100%", height: "900px", border: "1px solid #ddd" }}>
          <Plot
            data={data}
            layout={layout}
            config={config || {}}
            onRelayout={this.handleRelayout}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler={true}
          />
        </div>
      );
    } catch (error) {
      console.error('Error rendering Plot:', error);
      return <div style={{padding: '20px', color: 'red'}}>渲染错误：{error.message}</div>;
    }
  }
}

export default withStreamlitConnection(PlotlyZoomSync);
