import yfinance as yf
import pandas as pd

def get_price_on_or_before(ticker, date):
    stock = yf.Ticker(ticker)
    start = pd.to_datetime(date) - pd.Timedelta(days=5)
    end = pd.to_datetime(date) + pd.Timedelta(days=1)
    df = stock.history(start=start, end=end)
    # After getting df from yfinance
    if df.empty:
        return None
    # Ensure date is tz-aware and matches df.index timezone
    target_date = pd.to_datetime(date)
    if df.index.tz is not None:
        target_date = target_date.tz_localize(df.index.tz)
    df = df[df.index <= target_date]
    return df["Close"].iloc[-1]

def get_prices_for_periods(ticker, period_ends):
    prices = []
    for date in period_ends:
        price = get_price_on_or_before(ticker, date)
        prices.append(price)
    return pd.Series(prices, index=period_ends)


