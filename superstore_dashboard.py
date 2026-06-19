import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Superstore Supply Chain BI",
    page_icon="📦",
    layout="wide",
)

@st.cache_data
def load_data(path: str = "superstore_supply_chain.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Order Date", "Ship Date"])
    df["Order Year"] = df["Order Date"].dt.year
    df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df


df = load_data()

st.sidebar.header("Filters")

date_min, date_max = df["Order Date"].min(), df["Order Date"].max()
date_range = st.sidebar.date_input(
    "Order Date Range", value=(date_min, date_max), min_value=date_min, max_value=date_max
)

region_sel = st.sidebar.multiselect(
    "Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
)
category_sel = st.sidebar.multiselect(
    "Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
)
segment_sel = st.sidebar.multiselect(
    "Segment", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique())
)
warehouse_sel = st.sidebar.multiselect(
    "Warehouse", sorted(df["Warehouse"].unique()), default=sorted(df["Warehouse"].unique())
)

mask = (
    (df["Order Date"] >= pd.to_datetime(date_range[0]))
    & (df["Order Date"] <= pd.to_datetime(date_range[1]))
    & (df["Region"].isin(region_sel))
    & (df["Category"].isin(category_sel))
    & (df["Segment"].isin(segment_sel))
    & (df["Warehouse"].isin(warehouse_sel))
)
f = df.loc[mask]

st.sidebar.markdown(f"**Rows after filters:** {len(f):,} / {len(df):,}")

st.title("📦 Superstore Supply Chain BI Dashboard")
st.caption("Sales, Profitability & Inventory Health Overview")

total_sales = f["Sales"].sum()
total_profit = f["Profit"].sum()
profit_margin = (total_profit / total_sales * 100) if total_sales else 0
total_orders = f["Order ID"].nunique()
avg_ship_days = f["Days to Ship"].mean()
low_stock_count = (f["Stock_Status"] == "Low Stock").sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Profit", f"${total_profit:,.0f}")
k3.metric("Profit Margin", f"{profit_margin:.1f}%")
k4.metric("Total Orders", f"{total_orders:,}")
k5.metric("Avg Days to Ship", f"{avg_ship_days:.1f}")
k6.metric("Low Stock Items", f"{low_stock_count:,}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📈 Sales & Profit", "🗺️ Category & Region", "🏭 Inventory & Supply Chain"])

with tab1:
    col1, col2 = st.columns(2)

    monthly = f.groupby("Order Month").agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    ).reset_index()
    fig_trend = px.line(
        monthly, x="Order Month", y=["Sales", "Profit"],
        title="Monthly Sales & Profit Trend", markers=True
    )
    col1.plotly_chart(fig_trend, use_container_width=True)

    fig_disc = px.scatter(
        f, x="Discount", y="Profit", color="Category",
        title="Discount Impact on Profit", opacity=0.5
    )
    col2.plotly_chart(fig_disc, use_container_width=True)

    col3, col4 = st.columns(2)

    ship_perf = f.groupby("Ship Mode").agg(
        Avg_Days=("Days to Ship", "mean"), Orders=("Order ID", "nunique")
    ).reset_index()
    fig_ship = px.bar(
        ship_perf, x="Ship Mode", y="Avg_Days", text_auto=".1f",
        title="Average Shipping Time by Ship Mode"
    )
    col3.plotly_chart(fig_ship, use_container_width=True)

    top_products = (
        f.groupby("Product Name")["Profit"].sum().sort_values(ascending=False).head(10).reset_index()
    )
    fig_top = px.bar(
        top_products, x="Profit", y="Product Name", orientation="h",
        title="Top 10 Products by Profit"
    )
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    col4.plotly_chart(fig_top, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    cat_perf = f.groupby(["Category", "Sub-Category"]).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    ).reset_index()
    fig_treemap = px.treemap(
        cat_perf, path=["Category", "Sub-Category"], values="Sales",
        color="Profit", color_continuous_scale="RdYlGn",
        title="Sales by Category / Sub-Category (colored by Profit)"
    )
    col1.plotly_chart(fig_treemap, use_container_width=True)

    region_perf = f.groupby("Region").agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    ).reset_index()
    fig_region = px.bar(
        region_perf, x="Region", y=["Sales", "Profit"], barmode="group",
        title="Sales & Profit by Region"
    )
    col2.plotly_chart(fig_region, use_container_width=True)

    seg_perf = f.groupby("Segment").agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique")
    ).reset_index()
    fig_seg = px.pie(seg_perf, names="Segment", values="Sales", title="Sales Share by Segment", hole=0.4)
    st.plotly_chart(fig_seg, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)

    stock_status = f["Stock_Status"].value_counts().reset_index()
    stock_status.columns = ["Stock_Status", "Count"]
    fig_stock = px.pie(
        stock_status, names="Stock_Status", values="Count",
        title="Stock Status Distribution", hole=0.4,
        color="Stock_Status", color_discrete_map={"In Stock": "#2ecc71", "Low Stock": "#e74c3c"}
    )
    col1.plotly_chart(fig_stock, use_container_width=True)

    restock = f.groupby("Warehouse")["Restock_Needed"].sum().reset_index()
    fig_restock = px.bar(
        restock, x="Warehouse", y="Restock_Needed",
        title="Items Needing Restock by Warehouse", color="Restock_Needed",
        color_continuous_scale="Reds"
    )
    col2.plotly_chart(fig_restock, use_container_width=True)

    col3, col4 = st.columns(2)

    supplier_perf = f.groupby("Supplier").agg(
        Inventory_Value=("Inventory_Value", "sum"),
        Avg_Lead_Time=("Lead_Time_Days", "mean"),
        Items=("Product ID", "nunique"),
    ).reset_index().sort_values("Inventory_Value", ascending=False).head(10)
    fig_supplier = px.bar(
        supplier_perf, x="Inventory_Value", y="Supplier", orientation="h",
        title="Top 10 Suppliers by Inventory Value", color="Avg_Lead_Time",
        color_continuous_scale="Blues"
    )
    fig_supplier.update_layout(yaxis={"categoryorder": "total ascending"})
    col3.plotly_chart(fig_supplier, use_container_width=True)

    near_reorder = f[f["Stock_On_Hand"] <= f["Reorder_Point"] * 1.2].copy()
    near_reorder = near_reorder.sort_values("Stock_On_Hand").head(15)
    fig_reorder = px.bar(
        near_reorder, x="Stock_On_Hand", y="Product Name", orientation="h",
        title="Products Near/Below Reorder Point (Top 15 lowest stock)",
        color="Stock_Status", color_discrete_map={"In Stock": "#2ecc71", "Low Stock": "#e74c3c"}
    )
    fig_reorder.update_layout(yaxis={"categoryorder": "total ascending"})
    col4.plotly_chart(fig_reorder, use_container_width=True)

    st.subheader("⚠️ Low Stock / Restock Needed Items")
    low_stock_table = f[f["Restock_Needed"] == 1][
        ["Product Name", "Warehouse", "Supplier", "Stock_On_Hand", "Reorder_Point", "Lead_Time_Days"]
    ].sort_values("Stock_On_Hand")
    st.dataframe(low_stock_table, use_container_width=True, height=300)

st.divider()
st.caption("Built with Streamlit + Plotly — Superstore Supply Chain Dataset")
