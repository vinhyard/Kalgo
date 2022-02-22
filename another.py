import ccxt
import config
import schedule
import numpy as np
import pandas as pd
from datetime import datetime
import time
import warnings
from decimal import Decimal
import yfinance as yf
warnings.filterwarnings('ignore')
def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1d')
    return todays_data['Close'][0]


ask = input('Would you like to activate Kalgo for Shiba?(y/n): ')
def is_active():
    
  
    if ask == 'y' or ask == 'Y' or ask == 'Yes' or ask == 'YES' or ask == 'sure' or ask =='SURE' or ask == 'yes':
        is_act = True
     

    else: 
       is_act = False
    

    return is_act

if is_active():
    status = 'Enabled'
else:
    status = 'Disabled'

pd.set_option('display.max_rows', None)
exchange = ccxt.coinbasepro({
    "apiKey": config.COINBASE_API_KEY,
    "secret": config.COINBASE_SECRET_KEY,
    "password": config.COINBASE_PASS
})
papiya = exchange.fetch_balance()['SHIB']['total']
usdtb = exchange.fetch_balance()['USDT']['total']



print(f'SHIB Balance: {str(papiya)}\nUSDT Balance: {str(usdtb)}')

print(f'SHIBABot: {status}')
if ask == 'y' or ask == 'Y' or ask == 'Yes' or ask == 'YES' or ask == 'sure' or ask =='SURE':
    print('Please add % at the end if you would like to enter with a % of your USDT portfolio')
    howmuch = input('How much SHIBA would you like to buy/sell?: ')
    if howmuch[-1:] == '%':
        yessir = howmuch.rstrip(howmuch[-1])
        if float(yessir) == 100:
            yessir = float(yessir) - 3
        enteramount = (float(usdtb) * (float(yessir)/100))/float(get_current_price('SHIB-USD'))
        print(f'{round(enteramount,5)} SHIBA will be traded')
    else:
        enteramount = float(howmuch)
        print(f'{enteramount} SHIBA will be traded')

print('----------------------------')
def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = data['high'] - data['low']

    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low','high-pc','low-pc']].max(axis=1 )
    return tr


def atr(data, period):
    data['tr'] = tr(data)

    atr = data['tr'].rolling(period).mean()
    return atr



def supertrend(df, period=7, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    print('Calculating Cheatcodes for SHIBA')
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (multiplier * df['atr']) 
    df['lowerband'] = hl2 - (multiplier * df['atr']) 
    df['in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'] = False

        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]
            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
  
    return df

in_position = False
def check_buy_sell_signals(df):
    print("SHIBAbot: checking for buys and sells")

    global in_position
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        if not in_position:
            order = exchange.create_market_buy_order('SHIB/USDT', enteramount)
            print('BUY')
            print(order)
            print(f'SHIB Balance: {str(papiya)}\nUSDT Balance: {str(usdtb)}')
            in_position = True
        else:
            print('Already in position')

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            order = exchange.create_market_sell_order('SHIB/USDT', enteramount)
            print('SELL')
            print(order)
            print(f'SHIB Balance: {str(papiya)}\nUSDT Balance: {str(usdtb)}')
            in_position = False
        else:
            print('Not in position, nothing to sell')



def run_bot2():
    print(f"SHIB Kalgo Running")
    bars = exchange.fetch_ohlcv('SHIB/USDT',timeframe='15m', limit = 15)

    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
  
    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)