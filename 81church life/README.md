# 81 召會出席統計系統

每週統計 8 個小區的 6 項出席資料（主日、小排、晨興、禱告、出訪、受訪），自動產出 dashboard 網站 + LINE Bot 智能查詢。

**部署網址**：<https://kanforchlf-ai.github.io/81Y3-dashboard/>

---

## 專案結構

```
81church life/
├── 即時更新/                  # 每週新資料放這裡（gitignored）
│   ├── 主日最新.xls
│   ├── 小排最新.xls
│   ├── 晨興最新.xls
│   ├── 禱告最新.xls
│   ├── 出訪最新.xls
│   └── 受訪最新.xls
├── 歷史資料/                  # 累積歷史 + 名冊（gitignored）
│   ├── 81名單.csv             # 全員名冊（姓名/性別/小區/...）
│   ├── 81名單.bak.csv         # 自動補登前的備份
│   ├── 主日.csv / .xls        # 累積歷史
│   ├── 小排.csv / .xls
│   ├── 晨興.csv / .xls
│   ├── 禱告.csv / .xls
│   └── 81主日歷史資料.xls
├── update_dashboard.py        # 主腳本：讀 xls → 產生 20 個 HTML
├── sync_from_gsheet.py        # 從 Google Sheet 同步小區名單回 81名單.csv
├── deploy.sh                  # 一鍵：跑更新 + push 部署/備份 repo
├── snapshot.json              # 上次更新的週次 + 成員快照（偵測變動用）
├── valid_members.json         # 有效成員清單（LINE Bot 用）
├── 81Y3-dashboard/            # 部署 repo（獨立 git → kanforchlf-ai/81Y3-dashboard）
│   ├── index.html             # 首頁（總覽）
│   ├── weekly.html            # 本週點名（全員出席狀態）
│   ├── trend.html             # 出席趨勢
│   ├── leaderboard.html       # 排行榜
│   ├── invite.html            # 全會所挽回名單
│   ├── progress.html          # 月度進度
│   ├── cowork.html            # 配搭出席總覽
│   ├── guide.html             # 系統說明
│   ├── youth.html / hs.html / ms.html  # 三大群組頁
│   ├── y1, y2, y3/            # 青年三區（each: index.html + invite.html + json）
│   ├── hs1, hs2, hs3/         # 高中三區
│   ├── ms1, ms2/              # 國中兩區
│   ├── kids/                  # 兒童專區（12 歲以下）
│   ├── theme.css
│   ├── bot_server.py          # LINE Bot 伺服器
│   ├── dashboard_rag.py       # RAG（讀 dashboard 資料）
│   ├── Dockerfile             # LINE Bot 容器化
│   └── LINE_BOT_README.md     # LINE Bot 詳細說明
└── 81會所出席統計系統*.docx/.pptx  # 系統介紹講稿/簡報
```

---

## 每週工作流（標準三步驟）

### 1. 從教會系統匯出 6 個 xls

每週日聚會後，從教會內部系統匯出本週 6 個 xls，覆蓋到 `即時更新/`：

```
主日最新.xls  小排最新.xls  晨興最新.xls
禱告最新.xls  出訪最新.xls  受訪最新.xls
```

### 2. 同步小區名單（如有變動）

各小區用 Google Sheet 線上維護名單，Sheet ID：`1Dqaa1twL56c0yDqSVnOWwq856E6RF3TUfjf8_fUwQHI`（8 個分頁對應 8 區）。

```bash
python sync_from_gsheet.py
```

會把 8 區填寫合併寫回 `歷史資料/81名單.csv`。

### 3. 一鍵部署

```bash
./deploy.sh
```

`deploy.sh` 自動執行：

1. **跑 `update_dashboard.py`**：讀 6 個 xls → 重建 20 個 HTML。出現在出席資料但不在名單的人會自動補登到 `81名單.csv`（身分/性別留空），原檔備份為 `81名單.bak.csv`。輸出 `🆕 自動補登 X 位` 是預期行為。
2. **推部署 repo**：`cd 81Y3-dashboard && git push` → `kanforchlf-ai/81Y3-dashboard`（GitHub Pages 1-2 分鐘後更新網站）
3. **推備份 repo**：外層 push → `jameskan-TW/james-claude-project`

