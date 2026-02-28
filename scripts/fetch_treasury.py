"""
Treasury MSPD (Monthly Statement of Public Debt) 데이터 수집
Source: https://api.fiscaldata.treasury.gov
Total Public Debt Outstanding 월별 데이터
"""
import requests
import pandas as pd
import os
import sys

API_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_1"

def fetch_treasury_data(output_path):
    """Treasury Direct API에서 Total Public Debt Outstanding 수집"""
    
    all_records = []
    page = 1
    page_size = 1000
    
    while True:
        params = {
            'fields': 'record_date,security_type_desc,total_mil_amt',
            'filter': 'security_type_desc:eq:Total Public Debt Outstanding',
            'sort': '-record_date',
            'page[number]': page,
            'page[size]': page_size
        }
        
        print(f"Fetching page {page}...")
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        records = data.get('data', [])
        if not records:
            break
            
        all_records.extend(records)
        
        meta = data.get('meta', {})
        total_pages = meta.get('total-pages', 1)
        if page >= total_pages:
            break
        page += 1
    
    if not all_records:
        print("No data fetched!")
        sys.exit(1)
    
    df = pd.DataFrame(all_records)
    df['date'] = pd.to_datetime(df['record_date'])
    df['total_debt_mil'] = pd.to_numeric(df['total_mil_amt'], errors='coerce')
    
    # 월별 마지막 기록만 (MSPD는 보통 월말 데이터)
    df['YearMonth'] = df['date'].dt.to_period('M')
    monthly = df.sort_values('date').groupby('YearMonth').last().reset_index()
    monthly['date'] = monthly['YearMonth'].dt.to_timestamp() + pd.offsets.MonthEnd(0)
    
    result = monthly[['date', 'total_debt_mil']].sort_values('date')
    result['date'] = result['date'].dt.strftime('%Y-%m-%d')
    
    result.to_csv(output_path, index=False)
    print(f"Treasury MSPD data saved: {len(result)} rows")
    print(f"Range: {result['date'].iloc[0]} ~ {result['date'].iloc[-1]}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    output_path = os.path.join(base_dir, 'data', 'treasury_mspd.csv')
    
    fetch_treasury_data(output_path)
