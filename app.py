import streamlit as st
from get_odds import get_mlb_odds, save_to_csv

st.set_page_config(page_title="MLB Locks Dashboard", layout="wide")
st.title("🔒 Top MLB Locks Today")
st.caption("Filtered for unique games · FanDuel, DraftKings, BetMGM only")

try:
    df = get_mlb_odds()
    save_to_csv(df)

    # Only use trusted books
    trusted_books = ['FanDuel', 'DraftKings', 'BetMGM']
    df = df[df['book'].isin(trusted_books)]

    # Sort by edge
    df = df.sort_values('edge', ascending=False)

    def get_top_unique(df, market_key):
        market_df = df[df['market'] == market_key]
        market_df = market_df.drop_duplicates(subset='matchup', keep='first')
        return market_df.head(5)

    top_moneylines = get_top_unique(df, 'h2h')
    top_spreads = get_top_unique(df, 'spreads')
    top_totals = get_top_unique(df, 'totals')

    st.subheader("🟩 Top 5 Moneyline Picks")
    st.dataframe(top_moneylines[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])

    st.subheader("🟨 Top 5 Spread Picks")
    st.dataframe(top_spreads[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])

    st.subheader("🟦 Top 5 Over/Under Picks")
    st.dataframe(top_totals[['matchup', 'team_or_player', 'book', 'odds', 'implied_prob', 'projection', 'edge']])

except Exception as e:
    st.error(f"Error fetching odds: {e}")