import pandas as pd
import sys
import os

def process_btc_to_monthly(input_path, output_path):
    """BTC 일별 데이터를 월말 종가로 리샘플링"""
    df = pd.read_csv(input_path, parse_dates=['Date'])
    df = df.sort_values('Date')
    
    # 월말 종가 추출
    df['YearMonth'] = df['Date'].dt.to_period('M')
    monthly = df.groupby('YearMonth').last().reset_index()
    monthly['Date'] = monthly['YearMonth'].dt.to_timestamp() + pd.offsets.MonthEnd(0)
    
    result = monthly[['Date', 'Close']].copy()
    result.columns = ['date', 'btc_close']
    result['date'] = result['date'].dt.strftime('%Y-%m-%d')
    
    result.to_csv(output_path, index=False)
    print(f"BTC monthly data saved: {len(result)} rows")
    print(f"Range: {result['date'].iloc[0]} ~ {result['date'].iloc[-1]}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    input_path = os.path.join(base_dir, 'data', 'btc_daily.csv')
    output_path = os.path.join(base_dir, 'data', 'btc_monthly.csv')
    
    process_btc_to_monthly(input_path, output_path)
