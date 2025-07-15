import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

API_KEY = 'kh8rUz6TGRampn9TFFVe3rJo1CeprHLt'

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
    url = f'https://financialmodelingprep.com/api/v3/stock/list?apikey={API_KEY}'
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    japan_stocks = [item for item in data if item.get('symbol', '').endswith('.T')]
    return japan_stocks

def fetch_ratios(ticker):
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        latest = data[0]
        return {
            'PE': latest.get('priceEarningsRatio'),
            'PB': latest.get('priceToBookRatio'),
            'DividendYield': latest.get('dividendYield')
        }
    except Exception:
        return None

def fetch_balance_sheet(ticker):
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=1&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        latest = data[0]
        # 返回现金及现金等价物
        cash = latest.get('cashAndCashEquivalents', None)
        return cash
    except Exception:
        return None

def fetch_market_cap(ticker):
    rate_limiter.wait()
    url = f"https://financialmodelingprep.com/api/v3/market-capitalization/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        latest = data[0]
        return latest.get('marketCap', None)
    except Exception:
        return None

def save_to_csv(data, filename="筛选结果.csv"):
    if not data:
        st.warning("当前无数据可保存")
        return
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    st.success(f"数据已保存到文件: {filename}")

def process_stocks(stop_event, pe_limit, pb_limit, dividend_limit, cash_ratio_limit):
    st.session_state.is_running = True
    st.session_state.filtered_results = []

    japan_stocks = get_japan_tickers()
    if not japan_stocks:
        st.warning("获取日本股票列表失败！")
        st.session_state.is_running = False
        return

    total = len(japan_stocks)
    filtered_results = []

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
            progress_bar.progress(done_count / total)
            log_placeholder.text(f"已处理: {done_count} / {total} 只股票")
            if result:
                filtered_results.append(result)

    st.session_state.filtered_results = filtered_results
    st.session_state.is_running = False
    save_to_csv(filtered_results)

def process_single_stock(ticker, name, pe_limit, pb_limit, dividend_limit, cash_ratio_limit, stop_event):
    if stop_event.is_set():
        return None

    ratios = fetch_ratios(ticker)
    if ratios is None:
        return None
    try:
        pe = float(ratios['PE'])
        pb = float(ratios['PB'])
        dy = float(ratios['DividendYield'])
    except (TypeError, ValueError):
        return None

    if stop_event.is_set():
        return None

    cash = fetch_balance_sheet(ticker)
    if cash is None:
        return None
    market_cap = fetch_market_cap(ticker)
    if market_cap is None or market_cap == 0:
        return None

    cash_ratio = cash / market_cap

    if (pe < pe_limit) and (pb < pb_limit) and (dy > dividend_limit) and (cash_ratio > cash_ratio_limit):
        return {
            'Ticker': ticker,
            'CompanyName': name,
            'PE': pe,
            'PB': pb,
            'DividendYield': dy,
            'NetCashToMarketCap': cash_ratio
        }
    return None

def main():
    st.title("日本股票筛选器（带净现金/市值比筛选）")

    pe_limit = st.sidebar.number_input("最大PE", value=8.0, step=0.1)
    pb_limit = st.sidebar.number_input("最大PB", value=0.8, step=0.1)
    dividend_limit = st.sidebar.number_input("最小股息率 (%)", value=4.0, step=0.1) / 100
    cash_ratio_limit = st.sidebar.number_input("最小净现金/市值比例", value=0.6, step=0.05)

    st.sidebar.markdown("---")
    start_button = st.sidebar.button("开始筛选")
    stop_button = st.sidebar.button("停止抓取")

    PAGE_SIZE = 20

    if 'filtered_results' not in st.session_state:
        st.session_state.filtered_results = []
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 1
    if 'stop_event' not in st.session_state:
        st.session_state.stop_event = threading.Event()

    # UI占位
    st.session_state.status_placeholder = st.empty()
    st.session_state.progress_bar = st.progress(0)
    st.session_state.log_placeholder = st.empty()

    if start_button and not st.session_state.is_running:
        st.session_state.filtered_results = []
        st.session_state.stop_event.clear()
        # 启动线程传入参数，不要在线程内访问 session_state 参数
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
        st.info("无符合条件的股票或请先点击开始筛选")
        return

    total_pages = (total_filtered - 1) // PAGE_SIZE + 1
    page_num = st.sidebar.number_input("页码", min_value=1, max_value=total_pages, value=st.session_state.page_num, step=1)
    st.session_state.page_num = page_num

    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = filtered_results[start_idx:end_idx]

    st.write(f"显示第 {page_num} 页 / 共 {total_pages} 页，每页 {PAGE_SIZE} 条")

    for item in page_data:
        st.markdown(f"### {item['Ticker']} - {item['CompanyName']}")
        st.write(f"PE: {item['PE']:.2f}    PB: {item['PB']:.2f}    股息率: {item['DividendYield']*100:.2f}%    净现金/市值: {item['NetCashToMarketCap']:.2f}")

if __name__ == "__main__":
    main()
