import requests
import pandas as pd
import os
from datetime import datetime

API_KEY = 'ef7bdfe7ef53969d614e3b455fe7f324'

def get_mlb_odds():
    url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds'
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h,totals,spreads',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso'
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get odds: {response.status_code} {response.text}")

    games = response.json()
    rows = []

    for game in games:
        home = game['home_team']
        away = game['away_team']
        for bookmaker in game['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    try:
                        if market['key'] == 'spreads':
                            bet_label = f"{outcome['name']} {'+' if outcome['point'] > 0 else ''}{outcome['point']}"
                        elif market['key'] == 'totals':
                            bet_label = f"{outcome['name']} {outcome['point']}"
                        else:
                            bet_label = outcome['name']

                        rows.append({
                            'matchup': f"{away} @ {home}",
                            'book': bookmaker['title'],
                            'market': market['key'],
                            'team_or_player': bet_label,
                            'odds': outcome['price'],
                            'implied_prob': 1 / outcome['price']
                        })
                    except KeyError:
                        continue

    df = pd.DataFrame(rows)
    df = df[df['odds'] <= 3.0]  # Remove longshots
    df['projection'] = 0.55

    # Load recent performance log and set dynamic edge threshold
    log_path = 'data/book_performance_log.csv'
    if os.path.exists(log_path):
        history = pd.read_csv(log_path)
        history = history[history['win_pct'].notna()]
        recent = history.tail(5)
        avg_win_edge = recent[recent['win_pct'] > 50]['roi'].mean() / 100
        avg_loss_edge = recent[recent['win_pct'] <= 50]['roi'].mean() / 100

        # 🧠 Dynamically adjust edge threshold with sane boundaries
        if avg_win_edge > avg_loss_edge:
            edge_threshold = max(min(avg_win_edge, 0.20), 0.05)
        else:
            edge_threshold = 0.08
    else:
        edge_threshold = 0.10  # fallback if no logs

    print(f"📊 Using edge threshold: {edge_threshold:.2%}")

    # 📊 Assign weights based on historical book performance
    book_weights = {
        'BetMGM': 1.12,
        'PointsBet': 1.08,
        'Caesars': 1.10,
        'DraftKings': 1.15,
        'FanDuel': 1.05
    }
    df['book_weight'] = df['book'].map(book_weights).fillna(1.0)

    # 📈 Calculate edge
    df['edge'] = (df['projection'] - df['implied_prob']) * df['book_weight']

    # 🧠 Apply dynamic edge filter
    df = df[df['edge'] >= edge_threshold]

    df = df.sort_values('edge', ascending=False)
    df = df.drop_duplicates(subset=['matchup', 'market'], keep='first')
    return df.sort_values(['market', 'edge'], ascending=[True, False])

def save_top_bets(df, top_n=5):
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = 'daily_bets'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'{today}.csv')

    used_matchups = set()
    top_bets = []

    for market_key in ['h2h', 'spreads', 'totals']:
        filtered = df[df['market'] == market_key]
        for _, row in filtered.iterrows():
            if row['matchup'] not in used_matchups:
                top_bets.append(row)
                used_matchups.add(row['matchup'])
            if len([b for b in top_bets if b['market'] == market_key]) >= top_n:
                break

    top_df = pd.DataFrame(top_bets)
    top_df['result'] = ''  # Fill this in manually later
    top_df.to_csv(filepath, index=False)
    print(f"✅ Saved top bets to {filepath}")

def save_to_csv(df, filename='logged_bets.csv'):
    df.to_csv(filename, index=False)

if __name__ == '__main__':
    df = get_mlb_odds()
    save_top_bets(df)