無變動則跳過該步驟。

---

## 主要產出（20 個 HTML）

| 範圍       | 檔案                                                           | 內容                       |
| ---------- | -------------------------------------------------------------- | -------------------------- |
| 全會所     | `index.html`                                                   | 首頁總覽                   |
| 全會所     | `weekly.html`                                                  | 本週點名（全員出席狀態）   |
| 全會所     | `cowork.html`                                                  | 配搭出席總覽（核心成員）   |
| 全會所     | `trend.html`                                                   | 多週出席趨勢               |
| 全會所     | `invite.html`                                                  | 全會所挽回 + 不規律名單    |
| 全會所     | `leaderboard.html` / `progress.html` / `guide.html` / `kids/`  | 排行榜 / 月度進度 / 說明 / 兒童 |
| 各小區     | `<zone>/index.html`                                            | 該區出席狀態（8 區）        |
| 各小區     | `<zone>/invite.html`                                           | 該區挽回名單（8 區）        |

---

## 系統設定

| 設定項         | 值                                                                |
| -------------- | ----------------------------------------------------------------- |
| 8 區基數       | y1=20, y2=23, y3=26 / hs1=18, hs2=20, hs3=11 / ms1=56, ms2=49     |
| 兒童專區       | 12 歲以下，獨立呈現於 `kids/`                                       |
| 活動權重       | 主日 = 3，小排/晨興/禱告/出訪/受訪 = 1                              |
| 召會生活指標   | 小排 + 晨興 + 禱告 + 出訪 + 受訪（不含主日）                        |

---

## LINE Bot

`81Y3-dashboard/bot_server.py` 是基於 dashboard 資料 + Google Gemini 的智能查詢 Bot，部署在 Render。詳見 [`81Y3-dashboard/LINE_BOT_README.md`](81Y3-dashboard/LINE_BOT_README.md)。

範例查詢：

```
81人數助理 青年一區有多少人？
81人數助理 最近幾週主日出席趨勢如何？
81人數助理 誰的出席率最高？
```

---

## 注意事項

### Excel COM（Windows）

`update_dashboard.py` 用 `win32com.client.DispatchEx('Excel.Application')` 讀 xls（**不是** `Dispatch`），確保每個檔案都用全新 Excel instance。否則連讀 6 個檔案時，下一個 `Dispatch` 可能接到還在 Quit 中的同一個 Excel，報 `OLE error 0x800a01a8` 或 `AttributeError: Excel.Application.Workbooks`。

殘留 Excel/Python 程序卡住時：

```bash
taskkill //F //IM EXCEL.EXE
```

### Worktree 限制

`81Y3-dashboard/` 是獨立 git 子 repo，**不會**跟著 git worktree 複製。在 worktree 裡執行 `deploy.sh` 步驟 2 會誤推到外層 repo 的 worktree branch。**deploy.sh 一律在主目錄跑**：

```bash
cd "C:/Users/james/OneDrive/Desktop/Claude-workspace/projects/81church life" && ./deploy.sh
```

---

## 雜項腳本（平常用不到）

| 腳本                                                          | 用途                            |
| ------------------------------------------------------------- | ------------------------------- |
| `add_care.py` / `update_care.py` / `update_care2.py`          | 關懷頁批次改動（一次性）          |
| `add_cowork.py` / `fix_cowork.py` / `fix_cowork2.py`          | 配搭頁批次改動（一次性）          |
| `add_guide.py` / `add_modal.py` / `fix_modal_kids.py`         | 說明頁/彈窗批次改動（一次性）      |
| `build_progress_page.py` / `update_hero.py`                   | 月度進度頁/首頁建構（已整合）      |
| `fix_trend_gender.py` / `fix_trend_history.py`                | trend.html 歷史修補（一次性）     |
| `restore_member_data.py`                                      | 還原成員資料                    |
| `patch_theme.py`                                              | 批次套用 `theme.css` 到所有 HTML |
| `make_pptx.js` / `make_docx_script.js`                        | 產生系統介紹簡報 / 講稿          |
| `trial_y3.py`                                                 | y3 區試算腳本                   |
