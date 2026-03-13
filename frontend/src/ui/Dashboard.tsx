import React, { useMemo } from "react";
import GridLayout, { Layout } from "react-grid-layout";
import ReactECharts from "echarts-for-react";
import type { VizChartSpec } from "../protocol";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

type Props = {
  charts: VizChartSpec[];
  tablePreview: { columns: string[]; rows: unknown[][] } | null;
};

function toEChartsOption(spec: VizChartSpec, table: Props["tablePreview"]) {
  // Simple defaults: bind x/y from first two columns unless provided.
  const cols = table?.columns ?? [];
  const rows = table?.rows ?? [];
  const xField = (spec.dataBinding?.x as string) ?? cols[0];
  const yField = (spec.dataBinding?.y as string) ?? cols[1];

  const xIdx = cols.indexOf(xField);
  const yIdx = cols.indexOf(yField);

  const x = xIdx >= 0 ? rows.map((r) => r[xIdx]) : [];
  const y = yIdx >= 0 ? rows.map((r) => r[yIdx]) : [];

  if (spec.type === "pie") {
    const nameIdx = xIdx >= 0 ? xIdx : 0;
    const valIdx = yIdx >= 0 ? yIdx : 1;
    return {
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: "70%",
          data: rows.map((r) => ({ name: String(r[nameIdx]), value: Number(r[valIdx]) })),
        },
      ],
    };
  }

  if (spec.type === "scatter") {
    return {
      tooltip: { trigger: "item" },
      xAxis: { type: "category", data: x },
      yAxis: { type: "value" },
      series: [{ type: "scatter", data: y }],
    };
  }

  // line/bar/area
  const seriesType = spec.type === "area" ? "line" : spec.type;
  return {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: x },
    yAxis: { type: "value" },
    series: [
      {
        type: seriesType,
        areaStyle: spec.type === "area" ? {} : undefined,
        data: y,
      },
    ],
  };
}

export function Dashboard({ charts, tablePreview }: Props) {
  const layout: Layout[] = useMemo(() => {
    const base = charts.length ? charts : [];
    return base.map((c) => ({
      i: c.chartId,
      x: c.layout?.x ?? 0,
      y: c.layout?.y ?? 0,
      w: c.layout?.w ?? 6,
      h: c.layout?.h ?? 6,
    }));
  }, [charts]);

  if (!charts.length) {
    return <div className="muted" style={{ padding: 10 }}>等待模型返回图表配置…</div>;
  }

  return (
    <GridLayout
      className="grid"
      layout={layout}
      cols={12}
      rowHeight={26}
      width={500}
      compactType="vertical"
      isResizable
      isDraggable
    >
      {charts.map((c) => (
        <div key={c.chartId} style={{ padding: 6 }}>
          <div className="chartCard">
            <div className="chartCardHeader">
              <div style={{ fontWeight: 750 }}>{c.title}</div>
              <div className="muted">{c.type}</div>
            </div>
            <div className="chartCardBody">
              {c.type === "table" ? (
                <div className="muted" style={{ padding: 10 }}>
                  表格图将复用中间区域的结果预览（可扩展为独立表格组件）。
                </div>
              ) : (
                <ReactECharts
                  style={{ height: "100%", width: "100%" }}
                  option={toEChartsOption(c, tablePreview)}
                  notMerge
                  lazyUpdate
                />
              )}
            </div>
          </div>
        </div>
      ))}
    </GridLayout>
  );
}

