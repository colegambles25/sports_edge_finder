import requests
import pandas as pd

API_KEY = '2323490a159b58cfff6471be89e12d2d'

def get_mlb_odds():
    url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/odds'
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h,player_pitcher_strikeouts',
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
                    rows.append({
                        'matchup': f"{away} @ {home}",
                        'book': bookmaker['title'],
                        'market': market['key'],
                        'team_or_player': outcome['name'],
                        'odds': outcome['price']
                    })

    df = pd.DataFrame(rows)
    df['implied_prob'] = 1 / df['odds']
    df['projection'] = 0.55
    df['edge'] = df['projection'] - df['implied_prob']
    df = df[df['edge'] > 0]
    return df.sort_values('edge', ascending=False)

def save_to_csv(df, filename='logged_bets.csv'):
    df.to_csv(filename, index=False)