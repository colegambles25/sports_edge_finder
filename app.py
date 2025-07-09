import streamlit as st
from get_odds import get_mlb_odds, save_to_csv

st.set_page_config(page_title="MLB Value Edge Finder", layout="wide")

st.title("🧠 Top 5 MLB Value Bets")
st.caption("One bet per game · FanDuel, DraftKings, and BetMGM only")

try:
    df = get_mlb_odds()
    save_to_csv(df)

    # Filter to approved books
    target_books = ['FanDuel', 'DraftKings', 'BetMGM']
    df = df[df['book'].isin(target_books)]

    # Sort by edge
    df = df.sort_values('edge', ascending=False)

    # Deduplicate by matchup, keeping best edge per game
    df_unique = df.drop_duplicates(subset='matchup', keep='first')

    # Take top 5 unique games
    top_df = df_unique.head(5)

    st.success("✅ Top 5 bets — 1 per game — from top books")
    st.dataframe(top_df[['matchup', 'team_or_player', 'book', 'market', 'odds', 'implied_prob', 'projection', 'edge']])

except Exception as e:
    st.error(f"Error fetching odds: {e}")