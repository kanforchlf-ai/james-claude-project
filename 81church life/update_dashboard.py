#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
81Y3 Dashboard 週更新腳本
------------------------------------------------------------
用法：
  python update_dashboard.py

每週把新的 CSV 放到「即時更新」資料夾後執行此腳本，
自動更新所有 HTML 檔案（共 19 個）。

CSV 命名規則（資料夾：即時更新/）：
  主日最新.csv  小排最新.csv  晨興最新.csv  禱告最新.csv
------------------------------------------------------------
"""

import csv, json, re, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ============================================================
# 設定
# ============================================================

BASE        = Path(__file__).parent
CSV_DIR     = BASE / '即時更新'
DASH        = BASE / '81Y3-dashboard'

ACTS         = ['主日', '小排', '晨興', '禱告', '出訪', '受訪']
ACT_WEIGHT   = {'主日': 3, '小排': 1, '晨興': 1, '禱告': 1, '出訪': 1, '受訪': 1}
# 召會生活指標：主日以外的「參與型」活動（weekly.html 的 extra 區塊 + churchLifeCount 用）
CHURCH_LIFE_ACTS = ['小排', '晨興', '禱告', '出訪', '受訪']

# 各小區固定基數
BASE_SIZE = {
    'y1': 20, 'y2': 23, 'y3': 26,
    'hs1': 18, 'hs2': 20, 'hs3': 11,
    'ms1': 56, 'ms2': 49,
}

SUBZONE_MAP = {
    '青年一區': 'y1', '青年二區': 'y2', '青年三區': 'y3',
    '高中一區': 'hs1', '高中二區': 'hs2', '高中三區': 'hs3',
    '國中一區': 'ms1', '國中二區': 'ms2',
}
DK_NAME = {v: k for k, v in SUBZONE_MAP.items()}

DK_GROUP = {
    'y1': 'youth', 'y2': 'youth', 'y3': 'youth',
    'hs1': 'hs', 'hs2': 'hs', 'hs3': 'hs',
    'ms1': 'ms', 'ms2': 'ms',
}

# 兒童群組（12歲以下）
KIDS_GROUPS = {'學齡前', '小學'}

# 各小區配搭名單
COWORKERS_MAP = {
    'y1':  ['張鈞哲','廖健智','黃珮甄','鍾安怡','石真','鍾歆','塗家柔','蔡宜薰','鍾愛','王晨瑄'],
    'y2':  ['吳秉祈','史以凡','董宜睿','冉以琳','張詠恩','吳貞儀','陳聿新','陳家潔'],
    'y3':  ['彭柏愷','甘順基','沈以恩','朱璟軒','林書丞','王新恩','張若筠','吳汶靜','呂柔蒨','葉倢妤','戴采薰'],
    'hs1': ['石錄','吳均平','陳昱廷','吳秉佳','張韶謙'],
    'hs2': ['張宏恩','陳柏安','呂德鈞','方厚民','黃梓昀'],
    'hs3': ['蔡溢恩','黃梓恆','趙心樂','陸佳依'],
    'ms1': ['雷嗣益','呂德安','黃主業','陳信維','張怡東','于詮暐','吳均和','戴昀庭','簡若安','程琳','汪佩蒂','陳道璇','楊媃伊'],
    'ms2': ['呂士成','鍾禹鋒','程旭弘','江成聖','吳宇星','陸承光','許憶棻','戴采寧','廖智柔','莊丹萱','顏惟聆','強承安','廖宜人'],
}

DK_TITLE = {
    'y1':'青一', 'y2':'青二', 'y3':'青三',
    'hs1':'高一', 'hs2':'高二', 'hs3':'高三',
    'ms1':'國一', 'ms2':'國二',
}

GROUP_TITLE = {
    'youth': ('⚡', '青年大區', '#7c3aed'),
    'hs':    ('🔥', '高中大區', '#d97706'),
    'ms':    ('🌱', '國中大區', '#059669'),
}

GROUP_DKS = {
    'youth': ['y1','y2','y3'],
    'hs':    ['hs1','hs2','hs3'],
    'ms':    ['ms1','ms2'],
}

# CSV 欄位 (0-indexed)
COL_ZONE, COL_SUB, COL_PAI, COL_NAME, COL_GROUP = 0, 1, 2, 3, 5
COL_START = 8   # 第一個週次欄

# TREND_DATA 各組合
SEGMENTS = [
    'all', 'male', 'female',
    'daxue', 'qingzhi', 'zhongxue', 'xiaoxue', 'qingzhuang',
    'male_daxue', 'male_qingzhi', 'male_zhongxue', 'male_xiaoxue', 'male_qingzhuang',
    'female_daxue', 'female_qingzhi', 'female_zhongxue', 'female_xiaoxue', 'female_qingzhuang',
]

# 群組 → 'a' 編碼
GROUP_TO_A = {
    '大專': 'd',
    '青職': 'q',
    '中學': 'z',
    '小學': 'e',
    '青壯': 'o',
}

DK_TO_SUBS = {
    'y1': ['y1'], 'y2': ['y2'], 'y3': ['y3'],
    'hs1': ['hs1'], 'hs2': ['hs2'], 'hs3': ['hs3'],
    'ms1': ['ms1'], 'ms2': ['ms2'],
    'youth': ['y1', 'y2', 'y3'],
    'hs':    ['hs1', 'hs2', 'hs3'],
    'ms':    ['ms1', 'ms2'],
    'church': ['y1', 'y2', 'y3', 'hs1', 'hs2', 'hs3', 'ms1', 'ms2'],
}

# CSV 週次標籤 → WEEK_META label 轉換
# '3月第一週' → month='3月', label='W1'
WEEK_NUM_MAP = {'第一週': 'W1', '第二週': 'W2', '第三週': 'W3',
                '第四週': 'W4', '第五週': 'W5'}

# 週次標籤 → 主日日期（每週主日，格式 M/D）
# 腳本依此計算 weekly.html 的日期範圍 header
KNOWN_DATES = {
    ('3月', 'W1'): '3/2',  ('3月', 'W2'): '3/9',  ('3月', 'W3'): '3/16',
    ('3月', 'W4'): '3/23', ('3月', 'W5'): '3/30',
    ('4月', 'W1'): '4/6',  ('4月', 'W2'): '4/13', ('4月', 'W3'): '4/20',
    ('4月', 'W4'): '4/27',
    ('5月', 'W1'): '5/4',  ('5月', 'W2'): '5/11', ('5月', 'W3'): '5/18',
    ('5月', 'W4'): '5/25',
}

def week_date_range(month_str, label_str):
    """
    計算 weekly.html 的日期 header。
    輸入：month='4月', label='W2'
    回傳：('2026年4月7日 ～ 4月13日', '第15週')
    """
    date_str = KNOWN_DATES.get((month_str, label_str))
    if not date_str:
        return f'2026年{month_str}（{label_str}）', ''
    m, d = map(int, date_str.split('/'))
    end   = datetime(2026, m, d)
    start = end - timedelta(days=6)
    iso_week = end.isocalendar()[1]  # ISO 週次

    def fmt(dt):
        if dt.month == end.month:
            return f'{dt.month}月{dt.day}日'
        return f'{dt.month}月{dt.day}日'

    if start.month == end.month:
        range_str = f'2026年{start.month}月{start.day}日 ～ {end.day}日'
    else:
        range_str = f'2026年{start.month}月{start.day}日 ～ {end.month}月{end.day}日'

    return range_str, f'第{iso_week}週'


# ============================================================
# 讀取 CSV
# ============================================================

def read_csv(path):
    """讀取 CSV 或 Excel（.xlsx/.xls），統一回傳 list[list[str]]"""
    path = Path(path).resolve()
    if path.suffix.lower() in ('.xlsx', '.xls'):
        return _read_excel_via_com(path)
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def _read_excel_via_com(path):
    """讀取 .xls/.xlsx，轉成 list[list[str]]"""
    suffix = Path(path).suffix.lower()
    if suffix == '.xls':
        return _read_xls(path)
    return _read_xlsx(path)


def _read_xls(path):
    """用 Excel COM 讀取 .xls"""
    import win32com.client, pythoncom
    pythoncom.CoInitialize()
    xl = win32com.client.Dispatch('Excel.Application')
    try:
        xl.Visible = False
    except Exception:
        pass
    try:
        xl.DisplayAlerts = False
    except Exception:
        pass
    try:
        wb = xl.Workbooks.Open(str(path))
        ws = wb.ActiveSheet
        used = ws.UsedRange
        rows = []
        for r in range(1, used.Rows.Count + 1):
            row = []
            for c in range(1, used.Columns.Count + 1):
                v = used.Cells(r, c).Value
                if v is None:
                    row.append('')
                elif isinstance(v, float) and v == int(v):
                    row.append(str(int(v)))
                else:
                    row.append(str(v).strip())
            rows.append(row)
        wb.Close(False)
        return rows
    finally:
        try:
            xl.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


def _read_xlsx(path):
    """用 openpyxl 讀取 .xlsx"""
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        r = []
        for v in row:
            if v is None:
                r.append('')
            elif isinstance(v, float) and v == int(v):
                r.append(str(int(v)))
            else:
                r.append(str(v).strip())
        rows.append(r)
    wb.close()
    return rows


def get_week_meta(rows):
    """
    從 Row 0（月份標題）+ Row 1（週次標題）建立週次清單。
    回傳: [(col_idx, csv_label), ...]
    csv_label 格式：'3月第一週'
    """
    r0, r1 = rows[0], rows[1]
    month = None
    result = []
    for i in range(COL_START, max(len(r0), len(r1))):
        if i < len(r0) and r0[i].strip():
            m = re.search(r'(\d+)月', r0[i])
            if m:
                month = m.group(1) + '月'
        if month and i < len(r1) and r1[i].strip():
            result.append((i, month + r1[i].strip()))
    return result


def get_active_weeks(rows, week_meta):
    """只回傳有至少一筆 '1' 的週次。"""
    return [
        (col, lbl) for col, lbl in week_meta
        if any(
            len(row) > col and row[col] == '1'
            for row in rows[2:]
        )
    ]


def csv_label_to_trend(csv_lbl):
    """'3月第一週' → (month='3月', label='W1')"""
    m = re.match(r'(\d+月)(第.週)', csv_lbl)
    if m:
        return m.group(1), WEEK_NUM_MAP.get(m.group(2), m.group(2))
    return None, None


# ============================================================
# 建立成員字典
# ============================================================

def build_member_dict(csvs):
    """
    回傳:
      members    : {dk: {name: {pai, group, 主日:{label:0/1}, 小排:..., ...}}}
      week_meta  : [(col, csv_label), ...]
      active_weeks: [(col, csv_label), ...]  (有資料的週次)
    """
    sunday_rows  = csvs['主日']
    week_meta    = get_week_meta(sunday_rows)
    active_weeks = get_active_weeks(sunday_rows, week_meta)

    members = defaultdict(lambda: defaultdict(dict))

    for act, rows in csvs.items():
        wm         = get_week_meta(rows)
        label_to_col = {lbl: col for col, lbl in wm}

        for row in rows[2:]:
            if len(row) < 6:
                continue
            subzone = row[COL_SUB].strip()
            dk = SUBZONE_MAP.get(subzone)
            if not dk:
                continue
            name = row[COL_NAME].strip()
            if not name:
                continue

            m = members[dk][name]
            if 'pai' not in m:
                m['pai']   = row[COL_PAI].strip()
                m['group'] = row[COL_GROUP].strip()

            m[act] = {}
            for col, lbl in active_weeks:
                c   = label_to_col.get(lbl)
                val = 0
                if c is not None and len(row) > c and row[c] in ('0', '1'):
                    val = int(row[c])
                m[act][lbl] = val

    # 用 81名單.csv 的群組欄覆寫，確保與主名單同步
    roster_path = BASE / '歷史資料' / '81名單.csv'
    if roster_path.exists():
        with open(roster_path, encoding='utf-8-sig', newline='') as f:
            for row in csv.reader(f):
                if len(row) < 11:
                    continue
                name  = row[0].strip()
                group = row[10].strip()   # 群組欄（第11欄）
                if not name or not group:
                    continue
                for dk_members in members.values():
                    if name in dk_members:
                        dk_members[name]['group'] = group

    return members, week_meta, active_weeks


# ============================================================
# 工具函數
# ============================================================

def historical_rate(vals):
    """Float 0..1，保留 4 位小數。"""
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 4)


def get_window(m, act, labels):
    return [m.get(act, {}).get(lbl, 0) for lbl in labels]


def compute_flags(activities, recent_labels):
    """歷史出席率 ≥ 50% 但該週為 0 → 疑似漏填。"""
    flags = []
    for act in ACTS:
        info = activities[act]
        if info['historical'] >= 0.5:
            for i, v in enumerate(info['march']):
                if v == 0:
                    flags.append(act + recent_labels[i])
    return flags


# ============================================================
# 1. 小區出席頁 RAW_DATA（8 個 index.html）
# ============================================================

def build_raw_data(dk, members, active_weeks, n_recent=6):
    recent_labels = [lbl for _, lbl in active_weeks[-n_recent:]]
    result = []

    for name, m in members[dk].items():
        if m.get('group', '') in KIDS_GROUPS:
            continue
        activities = {}
        has_any = False
        for act in ACTS:
            march = get_window(m, act, recent_labels)
            hist  = historical_rate(march)
            if hist > 0 or any(v == 1 for v in march):
                has_any = True
            activities[act] = {
                'historical': hist,
                'march': march,
                'weeks': recent_labels,
            }

        if not has_any:
            continue

        result.append({
            '排':    m['pai'],
            '姓名':  name,
            '羣組':  m['group'],
            'activities': activities,
            'flags': compute_flags(activities, recent_labels),
        })

    return result


# ============================================================
# 2. 排行榜 DATA（8 個 leaderboard.html）
# ============================================================

def build_leaderboard(dk, members, active_weeks, n_board=4):
    board_labels = [lbl for _, lbl in active_weeks[-n_board:]]
    period = f'{board_labels[0]} ～ {board_labels[-1]}'

    rankings = []
    for name, m in members[dk].items():
        if m.get('group', '') in KIDS_GROUPS:
            continue
        breakdown = {}
        score = 0
        any_attended = False
        for act in ACTS:
            vals = get_window(m, act, board_labels)
            pts  = sum(vals) * ACT_WEIGHT[act]
            score += pts
            if any(v == 1 for v in vals):
                any_attended = True
            breakdown[act] = {'weeks': vals, 'points': pts}

        if not any_attended:
            continue

        rankings.append({'姓名': name, 'score': score, 'breakdown': breakdown})

    rankings.sort(key=lambda x: -x['score'])

    rank = 1
    for i, r in enumerate(rankings):
        if i > 0 and r['score'] < rankings[i - 1]['score']:
            rank = i + 1
        r['rank'] = rank

    return {
        'period':    period,
        'max_score': n_board * sum(ACT_WEIGHT.values()),
        'rankings':  rankings,
    }


# ============================================================
# 3. 本週點名 DISTRICTS + MEMBERS（weekly.html）
# ============================================================

def build_weekly(members, active_weeks):
    if not active_weeks:
        print('  ⚠ 沒有有效週次')
        return [], {}

    latest_lbl = active_weeks[-1][1]
    prev_lbls  = [lbl for _, lbl in active_weeks[:-1]]
    recent6    = [lbl for _, lbl in active_weeks[-6:]]

    districts   = []
    all_members = {}

    for dk in ['y1', 'y2', 'y3', 'hs1', 'hs2', 'hs3', 'ms1', 'ms2']:
        dk_m = members[dk]
        # 排除兒童（學齡前/小學）
        adult_m = {n: m for n, m in dk_m.items() if m.get('group', '') not in KIDS_GROUPS}

        # 本週主日出席人數
        attendees = [n for n, m in adult_m.items()
                     if m.get('主日', {}).get(latest_lbl, 0) == 1]
        total = len(attendees)
        base  = BASE_SIZE[dk]
        pct   = round(total / base * 100, 1)

        # 上月平均（前幾週平均）
        if prev_lbls:
            weekly_totals = [
                sum(1 for m in adult_m.values()
                    if m.get('主日', {}).get(lbl, 0) == 1)
                for lbl in prev_lbls
            ]
            march_avg = round(sum(weekly_totals) / len(weekly_totals))
        else:
            march_avg = total

        status = 'ok' if pct >= 70 else 'low'

        # 各排人數
        row_counts = defaultdict(int)
        for n in attendees:
            pai = adult_m[n].get('pai', '') or ''
            row_counts[pai] += 1
        rows = [{'name': k, 'count': v} for k, v in sorted(row_counts.items())]

        # 召會生活（小排/晨興/禱告/出訪/受訪）本週人數
        extra = {
            act: sum(1 for m in adult_m.values()
                     if m.get(act, {}).get(latest_lbl, 0) == 1)
            for act in CHURCH_LIFE_ACTS
        }

        districts.append({
            'id':         dk,
            'name':       DK_NAME[dk],
            'group':      DK_GROUP[dk],
            'total':      total,
            'base':       base,
            'pct':        pct,
            'march_avg':  march_avg,
            'status':     status,
            'rows':       rows,
            'zero_rows':  [],
            'extra':      extra,
        })

        # 成員清單（近 6 週有出席過任一活動的人）
        member_list = []
        for name, m in adult_m.items():
            sunday_window = get_window(m, '主日', recent6)
            combined = []
            for act in ACTS:
                combined += get_window(m, act, recent6)
            if not any(v == 1 for v in combined):
                continue
            hist_pct = round(historical_rate(sunday_window) * 100)
            member_list.append({
                'n':    name,
                'pai':  m.get('pai', ''),
                'hist': hist_pct,
                'a': {act: m.get(act, {}).get(latest_lbl, 0) for act in ACTS},
            })
        all_members[dk] = member_list

    # Header metadata（各區 total 已排除兒童）
    total_all  = sum(d['total'] for d in districts)
    base_all   = sum(d['base']  for d in districts)   # 223，維持架構表基數
    pct_all    = round(total_all / base_all * 100, 1) if base_all else 0
    zero_dks   = sum(1 for d in districts if d['total'] == 0)

    # 日期範圍
    month_str, label_str = csv_label_to_trend(latest_lbl)
    date_range, week_num = week_date_range(month_str or '', label_str or '')

    # footer 短日期（M/D～M/D）
    date_str = KNOWN_DATES.get((month_str, label_str), '')
    if date_str:
        m_end, d_end = map(int, date_str.split('/'))
        end_dt   = datetime(2026, m_end, d_end)
        start_dt = end_dt - timedelta(days=6)
        short_range = f'{start_dt.month}/{start_dt.day}～{end_dt.month}/{end_dt.day}'
    else:
        short_range = latest_lbl

    meta = {
        'date_range':   date_range,
        'week_num':     week_num,
        'total_all':    total_all,
        'base_all':     base_all,
        'pct_all':      pct_all,
        'zero_dks':     zero_dks,
        'short_range':  short_range,
        'latest_lbl':   latest_lbl,
    }

    return districts, all_members, meta


# ============================================================
# 4. 兒童專區 RAW_DATA（kids/index.html）
# ============================================================

def build_kids_raw(members, active_weeks, n_recent=6):
    recent_labels = [lbl for _, lbl in active_weeks[-n_recent:]]
    result = []

    for dk in ['y1', 'y2', 'y3', 'hs1', 'hs2', 'hs3', 'ms1', 'ms2']:
        for name, m in members[dk].items():
            if m.get('group', '') not in KIDS_GROUPS:
                continue

            activities = {}
            has_any = False
            for act in ACTS:
                march = get_window(m, act, recent_labels)
                hist  = historical_rate(march)
                if hist > 0 or any(v == 1 for v in march):
                    has_any = True
                activities[act] = {
                    'historical': hist,
                    'march': march,
                    'weeks': recent_labels,
                }

            if not has_any:
                continue

            result.append({
                '姓名':  name,
                '小區':  DK_NAME[dk],
                'dk':    dk,
                '羣組':  m['group'],
                '排':    m['pai'],
                'activities': activities,
                'flags': compute_flags(activities, recent_labels),
            })

    return result


# ============================================================
# 5. 出席趨勢 WEEK_META + TREND_DATA（trend.html）
# ============================================================

def load_trend_html():
    path = DASH / 'trend.html'
    return open(path, encoding='utf-8').read()


def extract_trend_data(html):
    """從 trend.html 解析 WEEK_META 和 TREND_DATA。"""
    # WEEK_META 用 JS 物件格式（非標準 JSON），需手動轉換
    wm_raw = re.search(r'const WEEK_META\s*=\s*(\[.*?\]);', html, re.DOTALL)
    if not wm_raw:
        raise ValueError('找不到 WEEK_META')
    # 將 JS object 轉換為 JSON（label:'W1' → "label":"W1"）
    js_obj = wm_raw.group(1)
    js_obj = re.sub(r"(\w+):'([^']*)'",   r'"\1":"\2"', js_obj)  # key:'val' → "key":"val"
    js_obj = re.sub(r'(\w+):\s*true\b',   r'"\1":true',  js_obj)
    js_obj = re.sub(r'(\w+):\s*false\b',  r'"\1":false', js_obj)
    js_obj = re.sub(r',\s*([}\]])',        r'\1',         js_obj)  # 移除 trailing comma
    week_meta = json.loads(js_obj)

    td_raw = re.search(r'const TREND_DATA\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not td_raw:
        raise ValueError('找不到 TREND_DATA')
    trend_data = json.loads(td_raw.group(1))

    md_raw = re.search(r'const MEMBER_DATA\s*=\s*(\{.*?\});', html, re.DOTALL)
    member_data = json.loads(md_raw.group(1)) if md_raw else {}

    return week_meta, trend_data, member_data


def load_roster():
    """讀 81名單.csv 回傳 {name: {gender, state, group_zh}}"""
    roster = {}
    path = BASE / '歷史資料' / '81名單.csv'
    if not path.exists():
        return roster
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.reader(f):
            if len(row) < 11 or row[0].strip() == '姓名':
                continue
            name = row[0].strip()
            if not name:
                continue
            roster[name] = {
                'gender': row[1].strip(),
                'state':  row[7].strip(),
                'group':  row[10].strip(),
            }
    return roster


def build_member_data(members, active_weeks, roster, n_recent=12):
    """依規則重建 MEMBER_DATA / BASE_DATA。
    納入條件：
      - 在 81名單.csv 中 狀態=正常
      - 群組非兒童（學齡前/小學）
      - 近 N 週（預設 12 週）內至少一項活動出席過 1 次
    """
    recent_labels = [lbl for _, lbl in active_weeks[-n_recent:]]

    member_data = {}
    base_data   = {}
    for dk in ['y1','y2','y3','hs1','hs2','hs3','ms1','ms2']:
        entries = []
        for name, m in members[dk].items():
            r = roster.get(name)
            if not r or r['state'] != '正常' or r['group'] in KIDS_GROUPS:
                continue
            has_recent = any(
                m.get(act, {}).get(lbl, 0) == 1
                for act in ACTS for lbl in recent_labels
            )
            if not has_recent:
                continue
            a_code = GROUP_TO_A.get(r['group'], 'q')
            entries.append({
                'n': name,
                'g': 'm' if r['gender'] == '男' else 'f',
                'a': a_code,
                'r': r['group'],
            })
        entries.sort(key=lambda e: e['n'])
        member_data[dk] = entries
        # BASE_DATA 維持寫死的 BASE_SIZE（官方登記人數），不跟著 MEMBER_DATA 變動
        base_data[dk] = BASE_SIZE[dk]

    # 群組/大區總和（維持原本寫死的數字：youth=69 hs=49 ms=105 church=223）
    for grp, sub_dks in GROUP_DKS.items():
        base_data[grp] = sum(base_data[d] for d in sub_dks)
    base_data['church'] = sum(base_data[d] for d in ['y1','y2','y3','hs1','hs2','hs3','ms1','ms2'])

    return member_data, base_data


def update_trend(members, active_weeks, html):
    """更新 trend.html 的 WEEK_META、TREND_DATA、MEMBER_DATA、BASE_DATA。"""

    week_meta, trend_data, _old_md = extract_trend_data(html)

    # 重建 MEMBER_DATA / BASE_DATA（使用 81名單.csv + 近 12 週活動紀錄）
    roster = load_roster()
    member_data, base_data = build_member_data(members, active_weeks, roster)

    existing_gender = {}
    member_a = {}
    for dk_list in member_data.values():
        for entry in dk_list:
            existing_gender[entry['n']] = entry['g']
            member_a[entry['n']]       = entry['a']

    def seg_match(name, seg):
        g = existing_gender.get(name)
        a = member_a.get(name)
        if g is None or a is None:
            return False  # 不在 MEMBER_DATA 白名單中，跳過
        if seg == 'all':               return True
        if seg == 'male':              return g == 'm'
        if seg == 'female':            return g == 'f'
        if seg == 'daxue':             return a == 'd'
        if seg == 'qingzhi':           return a == 'q'
        if seg == 'zhongxue':          return a == 'z'
        if seg == 'xiaoxue':           return a == 'e'
        if seg == 'qingzhuang':        return a == 'o'
        if seg == 'male_daxue':        return g == 'm' and a == 'd'
        if seg == 'male_qingzhi':      return g == 'm' and a == 'q'
        if seg == 'male_zhongxue':     return g == 'm' and a == 'z'
        if seg == 'male_xiaoxue':      return g == 'm' and a == 'e'
        if seg == 'male_qingzhuang':   return g == 'm' and a == 'o'
        if seg == 'female_daxue':      return g == 'f' and a == 'd'
        if seg == 'female_qingzhi':    return g == 'f' and a == 'q'
        if seg == 'female_zhongxue':   return g == 'f' and a == 'z'
        if seg == 'female_xiaoxue':    return g == 'f' and a == 'e'
        if seg == 'female_qingzhuang': return g == 'f' and a == 'o'
        return False

    # 建立 WEEK_META index lookup（month+label → index）
    wm_idx = {(w['month'], w['label']): i for i, w in enumerate(week_meta)}
    n_weeks = len(week_meta)

    td_districts = trend_data.get('districts', trend_data)  # 相容兩種格式

    for csv_lbl in [lbl for _, lbl in active_weeks]:
        month, label = csv_label_to_trend(csv_lbl)
        if not month:
            continue

        # 若此週尚未在 WEEK_META，新增它
        if (month, label) not in wm_idx:
            is_first = label == 'W1'
            date_str = KNOWN_DATES.get((month, label), '')
            week_meta.append({
                'label':  label,
                'month':  month,
                'first':  is_first,
                'date':   date_str,
            })
            wm_idx[(month, label)] = n_weeks
            n_weeks += 1
            # 所有 TREND_DATA 陣列補 0
            for dk_key in td_districts:
                for act_key in td_districts[dk_key]:
                    for seg_key in td_districts[dk_key][act_key]:
                        td_districts[dk_key][act_key][seg_key].append(0)
            print(f'  + 新增週次 {month}{label} 至 WEEK_META')

        idx = wm_idx[(month, label)]

        # 計算每個 dk / activity / segment 的出席人數
        for dk_key, sub_dks in DK_TO_SUBS.items():
            if dk_key not in td_districts:
                td_districts[dk_key] = {}
            for act in ACTS:
                if act not in td_districts[dk_key]:
                    td_districts[dk_key][act] = {}
                for seg in SEGMENTS:
                    if seg not in td_districts[dk_key][act]:
                        td_districts[dk_key][act][seg] = [0] * n_weeks

                    cnt = sum(
                        1
                        for sdk in sub_dks
                        for name, m in members[sdk].items()
                        if seg_match(name, seg)
                        and m.get(act, {}).get(csv_lbl, 0) == 1
                    )
                    arr = td_districts[dk_key][act][seg]
                    if idx < len(arr):
                        arr[idx] = cnt
                    else:
                        arr.extend([0] * (idx - len(arr)))
                        arr.append(cnt)

    # 將更新後的 WEEK_META 序列化回 JS 格式（非標準 JSON）
    wm_parts = []
    for w in week_meta:
        first_str = 'true' if w.get('first') else 'false'
        wm_parts.append(
            f"{{label:'{w['label']}',month:'{w['month']}',first:{first_str},date:'{w['date']}'}}"
        )
    new_wm_js = '[\n  ' + ','.join(wm_parts) + '\n]'

    # 更新 trend_data（確保使用 districts 鍵）
    if 'districts' in trend_data:
        trend_data['districts'] = td_districts
    else:
        trend_data = {'districts': td_districts}

    # 替換 HTML 中的 WEEK_META
    html = re.sub(
        r'(const WEEK_META\s*=\s*)(\[.*?\])(\s*;)',
        lambda m: m.group(1) + new_wm_js + m.group(3),
        html, flags=re.DOTALL
    )

    # 替換 HTML 中的 TREND_DATA
    html = re.sub(
        r'(const TREND_DATA\s*=\s*)(\{.*?\})(\s*;)',
        lambda m: m.group(1) + json.dumps(trend_data, ensure_ascii=False) + m.group(3),
        html, flags=re.DOTALL
    )

    # 重建 MEMBER_DATA / BASE_DATA 寫回 HTML
    # BASE_DATA 用非標準 JS 格式（key 不加引號）維持原樣
    base_parts = [f'{k}:{v}' for k, v in base_data.items()]
    new_base_js = '{\n  ' + ', '.join(base_parts) + ',\n}'
    html = re.sub(
        r'(const BASE_DATA\s*=\s*)(\{.*?\})(\s*;)',
        lambda m: m.group(1) + new_base_js + m.group(3),
        html, flags=re.DOTALL
    )
    html = re.sub(
        r'(const MEMBER_DATA\s*=\s*)(\{.*?\})(\s*;)',
        lambda m: m.group(1) + json.dumps(member_data, ensure_ascii=False) + m.group(3),
        html, flags=re.DOTALL
    )
    total = sum(len(v) for v in member_data.values())
    print(f'  + 重建 MEMBER_DATA：{total} 人（8 區）')

    return html


# ============================================================
# HTML 讀寫工具
# ============================================================

def read_html(path):
    return open(path, encoding='utf-8').read()


def write_html(path, content):
    import time
    if not content or len(content) < 500:
        print(f'  ✗ 拒絕寫入 {path}：內容異常（{len(content)} bytes），原檔案保留')
        return
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(content, encoding='utf-8')
    # 重試最多 5 次（應對 OneDrive 短暫鎖檔）
    for attempt in range(5):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt < 4:
                time.sleep(1)
            else:
                # 最後嘗試直接覆寫
                try:
                    Path(path).write_text(content, encoding='utf-8')
                    tmp.unlink(missing_ok=True)
                    return
                except Exception as e2:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(f'寫入失敗 {path}: {e2}')
    print(f'  ✓ {Path(path).relative_to(BASE)}')


def patch_const(html, var_name, new_json):
    """替換 HTML 中 const VAR_NAME = ...; 的值。"""
    pattern = rf'(const {re.escape(var_name)}\s*=\s*)(\[.*?\]|\{{.*?\}})(\s*;)'
    new_html, n = re.subn(
        pattern,
        lambda m: m.group(1) + new_json + m.group(3),
        html, flags=re.DOTALL
    )
    if n == 0:
        print(f'    ⚠ 找不到 const {var_name}')
    return new_html


# ============================================================
# 快照比對（名單 & 週次變動）
# ============================================================

SNAPSHOT_PATH = BASE / 'snapshot.json'

def load_snapshot():
    if not SNAPSHOT_PATH.exists():
        return None
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))
    except Exception:
        return None

def save_snapshot(members, active_weeks):
    snap = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'weeks': [lbl for _, lbl in active_weeks],
        'members': {
            dk: sorted(members[dk].keys())
            for dk in ['y1','y2','y3','hs1','hs2','hs3','ms1','ms2']
        },
    }
    SNAPSHOT_PATH.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding='utf-8')

def print_diff(old, members, active_weeks):
    print('\n🔍 與上次比對...')
    print(f'   (上次：{old["date"]})')

    # ── 週次變動 ──────────────────────────────────────────────
    old_weeks = set(old.get('weeks', []))
    new_weeks  = [lbl for _, lbl in active_weeks]
    added_weeks = [w for w in new_weeks if w not in old_weeks]
    if added_weeks:
        print(f'  📅 新增週次：{", ".join(added_weeks)}')
    else:
        print('  📅 週次無變動')

    # ── 成員變動 ──────────────────────────────────────────────
    any_member_change = False
    for dk in ['y1','y2','y3','hs1','hs2','hs3','ms1','ms2']:
        old_set = set(old.get('members', {}).get(dk, []))
        new_set = set(members[dk].keys())
        added   = new_set - old_set
        removed = old_set - new_set
        if added or removed:
            any_member_change = True
            label = DK_NAME.get(dk, dk)
            if added:
                print(f'  ✅ {label} 新增：{", ".join(sorted(added))}')
            if removed:
                print(f'  ❌ {label} 移除：{", ".join(sorted(removed))}')
    if not any_member_change:
        print('  👤 成員名單無變動')


# ============================================================
# 主程式
# ============================================================

def main():
    print('=' * 50)
    print('81Y3 Dashboard 週更新')
    print('=' * 50)

    # ── 讀取 CSV / Excel ─────────────────────────────────────
    print('\n📂 讀取資料檔...')
    csvs = {}
    for act in ACTS:
        # 優先找 Excel，找不到才找 CSV
        p = None
        for ext in ('.xlsx', '.xls', '.csv'):
            candidate = CSV_DIR / f'{act}最新{ext}'
            if candidate.exists():
                p = candidate
                break
        if p is None:
            print(f'  ✗ 找不到 {act}最新(.xlsx/.xls/.csv)，請放到「即時更新」資料夾')
            sys.exit(1)
        csvs[act] = read_csv(p)
        print(f'  ✓ {p.name} ({len(csvs[act])-2} 行)')

    # ── 解析資料 ────────────────────────────────────────────
    print('\n🔍 解析週次與成員...')
    members, week_meta_raw, active_weeks = build_member_dict(csvs)

    # ── 快照比對 ─────────────────────────────────────────────
    old_snap = load_snapshot()
    if old_snap:
        print_diff(old_snap, members, active_weeks)
    else:
        print('\n📸 首次執行，建立基準快照')

    print(f'  CSV 週次欄：{[lbl for _, lbl in week_meta_raw]}')
    print(f'  有效週次：  {[lbl for _, lbl in active_weeks]}')
    if active_weeks:
        print(f'  最新週次：  {active_weeks[-1][1]}')

    # 計算最新週的日期資訊（供 index / leaderboard 使用）
    latest_month_lbl, latest_week_lbl = csv_label_to_trend(active_weeks[-1][1])
    latest_date_slash = KNOWN_DATES.get((latest_month_lbl, latest_week_lbl), '')  # e.g. '4/13'
    # YYYY/MM/DD 格式
    if latest_date_slash:
        m_d = latest_date_slash.split('/')
        latest_date_full = f'2026/{int(m_d[0]):02d}/{int(m_d[1]):02d}'  # '2026/04/13'
    else:
        latest_date_full = '2026/??/??'
    latest_month_zh = f'2026年{latest_month_lbl}'   # '2026年4月'
    # 週次中文，e.g. 'W2' → '第二週'
    WN_ZH = {'W1':'第一週','W2':'第二週','W3':'第三週','W4':'第四週','W5':'第五週'}
    latest_week_zh = WN_ZH.get(latest_week_lbl, latest_week_lbl)  # '第二週'
    tip_text = (f'資料最後一週為 {latest_month_zh[4:]}{latest_week_zh}'
                f'（{latest_date_slash}），請回溯此日期的出席記錄')

    # ── 小區出席頁（8 個 index.html）───────────────────────
    print('\n📝 更新小區出席頁...')
    for dk in ['y1', 'y2', 'y3', 'hs1', 'hs2', 'hs3', 'ms1', 'ms2']:
        raw  = build_raw_data(dk, members, active_weeks)
        path = DASH / dk / 'index.html'
        html = read_html(path)
        html = patch_const(html, 'RAW_DATA', json.dumps(raw, ensure_ascii=False))

        dk_name = DK_NAME[dk]  # e.g. '國中一區'

        # <title>
        html = re.sub(
            r'(<title>.*?出席漏填警示\s*[—–-]\s*)([^<]+)(</title>)',
            rf'\g<1>{latest_month_zh}\g<3>',
            html
        )
        # <div class="subtitle">
        html = re.sub(
            r'(<div class="subtitle">[^·]*·\s*)([^·]+)(\s*·\s*歷史出席率)',
            rf'\g<1>{latest_month_zh}\g<3>',
            html
        )
        # 最新統計日期 stat-num + tooltip
        html = re.sub(
            r'(<div class="stat-num"[^>]*>)\d{4}/\d{2}/\d{2}(</div>)',
            rf'\g<1>{latest_date_full}\g<2>',
            html
        )
        html = re.sub(
            r'(data-tip=")([^"]*請回溯此日期[^"]*)',
            rf'\g<1>{tip_text}',
            html
        )

        # ── 上週比較（上週有來這週沒來 / 上週沒來這週來了）──
        if len(active_weeks) >= 2:
            this_lbl = active_weeks[-1][1]
            prev_lbl = active_weeks[-2][1]
            missing  = []   # 上週有來、這週沒來
            returned = []   # 上週沒來、這週來了
            for name, m in members[dk].items():
                this_w = m.get('主日', {}).get(this_lbl, 0)
                prev_w = m.get('主日', {}).get(prev_lbl, 0)
                if prev_w == 1 and this_w == 0:
                    missing.append(name)
                elif prev_w == 0 and this_w == 1:
                    returned.append(name)

            def make_tags(names, cls):
                if not names:
                    return '<span style="color:rgba(255,255,255,0.35);font-size:12px">（無）</span>'
                return ''.join(f'<span class="wc-tag {cls}">{n}</span>' for n in names)

            missing_html  = make_tags(missing,  'wc-tag-red')
            returned_html = make_tags(returned, 'wc-tag-green')

            # 替換 wc-missing 區塊的 wc-names
            html = re.sub(
                r'(wc-block wc-missing.*?<div class="wc-names">).*?(</div>\s*</div>\s*<div class="wc-divider">)',
                rf'\g<1>\n        {missing_html}\n      \g<2>',
                html, flags=re.DOTALL
            )
            # 替換 wc-returned 區塊的 wc-names
            html = re.sub(
                r'(wc-block wc-returned.*?<div class="wc-names">).*?(</div>\s*</div>\s*</div>\s*</div>)',
                rf'\g<1>\n        {returned_html}\n      \g<2>',
                html, flags=re.DOTALL
            )

        write_html(path, html)
        print(f'    {dk}: {len(raw)} 人')

    # ── 排行榜（8 個 leaderboard.html）─────────────────────
    print('\n🏆 更新排行榜...')
    for dk in ['y1', 'y2', 'y3', 'hs1', 'hs2', 'hs3', 'ms1', 'ms2']:
        lb   = build_leaderboard(dk, members, active_weeks)
        path = DASH / dk / 'leaderboard.html'
        html = read_html(path)
        html = patch_const(html, 'DATA', json.dumps(lb, ensure_ascii=False))

        # period-badge（靜態 HTML）
        html = re.sub(
            r'(<div class="period-badge">📅\s*計算區間：)[^<]*(</div>)',
            rf'\g<1>{lb["period"]}（共 4 週）\g<2>',
            html
        )

        write_html(path, html)
        print(f'    {dk}: {len(lb["rankings"])} 人，期間：{lb["period"]}')

    # ── 本週點名（weekly.html）──────────────────────────────
    print('\n📋 更新本週點名...')
    districts, all_members, meta = build_weekly(members, active_weeks)
    path = DASH / 'weekly.html'
    html = read_html(path)

    # JS 資料
    html = patch_const(html, 'DISTRICTS', json.dumps(districts, ensure_ascii=False))
    html = patch_const(html, 'MEMBERS',   json.dumps(all_members, ensure_ascii=False))

    # topbar-date（右上角小日期）
    html = re.sub(
        r'(<div class="topbar-date">)[^<]*(</div>)',
        rf'\g<1>{meta["short_range"]}\g<2>',
        html
    )

    # 日期 sub-header：<div class="sub">...</div>（h1 下方）
    html = re.sub(
        r'(<h1>[^<]*本週點名[^<]*</h1>\s*<div class="sub">)[^<]*(</div>)',
        rf'\g<1>{meta["date_range"]}（{meta["week_num"]}）\g<2>',
        html
    )

    # Summary cards（依序：本週總計、基數、出席率、未提交區）
    def replace_stat_val(html, old_val, new_val):
        return html.replace(
            f'<div class="val">{old_val}</div>',
            f'<div class="val">{new_val}</div>',
            1
        )

    # 用 regex 替換四個 stat card 的值（按順序）
    def patch_stat_cards(html, total, base, pct, zero):
        pattern = r'(<div class="stat-card[^"]*">\s*<div class="val">)([^<]*)(</div>\s*<div class="label">)(本週主日總計|全會所基數|出席比率|未提交排組)(</div>\s*</div>)'
        replacements = {
            '本週主日總計': str(total),
            '全會所基數':   str(base),
            '出席比率':     f'{pct}%',
            '未提交排組':   f'{zero}區',
        }
        def repl(m):
            label = m.group(4)
            new_v = replacements.get(label, m.group(2))
            return m.group(1) + new_v + m.group(3) + label + m.group(5)
        return re.sub(pattern, repl, html)

    html = patch_stat_cards(
        html,
        meta['total_all'], meta['base_all'],
        meta['pct_all'],   meta['zero_dks']
    )

    # Footer note
    html = re.sub(
        r'(本週資料為)[^\。。]+?(統計。)',
        rf'\g<1>{meta["short_range"]}\g<2>',
        html
    )

    write_html(path, html)
    print(f'    日期：{meta["date_range"]}（{meta["week_num"]}）')
    print(f'    總計：{meta["total_all"]}/{meta["base_all"]} ({meta["pct_all"]}%)')
    for d in districts:
        print(f'    {d["id"]}: {d["total"]}/{d["base"]} ({d["pct"]}%) | 上月均 {d["march_avg"]}')

    # ── 兒童專區（kids/index.html）──────────────────────────
    print('\n🎈 更新兒童專區...')
    kids = build_kids_raw(members, active_weeks)
    path = DASH / 'kids' / 'index.html'
    html = read_html(path)
    html = patch_const(html, 'RAW_DATA', json.dumps(kids, ensure_ascii=False))
    write_html(path, html)
    print(f'    共 {len(kids)} 位兒童')

    # ── 出席趨勢（trend.html）───────────────────────────────
    print('\n📈 更新出席趨勢...')
    path = DASH / 'trend.html'
    html = read_html(path)
    html = update_trend(members, active_weeks, html)
    write_html(path, html)

    # ── 配搭總覽（cowork.html）──────────────────────────────
    print('\n📬 更新挽回名單頁...')
    update_invite_pages(members, active_weeks)

    print('\n⭐ 更新配搭出席總覽...')
    update_cowork_page(members, active_weeks)

    # ── 首頁（index.html）更新動態欄位 ──────────────────────
    path = DASH / 'index.html'
    html = read_html(path)
    # 兒童人數
    html = re.sub(
        r'(12歲以下 · )\d+(人)',
        rf'\g<1>{len(kids)}\g<2>',
        html
    )
    # 本週點名日期（短日期格式 M/D～M/D）
    html = re.sub(
        r'(\d+/\d+～\d+/\d+ 追蹤)',
        meta['short_range'] + ' 追蹤',
        html
    )
    write_html(path, html)

    # ── 儲存快照 ─────────────────────────────────────────────
    save_snapshot(members, active_weeks)
    print('\n📸 快照已更新')

    # ── 完成 ─────────────────────────────────────────────────
    print('\n' + '=' * 50)
    print('✅ 全部更新完成！共 20 個 HTML 檔案')
    if active_weeks:
        print(f'   最新資料週次：{active_weeks[-1][1]}')
    print('=' * 50)


def _classify_invite(dk, members, active_weeks):
    """
    依規則產生優先挽回（RECOVERABLE）和不規律（IRREGULAR）名單。

    RECOVERABLE：近 4 週所有活動全缺席 + 近 6 週主日估算根基 ≥ 2 次
    IRREGULAR  ：近 4 週任一活動有出席 + 近 6 週主日 ≤ 3 次 + 根基 ≥ 2 次
    （兒童排除、RECOVERABLE 優先）

    HIST_MULT：把近 6 週主日出席率推算為等效 13 週次數，與試算腳本一致。
    """
    HIST_MULT = 13
    recent6_labels = [lbl for _, lbl in active_weeks[-6:]]
    month_map = {lbl: f'2026年{lbl.split("第")[0]}' for _, lbl in active_weeks}

    recoverable, irregular = [], []

    for name, m in members.get(dk, {}).items():
        if m.get('group', '') in KIDS_GROUPS:
            continue

        march = {a: get_window(m, a, recent6_labels) for a in ACTS}
        recent4 = {a: march[a][-4:] for a in ACTS}
        any_recent4   = any(sum(recent4[a]) > 0 for a in ACTS)
        all_absent_r4 = not any_recent4

        sunday_recent6   = sum(march['主日'])
        hist_sunday_est  = round(historical_rate(march['主日']) * HIST_MULT)
        recent_4weeks_cnt = sum(march['主日'][-4:])

        # 最後出席月份（任一活動）
        last_active_month = ''
        for _, lbl in reversed(active_weeks):
            if any(m.get(a, {}).get(lbl, 0) == 1 for a in ACTS):
                last_active_month = month_map.get(lbl, '')
                break

        entry = {
            '姓名': name,
            '受浸日期': '',
            'recent_4weeks': recent_4weeks_cnt,
            'attendance_since_sep': 0,
            'sep_to_feb': 0,
            'last_active_month': last_active_month,
        }

        if all_absent_r4 and hist_sunday_est >= 2:
            recoverable.append(entry)
        elif any_recent4 and sunday_recent6 <= 3 and hist_sunday_est >= 2:
            irregular.append(entry)

    # 依姓名排序，方便對照
    recoverable.sort(key=lambda x: x['姓名'])
    irregular.sort(key=lambda x: x['姓名'])
    return recoverable, irregular


def update_invite_pages(members, active_weeks):
    """重建各小區 invite.html 的 RECOVERABLE / IRREGULAR，並保留手動欄位。"""
    if not active_weeks:
        return

    for dk in ['y1','y2','y3','hs1','hs2','hs3','ms1','ms2']:
        path = DASH / dk / 'invite.html'
        if not path.exists():
            continue
        html = read_html(path)
        decoder = json.JSONDecoder()

        # ── 讀取現有列表，建立 name → 保留欄位 lookup ─────────────────
        preserved = {}   # {name: {受浸日期, attendance_since_sep, sep_to_feb}}
        for const_name in ('RECOVERABLE', 'IRREGULAR'):
            idx = html.find(f'const {const_name} = ')
            if idx < 0:
                continue
            start = idx + len(f'const {const_name} = ')
            try:
                existing, _ = decoder.raw_decode(html, start)
            except Exception:
                continue
            for p in existing:
                n = p.get('姓名', '')
                if n and n not in preserved:
                    preserved[n] = {
                        '受浸日期':           p.get('受浸日期', ''),
                        'attendance_since_sep': p.get('attendance_since_sep', 0),
                        'sep_to_feb':          p.get('sep_to_feb', 0),
                    }

        # ── 依規則重建名單 ──────────────────────────────────────────────
        new_rec, new_irr = _classify_invite(dk, members, active_weeks)

        # 合併保留欄位
        for lst in (new_rec, new_irr):
            for p in lst:
                saved = preserved.get(p['姓名'], {})
                p['受浸日期']           = saved.get('受浸日期', '')
                p['attendance_since_sep'] = saved.get('attendance_since_sep', 0)
                p['sep_to_feb']          = saved.get('sep_to_feb', 0)

        # ── 寫回 HTML ───────────────────────────────────────────────────
        def replace_const(h, const_name, new_data):
            idx = h.find(f'const {const_name} = ')
            if idx < 0:
                return h
            start = idx + len(f'const {const_name} = ')
            try:
                _, end_pos = decoder.raw_decode(h, start)
            except Exception:
                return h
            return h[:start] + json.dumps(new_data, ensure_ascii=False) + h[end_pos:]

        html = replace_const(html, 'RECOVERABLE', new_rec)
        html = replace_const(html, 'IRREGULAR',   new_irr)

        write_html(path, html)
        print(f'  ✓ {dk}/invite.html  (挽回:{len(new_rec)} 不規律:{len(new_irr)})')


def update_cowork_page(members, active_weeks):
    """生成 cowork.html：所有配搭最新週出席總覽。"""
    if not active_weeks:
        return
    latest_lbl = active_weeks[-1][1]   # e.g. '4月第二週'

    # 建立 {name: {act: 0/1}} 查找表
    by_name = {}
    for dk_members in members.values():
        for name, info in dk_members.items():
            by_name[name] = {act: info.get(act, {}).get(latest_lbl, -1) for act in ACTS}
    # -1 = 資料不存在, 0 = 未出席, 1 = 出席

    def pip(act, val):
        if val == 1:
            return f'<span class="cp ok">{act} ✓</span>'
        elif val == 0:
            return f'<span class="cp miss">{act} ✗</span>'
        else:
            return f'<span class="cp na">{act} –</span>'

    # 配搭「完整」只看核心 4 項（主日/小排/晨興/禱告）；出訪/受訪顯示但不計入判定
    CORE_ACTS = ['主日', '小排', '晨興', '禱告']

    def member_card(name):
        data = by_name.get(name)
        if data is None:
            return f'<div class="cm no-data"><div class="cm-name">⚠️ {name}</div><div class="cm-note">資料缺失</div></div>'
        missing = [a for a in CORE_ACTS if data[a] != 1]
        cls = 'all-ok' if not missing else 'has-miss'
        pips = ''.join(pip(a, data[a]) for a in ACTS)
        warn = f'<div class="cm-warn">補填：{"、".join(missing)}</div>' if missing else ''
        return f'<div class="cm {cls}"><div class="cm-name">{name}</div><div class="cm-pips">{pips}</div>{warn}</div>'

    def dk_block(dk):
        title = DK_TITLE[dk]
        names = COWORKERS_MAP.get(dk, [])
        total = len(names)
        ok = sum(1 for n in names if all(by_name.get(n, {}).get(a, -1) == 1 for a in CORE_ACTS))
        status_cls = 'all-ok-badge' if ok == total else 'partial-badge'
        status_txt = '✅ 全員核心完整' if ok == total else f'⚠️ {total - ok} 人核心待補'
        cards = ''.join(member_card(n) for n in names)
        return f'''
    <div class="dk-block">
      <div class="dk-header">
        <span class="dk-title">{title}</span>
        <span class="dk-badge {status_cls}">{status_txt}</span>
      </div>
      <div class="dk-grid">{cards}</div>
    </div>'''

    group_sections = ''
    for grp, dks in GROUP_DKS.items():
        icon, name, color = GROUP_TITLE[grp]
        dk_blocks = ''.join(dk_block(dk) for dk in dks)
        group_sections += f'''
  <section class="grp-section">
    <div class="grp-header" style="border-color:{color}">
      <span class="grp-icon">{icon}</span>
      <span class="grp-name">{name}</span>
    </div>
    <div class="grp-dks">{dk_blocks}</div>
  </section>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
(function(){{
  const KEY = 'auth_81y3', CORRECT = '5281';
  if (sessionStorage.getItem(KEY) !== CORRECT) {{
    const input = prompt('請輸入密碼');
    if (input !== CORRECT) {{
      document.documentElement.innerHTML = '<div style="font-family:sans-serif;text-align:center;margin-top:20%;color:#999">密碼錯誤</div>';
      throw new Error('unauthorized');
    }}
    sessionStorage.setItem(KEY, CORRECT);
  }}
}})();
</script>
<title>配搭出席總覽 · 81會所</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background: #0a0a14; color: #fff;
  min-height: 100vh; padding: 0 0 40px;
}}
header {{
  background: linear-gradient(135deg,#1a1a2e,#16213e);
  border-bottom: 2px solid rgba(247,208,96,0.25);
  padding: 18px 24px 16px;
  display: flex; align-items: center; gap: 14px;
}}
.back-btn {{
  color: #aaa; text-decoration: none; font-size: 22px; line-height: 1;
}}
.header-info {{ flex: 1; }}
.header-title {{ font-size: 17px; font-weight: 800; color: #f7d060; }}
.header-sub {{ font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px; }}
.main {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 0; }}
.grp-section {{ margin-bottom: 32px; }}
.grp-header {{
  display: flex; align-items: center; gap: 10px;
  border-left: 4px solid; padding-left: 12px;
  margin-bottom: 16px;
}}
.grp-icon {{ font-size: 20px; }}
.grp-name {{ font-size: 16px; font-weight: 800; }}
.grp-dks {{ display: flex; flex-wrap: wrap; gap: 16px; }}
.dk-block {{
  flex: 1; min-width: 220px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 14px 16px;
}}
.dk-header {{
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}}
.dk-title {{ font-size: 13px; font-weight: 800; color: #f7d060; }}
.dk-badge {{
  font-size: 10px; padding: 2px 8px; border-radius: 10px;
  font-weight: 700; margin-left: auto;
}}
.all-ok-badge {{ background: rgba(46,204,113,0.18); color: #2ecc71; }}
.partial-badge {{ background: rgba(231,76,60,0.18); color: #e74c3c; }}
.dk-grid {{ display: flex; flex-direction: column; gap: 7px; }}
.cm {{
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 9px; padding: 8px 10px;
}}
.cm.all-ok {{ border-color: rgba(46,204,113,0.3); }}
.cm.has-miss {{ border-color: rgba(231,76,60,0.35); background: rgba(231,76,60,0.05); }}
.cm.no-data {{ border-color: rgba(255,200,0,0.3); background: rgba(255,200,0,0.04); }}
.cm-name {{ font-size: 12px; font-weight: 700; margin-bottom: 5px; }}
.cm-pips {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.cp {{
  font-size: 10px; padding: 2px 6px; border-radius: 5px;
  font-weight: 600; white-space: nowrap;
}}
.cp.ok   {{ background: rgba(46,204,113,0.15); color: #2ecc71; border: 1px solid rgba(46,204,113,0.25); }}
.cp.miss {{ background: rgba(231,76,60,0.18); color: #e74c3c; border: 1px solid rgba(231,76,60,0.35); }}
.cp.na   {{ background: rgba(255,255,255,0.06); color: #888; border: 1px solid rgba(255,255,255,0.1); }}
.cm-warn {{ font-size: 10px; color: #e74c3c; margin-top: 4px; font-weight: 600; }}
.cm-note {{ font-size: 10px; color: #f7d060; }}
@media (max-width: 600px) {{
  .grp-dks {{ flex-direction: column; }}
  .dk-block {{ min-width: unset; }}
}}
</style>
</head>
<body>
<header>
  <a href="index.html" class="back-btn" title="返回首頁">‹</a>
  <div class="header-info">
    <div class="header-title">⭐ 配搭出席總覽</div>
    <div class="header-sub">最新週次：{latest_lbl} · 核心：主日 / 小排 / 晨興 / 禱告 &nbsp;·&nbsp; 參考：出訪 / 受訪</div>
  </div>
</header>
<div class="main">
{group_sections}
</div>
</body>
</html>'''

    out = DASH / 'cowork.html'
    out.write_text(html, encoding='utf-8')
    total_cw = sum(len(v) for v in COWORKERS_MAP.values())
    ok_all = sum(
        1 for dk, names in COWORKERS_MAP.items()
        for n in names
        if all(by_name.get(n, {}).get(a, -1) == 1 for a in CORE_ACTS)
    )
    print(f'  ✓ cowork.html ({latest_lbl}，{ok_all}/{total_cw} 人核心完整)')


if __name__ == '__main__':
    main()
