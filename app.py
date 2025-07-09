import streamlit as st
from get_odds import get_mlb_odds, save_to_csv

st.set_page_config(page_title="MLB Value Edge Finder", layout="wide")

st.title("🧠 Daily MLB Value Bets")
st.caption("Live moneylines + strikeout props with edge projections")

try:
    df = get_mlb_odds()
    save_to_csv(df)

    st.success(f"✅ {len(df)} value bets found today.")
    st.dataframe(df[['matchup', 'team_or_player', 'book', 'market', 'odds', 'implied_prob', 'projection', 'edge']])
except Exception as e:
    st.error(f"Error fetching odds: {e}")