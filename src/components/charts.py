import streamlit as st
"""
Plotly Visualizations Component.
Defines reusable methods for drawing conversion funnels, line trends, and bar charts.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def apply_premium_theme(fig: go.Figure) -> go.Figure:
    """
    Applies a premium, uniform dark mode visual theme to a Plotly Figure,
    matching the Stripe/Linear dashboard style guidelines.
    """
    layout_kwargs = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Geist, Inter, -apple-system, sans-serif",
            size=11,
            color="#A1A1AA"
        ),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.04)",
            linecolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.04)",
            tickfont=dict(color="#71717A"),
            title=dict(font=dict(color="#A1A1AA"))
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.04)",
            linecolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.04)",
            tickfont=dict(color="#71717A"),
            title=dict(font=dict(color="#A1A1AA"))
        ),
        legend=dict(
            bgcolor="rgba(8, 8, 8, 0.9)",
            bordercolor="rgba(255, 255, 255, 0.08)",
            borderwidth=1,
            font=dict(size=10, color="#A1A1AA"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=30, b=30)
    )
    if fig.layout.title and fig.layout.title.text:
        layout_kwargs["title"] = dict(
            text=fig.layout.title.text,
            font=dict(size=15, color="#FFFFFF"),
            x=0.0,
            y=0.96
        )
    fig.update_layout(**layout_kwargs)
    # Style hover tooltips
    fig.update_traces(
        hoverlabel=dict(
            bgcolor="#101010",
            bordercolor="rgba(255, 255, 255, 0.08)",
            font=dict(family="Inter, sans-serif", size=12, color="#FFFFFF")
        )
    )
    return fig

@st.cache_data(ttl=600)
def plot_conversion_funnel(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Plots a multi-stage user journey conversion funnel."""
    fig = px.funnel(
        df,
        y="stage_name",
        x="unique_users",
        color="stage_name",
        color_discrete_sequence=["#3B82F6", "#60A5FA", "#8B5CF6", "#A78BFA", "#22C55E", "#4ADE80", "#F59E0B"],
        labels={"unique_users": "Users", "stage_name": "Stage"}
    )
    fig = apply_premium_theme(fig)
    fig.update_layout(
        height=340,
        showlegend=False,
        margin=dict(l=125, r=30, t=20, b=20),
        yaxis_title=None,
        yaxis=dict(title=None, tickfont=dict(size=11, color="#A1A1AA")),
        xaxis=dict(showgrid=True)
    )
    fig.update_traces(
        textinfo="value+percent initial",
        textposition="inside",
        insidetextfont=dict(size=11, color="#FFFFFF")
    )
    return fig

