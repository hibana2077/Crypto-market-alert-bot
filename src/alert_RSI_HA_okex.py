#  (`-').->   _      <-.(`-')   (`-')  _  <-. (`-')_  (`-')  _                                          
#  (OO )__   (_)      __( OO)   (OO ).-/     \( OO) ) (OO ).-/                                          
# ,--. ,'-'  ,-(`-') '-'---.\   / ,---.   ,--./ ,--/  / ,---.    .----.    .----.   .-------. .-------. 
# |  | |  |  | ( OO) | .-. (/   | \ /`.\  |   \ |  |  | \ /`.\  \_,-.  |  /  ..  \  |   _   ' |   _   ' 
# |  `-'  |  |  |  ) | '-' `.)  '-'|_.' | |  . '|  |) '-'|_.' |    .' .' |  /  \  . `-' /  /  `-' /  /  
# |  .-.  | (|  |_/  | /`'.  | (|  .-.  | |  |\    | (|  .-.  |  .'  /_  '  \  /  '    .  /      .  /   
# |  | |  |  |  |'-> | '--'  /  |  | |  | |  | \   |  |  | |  | |      |  \  `'  /    /  /      /  /    
# `--' `--'  `--'    `------'   `--' `--' `--'  `--'  `--' `--' `------'   `---''    `--'      `--'     

#   _        _____     _____   _      
#  | |      |  __ \   / ____| | |     
#  | |      | |__) | | |  __  | |     
#  | |      |  ___/  | | |_ | | |     
#  | |____  | |      | |__| | | |____ 
#  |______| |_|       \_____| |______|
                                    
                                    
VERSION = '1.0.8'
from pprint import pprint
from talib import abstract
import time , ccxt , requests , fake_useragent ,schedule
import pandas as pd
import numpy as np

WEBHOOK_URL=input("請輸入webhook網址:")

okex = ccxt.okex5({
    'enableRateLimit': True,
    'options': {
        'fetchMarkets': ['swap'],
        'defaultType': 'swap',
    },
})

'''
f_zrsi(_source, _length) =>
    ta.rsi(_source, _length) - 50
'''

def f_zrsi(_src,_len0):
    return abstract.RSI(_src,_len0)-50

'''
f_zstoch(_source, _length, _smooth, _scale) =>
    float _zstoch = ta.stoch(_source, _source, _source, _length) - 50
    float _smoothed = ta.sma(_zstoch, _smooth)
    float _scaled = _smoothed / 100 * _scale
    _scaled
'''

def f_zstoch(_src,_len1,_smooth,_scale):
    _zstoch = abstract.STOCH(_src,_src,_src,_len1)[0]-50
    _smoothed = abstract.SMA(_zstoch,_smooth)
    _scaled = _smoothed/100*_scale
    return _scaled

'''
f_rsiHeikinAshi(_length) =>
    float _closeRSI = f_zrsi(close, _length)
    float _openRSI = nz(_closeRSI[1], _closeRSI)
    float _highRSI_raw = f_zrsi(high, _length)
    float _lowRSI_raw = f_zrsi(low, _length)
    float _highRSI = math.max(_highRSI_raw, _lowRSI_raw)
    float _lowRSI = math.min(_highRSI_raw, _lowRSI_raw)
    float _close = (_openRSI + _highRSI + _lowRSI + _closeRSI) / 4
    var float _open = na
    _open := na(_open[i_smoothing]) ? (_openRSI + _closeRSI) / 2 : (_open[1] * i_smoothing + _close[1]) / (i_smoothing + 1)
    float _high = math.max(_highRSI, math.max(_open, _close))
    float _low = math.min(_lowRSI, math.min(_open, _close))
    [_open, _high, _low, _close]
'''
def f_rsiHeikinAshi(_legth,close,highs,lows,i_smoothing):
    _closeRSI = f_zrsi(close,_legth)
    _openRSI = _closeRSI[-1] if _closeRSI[-1] != np.NaN else _closeRSI[-2] #changed
    _highRSI_raw = f_zrsi(highs,_legth)
    _lowRSI_raw = f_zrsi(lows,_legth)#
    _highRSI = np.maximum(_highRSI_raw,_lowRSI_raw)
    _lowRSI = np.minimum(_highRSI_raw,_lowRSI_raw)#
    _close = (_openRSI+_highRSI+_lowRSI+_closeRSI)/4#openRSI is nan , that's why _close is nan
    _open = np.full(len(_close),np.nan)
    _open = (_openRSI+_closeRSI)/2 if np.isnan(_open[i_smoothing]) else (_open[1]*i_smoothing+_close[1])/(i_smoothing+1)
    _high = np.maximum(_highRSI,np.maximum(_open,_close))
    _low = np.minimum(_lowRSI,np.minimum(_open,_close))
    return [_open,_high,_low,_close]


def send_webhook(message:str):
    data = {
        'msgtype': 'text',
        'text': {
            'content': message,
        },
    }
    ua = fake_useragent.UserAgent(verify_ssl=False)
    headers = {
        'User-Agent': ua.random,
        'Content-Type': 'application/json',
    }
    result = requests.post(WEBHOOK_URL, json=data , headers=headers)
    if result.status_code != 200:
        print("Webhook failed with status code: " + str(result.status_code))
        print("Message: " + message)
        print("URL: " + WEBHOOK_URL)
        print("Response: " + result.text)
        return False
    else:
        pprint(result.json())
        print("Webhook sent successfully")
        return True

