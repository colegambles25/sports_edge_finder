import streamlit as st
from get_odds import get_mlb_odds, save_to_csv

st.set_page_config(page_title="MLB Value Edge Finder", layout="wide")

st.title("🧠 Top 5 MLB Value Bets")
st.caption("Filtered to FanDuel, DraftKings, and BetMGM")

try:
    df = get_mlb_odds()
    save_to_csv(df)

    # Only keep bets from FanDuel, DraftKings, BetMGM
    target_books = ['FanDuel', 'DraftKings', 'BetMGM']
    df = df[df['book'].isin(target_books)]

    # Sort by edge and take top 5
    top_df = df.sort_values('edge', ascending=False).head(5)

    st.success(f"✅ Showing top 5 value bets from FanDuel, DraftKings, and BetMGM")
    st.dataframe(top_df[['matchup', 'team_or_player', 'book', 'market', 'odds', 'implied_prob', 'projection', 'edge']])
except Exception as e:
    st.error(f"Error fetching odds: {e}")