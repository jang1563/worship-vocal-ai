"""
Worship Vocal AI - Style Utilities
CSS injection and styled components
"""

import streamlit as st
from pathlib import Path


def inject_custom_css():
    """Inject custom CSS styles into the Streamlit app"""

    css_path = Path(__file__).parent.parent / "assets" / "styles" / "main.css"

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        # Fallback minimal CSS if file not found
        css = """
        :root {
            --gold-primary: #C9A962;
            --bg-primary: #0D0D12;
            --bg-secondary: #141420;
            --text-primary: #F4F4F5;
        }
        """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = None, icon: str = None):
    """
    Render a styled section header

    Args:
        title: Main title text
        subtitle: Optional subtitle
        icon: Optional icon (emoji or symbol)
    """

    icon_html = f'<div class="section-icon">{icon}</div>' if icon else ''
    subtitle_html = f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ''

    html = f"""
    <div class="section-header">
        {icon_html}
        <div class="section-title-group">
            <h2 class="section-title">{title}</h2>
            {subtitle_html}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def loading_spinner(message: str = "분석 중..."):
    """Render a custom loading spinner"""

    html = f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-message">{message}</p>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def skeleton_card():
    """Render a loading skeleton card"""

    html = """
    <div class="premium-card">
        <div class="skeleton" style="height: 24px; width: 60%; margin-bottom: 16px;"></div>
        <div class="skeleton" style="height: 16px; width: 100%; margin-bottom: 8px;"></div>
        <div class="skeleton" style="height: 16px; width: 85%; margin-bottom: 8px;"></div>
        <div class="skeleton" style="height: 16px; width: 90%;"></div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def skeleton_metric():
    """Render a loading skeleton metric"""

    html = """
    <div class="metric-card">
        <div class="skeleton" style="height: 48px; width: 80px; margin: 0 auto 12px;"></div>
        <div class="skeleton" style="height: 14px; width: 60%; margin: 0 auto;"></div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def divider():
    """Render a styled divider"""
    st.markdown("<hr>", unsafe_allow_html=True)
