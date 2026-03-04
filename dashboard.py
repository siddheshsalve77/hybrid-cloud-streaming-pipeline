"""
dashboard.py — Hybrid Cloud Pipeline Analytics
Run: python -m streamlit run dashboard.py
"""

import streamlit as st
import boto3
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="Pipeline Analytics",
    page_icon="🚀",
    layout="wide"
)

S3_BUCKET = "hybrid-pipeline-raw-zone"
S3_PREFIX = "large_streaming_data/"

@st.cache_data(ttl=300)
def load_data():
    try:
        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX)

        frames = []
        file_count = 0
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".parquet"):
                    body = s3.get_object(
                        Bucket=S3_BUCKET, Key=obj["Key"]
                    )["Body"].read()
                    frames.append(pd.read_parquet(BytesIO(body)))
                    file_count += 1

        if not frames:
            return pd.DataFrame(), 0

        df = pd.concat(frames, ignore_index=True)
        df = df.drop_duplicates(subset=["transaction_id"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["hour"] = df["timestamp"].dt.hour
        return df, file_count

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), 0


st.title("🚀 Hybrid Cloud Pipeline Dashboard")
st.caption("Kafka → Airflow → S3 → Parquet | Real-time Analytics")
st.markdown("---")

with st.spinner("Loading data from S3..."):
    df, file_count = load_data()

if df.empty:
    st.error("No data found. Make sure the pipeline ran and S3 has Parquet files.")
    st.stop()

st.success(f"Loaded {len(df):,} records from {file_count} Parquet files in S3")

st.sidebar.title("Filters")
products = ["All"] + sorted(df["product"].dropna().unique().tolist())
sel_product = st.sidebar.selectbox("Product", products)

statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())
sel_status = st.sidebar.selectbox("Order Status", statuses)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown(f"""
**Pipeline Info**
- Records: `{len(df):,}`
- Files: `{file_count}`
- Bucket: `{S3_BUCKET}`
""")

filtered = df.copy()
if sel_product != "All":
    filtered = filtered[filtered["product"] == sel_product]
if sel_status != "All":
    filtered = filtered[filtered["status"] == sel_status]

st.subheader("Key Metrics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Orders",    f"{len(filtered):,}")
c2.metric("Total Revenue",   f"${filtered['total_price'].sum():,.0f}")
c3.metric("Avg Order Value", f"${filtered['total_price'].mean():,.2f}")
c4.metric("Units Sold",      f"{filtered['quantity'].sum():,}")
completed = (filtered["status"] == "Completed").sum()
c5.metric("Completion Rate", f"{completed/len(filtered)*100:.1f}%")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by State (Top 15)")
    state_data = (
        filtered.groupby("state")["total_price"]
        .sum().sort_values(ascending=False).head(15).reset_index()
    )
    state_data.columns = ["State", "Revenue"]
    st.bar_chart(state_data.set_index("State"))

with col2:
    st.subheader("Best Selling Products")
    prod_data = (
        filtered.groupby("product")
        .agg(Revenue=("total_price","sum"), Units=("quantity","sum"), Orders=("transaction_id","count"))
        .sort_values("Revenue", ascending=False).reset_index()
    )
    prod_data["Revenue ($)"] = prod_data["Revenue"].apply(lambda x: f"${x:,.0f}")
    prod_data["Units Sold"]  = prod_data["Units"].apply(lambda x: f"{x:,}")
    st.dataframe(prod_data[["product","Revenue ($)","Units Sold","Orders"]], use_container_width=True, hide_index=True)

st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    st.subheader("Order Status Breakdown")
    status_data = filtered["status"].value_counts().reset_index()
    status_data.columns = ["Status", "Count"]
    st.bar_chart(status_data.set_index("Status"))
    status_data["Percentage"] = (status_data["Count"]/status_data["Count"].sum()*100).round(1).astype(str)+"%"
    st.dataframe(status_data, use_container_width=True, hide_index=True)

with col4:
    st.subheader("Payment Method Split")
    pay_data = (
        filtered.groupby("payment_method")
        .agg(Orders=("transaction_id","count"), Revenue=("total_price","sum"))
        .sort_values("Orders", ascending=False).reset_index()
    )
    st.bar_chart(pay_data.set_index("payment_method")["Orders"])
    pay_data["Revenue"] = pay_data["Revenue"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(pay_data, use_container_width=True, hide_index=True)

st.markdown("---")
col5, col6 = st.columns(2)

with col5:
    st.subheader("Hourly Transaction Volume")
    hourly = (
        filtered.groupby("hour")
        .agg(Transactions=("transaction_id","count"))
        .reset_index().sort_values("hour")
    )
    hourly["Hour"] = hourly["hour"].apply(lambda x: f"{x:02d}:00")
    st.line_chart(hourly.set_index("Hour")["Transactions"])

with col6:
    st.subheader("Device Type Analysis")
    device_data = (
        filtered.groupby("device_type")
        .agg(Orders=("transaction_id","count"), Avg_Value=("total_price","mean"))
        .reset_index()
    )
    device_data["Percentage"] = (device_data["Orders"]/device_data["Orders"].sum()*100).round(1).astype(str)+"%"
    device_data["Avg Order ($)"] = device_data["Avg_Value"].apply(lambda x: f"${x:,.2f}")
    st.bar_chart(device_data.set_index("device_type")["Orders"])
    st.dataframe(device_data[["device_type","Orders","Percentage","Avg Order ($)"]], use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Raw Data Explorer")
with st.expander("Click to view sample records"):
    cols = ["transaction_id","customer_name","product","quantity","total_price","state","payment_method","status","device_type","timestamp"]
    st.dataframe(filtered[cols].head(200), use_container_width=True)
    st.caption(f"Showing 200 of {len(filtered):,} filtered records")

st.markdown("---")
st.caption(f"Hybrid Cloud Pipeline · {len(filtered):,} records · {file_count} Parquet files · s3://{S3_BUCKET}/{S3_PREFIX}")