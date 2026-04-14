# =============================================================
# Revenue Leakage Audit Dashboard — Olist E-Commerce
# Independent CRO Analyst
# =============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
st.set_page_config(
    page_title="Revenue Leakage Audit — Olist E-Commerce",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None,
                "About": "Revenue Leakage Audit Dashboard — Independent CRO Analyst"}
)

# =============================================================
# CSS
# =============================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] { background-color: #2d1b4e !important; }
section[data-testid="stSidebar"] * { color: #e9d8fd !important; }
section[data-testid="stSidebar"] .stSelectbox > div > div { 
    background-color: #3d2060 !important; 
    color: #e9d8fd !important;
    border-color: #6b46c1 !important;
}
section[data-testid="stSidebar"] .stDateInput > div > div input { 
    background-color: #3d2060 !important; 
    color: #e9d8fd !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #d6bcfa !important; }
section[data-testid="stSidebar"] .stDivider { border-color: #6b46c1 !important; }
.hero-banner {
    background: linear-gradient(135deg, #1a3c5e 0%, #2e6da4 100%);
    padding: 28px 32px; border-radius: 12px; color: white; margin-bottom: 24px;
}
.hero-banner h1 { color: white; margin: 0 0 4px 0; font-size: 1.9rem; }
.hero-banner p  { color: #cce0f5; margin: 0; font-size: 1rem; }
.summary-box {
    background: #fffbeb; border-left: 5px solid #f59e0b;
    padding: 18px 22px; border-radius: 8px; margin-bottom: 20px;
    font-size: 1.05rem; line-height: 1.7; color: #1a202c;
}
.kpi-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 20px 18px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06); color: #1a202c;
}
.kpi-label { font-size: 0.82rem; color: #718096; text-transform: uppercase;
             letter-spacing: 0.05em; margin-bottom: 6px; }
.kpi-value { font-size: 2rem; font-weight: 700; color: #1a3c5e; }
.kpi-sub   { font-size: 0.85rem; color: #a0aec0; margin-top: 4px; }
.leakage-hero {
    background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
    border: 2px solid #fc8181; border-radius: 12px;
    padding: 24px 28px; text-align: center; margin-bottom: 20px; color: #1a202c;
}
.leakage-hero .label  { font-size: 0.9rem; color: #c53030; text-transform: uppercase; letter-spacing: 0.07em; }
.leakage-hero .amount { font-size: 3rem; font-weight: 800; color: #c53030; }
.leakage-hero .sub    { font-size: 0.95rem; color: #742a2a; margin-top: 6px; }
.action-card       { background: #f7fafc; border-left: 4px solid #3182ce;
                     border-radius: 6px; padding: 14px 18px; margin-bottom: 10px; color: #1a202c; }
.action-card.high  { border-color: #e53e3e; background: #fff5f5; color: #1a202c; }
.action-card.med   { border-color: #dd6b20; background: #fffaf0; color: #1a202c; }
.action-card.low   { border-color: #38a169; background: #f0fff4; color: #1a202c; }
.action-title { font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
.action-desc  { font-size: 0.87rem; color: #4a5568; }
.section-header {
    font-size: 1.15rem; font-weight: 700; color: #1a3c5e;
    border-bottom: 2px solid #ebf4ff; padding-bottom: 6px; margin: 24px 0 14px 0;
}
.method-note {
    background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 14px 18px; font-size: 0.83rem; color: #4a5568; margin-top: 12px;
}
.dash-footer {
    background: #1a3c5e; color: #90cdf4; padding: 16px 24px;
    border-radius: 10px; font-size: 0.83rem; text-align: center; margin-top: 32px;
}
.upload-box {
    background: #f0f4f9; border: 2px dashed #3182ce; border-radius: 10px;
    padding: 24px; text-align: center; margin: 20px 0;
}
div[data-testid="stMetricValue"] { font-size: 1.7rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================
# DATA LOADING — single pre-processed master file (5.5MB gzip)
# Loads directly from GitHub — no file uploads needed
# =============================================================
DATA_URL = "https://raw.githubusercontent.com/bryanmunuve74-beep/revenue-leakage-dashboard/main/olist_master.csv.gz"

@st.cache_data(show_spinner="Loading dashboard data… (~10 seconds on first visit)")
def load_data():
    df = pd.read_csv(DATA_URL, compression="gzip")

    ts_cols = ["order_purchase_timestamp","order_approved_at",
               "order_delivered_carrier_date","order_delivered_customer_date",
               "order_estimated_delivery_date"]
    for c in ts_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    df["actual_delivery_days"]    = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["estimated_delivery_days"] = (df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]).dt.days
    df["delivery_delay_days"]     = df["actual_delivery_days"] - df["estimated_delivery_days"]
    df["is_late"]      = df["delivery_delay_days"] > 0
    df["is_delivered"] = df["order_status"] == "delivered"
    df["is_canceled"]  = df["order_status"] == "canceled"
    df["year_month"]   = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    return df

df_raw = load_data()

# =============================================================
# SIDEBAR — FILTERS
# =============================================================
with st.sidebar:
    st.markdown("## 🔍 Filter Data")
    st.caption("Narrow the analysis to a specific segment")

    date_min = df_raw["order_purchase_timestamp"].min().date()
    date_max = df_raw["order_purchase_timestamp"].max().date()
    d_from, d_to = st.date_input(
        "Order Date Range",
        value=[date_min, date_max],
        min_value=date_min, max_value=date_max
    )

    states     = ["All"] + sorted(df_raw["customer_state"].dropna().unique().tolist())
    categories = ["All"] + sorted(df_raw["category"].dropna().unique().tolist())
    pay_types  = ["All"] + sorted(df_raw["payment_type"].dropna().unique().tolist())

    sel_state    = st.selectbox("Customer State",    states)
    sel_category = st.selectbox("Product Category",  categories)
    sel_payment  = st.selectbox("Payment Type",      pay_types)

    st.divider()
    st.markdown("**About this dashboard**")
    st.caption(
        "Built on the Olist public e-commerce dataset — 99,441 real orders "
        "from a Brazilian marketplace (2016–2018). All projections are scenario-based."
    )

# =============================================================
# APPLY FILTERS
# =============================================================
fdf = df_raw.copy()
fdf = fdf[
    (fdf["order_purchase_timestamp"].dt.date >= d_from) &
    (fdf["order_purchase_timestamp"].dt.date <= d_to)
]
if sel_state    != "All": fdf = fdf[fdf["customer_state"] == sel_state]
if sel_category != "All": fdf = fdf[fdf["category"]       == sel_category]
if sel_payment  != "All": fdf = fdf[fdf["payment_type"]   == sel_payment]

# Guard: empty filter result
if len(fdf) == 0:
    st.warning("No data matches the current filters. Please adjust the sidebar selections.")
    st.stop()

# Core metrics — safe division throughout
total_orders   = len(fdf)
delivered      = int(fdf["is_delivered"].sum())
canceled       = int(fdf["is_canceled"].sum())
approved       = int(fdf["order_approved_at"].notna().sum())
shipped        = int(fdf["order_delivered_carrier_date"].notna().sum())
total_revenue  = fdf[fdf["is_delivered"]]["total_payment"].sum()
canceled_rev   = fdf[fdf["is_canceled"]]["total_payment"].sum()
avg_order_val  = fdf[fdf["is_delivered"]]["total_payment"].mean() or 0
late_orders    = int(fdf["is_late"].sum())
on_time_orders = delivered - late_orders
avg_review     = fdf["review_score"].mean()
low_review     = int((fdf["review_score"] <= 2).sum())
late_pct       = (late_orders / delivered  * 100) if delivered  > 0 else 0
cancel_pct     = (canceled    / total_orders * 100) if total_orders > 0 else 0
delivery_conv  = (delivered   / total_orders * 100) if total_orders > 0 else 0

late_df            = fdf[fdf["is_late"] & fdf["delivery_delay_days"].notna()]
avg_delay          = late_df["delivery_delay_days"].mean() or 0
late_rev_at_risk   = fdf[fdf["is_late"]]["total_payment"].sum()
total_leakage      = canceled_rev + (late_rev_at_risk * 0.15)

on_time_score = fdf[fdf["is_delivered"] & ~fdf["is_late"]]["review_score"].mean() or 0
late_score    = fdf[fdf["is_delivered"] &  fdf["is_late"]]["review_score"].mean() or 0

# =============================================================
# §0  HERO BANNER
# =============================================================
st.markdown(f"""
<div class="hero-banner">
    <h1>📊 Revenue Leakage Audit — Olist E-Commerce</h1>
    <p>Post-Purchase Funnel Diagnostic &nbsp;·&nbsp; {total_orders:,} Orders &nbsp;·&nbsp;
    Independent CRO Analyst &nbsp;·&nbsp; <em>Olist Public Dataset · 2016–2018</em></p>
</div>
""", unsafe_allow_html=True)

# =============================================================
# §1  PLAIN-ENGLISH SUMMARY
# =============================================================
st.markdown(f"""
<div class="summary-box">
    <strong>What this audit found:</strong><br>
    This marketplace processed <strong>{total_orders:,} orders</strong> and delivered
    <strong>{delivered:,} successfully</strong> — a delivery rate of <strong>{delivery_conv:.1f}%</strong>.
    However, <strong>{late_orders:,} orders arrived late ({late_pct:.1f}% of deliveries)</strong>,
    averaging <strong>{avg_delay:.1f} days behind schedule</strong>.
    Late deliveries are the primary revenue leakage driver: they generate low review scores,
    reduce repeat purchase rates, and erode customer trust. This is a
    <em>structural fulfilment problem</em>, not a demand problem — customers are buying,
    but the post-purchase experience is losing them.
</div>
""", unsafe_allow_html=True)

# =============================================================
# §2  LEAKAGE HERO + KPIs
# =============================================================
st.markdown('<div class="section-header">💸 Estimated Revenue Being Lost</div>', unsafe_allow_html=True)

lc1, lc2 = st.columns([1, 2])
with lc1:
    st.markdown(f"""
    <div class="leakage-hero">
        <div class="label">Estimated Revenue at Risk</div>
        <div class="amount">${total_leakage:,.0f}</div>
        <div class="sub">
            ${canceled_rev:,.0f} lost to cancellations<br>
            + ${late_rev_at_risk * 0.15:,.0f} churn risk from late deliveries
        </div>
    </div>
    """, unsafe_allow_html=True)

with lc2:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Orders</div><div class="kpi-value">{total_orders:,}</div><div class="kpi-sub">Placed by customers</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Successfully Delivered</div><div class="kpi-value">{delivered:,}</div><div class="kpi-sub">{delivery_conv:.1f}% delivery rate</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Late Deliveries</div><div class="kpi-value">{late_orders:,}</div><div class="kpi-sub">{late_pct:.1f}% of deliveries</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Revenue</div><div class="kpi-value">${total_revenue/1e6:.2f}M</div><div class="kpi-sub">Avg order ${avg_order_val:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("")

# =============================================================
# §3  WHAT TO FIX FIRST
# =============================================================
with st.expander("🎯 What to Fix First — Priority Action Plan", expanded=True):
    st.markdown("Based on the data, here are the three highest-impact actions ranked by expected ROI:")
    recovery_est = late_orders * avg_order_val * 0.10

    st.markdown(f"""
    <div class="action-card high">
        <div class="action-title">🔴 Priority 1 — Fix Late Deliveries (Highest Impact)</div>
        <div class="action-desc">
            <strong>{late_orders:,} orders ({late_pct:.1f}%)</strong> arrived later than promised,
            averaging <strong>{avg_delay:.1f} days late</strong>. Late deliveries directly cause
            low review scores (1–2 stars), reduce repeat purchase likelihood, and generate refund requests.
            Improving carrier SLAs and setting more accurate delivery estimates could recover an estimated
            <strong>${recovery_est:,.0f}</strong> in at-risk repeat revenue.
        </div>
    </div>
    <div class="action-card med">
        <div class="action-title">🟠 Priority 2 — Recover Canceled Orders</div>
        <div class="action-desc">
            <strong>{canceled:,} orders were canceled</strong>, representing
            <strong>${canceled_rev:,.0f}</strong> in lost revenue.
            Implement proactive order status notifications and faster approval workflows
            to reduce cancellations before they are confirmed.
        </div>
    </div>
    <div class="action-card low">
        <div class="action-title">🟢 Priority 3 — Convert Low-Review Customers</div>
        <div class="action-desc">
            <strong>{low_review:,} customers left a review of 2 stars or below</strong>.
            A targeted follow-up sequence (apology + discount voucher) for 1–2 star reviewers
            can recover a portion before they churn permanently.
            Avg order value is <strong>${avg_order_val:,.0f}</strong> — even a 10% recovery rate is meaningful at scale.
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================
# §4  ORDER FUNNEL
# =============================================================
with st.expander("📊 Order Funnel — Where Orders Drop Off", expanded=True):
    st.caption("Each stage shows how many orders made it through. The gap between stages is where revenue is lost.")

    funnel_stages = ["Orders Placed", "Approved", "Shipped to Carrier", "Delivered to Customer"]
    funnel_counts = [total_orders, approved, shipped, delivered]
    funnel_pcts   = [
        100,
        approved  / total_orders * 100 if total_orders else 0,
        shipped   / total_orders * 100 if total_orders else 0,
        delivered / total_orders * 100 if total_orders else 0,
    ]

    fig_funnel = go.Figure(go.Funnel(
        y=funnel_stages, x=funnel_counts,
        textinfo="value+percent initial",
        marker=dict(color=["#2e6da4","#4299e1","#f6ad55","#fc8181"]),
        connector=dict(line=dict(color="#e2e8f0", width=1))
    ))
    fig_funnel.update_layout(height=340, margin=dict(l=20,r=20,t=20,b=20),
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_funnel, use_container_width=True)

    funnel_table = pd.DataFrame({
        "Stage": funnel_stages,
        "Orders": funnel_counts,
        "% of Total": [f"{p:.1f}%" for p in funnel_pcts],
        "Drop from Previous": [
            "—",
            f"-{total_orders - approved:,} ({100 - funnel_pcts[1]:.1f}%)",
            f"-{approved   - shipped:,}   ({funnel_pcts[1] - funnel_pcts[2]:.1f}%)",
            f"-{shipped    - delivered:,}  ({funnel_pcts[2] - funnel_pcts[3]:.1f}%)",
        ]
    })
    st.dataframe(funnel_table, use_container_width=True, hide_index=True)

# =============================================================
# §5  DELIVERY PERFORMANCE
# =============================================================
with st.expander("🚚 Delivery Performance — The Primary Leakage Driver", expanded=True):
    d1, d2 = st.columns(2)

    with d1:
        fig_pie = go.Figure(go.Pie(
            labels=["On Time", "Late"],
            values=[on_time_orders, late_orders],
            hole=0.45,
            marker=dict(colors=["#38a169","#e53e3e"]),
            textinfo="label+percent"
        ))
        fig_pie.update_layout(title="On-Time vs Late Deliveries", height=300,
                              margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    with d2:
        if len(late_df) > 0:
            fig_delay = px.histogram(late_df, x="delivery_delay_days", nbins=30,
                                     title="How Many Days Late (Late Orders Only)",
                                     labels={"delivery_delay_days":"Days Late"},
                                     color_discrete_sequence=["#e53e3e"])
            fig_delay.update_layout(height=300, margin=dict(l=20,r=20,t=40,b=20),
                                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_delay, use_container_width=True)

    state_perf = fdf[fdf["is_delivered"]].groupby("customer_state").agg(
        total_delivered=("order_id","count"),
        late=("is_late","sum"),
        avg_delay=("delivery_delay_days","mean")
    ).reset_index()
    state_perf["Late Rate %"] = (state_perf["late"] / state_perf["total_delivered"] * 100).round(1)
    state_perf = state_perf.sort_values("Late Rate %", ascending=False).head(10)
    state_perf.columns = ["State","Delivered","Late Orders","Avg Delay (Days)","Late Rate %"]
    state_perf["Avg Delay (Days)"] = state_perf["Avg Delay (Days)"].round(1)

    st.markdown("**States with Highest Late Delivery Rates:**")
    st.dataframe(state_perf, use_container_width=True, hide_index=True)
    st.caption("States with high late rates signal specific carrier or logistics gaps — highest-priority fix targets.")

# =============================================================
# §6  REVIEW SCORES
# =============================================================
with st.expander("⭐ Customer Reviews — The Consequence of Late Deliveries", expanded=False):
    r1, r2 = st.columns(2)

    with r1:
        review_dist = fdf["review_score"].dropna().apply(lambda x: round(x)).value_counts().sort_index()
        fig_rev = px.bar(
            x=review_dist.index, y=review_dist.values,
            title="Review Score Distribution",
            labels={"x":"Review Score (1–5)","y":"Number of Orders"},
            color=review_dist.values,
            color_continuous_scale=["#e53e3e","#f6ad55","#ecc94b","#68d391","#38a169"]
        )
        fig_rev.update_layout(height=300, showlegend=False, coloraxis_showscale=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_rev, use_container_width=True)

    with r2:
        rc = fdf[fdf["is_delivered"] & fdf["review_score"].notna()].groupby("is_late").agg(
            avg_score=("review_score","mean"), count=("order_id","count")
        ).reset_index()
        rc["Status"] = rc["is_late"].map({True:"Late",False:"On Time"})
        rc["Avg Score"] = rc["avg_score"].round(2)

        fig_rc = px.bar(rc, x="Status", y="Avg Score",
                        color="Status",
                        color_discrete_map={"On Time":"#38a169","Late":"#e53e3e"},
                        title="Avg Review Score: On Time vs Late", text="Avg Score")
        fig_rc.update_traces(textposition="outside")
        fig_rc.update_layout(height=300, showlegend=False,
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             margin=dict(l=20,r=20,t=40,b=20), yaxis_range=[0,5.5])
        st.plotly_chart(fig_rc, use_container_width=True)

    st.info(
        f"On-time deliveries average **{on_time_score:.2f} stars**. "
        f"Late deliveries average **{late_score:.2f} stars**. "
        f"That's a {on_time_score - late_score:.2f}-star gap caused by fulfilment failure, not product quality."
    )

# =============================================================
# §7  REVENUE TRENDS
# =============================================================
with st.expander("📈 Revenue Trends Over Time", expanded=False):
    monthly = fdf[fdf["is_delivered"]].groupby("year_month").agg(
        revenue=("total_payment","sum"),
        orders=("order_id","count")
    ).reset_index().sort_values("year_month")
    monthly = monthly[monthly["year_month"] < "2018-09"]   # drop incomplete final months

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(name="Revenue ($)", x=monthly["year_month"], y=monthly["revenue"],
               marker_color="#3182ce", opacity=0.8), secondary_y=False)
    fig_trend.add_trace(
        go.Scatter(name="Orders", x=monthly["year_month"], y=monthly["orders"],
                   mode="lines+markers", line=dict(color="#e53e3e", width=2)), secondary_y=True)
    fig_trend.update_layout(
        title="Monthly Revenue and Order Volume", height=340,
        margin=dict(l=20,r=20,t=40,b=60),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02), xaxis_tickangle=-45
    )
    fig_trend.update_yaxes(title_text="Revenue ($)", secondary_y=False, gridcolor="#e2e8f0")
    fig_trend.update_yaxes(title_text="Order Count", secondary_y=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# =============================================================
# §8  PRODUCT CATEGORY BREAKDOWN
# =============================================================
with st.expander("📦 Revenue by Product Category", expanded=False):
    cat_rev = fdf[fdf["is_delivered"]].groupby("category").agg(
        revenue=("total_payment","sum"),
        orders=("order_id","count"),
        avg_order=("total_payment","mean"),
        late_rate=("is_late","mean")
    ).reset_index().dropna(subset=["category"])
    cat_rev = cat_rev.sort_values("revenue", ascending=False).head(15)
    cat_rev["Late Rate %"] = (cat_rev["late_rate"] * 100).round(1)

    fig_cat = px.bar(cat_rev, x="revenue", y="category", orientation="h",
                     color="Late Rate %", color_continuous_scale="RdYlGn_r",
                     title="Top 15 Categories by Revenue (colour = late delivery rate)",
                     labels={"revenue":"Revenue ($)","category":"Category"})
    fig_cat.update_layout(height=420, margin=dict(l=20,r=20,t=40,b=20),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_cat, use_container_width=True)
    st.caption("Red = high late rate. High revenue + high late rate = highest-priority logistics fix.")

# =============================================================
# §9  PAYMENT TYPE ANALYSIS
# =============================================================
with st.expander("💳 Payment Method Breakdown", expanded=False):
    pay_agg = fdf[fdf["is_delivered"]].groupby("payment_type").agg(
        orders=("order_id","count"),
        revenue=("total_payment","sum"),
        avg_order=("total_payment","mean"),
        avg_installments=("installments","mean")
    ).reset_index().sort_values("revenue", ascending=False)
    pay_agg["payment_type"] = pay_agg["payment_type"].str.replace("_"," ").str.title()
    pay_agg.columns = ["Payment Type","Orders","Revenue ($)","Avg Order ($)","Avg Installments"]
    pay_agg["Revenue ($)"]       = pay_agg["Revenue ($)"].map("${:,.0f}".format)
    pay_agg["Avg Order ($)"]     = pay_agg["Avg Order ($)"].map("${:,.0f}".format)
    pay_agg["Avg Installments"]  = pay_agg["Avg Installments"].round(1)
    st.dataframe(pay_agg, use_container_width=True, hide_index=True)
    st.caption("High installment usage signals price sensitivity — customers need payment flexibility to complete purchases.")

# =============================================================
# §10  SCENARIO MODEL
# =============================================================
with st.expander("💰 Scenario Model — What Fixing This Is Worth", expanded=True):
    st.markdown("Use the sliders to model the financial impact of operational improvements.")

    sm1, sm2, sm3 = st.columns(3)
    with sm1:
        late_reduce = st.slider("If late deliveries are reduced by (%)", 0, 80, 30,
                                help="Operational improvement in on-time delivery rate.")
    with sm2:
        churn_rate = st.slider("Estimated % of late customers who don't return", 0, 50, 15,
                               help="Industry benchmark: 15–25% of customers with a bad delivery experience don't reorder.")
    with sm3:
        cancel_recover = st.slider("% of canceled orders that could be recovered", 0, 50, 20,
                                   help="With better order status alerts and faster approvals.")

    late_fixed           = int(late_orders * (late_reduce / 100))
    churn_recovered      = int(late_fixed * (churn_rate / 100))
    churn_rev_recovered  = churn_recovered * avg_order_val
    cancel_rev_recovered = canceled_rev * (cancel_recover / 100)
    total_recovery       = churn_rev_recovered + cancel_rev_recovered

    si1, si2, si3 = st.columns(3)
    si1.metric("Late Orders Fixed",             f"{late_fixed:,}",             delta=f"-{late_reduce}% late rate")
    si2.metric("Repeat Revenue Recovered",      f"${churn_rev_recovered:,.0f}", delta=f"{churn_recovered:,} customers retained")
    si3.metric("Cancellation Revenue Recovered",f"${cancel_rev_recovered:,.0f}",delta=f"+{cancel_recover}% recovery rate")

    fig_sc = go.Figure(go.Bar(
        x=["Repeat Revenue\n(Late Fix)", "Cancellation\nRecovery", "Total\nRecovery"],
        y=[churn_rev_recovered, cancel_rev_recovered, total_recovery],
        text=[f"${churn_rev_recovered:,.0f}", f"${cancel_rev_recovered:,.0f}", f"${total_recovery:,.0f}"],
        textposition="outside",
        marker_color=["#3182ce","#38a169","#1a3c5e"]
    ))
    fig_sc.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=40),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         yaxis=dict(gridcolor="#e2e8f0"))
    st.plotly_chart(fig_sc, use_container_width=True)

    st.success(
        f"Reducing late deliveries by {late_reduce}% and recovering {cancel_recover}% of canceled orders "
        f"could generate an estimated **${total_recovery:,.0f}** in additional revenue."
    )
    st.markdown("""
    <div class="method-note">
    <strong>Methodology note:</strong> Repeat revenue recovery = late orders fixed × estimated churn rate × avg order value.
    Cancellation recovery = canceled order value × recovery rate. All figures are scenario-based projections.
    Churn rate benchmark: e-commerce industry average (15–25% for negative delivery experiences).
    Actual results depend on implementation quality, carrier contracts, and customer behaviour.
    </div>
    """, unsafe_allow_html=True)

# =============================================================
# §11  FULL FINDINGS & RECOMMENDATIONS
# =============================================================
with st.expander("🧠 Full Findings & Recommendations", expanded=False):
    f1, f2 = st.columns(2)

    delivered_fdf = fdf[fdf["is_delivered"]]
    top_state = delivered_fdf.groupby("customer_state")["total_payment"].sum().idxmax() if len(delivered_fdf) > 0 else "N/A"
    top_cat   = delivered_fdf.dropna(subset=["category"]).groupby("category")["total_payment"].sum().idxmax() if len(delivered_fdf) > 0 else "N/A"
    avg_actual_days = fdf["actual_delivery_days"].mean() or 0

    with f1:
        st.subheader("✅ Key Findings")
        st.markdown(f"""
**Order Funnel**
- Total orders: **{total_orders:,}** | Delivered: **{delivered:,}** ({delivery_conv:.1f}%)
- Canceled: **{canceled:,}** → **${canceled_rev:,.0f}** in lost revenue
- Avg order value: **${avg_order_val:,.0f}**

**Delivery Performance**
- Late deliveries: **{late_orders:,}** ({late_pct:.1f}% of deliveries)
- Average delay (late orders): **{avg_delay:.1f} days**
- Promised delivery: {fdf['estimated_delivery_days'].mean():.0f} days avg vs actual {avg_actual_days:.0f} days

**Customer Satisfaction**
- Avg review score: **{avg_review:.2f} / 5.0**
- Low reviews (1–2 stars): **{low_review:,} customers**
- On-time score: **{on_time_score:.2f}** vs late score: **{late_score:.2f}**

**Revenue**
- Total delivered revenue: **${total_revenue:,.0f}**
- Top state by revenue: **{top_state}**
- Top category by revenue: **{top_cat}**
        """)

    with f2:
        st.subheader("🎯 Recommendations")
        st.markdown(f"""
**1. Fix Late Deliveries — Highest Priority**
- Audit carrier performance by state — identify worst routes
- Set realistic delivery promises (actual avg: {avg_actual_days:.0f} days)
- Add real-time tracking notifications to reduce customer anxiety

**2. Recover Canceled Orders**
- Proactive order status updates before customers cancel
- 1-hour cancellation window with "keep my order" incentive
- Faster payment approval workflows

**3. Win Back Low-Review Customers**
- Automated follow-up for 1–2 star reviews within 48 hours
- Discount voucher on next order as recovery mechanism
- Track repeat purchase rate: recovered vs unrecovered

**4. Concentrate on High-Revenue States**
- **{top_state}** drives the most revenue — prioritise carrier reliability there first
- High revenue + high late rate = highest ROI fix targets

**5. Build a Delivery KPI Cadence**
- Weekly: on-time rate, avg delay, cancellation rate
- Monthly: review score trend, repeat purchase by delivery experience
- Internal SLA target: on-time rate above 90%
        """)

# =============================================================
# §12  DATA EXPLORER
# =============================================================
with st.expander("🔍 Explore the Underlying Data", expanded=False):
    st.caption(f"Showing {len(fdf):,} records based on current filters")
    display_cols = ["order_id","customer_state","order_status","category",
                    "total_payment","payment_type","review_score",
                    "actual_delivery_days","delivery_delay_days","is_late",
                    "order_purchase_timestamp","order_delivered_customer_date"]
    available = [c for c in display_cols if c in fdf.columns]
    sel_cols = st.multiselect("Choose columns:", fdf.columns.tolist(), default=available)
    if sel_cols:
        st.dataframe(fdf[sel_cols].reset_index(drop=True), use_container_width=True, height=400)
    else:
        st.info("Select at least one column above.")

# =============================================================
# FOOTER
# =============================================================
st.markdown("""
<div class="dash-footer">
    <strong>Revenue Leakage Audit Dashboard — Olist E-Commerce</strong> &nbsp;·&nbsp;
    Independent CRO Analyst &nbsp;·&nbsp; Python · Pandas · Plotly · Streamlit<br>
    <span style="font-size:0.78rem; opacity:0.7;">
    All projections are scenario-based estimates. Actual results depend on implementation quality and operational constraints.
    Data source: Olist Public E-Commerce Dataset (Kaggle). For a personalised audit of your store, get in touch.
    </span>
</div>
""", unsafe_allow_html=True)