'''
[O, H, L, C] = f_rsiHeikinAshi(i_lenHARSI)
color bodyColour = C > O ? i_colUp : i_colDown
color wickColour = i_colWick
plotcandle(O, H, L, C, '附图蜡烛', bodyColour, wickColour, bordercolor=bodyColour)
'''

def combine_message(timeframe,over_buy_symbols,over_sell_symbols,keyword):
    os = '\n\t\t\t\t'.join(over_sell_symbols)
    ob = '\n\t\t\t\t'.join(over_buy_symbols)
    message = f'''
    ===== RSI Heikin Ashi 指標信號提醒 =====
    來自 Okex(歐易) 交易所的資料
    当前周期 {timeframe}min:
    📉下列品种收线在超卖区:\n\t\t\t\t{os}\n
    📈下列品种收线在超买区:\n\t\t\t\t{ob}\n
    🤖以上是机器指标，仅供参考，不作为交易依据。
    ⏰Time : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
    🗝️keyword: {keyword}
    ===================================
    '''
    return message

def indicator(value,overbuy,oversell):return (True,'overbuy') if value >= overbuy else (True,'oversell') if value <= oversell else (False,'hold')

def do(symbol , timeframe , limit , params:dict):
    over_buy_symbols = []
    over_sell_symbols = []
    start = time.time()
    for t in symbol:
        ohlcv = okex.fetch_ohlcv(t,timeframe=timeframe,limit=limit*3)
        df = pd.DataFrame(ohlcv,columns=['time','open','high','low','close','volume'])
        df['time'] = pd.to_datetime(df['time'],unit='ms')
        df.set_index('time',inplace=True)
        df['rsiHA_Open'],df['rsiHA_High'],df['rsiHA_Low'],df['rsiHA_Close'] = f_rsiHeikinAshi(limit,df['close'],df['high'],df['low'],i_smoothing=params['smooth_length'])
        status, trend = indicator(df['rsiHA_Close'][-1],overbuy=params['over_buy'],oversell=params['over_sell'])
        if status:
            if trend == 'overbuy':
                over_buy_symbols.append(f"{t} : RSI_CLOSE {df['rsiHA_Close'][-1]:.3f} REAL_CLOSE {df['close'][-1]:.3f}")
            else:
                over_sell_symbols.append(f"{t} : RSI_CLOSE {df['rsiHA_Close'][-1]:.3f} REAL_CLOSE {df['close'][-1]:.3f}")
        else:
            pass
    end = time.time()
    if len(over_buy_symbols) > 0 or len(over_sell_symbols) > 0:
        message = combine_message(timeframe,over_buy_symbols,over_sell_symbols,params['keyword'])
        send_webhook(message)
    else:
        print(f'No signal in {timeframe}min')
    print(f'總共耗时{end-start}秒')
    return (True,'Done')

def main(symbol_list,timeframe,length,params):
    try:
        s = time.time()
        okex.load_markets()
        status , message = do(symbol_list,f'{timeframe}m',length,params = params)
        e = time.time()
        report = f'''
        ===== 效能報告 =====
        ⏰總共耗時: {e-s:.3f}秒
        ▶️狀態: {status}
        📨訊息: {message}
        🪧總共檢測交易對: {len(symbol_list)}
        ==================='''
        print(report)
    except Exception as e:
        print(e)
        print("Error")

def delay():
    s = time.time()
    _ = okex.fetch_ticker('ADA/USDT:USDT')['last']
    e = time.time()
    return f"{e-s:.3f}s"

def sorted_by_trades(symbol_list):
    symbol_list.sort(key=lambda x:(okex.fetch_ohlcv(x,timeframe='1d',limit=2)[0][-1])*sum(okex.fetch_ohlcv(x,timeframe='1d',limit=2)[0][1:-1:])/4,reverse=True)
    return symbol_list

if __name__ == '__main__':
    print('=== 系統啟動 ===')
    print(f'系統時間: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
    print(f'系統版本: {VERSION}')
    print(f'系統狀態: 啟動中')
    print(f'系統延遲: {delay()}')
    print('================')
    symbol_list = input("請輸入幣種代號(以空格分隔)(如要使用全部幣種請輸入ALL):")
    okex.load_markets()
    symbol_list = symbol_list.split(' ') if symbol_list != 'ALL' else [t for t in okex.symbols if t.endswith(':USDT')]
    print(f'總共有{len(symbol_list)}個幣種，正在排序中...')
    symbol_list = sorted_by_trades(symbol_list)[:int(input('請輸入排名:'))]
    print(f'排序完成!')
    length = int(input("請輸入長度:"))
    smooth_length = int(input("請輸入平滑長度:"))
    over_buy = int(input("請輸入超買門檻:"))
    over_sell = int(input("請輸入超賣門檻:"))
    timeframe = int(input("請輸入時間框架:"))
    keyword = input("請輸入關鍵字:")
    print('================')
    print('系統狀態: 啟動完成')
    schedule.every(timeframe).minutes.at(":01").do(main,symbol_list=symbol_list,timeframe=timeframe,length=length,params={'smooth_length': smooth_length,'over_buy': over_buy,'over_sell': over_sell,'timeframe': timeframe,'keyword':keyword})
    while True:
        schedule.run_pending()
        time.sleep(1)


'''
candel = [ timestamp, open, high, low, close, volume ]
'''
