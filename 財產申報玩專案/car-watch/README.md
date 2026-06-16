# 🚗 民代車庫

台灣公職人員每年依法申報財產，範圍包含本人及配偶名下車輛。本專案將 677 位立委與縣市議員的申報資料整理成互動式網站，讓公民一眼看出：你選的人，開什麼車？

## 功能

| 頁面 | 說明 |
|------|------|
| 🏆 品牌排行榜 | 995 台申報車輛的品牌分布，Toyota 遙遙領先 |
| 🗺️ 農村才是豪車天堂 | 各縣市豪車率排行，雲林縣逾 50% |
| 🏎️ 超跑名人堂 | 申報 Ferrari、Lamborghini、McLaren、Bentley 等超跑的民代 |
| 🔍 查你的民代 | 依縣市 / 政黨 / 姓名搜尋，看特定民代家有哪些車 |
| 🌱 Tesla 與環保 | 哪些民代家有 Tesla，黨籍與縣市分布 |
| 🅿️ 政黨停車場 | 各黨豪車率與品牌偏好比較 |
| 👥 性別分析 | 男女民代的車型與豪車率是否有差異 |
| 💰 最貴車庫排行 | 申報車輛總價加總，彰化縣議員黃正盛近 3,200 萬元 |

## 資料說明

- **來源**：廉政專刊財產申報公開資料
- **範圍**：立法委員、縣市議員、議長、副議長
- **申報規定**：依法涵蓋本人及配偶財產，每位民代的車輛資料反映整個家庭的申報車輛
- **價格說明**：依法規定，取得超過五年的車輛不需申報價格（約 43% 的車填「超過五年」）。系統已嘗試從歷史申報記錄回溯原始購買價格，成功回溯者標有 ✱ 符號
- **豪車定義**：Lexus、Benz、BMW、Audi、Porsche、Volvo、Land Rover、MINI、Maserati、Ferrari、Lamborghini、Bentley、McLaren、Jaguar、Rolls-Royce、Acura

## 技術架構

純靜態單頁應用（SPA），無需後端。所有資料 inline 於 `index.html`，可直接開啟瀏覽。

```
data-json-0429/
├── export_cars.py      # 從原始 JSON 匯出 cars_data.json
├── compute_stats.py    # 計算統計資料，輸出 stats.json
└── build_index.py      # 將兩份 JSON inline 成最終 index.html

car-watch/
├── index.html          # 最終輸出，單檔 SPA（約 844 KB）
├── cars_data.json      # 1,424 人的完整車輛資料
└── stats.json          # 預計算統計（品牌榜、縣市率、超跑等）
```

更新資料時依序執行：

```bash
python export_cars.py
python compute_stats.py
python build_index.py
```

## 授權與聲明

資料來源為政府公開資訊，本站僅供公益資訊用途。
