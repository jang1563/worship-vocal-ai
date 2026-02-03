"""
Worship Vocal AI - Premium Card Components
"""

import streamlit as st


def premium_card(
    title: str,
    content: str = None,
    icon: str = None,
    subtitle: str = None,
    variant: str = "default"
):
    """
    Render a premium card component

    Args:
        title: Card title
        content: Card body content (supports HTML)
        icon: Icon character (emoji)
        subtitle: Optional subtitle text
        variant: "default", "signature", "enemy"
    """

    variant_classes = {
        "default": "premium-card",
        "signature": "premium-card signature-card",
        "enemy": "premium-card enemy-card",
    }

    card_class = variant_classes.get(variant, "premium-card")

    icon_html = f'<div class="premium-card-icon">{icon}</div>' if icon else ''
    subtitle_html = f'<p class="premium-card-subtitle">{subtitle}</p>' if subtitle else ''
    content_html = f'<div class="premium-card-content">{content}</div>' if content else ''

    html = f"""
    <div class="{card_class}">
        <div class="premium-card-header">
            {icon_html}
            <div>
                <h4 class="premium-card-title">{title}</h4>
                {subtitle_html}
            </div>
        </div>
        {content_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def metric_card(
    label: str,
    value: str,
    delta: str = None,
    delta_positive: bool = True,
    icon: str = None
):
    """
    Render a premium metric card

    Args:
        label: Metric label
        value: Metric value to display
        delta: Optional change indicator
        delta_positive: Whether delta is positive (green) or negative (red)
        icon: Optional icon
    """

    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ''
    delta_class = "positive" if delta_positive else "negative"
    delta_prefix = "+" if delta_positive and delta else ""
    delta_html = f'<div class="metric-delta {delta_class}">{delta_prefix}{delta}</div>' if delta else ''

    html = f"""
    <div class="metric-card">
        {icon_html}
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def persona_badge(name: str, icon: str = None):
    """
    Render a persona badge

    Args:
        name: Persona name
        icon: Optional icon/emoji
    """

    icon_html = f'{icon} ' if icon else ''

    html = f"""
    <div class="persona-badge">
        {icon_html}{name}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def mbti_card(
    code: str,
    name_en: str,
    name_kr: str,
    description: str,
    is_active: bool = False,
    strengths: list = None,
    role_models: list = None
):
    """
    Render an MBTI type card

    Args:
        code: Type code (e.g., "ST", "WL")
        name_en: English name
        name_kr: Korean name
        description: Type description
        is_active: Whether this is the user's type
        strengths: List of strengths
        role_models: List of role models
    """

    active_class = "mbti-card active" if is_active else "mbti-card"

    strengths_html = ""
    if strengths:
        items = "".join([f"<li>{s}</li>" for s in strengths])
        strengths_html = f'<ul style="margin: 0.5rem 0; padding-left: 1.25rem; color: #A1A1AA;">{items}</ul>'

    models_html = ""
    if role_models:
        models_html = f'<p style="color: #C9A962; font-size: 0.875rem; margin-top: 0.5rem;">롤모델: {", ".join(role_models)}</p>'

    html = f"""
    <div class="{active_class}">
        <div class="mbti-code">{code}</div>
        <div class="mbti-name">{name_en}</div>
        <div class="mbti-subtitle">{name_kr}</div>
        <p style="color: #A1A1AA; margin: 0.75rem 0; line-height: 1.5;">{description}</p>
        {strengths_html}
        {models_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def info_box(content: str, variant: str = "info"):
    """
    Render a styled info box

    Args:
        content: Box content (supports HTML)
        variant: "info", "success", "warning", "error"
    """

    colors = {
        "info": ("#60A5FA", "rgba(96, 165, 250, 0.1)"),
        "success": ("#4ADE80", "rgba(74, 222, 128, 0.1)"),
        "warning": ("#FBBF24", "rgba(251, 191, 36, 0.1)"),
        "error": ("#F87171", "rgba(248, 113, 113, 0.1)"),
    }

    border_color, bg_color = colors.get(variant, colors["info"])

    html = f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {border_color};
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        color: #F4F4F5;
        line-height: 1.6;
    ">
        {content}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def stat_row(stats: dict):
    """
    Render a row of stats

    Args:
        stats: Dictionary of {label: value} pairs
    """

    items_html = ""
    for label, value in stats.items():
        items_html += f"""
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #C9A962;">{value}</div>
            <div style="font-size: 0.75rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
        </div>
        """

    html = f"""
    <div style="
        display: flex;
        gap: 1rem;
        background: #141420;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
    ">
        {items_html}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
