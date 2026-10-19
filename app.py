from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="Food Price Inflation Analysis",
    page_icon="🥦",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "food_prices.csv"


@st.cache_data
def load_data(file) -> pd.DataFrame:
    """Load the CSV and perform basic, repeatable cleaning."""
    data = pd.read_csv(file)

    required = {"date", "commodity", "price", "unit", "pricetype", "currency"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["price"] = pd.to_numeric(data["price"], errors="coerce")
    data["usdprice"] = pd.to_numeric(data["usdprice"], errors="coerce") if "usdprice" in data.columns else pd.NA

    data = data.dropna(subset=["date", "price", "commodity", "unit", "pricetype"]).copy()
    for col in ["commodity", "unit", "pricetype", "currency", "category", "market"]:
        if col in data.columns:
            data[col] = data[col].astype("string").str.strip()

    return data


def format_inr(value):
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.2f}"


st.title("🥦 Food Price Inflation Analysis")
st.caption(
    "Explore food prices over time. Comparisons are kept within the selected commodity, "
    "unit, and price type to avoid mixing unlike prices."
)

# ----------------------------
# Load data
# ----------------------------
uploaded_file = st.sidebar.file_uploader("Optional: upload your food_prices.csv", type=["csv"])

try:
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    elif DATA_PATH.exists():
        df = load_data(DATA_PATH)
    else:
        st.error(
            "Dataset not found. Put your CSV at "
            "`data/food_prices.csv`, or upload it using the sidebar."
        )
        st.stop()
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

if df.empty:
    st.error("No valid rows remain after cleaning. Check the CSV's date and price columns.")
    st.stop()

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

commodities = sorted(df["commodity"].dropna().unique().tolist())
selected_commodity = st.sidebar.selectbox(
    "Food commodity",
    commodities,
    index=commodities.index("Rice") if "Rice" in commodities else 0,
)

units = sorted(df.loc[df["commodity"] == selected_commodity, "unit"].dropna().unique().tolist())
selected_unit = st.sidebar.selectbox("Unit", units)

types = sorted(
    df.loc[
        (df["commodity"] == selected_commodity) & (df["unit"] == selected_unit),
        "pricetype",
    ].dropna().unique().tolist()
)
selected_type = st.sidebar.selectbox(
    "Price type",
    types,
    index=types.index("Retail") if "Retail" in types else 0,
)

filtered = df[
    (df["commodity"] == selected_commodity)
    & (df["unit"] == selected_unit)
    & (df["pricetype"] == selected_type)
].copy()

if filtered.empty:
    st.warning("No records match these filters.")
    st.stop()

min_date = filtered["date"].min().date()
max_date = filtered["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["date"].dt.date >= start_date)
        & (filtered["date"].dt.date <= end_date)
    ]

if filtered.empty:
    st.warning("No records are available for the selected date range.")
    st.stop()

# ----------------------------
# Key metrics
# ----------------------------
monthly = (
    filtered.assign(month=filtered["date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .agg(
        median_price=("price", "median"),
        average_price=("price", "mean"),
        records=("price", "size"),
    )
    .sort_values("month")
)

first_price = monthly["median_price"].iloc[0]
last_price = monthly["median_price"].iloc[-1]
if pd.notna(first_price) and first_price != 0:
    total_change_pct = ((last_price - first_price) / first_price) * 100
else:
    total_change_pct = float("nan")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Records in selection", f"{len(filtered):,}")
col2.metric("Median price", format_inr(filtered["price"].median()))
col3.metric("First month median", format_inr(first_price))
col4.metric(
    "Change: first to last month",
    f"{total_change_pct:+.2f}%" if pd.notna(total_change_pct) else "N/A",
)

st.caption(
    f"Selected: **{selected_commodity}** · **{selected_unit}** · **{selected_type}**. "
    "Monthly median prices are used for the trend to reduce the effect of unusually high or low observations."
)

# ----------------------------
# Charts
# ----------------------------
st.subheader("1. Price trend over time")
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(monthly["month"], monthly["median_price"], linewidth=2)
ax.set_xlabel("Month")
ax.set_ylabel(f"Price (INR per {selected_unit})")
ax.set_title(f"Monthly median price — {selected_commodity}")
ax.grid(True, alpha=0.3)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.subheader("2. Monthly percentage change")
monthly["monthly_change_pct"] = monthly["median_price"].pct_change() * 100
change_data = monthly.dropna(subset=["monthly_change_pct"])

if change_data.empty:
    st.info("There are not enough months in this selection to calculate monthly percentage changes.")
else:
    fig2, ax2 = plt.subplots(figsize=(11, 4))
    ax2.bar(change_data["month"], change_data["monthly_change_pct"], width=20)
    ax2.axhline(0, linewidth=1)
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Change (%)")
    ax2.set_title("Month-to-month change in median price")
    ax2.grid(True, axis="y", alpha=0.3)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

# ----------------------------
# Explore commodity averages (unit-aware)
# ----------------------------
st.subheader("3. Compare commodities")
st.write(
    "This table compares average prices only for the chosen unit and price type. "
    "Different units such as KG, L, and 100 KG should not be compared as if they were the same."
)

same_unit = df[
    (df["unit"] == selected_unit)
    & (df["pricetype"] == selected_type)
].copy()

if same_unit.empty:
    st.info("No other commodities match the selected unit and price type.")
else:
    commodity_summary = (
        same_unit.groupby("commodity", as_index=False)
        .agg(
            average_price=("price", "mean"),
            median_price=("price", "median"),
            records=("price", "size"),
        )
        .sort_values("average_price", ascending=False)
    )
    st.dataframe(
        commodity_summary.style.format(
            {"average_price": "₹{:,.2f}", "median_price": "₹{:,.2f}", "records": "{:,.0f}"}
        ),
        use_container_width=True,
        hide_index=True,
    )

# ----------------------------
# Data table and download
# ----------------------------
with st.expander("View filtered records"):
    display_cols = [
        col for col in
        ["date", "commodity", "category", "market", "unit", "pricetype", "currency", "price"]
        if col in filtered.columns
    ]
    st.dataframe(
        filtered[display_cols].sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered data as CSV",
    data=csv_bytes,
    file_name="filtered_food_prices.csv",
    mime="text/csv",
)

st.divider()
st.caption(
    "Note: This dashboard describes price movements in the supplied dataset. "
    "It is not an official CPI inflation measure. Results depend on the coverage and consistency "
    "of the recorded markets, dates, units, and price types."
)
