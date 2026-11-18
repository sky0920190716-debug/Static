# AI SMART TRADER V2.0

繁體中文響應式交易分析 Web App 原型。

## 啟動
Python 3.10+
```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```
瀏覽器開啟 http://127.0.0.1:8000

## V2.0 功能
- 響應式手機／桌面版介面
- 多市場商品清單：貴金屬、台股、美股、ETF、外匯、期貨、加密貨幣
- 1D、4H、1H、30M、15M、5M、1M 多週期分析
- EMA20／50／200、RSI、ATR、候選訊號、ATR 停損與兩段止盈
- 全市場掃描與依評分排序
- 風險計算器（單筆風險預算及停損距離）
- 示範策略回測 API 與前端結果摘要
- 新聞中心明確顯示資料源尚未連接
- API: /api/markets, /api/analyze, /api/scan, /api/backtest, /api/news, /health

## 非常重要
所有行情由 DemoProvider 合成，並非即時行情。回測也只在合成行情上運作，不能用來推論真實勝率或獲利能力。新聞 API 尚未連接。不可用本版本直接交易。

## 正式上線前工作
1. 接入具市場授權的行情服務與 WebSocket。
2. 各商品規格化：交易時段、時區、tick size、合約乘數、點值、幣別、複權與期貨換月。
3. 接入授權新聞與經濟日曆；保存來源 URL、發布時間、時區與商品關聯。
4. 加入真實歷史資料、滑價、費用、樣本外回測、walk-forward 分析。
5. 加入登入、加密金鑰管理、審計紀錄、速率限制與部署監控。
6. 自動下單不在 V2 範圍；未來需券商授權、人工確認、最大曝險限制及緊急停止。

## 專案結構
```
ai_smart_trader_v2/
  app.py
  requirements.txt
  README.md
  static/index.html
```
