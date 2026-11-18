from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime, timezone
import math, random, hashlib

BASE = Path(__file__).parent
app = FastAPI(title="AI SMART TRADER", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

MARKETS = [
    {"symbol":"XAUUSD","name":"黃金","category":"貴金屬","currency":"USD","precision":2},
    {"symbol":"XAGUSD","name":"白銀","category":"貴金屬","currency":"USD","precision":3},
    {"symbol":"0050.TW","name":"元大台灣50","category":"台股 ETF","currency":"TWD","precision":2},
    {"symbol":"0056.TW","name":"元大高股息","category":"台股 ETF","currency":"TWD","precision":2},
    {"symbol":"^TWII","name":"台灣加權指數","category":"台股指數","currency":"TWD","precision":0},
    {"symbol":"AAPL","name":"Apple","category":"美股","currency":"USD","precision":2},
    {"symbol":"NVDA","name":"NVIDIA","category":"美股","currency":"USD","precision":2},
    {"symbol":"MSFT","name":"Microsoft","category":"美股","currency":"USD","precision":2},
    {"symbol":"SPY","name":"S&P 500 ETF","category":"美股 ETF","currency":"USD","precision":2},
    {"symbol":"QQQ","name":"Nasdaq 100 ETF","category":"美股 ETF","currency":"USD","precision":2},
    {"symbol":"EURUSD","name":"歐元／美元","category":"外匯","currency":"USD","precision":5},
    {"symbol":"USDJPY","name":"美元／日圓","category":"外匯","currency":"JPY","precision":3},
    {"symbol":"AUDUSD","name":"澳幣／美元","category":"外匯","currency":"USD","precision":5},
    {"symbol":"ES=F","name":"E-mini S&P 500","category":"期貨","currency":"USD","precision":2},
    {"symbol":"NQ=F","name":"E-mini Nasdaq 100","category":"期貨","currency":"USD","precision":2},
    {"symbol":"CL=F","name":"WTI 原油","category":"商品期貨","currency":"USD","precision":2},
    {"symbol":"BTC-USD","name":"Bitcoin","category":"加密貨幣","currency":"USD","precision":1},
    {"symbol":"ETH-USD","name":"Ethereum","category":"加密貨幣","currency":"USD","precision":2},
    {"symbol":"SOL-USD","name":"Solana","category":"加密貨幣","currency":"USD","precision":2},
]
FRAMES = ["1D","4H","1H","30M","15M","5M","1M"]
BASE_PRICE = {"XAUUSD":2350,"XAGUSD":28,"0050.TW":180,"0056.TW":38,"^TWII":22000,
"AAPL":220,"NVDA":140,"MSFT":420,"SPY":600,"QQQ":520,"EURUSD":1.08,"USDJPY":150,
"AUDUSD":.65,"ES=F":6000,"NQ=F":21000,"CL=F":70,"BTC-USD":95000,"ETH-USD":3500,"SOL-USD":180}

class DemoProvider:
    """可替換成有授權的即時行情供應商；目前明確標示為模擬行情。"""
    def candles(self, symbol, timeframe, limit=220):
        seed = int(hashlib.sha256(f"{symbol}:{timeframe}".encode()).hexdigest()[:8],16)
        rng = random.Random(seed)
        p = BASE_PRICE.get(symbol,100)
        vol = .0018 if p > 100 else .0028
        if symbol in ("BTC-USD","ETH-USD","SOL-USD"): vol=.008
        if symbol in ("XAUUSD","XAGUSD","CL=F"): vol=.0035
        out=[]
        for i in range(limit):
            drift = math.sin(i/17)*vol*.12 + (0.00012 if i%61<32 else -0.00010)
            o=p; c=max(.000001,p*(1+rng.gauss(drift,vol)))
            h=max(o,c)*(1+abs(rng.gauss(0,vol*.35)))
            l=min(o,c)*(1-abs(rng.gauss(0,vol*.35)))
            out.append({"time":i,"open":o,"high":h,"low":l,"close":c,"volume":rng.uniform(100,10000)})
            p=c
        return out

provider=DemoProvider()

def ema(v,n):
    if not v:return []
    k=2/(n+1); out=[v[0]]
    for x in v[1:]:out.append(x*k+out[-1]*(1-k))
    return out

def rsi(v,n=14):
    if len(v)<n+1:return 50.0
    ds=[v[i]-v[i-1] for i in range(1,len(v))]
    gains=[max(x,0) for x in ds]; losses=[max(-x,0) for x in ds]
    ag=sum(gains[:n])/n; al=sum(losses[:n])/n
    for i in range(n,len(ds)):
        ag=(ag*(n-1)+gains[i])/n; al=(al*(n-1)+losses[i])/n
    if al==0:return 100.0
    return 100-100/(1+ag/al)

def atr(cs,n=14):
    tr=[]
    for i,c in enumerate(cs):
        prev=cs[i-1]["close"] if i else c["close"]
        tr.append(max(c["high"]-c["low"],abs(c["high"]-prev),abs(c["low"]-prev)))
    return sum(tr[-n:])/min(n,len(tr))

def analyze(symbol, timeframe):
    cs=provider.candles(symbol,timeframe)
    cl=[x["close"] for x in cs]
    e20,e50,e200=ema(cl,20),ema(cl,50),ema(cl,200)
    rv, av = rsi(cl), atr(cs)
    price=cl[-1]
    trend = "多頭" if e20[-1]>e50[-1] and price>e200[-1] else "空頭" if e20[-1]<e50[-1] and price<e200[-1] else "盤整"
    score=0; reasons=[]
    if e20[-1]>e50[-1]: score+=25; reasons.append("EMA20 高於 EMA50")
    else: reasons.append("EMA20 未高於 EMA50")
    if price>e200[-1]: score+=20; reasons.append("價格位於 EMA200 上方")
    else: reasons.append("價格位於 EMA200 下方")
    if 50<rv<68: score+=20; reasons.append("RSI 動能偏多且未明顯過熱")
    elif 32<rv<50: score+=20; reasons.append("RSI 動能偏空且未明顯超賣")
    else: reasons.append("RSI 位於中性或極端區域")
    slope_up=e20[-1]>e20[-6]
    if slope_up: score+=15; reasons.append("短期 EMA 斜率向上")
    else: reasons.append("短期 EMA 斜率向下")
    # Momentum confirmation: last close relative to previous 5 bars.
    momentum_up=cl[-1]>cl[-5]
    if momentum_up: score+=20; reasons.append("近端價格動能向上")
    else: reasons.append("近端價格動能向下")
    signal="WAIT"
    if trend=="多頭" and 50<rv<68 and slope_up and momentum_up: signal="BUY"
    elif trend=="空頭" and 32<rv<50 and not slope_up and not momentum_up: signal="SELL"
    # A signal is a candidate only, never an order.
    stop_dist=max(av*1.5,price*.001)
    entry=price
    stop=entry-stop_dist if signal=="BUY" else entry+stop_dist if signal=="SELL" else None
    tp1=entry+stop_dist*1.5 if signal=="BUY" else entry-stop_dist*1.5 if signal=="SELL" else None
    tp2=entry+stop_dist*2.5 if signal=="BUY" else entry-stop_dist*2.5 if signal=="SELL" else None
    if signal=="WAIT": reasons.append("完整條件尚未同時成立，建議等待")
    return {"symbol":symbol,"timeframe":timeframe,"trend":trend,"signal":signal,"score":score,
            "price":price,"rsi":round(rv,2),"atr":av,"ema20":e20[-1],"ema50":e50[-1],
            "ema200":e200[-1],"entry":entry if signal!="WAIT" else None,"stop":stop,"tp1":tp1,"tp2":tp2,
            "rr":"1:1.5 / 1:2.5" if signal!="WAIT" else None,"reasons":reasons,
            "candles":cs[-100:],"data_mode":"DEMO","updated_at":datetime.now(timezone.utc).isoformat()}

@app.get("/",response_class=HTMLResponse)
def home(): return (BASE/"static"/"index.html").read_text(encoding="utf-8")

@app.get("/api/markets")
def markets(): return MARKETS

@app.get("/api/analyze")
def api_analyze(symbol:str=Query("XAUUSD"),timeframe:str=Query("15M")):
    if symbol not in BASE_PRICE:return {"error":"unknown symbol"}
    if timeframe not in FRAMES: timeframe="15M"
    return analyze(symbol,timeframe)

@app.get("/api/scan")
def scan(timeframe:str=Query("15M")):
    if timeframe not in FRAMES: timeframe="15M"
    results=[]
    for m in MARKETS:
        a=analyze(m["symbol"],timeframe)
        results.append({k:a[k] for k in ("symbol","trend","signal","score","price","rsi")})
    results.sort(key=lambda x:(x["signal"]!="WAIT",x["score"]),reverse=True)
    return {"timeframe":timeframe,"mode":"DEMO","results":results}

@app.get("/api/news")
def news():
    return {"mode":"NOT_CONNECTED","items":[
      {"title":"即時新聞尚未連接","detail":"正式版需接入有授權的財經新聞與經濟日曆資料源。","impact":"未評估"},
      {"title":"重大經濟事件監控待啟用","detail":"預計追蹤 CPI、PCE、非農、FOMC、央行利率決策與地緣政治事件。","impact":"未評估"}
    ]}

@app.get("/api/backtest")
def backtest(symbol:str=Query("XAUUSD"),timeframe:str=Query("15M"),risk_pct:float=Query(1.0,ge=.1,le=5)):
    # Transparent educational walk-forward toy backtest on generated candles.
    cs=provider.candles(symbol,timeframe,500)
    wins=losses=0; trades=0; equity=100.0; peak=100.0; maxdd=0.0
    closes=[c["close"] for c in cs]
    for i in range(210,len(cs)-3):
        hist=closes[:i+1]; e20=ema(hist,20)[-1]; e50=ema(hist,50)[-1]
        rv=rsi(hist); e20prev=ema(hist[:-5],20)[-1] if len(hist)>205 else e20
        direction=1 if e20>e50 and 50<rv<68 and e20>e20prev else -1 if e20<e50 and 32<rv<50 and e20<e20prev else 0
        if not direction: continue
        entry=closes[i]; vol=atr(cs[:i+1]); stop=max(vol*1.5,entry*.001)
        outcome=None
        for future in cs[i+1:i+4]:
            if direction==1:
                if future["low"]<=entry-stop: outcome=-1; break
                if future["high"]>=entry+stop*1.5: outcome=1.5; break
            else:
                if future["high"]>=entry+stop: outcome=-1; break
                if future["low"]<=entry-stop*1.5: outcome=1.5; break
        if outcome is None: continue
        trades+=1
        if outcome>0:wins+=1
        else:losses+=1
        equity*=1+(risk_pct/100)*outcome
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak*100)
    return {"symbol":symbol,"timeframe":timeframe,"trades":trades,"wins":wins,"losses":losses,
            "win_rate":round(wins/trades*100,1) if trades else None,"ending_index":round(equity,2),
            "max_drawdown_pct":round(maxdd,2),"mode":"DEMO_SYNTHETIC",
            "note":"僅為合成資料上的示範回測，不代表真實市場績效；未納入完整手續費、滑價、融資成本及市場微結構。"}

@app.get("/health")
def health():return {"status":"ok","version":"2.0.0","data_mode":"DEMO"}
