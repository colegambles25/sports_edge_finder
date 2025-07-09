import requests
import pandas as pd
import os
from datetime import datetime

API_KEY = '2323490a159b58cfff6471be89e12d2d'

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

    # 🚫 Remove bad lines
    df = df[df['odds'] <= 3.0]  # No longshots over +200

    # 📈 Add projection (placeholder: 55% chance to beat book)
    df['projection'] = 0.55

    # 🧠 Add sharp book weight
    sharp_books = ['BetMGM', 'PointsBet', 'Caesars', 'DraftKings']
    df['book_weight'] = df['book'].apply(lambda x: 1.1 if x in sharp_books else 1.0)

    # 💥 Edge calculation
    df['edge'] = (df['projection'] - df['implied_prob']) * df['book_weight']

    # 🔒 Keep best per market per matchup
    df = df.sort_values('edge', ascending=False)
    df = df.drop_duplicates(subset=['matchup', 'market'], keep='first')

    return df.sort_values(['market', 'edge'], ascending=[True, False])

def save_top_bets(df, top_n=5):
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = 'daily_bets'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'{today}.csv')

    top_bets = pd.concat([
        df[df['market'] == 'h2h'].nlargest(5, 'edge'),
        df[df['market'] == 'spreads'].nlargest(5, 'edge'),
        df[df['market'] == 'totals'].nlargest(5, 'edge')
    ])

    top_bets['result'] = ''  # You’ll fill this in manually (W or L)
    top_bets.to_csv(filepath, index=False)
    print(f"✅ Saved top bets to {filepath}")

def save_to_csv(df, filename='logged_bets.csv'):
    df.to_csv(filename, index=False)

if __name__ == '__main__':
    df = get_mlb_odds()
    save_top_bets(df)