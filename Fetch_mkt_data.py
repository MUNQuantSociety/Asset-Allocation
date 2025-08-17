FMP_API_KEY = "API_KEY_HERE"  # Replace with actual API key, ask Joshua for it.

import requests
import csv
import time
import os

# --- PART 1: Function to get the top 500 tickers ---
# This part of your code is correct and needs no changes.
def get_top_traded_nasdaq_stocks(api_key, num_stocks=500):
    """
    Fetches the tickers for the top N most traded stocks on the NASDAQ.
    """
    print("Step 1: Identifying the top 500 most traded NASDAQ stocks...")
    screener_url = "https://financialmodelingprep.com/api/v3/stock-screener"
    params = {
        "exchange": "NASDAQ",
        "isActivelyTrading": "true",
        "limit": 2000, # Fetch a larger pool to sort from
        "apikey": api_key
    }
    
    try:
        response = requests.get(screener_url, params=params)
        response.raise_for_status()
        all_stocks = response.json()
        
        if not all_stocks:
            print("❌ Screener API returned no data.")
            return []
            
        # Sort stocks by trading volume in descending order
        sorted_stocks = sorted(all_stocks, key=lambda x: x.get('volume', 0), reverse=True)
        top_stocks = sorted_stocks[:num_stocks]
        top_tickers = [stock['symbol'] for stock in top_stocks]
        
        print(f"✅ Found {len(top_tickers)} tickers. Proceeding to fetch historical data.")
        return top_tickers
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching top tickers: {e}")
        return []

# --- PART 2: Function to get historical data for a single ticker ---

def get_historical_data(ticker, api_key):
    """
    Fetches the full historical end-of-day data for a given stock ticker.
    """
    # Cleaner way to build the URL and parameters
    history_url = "https://financialmodelingprep.com/stable/historical-price-eod/full"
    params = {
        "symbol": ticker,
        "apikey": api_key
    }
    
    try:
        response = requests.get(history_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"    - Could not fetch data for {ticker}: {e}")
        return None
    # No longer need a KeyError check since we are not accessing a specific key.
    except Exception as e:
        print(f"    - An unexpected error occurred for {ticker}: {e}")
        return None

# --- Main Execution Block ---
# This part of your code is correct and needs no changes.
if __name__ == "__main__":
    if FMP_API_KEY == "YOUR_API_KEY" or not FMP_API_KEY:
        print("⚠️ Please set your FMP_API_KEY at the top of the script.")
    else:
        # Get the list of top 500 tickers
        top_500_tickers = get_top_traded_nasdaq_stocks(FMP_API_KEY)
        
        if top_500_tickers:
            all_historical_data = []
            
            print("\nStep 2: Fetching historical data for each ticker...")
            
            # Loop through each ticker to get its data
            for i, ticker in enumerate(top_500_tickers, 1):
                print(f"  Fetching ({i}/{len(top_500_tickers)}): {ticker}")
                
                historical_data = get_historical_data(ticker, FMP_API_KEY)
                
                if historical_data:
                    all_historical_data.extend(historical_data)
                
                time.sleep(0.2) 

            # --- PART 3: Save all collected data to a CSV file ---
            if all_historical_data:
                output_filename = "mkt_data_top_500_traded_nasdaq.csv"
                print(f"\nStep 3: Saving all data to '{output_filename}'...")
                
                headers = all_historical_data[0].keys()
                
                try:
                    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(all_historical_data)
                    
                    print(f"✅ Success! Data for {len(all_historical_data)} records saved.")
                except IOError as e:
                    print(f"❌ Error writing to CSV file: {e}")
            else:
                print("⚠️ No historical data was collected. CSV file not created.")