import sys, os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import datetime
from odds_engine import get_mlb_odds, save_top_bets, save_to_csv

st.set_page_config(page_title="MLB Locks Dashboard", layout="wide")
st.title("🔒 Top MLB Locks Today")
st.caption("1 bet per game · Best available across all sportsbooks")

# Cache to limit API calls
@st.cache_data(ttl=3600)
def fetch_odds():
    return get_mlb_odds()

df = fetch_odds()

# 🔁 Always save daily picks (overwrite allowed to avoid caching issues)
save_top_bets(df)

save_to_csv(df)

# Display top 5 bets per market with unique matchups across all
df = df.sort_values('edge', ascending=False)
used_matchups = set()

def top_unique(df, market_key):
    picks = []
    filtered = df[df['market'] == market_key]
    for _, row in filtered.iterrows():
        if row['matchup'] not in used_matchups:
            picks.append(row.to_dict())  # Ensure each row is a dict
            used_matchups.add(row['matchup'])
        if len(picks) == 5:
            break
    return pd.DataFrame(picks) if picks else pd.DataFrame(columns=df.columns)

top_ml = top_unique(df, 'h2h')
top_spread = top_unique(df, 'spreads')
top_total = top_unique(df, 'totals')

st.subheader("🟩 Top 5 Moneyline Bets")
if not top_ml.empty:
    st.dataframe(top_ml[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])
else:
    st.info("No moneyline bets available.")

st.subheader("🟨 Top 5 Spread Bets")
if not top_spread.empty:
    st.dataframe(top_spread[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])
else:
    st.info("No spread bets available.")

st.subheader("🟦 Top 5 Over/Under Bets")
if not top_total.empty:
    st.dataframe(top_total[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])
else:
    st.info("No totals bets available.")

# 📥 Allow download of today's picks
from io import StringIO

st.subheader("📥 Download Today's Picks")

csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Download CSV",
    data=csv_buffer.getvalue(),
    file_name=f"{datetime.datetime.now().strftime('%Y-%m-%d')}.csv",
    mime="text/csv"
)

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}")