@st.cache_data(ttl=600)
def plot_stage_conversion(df: pd.DataFrame, title: str = "Stage-to-Stage Conversion Rates") -> go.Figure:
    """Plots a horizontal bar comparing step-to-step transition conversion rates."""
    fig = px.bar(
        df,
        x="conversion_rate",
        y="transition",
        orientation="h",
        title=title,
        labels={"conversion_rate": "Conversion Rate (%)", "transition": "Stage Transition"},
        color="conversion_rate",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_channel_roi(df: pd.DataFrame) -> go.Figure:
    """Plots a horizontal bar chart of ROI percentage split by marketing channel."""
    fig = px.bar(
        df,
        x="roi_pct",
        y="acquisition_channel",
        orientation="h",
        title="Return on Investment (ROI) by Marketing Channel",
        labels={"roi_pct": "ROI (%)", "acquisition_channel": "Marketing Channel"},
        color="roi_pct",
        color_continuous_scale="RdYlGn"
    )
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_spend_vs_revenue(df: pd.DataFrame) -> go.Figure:
    """Plots a grouped bar chart comparing marketing spend and revenue per channel."""
    fig = px.bar(
        df,
        x="acquisition_channel",
        y=["marketing_spend", "estimated_revenue"],
        barmode="group",
        title="Marketing Spend vs. Estimated Revenue",
        labels={"value": "Amount (INR)", "variable": "Financial Metric", "acquisition_channel": "Channel"},
        color_discrete_map={"marketing_spend": "#EF4444", "estimated_revenue": "#22C55E"}
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_channel_cac(df: pd.DataFrame) -> go.Figure:
    """Plots a horizontal bar chart of Customer Acquisition Cost (CAC) by channel."""
    fig = px.bar(
        df,
        x="customer_acquisition_cost",
        y="acquisition_channel",
        orientation="h",
        title="Customer Acquisition Cost (CAC) by Channel",
        labels={"customer_acquisition_cost": "CAC (INR)", "acquisition_channel": "Marketing Channel"},
        color="customer_acquisition_cost",
        color_continuous_scale="Reds"
    )
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total descending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_histogram(df: pd.DataFrame, column: str, title: str, x_label: str = "", nbins: int = 30) -> go.Figure:
    """Plots a histogram for a continuous numeric variable."""
    fig = px.histogram(
        df,
        x=column,
        nbins=nbins,
        title=title,
        labels={column: x_label or column}
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_pie(df: pd.DataFrame, values: str, names: str, title: str) -> go.Figure:
    """Plots a pie chart."""
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_bar_vertical(df: pd.DataFrame, x: str, y: str, title: str, x_label: str = "", y_label: str = "") -> go.Figure:
    """Plots a vertical bar chart."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        labels={x: x_label or x, y: y_label or y}
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_bar_horizontal(df: pd.DataFrame, x: str, y: str, title: str, x_label: str = "", y_label: str = "") -> go.Figure:
    """Plots a horizontal bar chart."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        title=title,
        labels={x: x_label or x, y: y_label or y}
    )
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_experiment_comparison(df: pd.DataFrame) -> go.Figure:
    """Plots a grouped bar chart comparing conversion rates of Control vs Treatment."""
    fig = px.bar(
        df,
        x="experiment_name",
        y="conversion_rate",
        color="variant",
        barmode="group",
        title="Control vs. Treatment Conversion Rate",
        labels={"conversion_rate": "Conversion Rate (%)", "experiment_name": "Experiment", "variant": "Cohort"},
        color_discrete_map={"Control": "#3B82F6", "Treatment": "#8B5CF6"}
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_experiment_lift(df: pd.DataFrame) -> go.Figure:
    """Plots a horizontal bar chart displaying conversion lift percentage."""
    fig = px.bar(
        df,
        x="lift_pct",
        y="experiment_name",
        orientation="h",
        title="Conversion Lift (%) by Experiment",
        labels={"lift_pct": "Relative Conversion Lift (%)", "experiment_name": "Experiment"},
        color="lift_pct",
        color_continuous_scale="Geyser"
    )
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_revenue_lift(df: pd.DataFrame) -> go.Figure:
    """Plots a vertical bar chart of incremental revenue lift."""
    fig = px.bar(
        df,
        x="experiment_name",
        y="incremental_revenue",
        title="Incremental Revenue Lift (INR)",
        labels={"incremental_revenue": "Incremental Revenue (INR)", "experiment_name": "Experiment"},
        color="incremental_revenue",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(height=400)
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_confidence_scores(df: pd.DataFrame) -> go.Figure:
    """Plots horizontal absolute Z-scores colored by significance status."""
    fig = px.bar(
        df,
        x="abs_z_score",
        y="experiment_name",
        orientation="h",
        color="significance_status",
        title="Statistical Confidence Levels (Absolute Z-Score)",
        labels={"abs_z_score": "|Z-Score|", "experiment_name": "Experiment", "significance_status": "Confidence Threshold"},
        color_discrete_map={"Significant": "#22C55E", "Not Significant": "#F59E0B"}
    )
    fig.add_vline(x=1.96, line_dash="dash", line_color="#EF4444", annotation_text="95% Confidence Threshold (Z=1.96)")
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_user_trend(df: pd.DataFrame) -> go.Figure:
    """
    Plots daily registrations (Users) and app opens.
    """
    fig = go.Figure()
    
    df_copy = df.copy()
    if 'date' in df_copy.columns:
        try:
            df_copy['date_formatted'] = pd.to_datetime(df_copy['date']).dt.strftime('%b %d')
        except:
            df_copy['date_formatted'] = df_copy['date'].astype(str)
    else:
        df_copy['date_formatted'] = df_copy.index.astype(str)
        
    fig.add_trace(go.Scatter(
        x=df_copy['date_formatted'],
        y=df_copy['users'],
        mode='lines+markers',
        name='Users',
        line=dict(color='#3B82F6', width=2.5),
        marker=dict(size=6, color='#3B82F6', line=dict(color='#050505', width=1.5))
    ))
    
    fig.add_trace(go.Scatter(
        x=df_copy['date_formatted'],
        y=df_copy['app_opens'],
        mode='lines+markers',
        name='App Opens',
        line=dict(color='#8B5CF6', width=2.5),
        marker=dict(size=6, color='#8B5CF6', line=dict(color='#050505', width=1.5))
    ))
    
    fig.update_layout(
        height=300,
        hovermode="x unified",
        margin=dict(l=30, r=20, t=10, b=20),
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True, title=None)
    )
    
    return apply_premium_theme(fig)

@st.cache_data(ttl=600)
def plot_channel_spend_donut(df: pd.DataFrame, total_spend_formatted: str = "₹12.00Cr") -> go.Figure:
    """
    Plots a donut chart representing marketing spend by acquisition channel.
    """
    fig = px.pie(
        df,
        values="marketing_spend",
        names="acquisition_channel",
        hole=0.6,
        color="acquisition_channel",
        color_discrete_map={
            "Google Ads": "#3B82F6",
            "Meta Ads": "#8B5CF6",
            "Instagram": "#22C55E",
            "YouTube": "#F59E0B",
            "Others": "#6B7280"
        }
    )
    
    fig.update_traces(
        textinfo='none',
        hoverinfo='label+percent'
    )
    
    fig.update_layout(
        height=260,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(
            text=f"<span style='font-size:11px;color:#6B7280;'>Total Spend</span><br><b style='font-size:16px;color:#FFFFFF;'>{total_spend_formatted}</b>",
            x=0.5, y=0.5,
            showarrow=False,
            align="center"
        )]
    )
    
    return apply_premium_theme(fig)

