"""
Worship Vocal AI - Premium Chart Theme
Unified Plotly styling for all charts
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================
# Premium Chart Theme Configuration
# =============================================

CHART_THEME = {
    "colors": {
        "gold": "#C9A962",
        "gold_light": "#E8D5A3",
        "purple": "#7C5CBF",
        "purple_light": "#A78BFA",
        "success": "#4ADE80",
        "info": "#60A5FA",
        "warning": "#FBBF24",
        "danger": "#F87171",
        "pink": "#F472B6",
        "cyan": "#22D3EE",
    },
    "backgrounds": {
        "paper": "rgba(20, 20, 32, 0.95)",
        "plot": "rgba(13, 13, 18, 0.7)",
        "grid": "rgba(255, 255, 255, 0.05)",
    },
    "text": {
        "primary": "#F4F4F5",
        "secondary": "#A1A1AA",
        "muted": "#71717A",
    },
    "fonts": {
        "family": "Noto Sans KR, -apple-system, BlinkMacSystemFont, sans-serif",
        "title": 16,
        "axis": 12,
        "tick": 11,
    }
}

# Chart color palette (ordered for consistency)
CHART_COLORS = [
    CHART_THEME["colors"]["gold"],
    CHART_THEME["colors"]["purple"],
    CHART_THEME["colors"]["success"],
    CHART_THEME["colors"]["info"],
    CHART_THEME["colors"]["pink"],
    CHART_THEME["colors"]["warning"],
]


def get_premium_layout(title: str = None, legend: dict = None, yaxis: dict = None, xaxis: dict = None, **kwargs):
    """
    Get base Plotly layout with premium theme

    Usage:
        fig.update_layout(**get_premium_layout(title="Chart Title", height=300))
    """
    # Build title dict if title string provided
    title_dict = dict(
        font=dict(
            size=CHART_THEME["fonts"]["title"],
            color=CHART_THEME["text"]["primary"],
        ),
        x=0.5,
        xanchor="center",
    )
    if title:
        title_dict["text"] = title

    # Build legend dict with defaults
    legend_dict = dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(
            size=CHART_THEME["fonts"]["axis"],
            color=CHART_THEME["text"]["secondary"],
        ),
    )
    if legend:
        legend_dict.update(legend)

    # Build xaxis dict with defaults
    xaxis_dict = dict(
        gridcolor=CHART_THEME["backgrounds"]["grid"],
        zerolinecolor=CHART_THEME["backgrounds"]["grid"],
        tickfont=dict(
            size=CHART_THEME["fonts"]["tick"],
            color=CHART_THEME["text"]["secondary"],
        ),
        title_font=dict(
            size=CHART_THEME["fonts"]["axis"],
            color=CHART_THEME["text"]["secondary"],
        ),
    )
    if xaxis:
        xaxis_dict.update(xaxis)

    # Build yaxis dict with defaults
    yaxis_dict = dict(
        gridcolor=CHART_THEME["backgrounds"]["grid"],
        zerolinecolor=CHART_THEME["backgrounds"]["grid"],
        tickfont=dict(
            size=CHART_THEME["fonts"]["tick"],
            color=CHART_THEME["text"]["secondary"],
        ),
        title_font=dict(
            size=CHART_THEME["fonts"]["axis"],
            color=CHART_THEME["text"]["secondary"],
        ),
    )
    if yaxis:
        yaxis_dict.update(yaxis)

    base_layout = dict(
        paper_bgcolor=CHART_THEME["backgrounds"]["paper"],
        plot_bgcolor=CHART_THEME["backgrounds"]["plot"],
        font=dict(
            family=CHART_THEME["fonts"]["family"],
            color=CHART_THEME["text"]["primary"],
        ),
        title=title_dict,
        margin=dict(l=60, r=40, t=50, b=50),
        xaxis=xaxis_dict,
        yaxis=yaxis_dict,
        legend=legend_dict,
        hoverlabel=dict(
            bgcolor=CHART_THEME["backgrounds"]["paper"],
            font_size=13,
            font_family=CHART_THEME["fonts"]["family"],
        ),
    )

    # Merge with kwargs
    base_layout.update(kwargs)

    return base_layout


def style_radar_chart(fig: go.Figure, title: str = None) -> go.Figure:
    """Apply premium styling to radar chart"""

    fig.update_layout(
        polar=dict(
            bgcolor=CHART_THEME["backgrounds"]["plot"],
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(
                    color=CHART_THEME["text"]["muted"],
                    size=10,
                ),
                gridcolor=CHART_THEME["backgrounds"]["grid"],
                linecolor=CHART_THEME["backgrounds"]["grid"],
            ),
            angularaxis=dict(
                tickfont=dict(
                    color=CHART_THEME["text"]["primary"],
                    size=12,
                ),
                gridcolor=CHART_THEME["backgrounds"]["grid"],
                linecolor=CHART_THEME["backgrounds"]["grid"],
            ),
        ),
        paper_bgcolor=CHART_THEME["backgrounds"]["paper"],
        showlegend=False,
        margin=dict(l=80, r=80, t=60, b=40),
    )

    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(
                    size=16,
                    color=CHART_THEME["text"]["primary"],
                ),
                x=0.5,
            ),
        )

    # Update trace colors
    for trace in fig.data:
        if hasattr(trace, 'fillcolor'):
            trace.fillcolor = 'rgba(201, 169, 98, 0.2)'
        if hasattr(trace, 'line'):
            trace.line.color = CHART_THEME["colors"]["gold"]
            trace.line.width = 2.5
        if hasattr(trace, 'marker'):
            trace.marker.color = CHART_THEME["colors"]["gold"]
            trace.marker.size = 8
            trace.marker.line = dict(color=CHART_THEME["backgrounds"]["paper"], width=2)

    return fig


def style_bar_chart(fig: go.Figure, title: str = None, colors: list = None) -> go.Figure:
    """Apply premium styling to bar chart"""

    fig.update_layout(**get_premium_layout(title=title, height=300, bargap=0.3))

    # Update trace colors
    if colors is None:
        colors = CHART_COLORS

    for i, trace in enumerate(fig.data):
        if hasattr(trace, 'marker'):
            trace.marker.color = colors[i % len(colors)]
            trace.marker.line = dict(width=0)

    return fig


def style_line_chart(fig: go.Figure, title: str = None, color: str = None) -> go.Figure:
    """Apply premium styling to line chart"""

    fig.update_layout(**get_premium_layout(title=title, height=250))

    if color is None:
        color = CHART_THEME["colors"]["gold"]

    for trace in fig.data:
        if hasattr(trace, 'line'):
            trace.line.color = color
            trace.line.width = 2
        if hasattr(trace, 'fill') and trace.fill:
            # Extract RGB from hex
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            trace.fillcolor = f'rgba({r}, {g}, {b}, 0.15)'

    return fig


def style_histogram(fig: go.Figure, title: str = None, color: str = None) -> go.Figure:
    """Apply premium styling to histogram"""

    fig.update_layout(**get_premium_layout(title=title, height=250, bargap=0.05))

    if color is None:
        color = CHART_THEME["colors"]["purple"]

    for trace in fig.data:
        if hasattr(trace, 'marker'):
            trace.marker.color = color
            trace.marker.line = dict(
                color=CHART_THEME["backgrounds"]["paper"],
                width=1
            )

    return fig


def style_scatter_chart(fig: go.Figure, title: str = None) -> go.Figure:
    """Apply premium styling to scatter chart"""

    fig.update_layout(**get_premium_layout(title=title, height=280))

    return fig


def add_reference_line(fig: go.Figure, y: float, text: str, color: str = None, dash: str = "dash"):
    """Add a styled reference line to chart"""

    if color is None:
        color = CHART_THEME["text"]["muted"]

    fig.add_hline(
        y=y,
        line_dash=dash,
        line_color=color,
        annotation_text=text,
        annotation_font=dict(
            color=CHART_THEME["text"]["secondary"],
            size=11,
        ),
        annotation_position="right",
    )

    return fig


# =============================================
# Pre-configured Chart Templates
# =============================================

def create_premium_radar(categories: list, values: list, title: str = "") -> go.Figure:
    """Create a premium styled radar chart"""

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(201, 169, 98, 0.2)',
        line=dict(
            color=CHART_THEME["colors"]["gold"],
            width=2.5,
        ),
        marker=dict(
            size=8,
            color=CHART_THEME["colors"]["gold"],
            line=dict(
                color=CHART_THEME["backgrounds"]["paper"],
                width=2
            ),
        ),
        hovertemplate='%{theta}: %{r:.0f}<extra></extra>',
    ))

    fig = style_radar_chart(fig, title)
    fig.update_layout(height=380)

    return fig


def create_premium_bars(categories: list, values: list, title: str = "", colors: list = None) -> go.Figure:
    """Create a premium styled bar chart"""

    if colors is None:
        colors = CHART_COLORS[:len(categories)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f'{v:.0f}' for v in values],
        textposition='outside',
        textfont=dict(
            color=CHART_THEME["text"]["primary"],
            size=13,
        ),
        hovertemplate='%{x}: %{y:.1f}<extra></extra>',
    ))

    fig = style_bar_chart(fig, title, colors)
    fig.update_layout(
        yaxis=dict(range=[0, max(values) * 1.2] if values else [0, 100]),
        xaxis=dict(tickangle=0),
    )

    return fig


def create_premium_line(x: list, y: list, title: str = "", color: str = None, fill: bool = True) -> go.Figure:
    """Create a premium styled line chart"""

    if color is None:
        color = CHART_THEME["colors"]["gold"]

    fig = go.Figure()

    # Extract RGB for fill
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(
            color=color,
            width=2,
            shape='spline',
        ),
        fill='tozeroy' if fill else None,
        fillcolor=f'rgba({r}, {g}, {b}, 0.15)' if fill else None,
        hovertemplate='%{x}: %{y:.2f}<extra></extra>',
    ))

    fig = style_line_chart(fig, title, color)

    return fig
