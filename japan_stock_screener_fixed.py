import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
import os

# FIXED: Secure API key handling
def get_api_key():
    """Securely retrieve API key from environment variables or Streamlit secrets."""
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key and hasattr(st, 'secrets'):
        try:
            api_key = st.secrets['FMP_API_KEY']
        except KeyError:
            pass
    
    if not api_key:
        st.error("🔑 API key not found!")
        st.info("Please set the FMP_API_KEY environment variable or add it to Streamlit secrets.")
        st.markdown("""
        ### How to set up the API key:
        
        **Option 1: Environment Variable**
        ```bash
        export FMP_API_KEY=your_api_key_here
        ```
        
        **Option 2: Streamlit Secrets**
        Create `.streamlit/secrets.toml`:
        ```toml
        FMP_API_KEY = "your_api_key_here"
        ```
        """)
        st.stop()
    
    return api_key

# Initialize API key securely
try:
    API_KEY = get_api_key()
except Exception as e:
    st.error(f"Failed to initialize API key: {e}")
    st.stop()

class RateLimiter:
    def __init__(self, max_calls_per_sec):
        self.max_calls = max_calls_per_sec
        self.lock = threading.Lock()
        self.call_times = []

    def wait(self):
        with self.lock:
            now = time.perf_counter()
            self.call_times = [t for t in self.call_times if now - t < 1.0]
            if len(self.call_times) >= self.max_calls:
                wait_time = 1.0 - (now - self.call_times[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                now = time.perf_counter()
                self.call_times = [t for t in self.call_times if now - t < 1.0]
            self.call_times.append(time.perf_counter())

rate_limiter = RateLimiter(max_calls_per_sec=5)

@st.cache_data(ttl=3600)
def get_japan_tickers():
    """Fetch Japanese stock tickers with improved error handling."""
    url = f'https://financialmodelingprep.com/api/v3/stock/list?apikey={API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        if not isinstance(data, list):
            st.error("Invalid response format from API")
            return []
            
        japan_stocks = [item for item in data if item.get('symbol', '').endswith('.T')]
        
        if not japan_stocks:
            st.warning("No Japanese stocks found in the response")
        
        return japan_stocks
    except requests.exceptions.Timeout:
        st.error("Timeout while fetching stock list")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Connection error while fetching stock list")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error while fetching stock list: {e.response.status_code}")
        return []
    except Exception as e:
        st.error(f"Unexpected error while fetching stock list: {e}")
        return []

def fetch_ratios(ticker):
    """Fetch financial ratios with improved error handling."""
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data or not isinstance(data, list):
            return None
            
        latest = data[0]
        
        # Improved data validation
        ratios = {}
        for key, api_key in [('PE', 'priceEarningsRatio'), ('PB', 'priceToBookRatio'), ('DividendYield', 'dividendYield')]:
            value = latest.get(api_key)
            if value is None:
                ratios[key] = None
            else:
                try:
                    converted_value = float(value)
                    # Basic validation for reasonable ranges
                    if key in ['PE', 'PB'] and converted_value < 0:
                        ratios[key] = None
                    elif key == 'DividendYield' and (converted_value < 0 or converted_value > 1):
                        ratios[key] = None
                    else:
                        ratios[key] = converted_value
                except (ValueError, TypeError):
                    ratios[key] = None
        
        return ratios
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            time.sleep(1)  # Rate limit hit, wait a bit longer
        return None
    except Exception:
        return None

def fetch_balance_sheet(ticker):
    """Fetch balance sheet data with improved error handling."""
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=1&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data or not isinstance(data, list):
            return None
            
        latest = data[0]
        cash = latest.get('cashAndCashEquivalents', None)
        
        if cash is not None:
            try:
                return float(cash)
            except (ValueError, TypeError):
                return None
        return None
    except Exception:
        return None

def fetch_market_cap(ticker):
    """Fetch market cap with improved error handling."""
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/market-capitalization/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data or not isinstance(data, list):
            return None
            
        latest = data[0]
        market_cap = latest.get('marketCap', None)
        
        if market_cap is not None:
            try:
                return float(market_cap)
            except (ValueError, TypeError):
                return None
        return None
    except Exception:
        return None

def save_to_csv(data, filename="筛选结果.csv"):
    """Save filtered results to CSV file."""
    if not data:
        st.warning("当前无数据可保存")
        return
    
    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        st.success(f"数据已保存到文件: {filename}")
    except Exception as e:
        st.error(f"保存文件时出错: {e}")

def process_stocks(stop_event, pe_limit, pb_limit, dividend_limit, cash_ratio_limit):
    """Process stocks with improved error handling and user feedback."""
    st.session_state.is_running = True
    st.session_state.filtered_results = []

    japan_stocks = get_japan_tickers()
    if not japan_stocks:
        st.error("无法获取日本股票列表！")
        st.session_state.is_running = False
        return

    total = len(japan_stocks)
    filtered_results = []
    
    # Show initial status
    st.session_state.status_placeholder.info(f"开始处理 {total} 只股票...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for stock in japan_stocks:
            if stop_event.is_set():
                break
            ticker = stock.get('symbol', '')
            futures[executor.submit(process_single_stock, ticker, stock.get('name', ''), pe_limit, pb_limit, dividend_limit, cash_ratio_limit, stop_event)] = ticker

        done_count = 0
        progress_bar = st.session_state.progress_bar
        status_placeholder = st.session_state.status_placeholder
        log_placeholder = st.session_state.log_placeholder

        for future in as_completed(futures):
            if stop_event.is_set():
                status_placeholder.warning("用户请求停止抓取，准备保存数据...")
                break
            result = future.result()
            done_count += 1
            
            # Update progress
            progress = done_count / total
            progress_bar.progress(progress)
            log_placeholder.text(f"已处理: {done_count} / {total} 只股票")
            
            if result:
                filtered_results.append(result)
                status_placeholder.success(f"找到 {len(filtered_results)} 只符合条件的股票")

    st.session_state.filtered_results = filtered_results
    st.session_state.is_running = False
    
    if filtered_results:
        save_to_csv(filtered_results)
        st.success(f"筛选完成！共找到 {len(filtered_results)} 只符合条件的股票")
    else:
        st.info("未找到符合条件的股票，请尝试调整筛选条件")

def process_single_stock(ticker, name, pe_limit, pb_limit, dividend_limit, cash_ratio_limit, stop_event):
    """Process a single stock with comprehensive validation."""
    if stop_event.is_set():
        return None

    ratios = fetch_ratios(ticker)
    if ratios is None:
        return None
    
    # Validate all required ratios are present
    pe = ratios.get('PE')
    pb = ratios.get('PB')
    dy = ratios.get('DividendYield')
    
    if any(x is None for x in [pe, pb, dy]):
        return None

    if stop_event.is_set():
        return None

    cash = fetch_balance_sheet(ticker)
    if cash is None or cash <= 0:
        return None
        
    market_cap = fetch_market_cap(ticker)
    if market_cap is None or market_cap <= 0:
        return None

    try:
        cash_ratio = cash / market_cap
    except (ZeroDivisionError, TypeError):
        return None

    # Apply filters with proper validation
    if (pe < pe_limit) and (pb < pb_limit) and (dy > dividend_limit) and (cash_ratio > cash_ratio_limit):
        return {
            'Ticker': ticker,
            'CompanyName': name,
            'PE': round(pe, 2),
            'PB': round(pb, 2),
            'DividendYield': round(dy * 100, 2),  # Convert to percentage
            'NetCashToMarketCap': round(cash_ratio, 3)
        }
    return None

def main():
    st.title("日本股票筛选器（带净现金/市值比筛选）")
    
    # Add API key status indicator
    if API_KEY:
        st.sidebar.success("✅ API Key 已配置")
    
    # Input controls with validation
    pe_limit = st.sidebar.number_input("最大PE", value=8.0, min_value=0.1, step=0.1)
    pb_limit = st.sidebar.number_input("最大PB", value=0.8, min_value=0.1, step=0.1)
    dividend_limit = st.sidebar.number_input("最小股息率 (%)", value=4.0, min_value=0.0, step=0.1) / 100
    cash_ratio_limit = st.sidebar.number_input("最小净现金/市值比例", value=0.6, min_value=0.0, max_value=1.0, step=0.05)

    st.sidebar.markdown("---")
    start_button = st.sidebar.button("开始筛选", disabled=st.session_state.get('is_running', False))
    stop_button = st.sidebar.button("停止抓取", disabled=not st.session_state.get('is_running', False))

    PAGE_SIZE = 20

    # Initialize session state
    if 'filtered_results' not in st.session_state:
        st.session_state.filtered_results = []
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 1
    if 'stop_event' not in st.session_state:
        st.session_state.stop_event = threading.Event()

    # UI placeholders
    st.session_state.status_placeholder = st.empty()
    st.session_state.progress_bar = st.progress(0)
    st.session_state.log_placeholder = st.empty()

    if start_button and not st.session_state.is_running:
        st.session_state.filtered_results = []
        st.session_state.stop_event.clear()
        # Start processing in a thread
        threading.Thread(
            target=process_stocks,
            args=(st.session_state.stop_event, pe_limit, pb_limit, dividend_limit, cash_ratio_limit),
            daemon=True
        ).start()

    if stop_button:
        st.session_state.stop_event.set()

    filtered_results = st.session_state.filtered_results
    total_filtered = len(filtered_results)

    if total_filtered == 0:
        if not st.session_state.is_running:
            st.info("无符合条件的股票或请先点击开始筛选")
        return

    # Pagination
    total_pages = (total_filtered - 1) // PAGE_SIZE + 1
    page_num = st.sidebar.number_input("页码", min_value=1, max_value=total_pages, value=st.session_state.page_num, step=1)
    st.session_state.page_num = page_num

    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = filtered_results[start_idx:end_idx]

    st.write(f"显示第 {page_num} 页 / 共 {total_pages} 页，每页 {PAGE_SIZE} 条")
    st.write(f"总共找到 {total_filtered} 只符合条件的股票")

    # Display results in a more organized way
    for item in page_data:
        with st.container():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"### {item['Ticker']}")
                st.write(f"**{item['CompanyName']}**")
            with col2:
                st.write(f"**PE:** {item['PE']:.2f} | **PB:** {item['PB']:.2f}")
                st.write(f"**股息率:** {item['DividendYield']:.2f}% | **净现金/市值:** {item['NetCashToMarketCap']:.3f}")
            st.markdown("---")

if __name__ == "__main__":
    main()