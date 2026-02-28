"""
Treasury MSPD와 BTC 월별 데이터를 병합하고
12-Month Change를 계산한 뒤 z-score 정규화.
Chart.js용 JSON 파일 출력.
"""
import pandas as pd
import numpy as np
import json
import os

def compute_correlation(x, y):
    """피어슨 상관계수 계산"""
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    if len(x_clean) < 3:
        return 0.0
    return np.corrcoef(x_clean, y_clean)[0, 1]

def process_combined_data(data_dir):
    """데이터 병합 및 처리"""
    
    # 1. BTC 월별 데이터 로드
    btc_path = os.path.join(data_dir, 'btc_monthly.csv')
    btc = pd.read_csv(btc_path, parse_dates=['date'])
    btc = btc.sort_values('date')
    
    # 2. Treasury MSPD 데이터 로드
    treasury_path = os.path.join(data_dir, 'treasury_mspd.csv')
    treasury = pd.read_csv(treasury_path, parse_dates=['date'])
    treasury = treasury.sort_values('date')
    
    # 3. 월 기준으로 병합
    btc['year_month'] = btc['date'].dt.to_period('M')
    treasury['year_month'] = treasury['date'].dt.to_period('M')
    
    merged = pd.merge(
        btc[['year_month', 'btc_close']],
        treasury[['year_month', 'total_debt_mil']],
        on='year_month',
        how='inner'
    )
    merged = merged.sort_values('year_month')
    
    # 4. 12-Month Change 계산
    # BTC: 12개월 수익률 (%)
    merged['btc_12m_change'] = merged['btc_close'].pct_change(12) * 100
    
    # Treasury: 12개월 절대 변화량 (millions)
    merged['treasury_12m_change'] = merged['total_debt_mil'].diff(12)
    
    # 5. Z-score 정규화 (NaN 제외)
    for col in ['btc_12m_change', 'treasury_12m_change']:
        valid = merged[col].dropna()
        mean = valid.mean()
        std = valid.std()
        merged[f'{col}_zscore'] = (merged[col] - mean) / std
    
    # 6. 상관계수 계산
    r = compute_correlation(
        merged['btc_12m_change_zscore'].values,
        merged['treasury_12m_change_zscore'].values
    )
    
    # 7. JSON 출력 (Chart.js용)
    chart_data = {
        'labels': [],
        'btc': [],
        'treasury': [],
        'correlation': round(r, 2),
        'last_updated': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')
    }
    
    for _, row in merged.iterrows():
        label = str(row['year_month'])
        chart_data['labels'].append(label)
        
        btc_val = None if pd.isna(row['btc_12m_change_zscore']) else round(float(row['btc_12m_change_zscore']), 4)
        treasury_val = None if pd.isna(row['treasury_12m_change_zscore']) else round(float(row['treasury_12m_change_zscore']), 4)
        
        chart_data['btc'].append(btc_val)
        chart_data['treasury'].append(treasury_val)
    
    output_path = os.path.join(data_dir, 'combined_data.json')
    with open(output_path, 'w') as f:
        json.dump(chart_data, f, indent=2)
    
    print(f"Combined data saved: {len(merged)} months")
    print(f"Date range: {merged['year_month'].iloc[0]} ~ {merged['year_month'].iloc[-1]}")
    print(f"Pearson correlation (r): {r:.4f}")
    print(f"Valid data points: {merged['btc_12m_change_zscore'].notna().sum()}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(base_dir, 'data')
    
    process_combined_data(data_dir)
