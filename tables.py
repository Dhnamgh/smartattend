"""
Interactive Streamlit tabular presentation helper.
"""

import streamlit as st
import pandas as pd


def render_ogsm_table(df: pd.DataFrame) -> None:
    """Renders a styled interactive data table for OGSM items."""
    if df.empty:
        st.info("Chưa có dữ liệu OGSM để hiển thị.")
        return

    display_cols = [
        "Objective_ID", "Goal_ID", "Strategy_ID", "Measure_ID",
        "Measure_Desc", "Unit", "Target", "Actual", "Owner", "Status"
    ]
    available_cols = [c for c in display_cols if c in df.columns]

    st.dataframe(
        df[available_cols],
        use_container_width=True,
        hide_index=True,
    )
