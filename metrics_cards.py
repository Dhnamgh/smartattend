"""
Metric KPI Cards UI component.
"""

import streamlit as st
from typing import Dict, Any


def render_metrics_cards(kpis: Dict[str, Any]) -> None:
    """Renders 4 metric cards on top of dashboard."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Mục Tiêu Chi Chiến Lược (Objectives)",
            value=kpis.get("total_objectives", 0),
        )

    with col2:
        st.metric(
            label="Chiến Lược Hoạt Động (Strategies)",
            value=kpis.get("total_strategies", 0),
        )

    with col3:
        st.metric(
            label="Chỉ Số Đo Lường (Measures)",
            value=kpis.get("total_measures", 0),
        )

    with col4:
        st.metric(
            label="Tỷ Lệ Hoàn Thành Trung Bình",
            value=f"{kpis.get('avg_completion_rate', 0.0)}%",
            delta=f"{kpis.get('completed_measures', 0)} Đã Hoàn Thành",
        )
