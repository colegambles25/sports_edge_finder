import streamlit as st
from get_odds import get_mlb_odds, save_to_csv

st.set_page_config(page_title="MLB Locks Dashboard", layout="wide")
st.title("🔒 Top MLB Locks Today")
st.caption("1 bet per game · FanDuel, DraftKings, BetMGM only")

try:
    df = get_mlb_odds()
    save_to_csv(df)

    # Filter for top books only
    trusted_books = ['FanDuel', 'DraftKings', 'BetMGM']
    df = df[df['book'].isin(trusted_books)]

    # Sort by edge
    df = df.sort_values('edge', ascending=False)

    # Helper to extract top 5 per market with unique matchups
    def top_unique(df, market_key):
        filtered = df[df['market'] == market_key]
        filtered = filtered.drop_duplicates(subset='matchup', keep='first')
        return filtered.head(5)

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

except Exception as e:
    st.error(f"Error fetching odds: {e}")