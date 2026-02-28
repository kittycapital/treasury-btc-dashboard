"""
CoinGecko API로 BTC/USD 일별 가격 수집
기존 btc_daily.csv에 새 데이터를 append
"""
import requests
import pandas as pd
import os
from datetime import datetime, timedelta

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"

def fetch_btc_daily(data_path):
    """CoinGecko에서 BTC 일별 가격 수집 및 업데이트"""
    
    daily_path = os.path.join(data_path, 'btc_daily.csv')
    
    # 기존 데이터 로드
    if os.path.exists(daily_path):
        existing = pd.read_csv(daily_path, parse_dates=['Date'])
        last_date = existing['Date'].max()
        start_date = last_date + timedelta(days=1)
        print(f"Existing data up to: {last_date.strftime('%Y-%m-%d')}")
    else:
        existing = pd.DataFrame()
        start_date = datetime(2014, 9, 17)
        print("No existing data, fetching from 2014-09-17")
    
    end_date = datetime.now()
    
    if start_date >= end_date:
        print("Data is already up to date.")
        return
    
    # CoinGecko API 호출 (Unix timestamp)
    from_ts = int(start_date.timestamp())
    to_ts = int(end_date.timestamp())
    
    params = {
        'vs_currency': 'usd',
        'from': from_ts,
        'to': to_ts
    }
    
    print(f"Fetching BTC data: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    response = requests.get(COINGECKO_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    prices = data.get('prices', [])
    if not prices:
        print("No new price data available.")
        return
    
    # DataFrame 변환
    df_new = pd.DataFrame(prices, columns=['timestamp', 'Close'])
    df_new['Date'] = pd.to_datetime(df_new['timestamp'], unit='ms').dt.normalize()
    df_new = df_new.drop_duplicates(subset='Date', keep='last')
    df_new = df_new[['Date', 'Close']]
    
    # High, Low, Open, Volume은 CoinGecko market_chart에서 제공하는 만큼 추가
    total_volumes = data.get('total_volumes', [])
    if total_volumes:
        df_vol = pd.DataFrame(total_volumes, columns=['timestamp', 'Volume'])
        df_vol['Date'] = pd.to_datetime(df_vol['timestamp'], unit='ms').dt.normalize()
        df_vol = df_vol.drop_duplicates(subset='Date', keep='last')[['Date', 'Volume']]
        df_new = df_new.merge(df_vol, on='Date', how='left')
    
    # 기존 데이터와 병합
    if not existing.empty:
        # 기존 형식에 맞추기
        for col in ['High', 'Low', 'Open']:
            if col not in df_new.columns:
                df_new[col] = df_new['Close']
        if 'Volume' not in df_new.columns:
            df_new['Volume'] = 0
            
        df_new = df_new[['Date', 'Close', 'High', 'Low', 'Open', 'Volume']]
        combined = pd.concat([existing, df_new], ignore_index=True)
        combined = combined.drop_duplicates(subset='Date', keep='last')
        combined = combined.sort_values('Date')
    else:
        for col in ['High', 'Low', 'Open']:
            if col not in df_new.columns:
                df_new[col] = df_new['Close']
        if 'Volume' not in df_new.columns:
            df_new['Volume'] = 0
        combined = df_new[['Date', 'Close', 'High', 'Low', 'Open', 'Volume']]
    
    combined.to_csv(daily_path, index=False)
    print(f"BTC daily data saved: {len(combined)} rows")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_path = os.path.join(base_dir, 'data')
    
    fetch_btc_daily(data_path)
