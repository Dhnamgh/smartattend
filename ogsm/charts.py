"""
Plotly Chart Builders for OGSM Portal.
Sửa triệt để logic lọc năm hiện hành (Regex extraction) để 2 biểu đồ tỷ lệ hoàn thành khác biệt chuẩn xác.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime
import re


def extract_year(val) -> int:
    """Trích xuất con số năm 4 chữ số từ bất kỳ định dạng văn bản nào (ví dụ: '2026', 'Năm 2026' -> 2026)"""
    if pd.isna(val):
        return 2030
    val_str = str(val).strip()
    match = re.search(r'\b(202[4-9]|203[0-0])\b', val_str)
    if match:
        return int(match.group(1))
    # Tìm bất kỳ 4 chữ số nào nếu không thuộc 2024-2030
    match_any = re.search(r'\b\d{4}\b', val_str)
    if match_any:
        return int(match_any.group(1))
    return 2030


def create_status_donut_chart(df_status: pd.DataFrame) -> go.Figure:
    if df_status.empty:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu trạng thái")
        return fig

    color_map = {
        "Hoàn thành": "#0f4c5c",      # Xanh lam đậm
        "Đang thực hiện": "#fb8b24",  # Cam
        "Không đạt": "#1f5f3e",       # Xanh lá
        "Chưa đến hạn": "#00a8e8",    # Xanh dương
    }

    fig = px.pie(
        df_status,
        names="Status",
        values="Count",
        hole=0.4,
        color="Status",
        color_discrete_map=color_map,
        title="Biểu đồ: Phân bố trạng thái thực hiện Measures",
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(
        showlegend=True, 
        margin=dict(t=50, b=10, l=10, r=10),
        title=dict(font=dict(size=15, color="#1877F2"))
    )
    return fig


def create_objective_progress_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Objective_ID" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu Mục tiêu chiến lược")
        return fig

    df_calc = df.copy()
    df_calc["Obj_Label"] = df_calc["Objective_ID"].astype(str).str.strip()
    status_order = ["Hoàn thành", "Đang thực hiện", "Không đạt", "Chưa đến hạn"]
    
    color_map = {
        "Hoàn thành": "#0f4c5c",
        "Đang thực hiện": "#fb8b24",
        "Không đạt": "#1f5f3e",
        "Chưa đến hạn": "#00a8e8",
    }

    obj_status = df_calc.groupby(["Obj_Label", "Status"]).size().unstack(fill_value=0)
    if obj_status.empty:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu Objectives")
        return fig

    obj_pct = obj_status.div(obj_status.sum(axis=1), axis=0) * 100
    fig = go.Figure()

    for status in status_order:
        if status in obj_pct.columns:
            fig.add_trace(go.Bar(
                name=f"KPI {status.lower()}",
                x=obj_pct.index,
                y=obj_pct[status],
                marker_color=color_map.get(status, "#757575")
            ))

    fig.update_layout(
        barmode="stack",
        title=dict(text="<b>Biểu đồ: Tiến độ thực hiện theo từng Mục tiêu chiến lược (Objectives)</b>", font=dict(size=15, color="#1877F2")),
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(ticksuffix="%", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
        margin=dict(t=50, b=80, l=10, r=10),
        height=450
    )
    return fig


def create_stacked_kpi_by_unit_chart(df: pd.DataFrame, current_year_only: bool = False) -> go.Figure:
    if df.empty or "Unit_Code" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu biểu đồ")
        return fig

    df_calc = df.copy()
    current_year = datetime.datetime.now().year

    if current_year_only:
        # Sử dụng hàm extract_year để bóc tách chính xác năm
        year_col = "Target_Year" if "Target_Year" in df_calc.columns else "Year"
        if year_col in df_calc.columns:
            df_calc["Extracted_Year"] = df_calc[year_col].apply(extract_year)
            df_calc = df_calc[df_calc["Extracted_Year"] <= current_year]

    if df_calc.empty:
        fig = go.Figure()
        fig.update_layout(title=f"Không có KPI nào có hạn đến năm {current_year}")
        return fig

    status_order = ["Hoàn thành", "Đang thực hiện", "Không đạt", "Chưa đến hạn"]
    color_map = {
        "Hoàn thành": "#0f4c5c",
        "Đang thực hiện": "#fb8b24",
        "Không đạt": "#1f5f3e",
        "Chưa đến hạn": "#00a8e8",
    }

    unit_status = df_calc.groupby(["Unit_Code", "Status"]).size().unstack(fill_value=0)
    unit_pct = unit_status.div(unit_status.sum(axis=1), axis=0) * 100

    fig = go.Figure()
    for status in status_order:
        if status in unit_pct.columns:
            fig.add_trace(go.Bar(
                name=f"KPI {status.lower()}",
                x=unit_pct.index,
                y=unit_pct[status],
                marker_color=color_map.get(status, "#757575")
            ))

    chart_title = (
        f"Biểu đồ: Tiến độ thực hiện KPI đến hạn theo đơn vị (đến năm {current_year})"
        if current_year_only
        else "Biểu đồ: Cơ cấu thực hiện KPI giai đoạn 2025–2030 theo đơn vị"
    )

    fig.update_layout(
        barmode="stack",
        title=dict(text=f"<b>{chart_title}</b>", font=dict(size=15, color="#1877F2")),
        xaxis_title=None,
        yaxis_title=None,
        yaxis=dict(ticksuffix="%", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
        margin=dict(t=50, b=80, l=10, r=10),
        height=480
    )
    return fig


def create_total_kpis_by_unit_chart(df: pd.DataFrame) -> go.Figure:
    """Biểu đồ: Tổng số KPI theo đơn vị"""
    if df.empty or "Unit_Code" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu tổng số KPI theo đơn vị")
        return fig

    counts = df.groupby("Unit_Code").size().reset_index(name="Total_KPIs")
    counts = counts.sort_values(by="Total_KPIs", ascending=True)

    fig = go.Figure(go.Bar(
        x=counts["Total_KPIs"],
        y=counts["Unit_Code"],
        orientation="h",
        marker_color="#185a7d",
        text=counts["Total_KPIs"],
        textposition="outside"
    ))

    fig.update_layout(
        title=dict(text="<b>Biểu đồ: Tổng số KPI theo đơn vị</b>", font=dict(size=16, color="#d90429")),
        xaxis_title=None,
        yaxis_title=None,
        margin=dict(t=50, b=30, l=10, r=40),
        height=max(450, len(counts) * 22)
    )
    return fig


def create_completion_rate_by_unit_chart(df: pd.DataFrame, current_year_only: bool = False) -> go.Figure:
    """Biểu đồ: Tỷ lệ hoàn thành theo đơn vị (Phân biệt rõ năm hiện hành vs Cả giai đoạn)"""
    if df.empty or "Unit_Code" not in df.columns or "Status" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu tỷ lệ hoàn thành")
        return fig

    df_calc = df.copy()
    current_year = datetime.datetime.now().year

    # Lọc năm bằng hàm trích xuất regex
    if current_year_only:
        year_col = "Target_Year" if "Target_Year" in df_calc.columns else "Year"
        if year_col in df_calc.columns:
            df_calc["Extracted_Year"] = df_calc[year_col].apply(extract_year)
            df_calc = df_calc[df_calc["Extracted_Year"] <= current_year]

    if df_calc.empty:
        fig = go.Figure()
        fig.update_layout(title=f"Không có dữ liệu KPI cho các mục tiêu đến năm {current_year}")
        return fig

    # Tính tỷ lệ % Hoàn thành thực tế
    grouped = df_calc.groupby("Unit_Code")
    rates = []
    for unit, group in grouped:
        total = len(group)
        done = len(group[group["Status"] == "Hoàn thành"])
        rate = (done / total * 100) if total > 0 else 0
        rates.append({"Unit_Code": unit, "Rate": round(rate, 2)})

    df_rate = pd.DataFrame(rates).sort_values(by="Rate", ascending=True)

    fig = go.Figure(go.Bar(
        x=df_rate["Rate"],
        y=df_rate["Unit_Code"],
        orientation="h",
        marker_color="#185a7d",
        text=[f"{r:.2f}%" for r in df_rate["Rate"]],
        textposition="outside"
    ))

    chart_title = (
        f"Biểu đồ: Tỷ lệ hoàn thành theo đơn vị năm {current_year}"
        if current_year_only
        else "Biểu đồ: Tỷ lệ hoàn thành theo đơn vị giai đoạn 2025–2030"
    )

    fig.update_layout(
        title=dict(text=f"<b>{chart_title}</b>", font=dict(size=16, color="#d90429")),
        xaxis=dict(ticksuffix="%", range=[0, 115]),
        margin=dict(t=50, b=30, l=10, r=50),
        height=max(450, len(df_rate) * 22)
    )
    return fig
