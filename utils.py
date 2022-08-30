from datetime import datetime
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties 
from mplfinance.original_flavor import candlestick_ohlc

from typing import Tuple

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

font = FontProperties(fname = os.path.dirname(__file__) + '/events/fonts/simsun.ttc', size=30)

async def market_linechart(figsize: Tuple[int,int], market_history:list, title:str) -> BytesIO:
    """
    生成股价折线图（120）
    :param figsize: 图片尺寸
    :param market_history: 历史数据
    :param title: 标题
    """
    N = len(market_history) if len(market_history) < 120 else 120
    buy = []
    sell = []
    T = []
    for i in range(N):
        T.append(datetime.fromtimestamp(market_history[-i-1][0]).strftime("%H:%M"))
        buy.append(market_history[-i-1][1])
        sell.append(market_history[-i-1][2])
    else:
        T.reverse()
        buy.reverse()
        sell.reverse()

    plt.figure(figsize = figsize, dpi = 100)
    plt.plot(T, buy, c = 'darkblue', linestyle = '-')
    plt.plot(T, sell, c = 'black', linestyle = '-')
    plt.xlim((-1,N))
    plt.xticks(rotation = 45)
    plt.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.1)
    plt.title(title, fontproperties = font)
    plt.grid(True, linestyle='-', alpha=0.3)
    output = BytesIO()
    plt.savefig(output)
    return output

async def market_candlestick(figsize: Tuple[int,int],datalenth: int, market_history:list, title:str) -> BytesIO:
    """
    生成股价K线图(60)
    :param figsize: 图片尺寸
    :param datalenth: OHLC采样长度
    :param market_history: 历史数据
    :param title: 标题
    """
    N = len(market_history) if len(market_history) < 60 * datalenth else 60 * datalenth
    buy = []
    sell = []
    T = []
    for i in range(N):
        T.append(datetime.fromtimestamp(market_history[-i-1][0]).strftime("%H:%M"))
        buy.append(market_history[-i-1][1])
        sell.append(market_history[-i-1][2])
    else:
        T.reverse()
        buy.reverse()
        sell.reverse()

    _T = list_split(T,datalenth)
    _buy = list_split(buy,datalenth)
    _sell = list_split(sell,datalenth)

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

    fig, ax = plt.subplots(figsize = figsize, dpi = 100)
    plt.plot(xtime, min_buy, c = 'darkblue', linestyle = '-')
    plt.plot(xtime, avg_sell, c = 'black', linestyle = '-')
    candlestick_ohlc(ax, dataList, width = 0.4, colorup = 'red', colordown = 'limegreen', alpha = 1)
    N = len(dataList)
    plt.xlim((-1,N))
    plt.xticks(range(N), xtime, rotation = 30)
    plt.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.1)
    plt.title(title, fontproperties=font)
    plt.grid(True, linestyle='--', alpha=0.3)
    output = BytesIO()
    plt.savefig(output)
    return output