import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="📈 ROI Dashboard", layout="wide")

st.title("📊 Daily Betting Performance Tracker")
st.caption("Win/loss, ROI, and market performance")

# 🔁 Load all CSVs
@st.cache_data
def load_all_bets():
    files = glob.glob("daily_bets/*.csv")
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["date"] = os.path.basename(f).replace(".csv", "")
            dfs.append(df)
        except Exception as e:
            st.warning(f"Could not read {f}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = load_all_bets()

if df.empty:
    st.error("No bet data found.")
    st.stop()

# Clean + prepare
df['result'] = df['result'].fillna('').str.upper()
df['result'] = df['result'].fillna('').str.upper()
df = df[df['result'].isin(['W', 'L', 'P'])]
def calc_units(row):
    if row['result'] == 'W':
        return row['odds'] - 1
    elif row['result'] == 'L':
        return -1
    elif row['result'] == 'P':
        return 0
    else:
        return None  # for blanks or errors

df['units'] = df.apply(calc_units, axis=1)

# Sidebar filters
with st.sidebar:
    st.header("📅 Filters")
    all_dates = sorted(df['date'].unique())
    selected_dates = st.multiselect("Select Dates", all_dates, default=all_dates)
    selected_markets = st.multiselect("Market Types", df['market'].unique(), default=df['market'].unique())
    df = df[df['date'].isin(selected_dates) & df['market'].isin(selected_markets)]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("📅 Days Tracked", df['date'].nunique())
col2.metric("💥 Total Bets", len(df))
win_df = df[df['result'].isin(['W', 'L'])]  # exclude pushes
col3.metric("✅ Win %", f"{(win_df['result']=='W').mean()*100:.1f}%")
col4.metric("📈 ROI", f"{df['units'].sum() / len(df) * 100:.2f}%")

# 🧠 Learning from Edges
if 'edge' in df.columns:
    win_edge = df[df['result'] == 'W']['edge'].mean()
    loss_edge = df[df['result'] == 'L']['edge'].mean()

    st.subheader("🧠 Learning from Edges")
    col1, col2 = st.columns(2)
    col1.metric("📈 Avg Edge on Wins", f"{win_edge:.2%}")
    col2.metric("📉 Avg Edge on Losses", f"{loss_edge:.2%}")

# 📐 Win % by Edge Tier
df_edge_filtered = df[df['result'].isin(['W', 'L'])].copy()
df_edge_filtered['edge_bucket'] = pd.qcut(df_edge_filtered['edge'], q=4, labels=['Low', 'Med', 'High', 'Very High'])

edge_analysis = df_edge_filtered.groupby('edge_bucket').agg(
    win_rate=('result', lambda x: (x == 'W').mean() * 100),
    count=('result', 'count')
).reset_index()

st.subheader("📐 Win % by Edge Tier")
st.dataframe(edge_analysis.style.format({'win_rate': '{:.1f}%', 'count': '{:,.0f}'}))

# 🧯 Flagging Underperformance
underperforming = edge_analysis[edge_analysis['win_rate'] < 50]
if not underperforming.empty:
    st.warning("⚠️ Underperforming Edge Buckets Detected:")
    st.dataframe(underperforming)

# 📉 Daily ROI Chart
roi_by_day = df.groupby('date').agg({'units': ['sum', 'count']})
roi_by_day.columns = ['units', 'bets']
roi_by_day['ROI'] = roi_by_day['units'] / roi_by_day['bets'] * 100

st.subheader("📆 ROI Over Time")
st.line_chart(roi_by_day['ROI'])

# 📊 Market Breakdown
st.subheader("📊 Performance by Market")
market_summary = df.groupby('market').agg(
    bets=('result', 'count'),
    wins=('result', lambda x: (x == 'W').sum()),
    losses=('result', lambda x: (x == 'L').sum()),
    pushes=('result', lambda x: (x == 'P').sum()),
    win_pct=('result', lambda x: (x[x.isin(['W', 'L'])] == 'W').mean() * 100),
    roi=('units', lambda x: (x.sum() / len(x)) * 100)
).reset_index()
st.dataframe(market_summary.style.format({'win_pct': '{:.1f}%', 'roi': '{:.2f}%'}))

# 🏦 Performance by Sportsbook
st.subheader("🏦 Performance by Sportsbook")
book_summary = df.groupby('book').agg(
    bets=('result', 'count'),
    wins=('result', lambda x: (x == 'W').sum()),
    losses=('result', lambda x: (x == 'L').sum()),
    pushes=('result', lambda x: (x == 'P').sum()),
    win_pct=('result', lambda x: (x[x.isin(['W', 'L'])] == 'W').mean() * 100),
    roi=('units', lambda x: (x.sum() / len(x)) * 100)
).reset_index()
st.dataframe(book_summary.style.format({'win_pct': '{:.1f}%', 'roi': '{:.2f}%'}))

# 📋 Full Bet Log
with st.expander("📋 View Full Bet History"):
    st.dataframe(df.sort_values(['date', 'market', 'edge'], ascending=[False, True, False]))

# 📝 Store daily performance
daily_log = book_summary.copy()
daily_log['log_date'] = pd.Timestamp.now().date()
log_path = 'data/book_performance_log.csv'
os.makedirs('data', exist_ok=True)

if os.path.exists(log_path):
    existing = pd.read_csv(log_path)
    updated = pd.concat([existing, daily_log], ignore_index=True)
else:
    updated = daily_log

updated.to_csv(log_path, index=False)