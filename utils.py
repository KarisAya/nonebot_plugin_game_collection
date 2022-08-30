from datetime import datetime
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties 
from mplfinance.original_flavor import candlestick_ohlc

import os

try:
    import ujson as json
except ModuleNotFoundError:
    import json

def get_message_at(data: str) -> list:
    qq_list = []
    data = json.loads(data)
    try:
        for msg in data['message']:
            if msg['type'] == 'at':
                qq_list.append(int(msg['data']['qq']))
        return qq_list
    except Exception:
        return []

def is_number(s) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

font = FontProperties(fname = os.path.dirname(__file__) + '/events/fonts/simsun.ttc', size=30)

def market_fig(market_history:list,title:str) -> BytesIO:
    """
    生成股价折线图
    """
    buy = []
    sell = []
    T = []
    for i in range(len(market_history) if len(market_history) < 200 else 200):
        T.append(datetime.fromtimestamp(market_history[-i-1][0]).strftime("%H:%M"))
        buy.append(market_history[-i-1][1])
        sell.append(market_history[-i-1][2])
    else:
        T.reverse()
        buy.reverse()
        sell.reverse()

    plt.figure(figsize=(16, 9), dpi = 100)
    plt.plot(T, buy, c = 'darkblue', linestyle = '-')
    plt.plot(T, sell, c = 'black', linestyle = '-')
    plt.xticks(rotation=30)
    plt.title(title, fontproperties=font)
    plt.grid(True, linestyle='-', alpha=0.3)
    output = BytesIO()
    plt.savefig(output)
    return output

def list_split(data:list,lenth:int) -> list:
    new_list = []
    old_list = list(data)
    while old_list:
        tmp = []
        i = 0
        for i in range (lenth if lenth < len(old_list) else len(old_list)):
            tmp.append(old_list[0])
            del old_list[0]
        else:
            new_list.append(tmp)
    else:
        return new_list

def market_candlestick(market_history:list,title:str) -> BytesIO:
    """
    生成股价K线图(4天)
    """
    buy = []
    sell = []
    T = []
    for i in range(len(market_history) if len(market_history) < 1200 else 1200):
        T.append(datetime.fromtimestamp(market_history[-i-1][0]).strftime("%H:%M"))
        buy.append(market_history[-i-1][1])
        sell.append(market_history[-i-1][2])
    else:
        T.reverse()
        buy.reverse()
        sell.reverse()

    _T = list_split(T,6)
    _buy = list_split(buy,6)
    _sell = list_split(sell,6)

    dataList = []
    xtime = []
    min_buy = []
    avg_sell = []
    for i in range(len(_sell)):

        O = _sell[i][0]
        H = max(_sell[i])
        L = min(_sell[i])
        C = _sell[i][-1]

        dataList.append((i,O,H,L,C))
        xtime.append(_T[i][0])
        min_buy.append(min(_buy[i]))
        avg_sell.append(sum(_sell[i])/len(_sell[i]))

    fig, ax = plt.subplots(figsize = (16,9),dpi = 100)
    plt.xticks(range(len(dataList)),xtime,rotation=30)
    plt.plot(xtime, min_buy, c = 'darkblue', linestyle = '-')
    plt.plot(xtime, avg_sell, c = 'black', linestyle = '-')
    candlestick_ohlc(ax, dataList, width = 0.4, colorup = 'red', colordown = 'limegreen', alpha = 1)
    plt.title(title, fontproperties=font)
    plt.grid(True, linestyle='--', alpha=0.3)
    output = BytesIO()
    plt.savefig(output)
    return output