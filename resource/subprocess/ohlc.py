from typing import Tuple
from pathlib import Path

import mplfinance as mpf
import pandas as pd

import sys
import time
from datetime import datetime

try:
    import ujson as json
except ModuleNotFoundError:
    import json

def market_candlestick(figsize:Tuple[int,int], length:int, history:list, savefig):
    """
    生成股价K线图
        figsize:图片尺寸
        length:OHLC采样长度
        history:历史数据
        title:标题
    """
    T, buy, sell = zip(*history)
    l = len(T)
    T = [T[i:i+length] for i in range(0, l, length)]
    buy = [buy[i:i+length] for i in range(0, l, length)]
    sell = [sell[i:i+length] for i in range(0, l, length)]
    D,O,H,L,C = [],[],[],[],[]
    for i in range(len(sell)):
        D.append(pd.to_datetime(T[i][0], unit = 's'))
        O.append(sell[i][0])
        H.append(max(sell[i]))
        L.append(min(sell[i]))
        C.append(sell[i][-1])

    data = pd.DataFrame({'date': D,'open': O,'high': H,'low': L,'close': C})
    data = data.set_index('date')
    style = mpf.make_mpf_style(
        base_mpf_style = "charles",
        marketcolors = mpf.make_marketcolors(
            up = "#a02128",
            down = "#006340",
            edge = "none"
            ),
        y_on_right = False,
        facecolor = "#FFFFFF99",
        figcolor = "none",
        )
    mpf.plot(
        data,
        type = 'candlestick',
        xlabel = "",
        ylabel = "",
        datetime_format = '%H:%M',
        timezone = datetime.now().astimezone().tzinfo,
        tight_layout = True,
        style = style,
        figsize = figsize,
        savefig = savefig
        )

if __name__ == "__main__":
    russian_path = Path(sys.argv[1])
    company_id = sys.argv[2]
    candlestick_cache = russian_path / "candlestick"
    candlestick_cache.mkdir(parents = True, exist_ok = True)
    candlestick = Path(candlestick_cache / f"{company_id}.png")
    if candlestick.exists() and time.time() - candlestick.stat().st_ctime < 600:
        sys.exit(0)
    history_file = russian_path / "market_history.json"
    with open(history_file, "r", encoding="utf8") as f:
        market_history = json.load(f)
    market_candlestick((9.5,3), 12, market_history[company_id], candlestick_cache / f"{company_id}.png")