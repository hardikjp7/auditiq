# src/charts.py — Plotly chart generators for auditiq Gradio UI

import plotly.graph_objects as go
import plotly.express as px

RISK_COLORS = {
    "LOW":      "#16a34a",
    "MEDIUM":   "#ca8a04",
    "HIGH":     "#ea580c",
    "CRITICAL": "#dc2626"
}

STATUS_COLORS = {
    "COMPLIANT":       "#16a34a",
    "NON_COMPLIANT":   "#dc2626",
    "PARTIAL":         "#ca8a04",
    "NOT_APPLICABLE":  "#6b7280"
}

def make_gauge_chart(score: float, risk_level: str) -> go.Figure:
    """Gauge chart for overall compliance score"""
    color = RISK_COLORS.get(risk_level, "#6b7280")

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = score,
        delta = {"reference": 80, "increasing": {"color": "#16a34a"},
                 "decreasing": {"color": "#dc2626"}},
        title = {"text": "Overall Compliance Score", "font": {"size": 18}},
        number= {"suffix": "%", "font": {"size": 36}},
        gauge = {
            "axis"  : {"range": [0, 100], "tickwidth": 1},
            "bar"   : {"color": color, "thickness": 0.3},
            "steps" : [
                {"range": [0,  40], "color": "#fee2e2"},
                {"range": [40, 60], "color": "#ffedd5"},
                {"range": [60, 80], "color": "#fef9c3"},
                {"range": [80,100], "color": "#dcfce7"}
            ],
            "threshold": {
                "line" : {"color": "#1e3a5f", "width": 4},
                "thickness": 0.75,
                "value": 80
            }
        }
    ))

    fig.update_layout(
        height  = 280,
        margin  = dict(t=60, b=20, l=40, r=40),
        paper_bgcolor = "white",
        font    = dict(family="Arial")
    )
    return fig


def make_framework_bar(framework_scores: dict) -> go.Figure:
    """Horizontal bar chart for per-framework scores"""
    if not framework_scores:
        return go.Figure()

    frameworks = list(framework_scores.keys())
    scores     = list(framework_scores.values())
    colors     = [
        "#16a34a" if s >= 80 else
        "#ca8a04" if s >= 60 else
        "#ea580c" if s >= 40 else
        "#dc2626"
        for s in scores
    ]

    fig = go.Figure(go.Bar(
        x           = scores,
        y           = frameworks,
        orientation = "h",
        marker_color= colors,
        text        = [f"{s}%" for s in scores],
        textposition= "outside",
        hovertemplate = "%{y}: %{x}%<extra></extra>"
    ))

    fig.update_layout(
        title   = {"text": "Compliance Score by Framework", "font": {"size": 16}},
        xaxis   = {"range": [0, 115], "title": "Score (%)"},
        yaxis   = {"title": ""},
        height  = 280,
        margin  = dict(t=50, b=40, l=120, r=60),
        paper_bgcolor = "white",
        plot_bgcolor  = "#f9fafb",
        font    = dict(family="Arial")
    )
    return fig


def make_status_pie(status_counts: dict) -> go.Figure:
    """Pie chart for validation status breakdown"""
    filtered = {k: v for k, v in status_counts.items() if k != "NOT_APPLICABLE"}
    if not filtered:
        filtered = status_counts

    labels = list(filtered.keys())
    values = list(filtered.values())
    colors = [STATUS_COLORS.get(l, "#6b7280") for l in labels]
    icons  = {"COMPLIANT": "✅ ", "NON_COMPLIANT": "❌ ",
              "PARTIAL": "⚠️ ", "NOT_APPLICABLE": "➖ "}
    labels_display = [f"{icons.get(l,'')}{l.replace('_',' ')}" for l in labels]

    fig = go.Figure(go.Pie(
        labels       = labels_display,
        values       = values,
        marker_colors= colors,
        hole         = 0.45,
        textinfo     = "label+percent",
        hovertemplate= "%{label}: %{value} rules<extra></extra>"
    ))

    fig.update_layout(
        title   = {"text": "Validation Status Breakdown", "font": {"size": 16}},
        height  = 280,
        margin  = dict(t=50, b=20, l=20, r=20),
        paper_bgcolor = "white",
        font    = dict(family="Arial"),
        showlegend = False
    )
    return fig
