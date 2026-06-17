"""
匯出立委 + 議員 汽車申報資料 → cars_data.json
輸出到 ../car-watch/ 目錄（跟 car-watch.html 同層）
"""
import os, json, sys, csv, re as _re_elc
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

# 選舉代碼 → 民國年，用來判斷哪筆黨籍最新
_LO_YEARS = {1:75,2:79,3:83,4:87,5:91,6:95,7:98,8:101,9:105,10:109,11:113}
def _election_year(code):
    m = _re_elc.match(r'ELC-L0-(\d+)', code)
    if m:
        return _LO_YEARS.get(int(m.group(1)), 0)
    m = _re_elc.match(r'ELC-\w{2}-(\d+)', code)
    if m:
        return int(m.group(1))
    return 0

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data-json')
PARTIES_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'political-donation', 'parties.csv')
ELECTION_JSONL = os.path.join(os.path.dirname(__file__), '..', 'people_20260505_115757_mixed-tw.gov.cec.data-選舉資料庫.jsonl')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'car-watch')
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_TITLES = {'議員', '立法委員', '議長', '副議長'}

BRAND_MAP = {
    '國瑞': 'Toyota', 'TOYOTA': 'Toyota', '豐田': 'Toyota',
    'LEXUS': 'Lexus', 'Lexus': 'Lexus', '凌志': 'Lexus',
    'Mercedes-Benz': 'Benz', 'MERCEDES-BENZ': 'Benz', 'BENZ': 'Benz', 'Benz': 'Benz',
    '賓士': 'Benz', 'MERCEDESBENZ': 'Benz', 'Merceces-Benz': 'Benz',
    '中華賓士': 'Benz',
    'BMW': 'BMW', '寶馬': 'BMW', 'BNW': 'BMW',
    'VOLKSWAGEN': 'VW', 'Volkswagen': 'VW', '福斯': 'VW',
    'AUDI': 'Audi', 'Audi': 'Audi', '奧迪': 'Audi',
    'VOLVO': 'Volvo', 'VOVOL': 'Volvo',
    'PORSCHE': 'Porsche', '保時捷': 'Porsche',
    '中華': '中華三菱', '三菱': '中華三菱',
    '本田': 'Honda', 'HONDA': 'Honda',
    '日產': 'Nissan', 'NISSAN': 'Nissan',
    '福特六和': 'Ford', 'FORD': 'Ford',
    'MAZDA': 'Mazda', '馬自達': 'Mazda',
    '三陽': '三陽SYM',
    'SUZUKI': 'Suzuki', '鈴木': 'Suzuki',
    '納智捷': 'Luxgen',
    'MINI': 'MINI',
    'AUSTINMINIMAYFAIR': 'Austin Mini', 'AUSTINMINI': 'Austin Mini',
    'MINICOOPER': 'MINI', 'MINICOOPERCOUPE': 'MINI', 'MINICOOPERCABRIO': 'MINI',
    'TOYOTARAV4': 'Toyota', 'TOYOTAPREVIA': 'Toyota', 'TOYOTACAMRY': 'Toyota',
    'MITSUBISHI': '中華三菱',
    'SMART': 'Smart',
    'INFINITI': 'Infiniti',
    'YAMAHA': 'Yamaha', '山葉': 'Yamaha',
    'PIAGGIO': 'Piaggio',
    'LANDROVER': 'Land Rover', 'Land': 'Land Rover',
    'SUBARU': 'Subaru',
    'Tesla': 'Tesla', 'TESLA': 'Tesla',
    'SKODA': 'Skoda',
    'JAGUAR': 'Jaguar',
    'MASERATI': 'Maserati',
    'FERRARI': 'Ferrari',
    'LAMBORGHINI': 'Lamborghini',
    'BENTLEY': 'Bentley',
    'MCLAREN': 'McLaren',
    'KIA': 'Kia', '起亞': 'Kia',
    'HYUNDAI': 'Hyundai', '現代': 'Hyundai',
    'PEUGEOT': 'Peugeot',
    'JEEP': 'Jeep',
    'CHRYSLER': 'Chrysler',
    'ALFA': 'Alfa Romeo',
    'HARLEY-DAVIDSON': 'Harley-Davidson',
    'TRIUMPH': 'Triumph',
    'DAIHATSU': 'Daihatsu',
    'ROVER': 'Land Rover',
    'ACURA': 'Acura',
    '勞斯萊斯': 'Rolls-Royce', 'ROLLSROYCE': 'Rolls-Royce',
    '中華名爵': 'MG', 'MG': 'MG',
    'SAAB': 'Saab',
    'SSANGYONG': 'SsangYong',
    'MAHINDRA': 'Mahindra',
    '光陽': 'KYMCO', 'KYMCO': 'KYMCO',
    '宏佳騰': '宏佳騰',
    '裕隆': '裕隆',
    '日野': '日野',
    'DAIHHATSU': 'Daihatsu',
    'VENUE': 'Hyundai',
    'C200': 'Benz',
    '國產TIIDA': 'Nissan',
    'AUSTIN': 'Austin Mini',
    'ZSG10L-EHXGKR': 'Toyota',
}

LUXURY_BRANDS = {
    'Lexus', 'Benz', 'BMW', 'Audi', 'Porsche', 'Volvo', 'Land Rover',
    'Maserati', 'Ferrari', 'Lamborghini', 'Bentley', 'McLaren', 'Jaguar',
    'Rolls-Royce', 'Acura', 'MINI', 'Tesla',
}

SUPERCAR_BRANDS = {'Ferrari', 'Lamborghini', 'McLaren', 'Bentley', 'Maserati', 'Rolls-Royce'}

PARTY_SHORT = {
    '中國國民黨': '國民黨',
    '民主進步黨': '民進黨',
    '台灣民眾黨': '民眾黨',
    '親民黨': '親民黨',
    '時代力量': '時代力量',
    '台灣團結聯盟': '台聯',
    '新黨': '新黨',
    '台灣基進': '台灣基進',
    '無黨籍及未經政黨推薦': '無黨籍',
    '無': '無黨籍',
}

COUNTY_REGION = {
    '台北市': '六都', '新北市': '六都', '桃園市': '六都',
    '台中市': '六都', '台南市': '六都', '高雄市': '六都',
    '基隆市': '北部', '新竹市': '北部', '新竹縣': '北部',
    '宜蘭縣': '北部', '苗栗縣': '中部',
    '彰化縣': '中部', '南投縣': '中部', '雲林縣': '中部',
    '嘉義市': '南部', '嘉義縣': '南部', '屏東縣': '南部',
    '花蓮縣': '東部', '台東縣': '東部',
    '澎湖縣': '離島', '金門縣': '離島', '連江縣': '離島',
    '立法院': '立法院',
}

import re as _re

def parse_price(s):
    """Return int price (NTD), 'over5', or None."""
    s = s.strip()
    if not s:
        return None
    if '超過五年' in s or '超過5年' in s:
        return 'over5'
    # 取開頭的金額數字，容許後面接括號註記（分期付款/二手車/登記原因等）
    m = _re.match(r'[\d,，]+', s)
    if m:
        v = int(m.group(0).replace(',', '').replace('，', ''))
        if 1_000 <= v <= 100_000_000:
            return v
    return None

def car_key(car):
    """廠牌型號 + 汽缸容量 + 所有人 → 跨年比對同一台車的 key"""
    brand = car.get('廠牌型號', '').strip().upper()
    cc    = car.get('汽缸容量', '').replace(',', '').strip()
    owner = car.get('所有人', '').strip()
    return (brand, cc, owner)

# Prefix list sorted longest-first for greedy prefix matching
_BRAND_PREFIXES = sorted(BRAND_MAP.keys(), key=len, reverse=True)

def normalize_brand(raw):
    raw = raw.strip()
    # Strip trailing parenthetical notes e.g. "(汽車)", "（大型重型機器腳踏車）"
    clean = _re.sub(r'[\(（].*', '', raw).strip()
    first = clean.split()[0] if clean else ''

    b = (BRAND_MAP.get(first)
         or BRAND_MAP.get(first.upper())
         or BRAND_MAP.get(clean)
         or BRAND_MAP.get(clean.upper()))

    if not b:
        # Prefix matching: check if cleaned string starts with a known brand key
        clean_up = clean.upper()
        for prefix in _BRAND_PREFIXES:
            if clean_up.startswith(prefix.upper()):
                b = BRAND_MAP[prefix]
                break

    return b or first or '其他'

def get_county(org):
    for c in ['臺北市','台北市','新北市','桃園市','台中市','臺中市',
              '台南市','臺南市','高雄市','基隆市','新竹市','嘉義市',
              '宜蘭縣','新竹縣','苗栗縣','彰化縣','南投縣','雲林縣',
              '嘉義縣','屏東縣','花蓮縣','台東縣','臺東縣','澎湖縣',
              '金門縣','連江縣']:
        if c in org:
            return c.replace('臺', '台')
    if '立法院' in org:
        return '立法院'
    return '其他'

# ── 第一層：parties.csv（舊有資料，作為後補）────────────────────────────────
name_gender = {}
name_party = {}
_party_candidates = defaultdict(list)  # name → [(date_str, party)]

with open(PARTIES_CSV, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        n    = row.get('姓名', '').strip()
        g    = row.get('性別', '').strip()
        p    = row.get('政黨', '').strip()
        code = row.get('選舉代碼', '').strip()
        if n and g and n not in name_gender:
            name_gender[n] = g
        if n and p and code:
            # 把選舉代碼轉成 YYYY-MM-DD 格式以便與 JSONL 統一比較
            yr = _election_year(code)
            fake_date = f'{yr:04d}-12-31' if yr else '1900-01-01'
            _party_candidates[n].append((fake_date, p))

for n, records in _party_candidates.items():
    records.sort(key=lambda x: x[0])
    name_party[n] = records[-1][1]

# ── 第二層：選舉資料庫 JSONL（有實際日期，覆蓋 CSV）──────────────────────────
import unicodedata as _ud

def _cjk_prefix(s):
    """擷取字串開頭連續的 CJK 中文字元，用於正規化原住民族複合姓名。
    e.g. '李紀財MulanengPaliuliu' → '李紀財'
         '鄭天財 Sra．Kacaw'     → '鄭天財'
    """
    out = []
    for ch in s:
        cat = _ud.category(ch)
        # CJK 統一漢字、延伸區、相容區
        if cat.startswith('L') and '一' <= ch <= '鿿' or \
           '㐀' <= ch <= '䶿' or '豈' <= ch <= '﫿':
            out.append(ch)
        elif ch in ('·', '‧', '・', '·', '．'):
            # 不中斷（間隔號）
            break
        elif out:
            # 遇到非 CJK 就停
            break
    return ''.join(out)

_jsonl_candidates = defaultdict(list)  # name → [(date_str, party)]

if os.path.exists(ELECTION_JSONL):
    with open(ELECTION_JSONL, 'r', encoding='utf-8') as _jf:
        for _line in _jf:
            _line = _line.strip()
            if not _line:
                continue
            try:
                _obj = json.loads(_line)
                for _rec in _obj.get('records', []):
                    _vals = _rec.get('values', {})
                    _n = _vals.get('姓名', '').strip()
                    _p = _vals.get('政黨', '').strip()
                    _g = _vals.get('性別', '').strip()
                    _t = _rec.get('time', '')
                    if _n and _p and _t:
                        # 完整姓名
                        _jsonl_candidates[_n].append((_t, _p))
                        # 同時以「純中文前綴」登記，讓財產申報的純中文姓名也能查到
                        _cjk = _cjk_prefix(_n)
                        if _cjk and _cjk != _n:
                            _jsonl_candidates[_cjk].append((_t, _p))
                        # 財產申報有時寫成「李紀財MulanengPaliuliu」（無空格），也登記
                        _no_space = _n.replace(' ', '')
                        if _no_space != _n:
                            _jsonl_candidates[_no_space].append((_t, _p))
                    if _n and _g:
                        _cjk = _cjk_prefix(_n)
                        for _key in [_n, _cjk, _n.replace(' ', '')]:
                            if _key and _key not in name_gender:
                                name_gender[_key] = _g
            except Exception:
                pass

for _n, _records in _jsonl_candidates.items():
    _records.sort(key=lambda x: x[0])
    name_party[_n] = _records[-1][1]   # 最新一筆日期的黨籍

# 財產申報名字可能含原住民族後綴（無空格），以 CJK 前綴回頭補查
# e.g. '李紀財MulanengPaliuliu' → 如果直接在 name_party 找不到，改查 '李紀財'
def _lookup_party(full_name):
    if full_name in name_party:
        return name_party[full_name]
    cjk = _cjk_prefix(full_name)
    if cjk and cjk in name_party:
        return name_party[cjk]
    return ''

# ── 第三層：手動覆寫（轉黨、資料有誤、字形差異等）────────────────────────────
PARTY_OVERRIDE = {
    '林國成': '台灣民眾黨',
    '郭美秀': '中國國民黨',
    # JSONL 字形差異：鳯(U+9CF3) vs 鳳(U+9CF3→U+9CE5)
    '林蔡鳳梅': '無黨籍及未經政黨推薦',
    # JSONL 使用簡體 黄(U+9EC4) 而非正體 黃(U+9EC3)
    '黃肇輝': '民主進步黨',
    # 不在選舉資料庫，手動補登
    '李啟維': '民主進步黨',
    '林庭秝': '中國國民黨',
    '許采蓁': '中國國民黨',
}
name_party.update(PARTY_OVERRIDE)

people = {}  # name -> record

# 已過世或其他需排除的人員
EXCLUDE_NAMES = {'許家蓓'}

for person_dir_name in os.listdir(DATA_DIR):
    person_dir = os.path.join(DATA_DIR, person_dir_name)
    if not os.path.isdir(person_dir):
        continue

    person_recs = []
    for f in sorted(os.listdir(person_dir)):
        if not f.endswith('.json'):
            continue
        try:
            with open(os.path.join(person_dir, f), encoding='utf-8') as fp:
                d = json.load(fp)
            # 只收錄廉政專刊第291期（含）之後的申報
            link = d.get('原始連結', '')
            m = _re.search(r'第(\d+)期', link)
            if not m or int(m.group(1)) < 291:
                continue
            # 排除卸(離)職申報，只保留就職/年度申報
            if '卸' in d.get('申報類別', '') or '離職' in d.get('申報類別', ''):
                continue
            titles = [s.get('職稱', '') for s in d.get('服務機關紀錄', [])]
            if not any(t in TARGET_TITLES for t in titles):
                continue
            date = d.get('申報日', '')
            person_recs.append((date, d, titles))
        except Exception:
            pass

    if not person_recs:
        continue

    # ── 只保留現任 ──────────────────────────────────────────────────────────────
    # 立法委員：第11屆任期自 2024-02-01，須有該日期之後的申報
    # 議員/議長/副議長：第19屆任期自 2022-12，須有 2023-01-01 之後的申報
    latest_date_check = max(r[0] for r in person_recs)
    all_titles = {t for _, _, ts in person_recs for t in ts}
    is_legislator_only = '立法委員' in all_titles and not any(
        t in {'議員', '議長', '副議長'} for t in all_titles)
    if is_legislator_only:
        if latest_date_check < '2024-02-01':
            continue
    else:
        if latest_date_check < '2023-01-01':
            continue

    # 按「日期 asc, 車輛數 desc」排序
    # 同一天有多份申報時，優先保留車輛最多的那份作為代表
    person_recs.sort(key=lambda x: (x[0], -len(x[1].get('汽車', []))))

    # ── 建立歷史價格表：car_key → (price, date)（每個 key 只保留最早有效價格）──
    price_history = {}
    for hist_date, hist_d, _ in person_recs:
        for car in hist_d.get('汽車', []):
            k = car_key(car)
            p = parse_price(car.get('取得價額', ''))
            if isinstance(p, int) and k not in price_history:
                price_history[k] = (p, hist_date)

    # ── 最新申報（同日期取車輛最多者，已排在前）──────────────────────────────
    # 找最新日期，再取該日期中車輛最多的那份
    latest_date = person_recs[-1][0]
    latest_candidates = [(d, titles) for date, d, titles in person_recs if date == latest_date]
    latest_candidates.sort(key=lambda x: -len(x[0].get('汽車', [])))
    d, titles = latest_candidates[0]

    name = d.get('申報人姓名', person_dir_name)
    if name in EXCLUDE_NAMES:
        continue

    svc = (d.get('服務機關紀錄') or [{}])[0]
    org = svc.get('服務機關', '')
    title = next((t for t in titles if t in TARGET_TITLES), titles[0])
    county = get_county(org)
    gender = name_gender.get(name, '') or name_gender.get(_cjk_prefix(name), '')
    party_raw = _lookup_party(name)
    party = PARTY_SHORT.get(party_raw, party_raw or '不明')
    region = COUNTY_REGION.get(county, '其他')
    date = person_recs[-1][0]

    NO_BRAND = {'大型重型機車'}

    cars_raw = d.get('汽車', [])
    cars = []
    for car in cars_raw:
        raw = car.get('廠牌型號', '').strip()
        brand = normalize_brand(raw)
        if brand in NO_BRAND:
            continue
        cc_str = car.get('汽缸容量', '').replace(',', '').strip()
        try:
            cc = int(float(cc_str)) if cc_str else 0
        except Exception:
            cc = 0
        price = parse_price(car.get('取得價額', ''))

        # 「超過五年」→ 嘗試從歷史申報回溯
        price_traced = False
        price_traced_date = None
        if price == 'over5':
            k = car_key(car)
            hist = price_history.get(k)
            if hist:
                price = hist[0]
                price_traced = True
                price_traced_date = hist[1]

        # 同一台車重複申報（如換車牌、車牌遺失重領）→ 只計一次，避免總額重複加總
        _note = car.get('取得價額', '') or ''
        if ('同一台車' in _note or '同一輛車' in _note) and any(
                c['brand'] == brand and c['cc'] == cc and c['price'] == price for c in cars):
            continue

        acquired = car.get('登記取得時間', '').strip()
        owner = car.get('所有人', '').strip()

        cars.append({
            'brand': brand,
            'raw': raw,
            'cc': cc,
            'luxury': brand in LUXURY_BRANDS,
            'supercar': brand in SUPERCAR_BRANDS,
            'price': price,
            'price_traced': price_traced,
            'price_traced_date': price_traced_date,
            'acquired': acquired,
            'owner': owner,
        })


    # tag each car: is_self = owner name matches politician name
    for car in cars:
        car['is_self'] = (car['owner'] == name)

    luxury_count = sum(1 for c in cars if c['luxury'])
    supercar_count = sum(1 for c in cars if c['supercar'])
    known_prices = [c['price'] for c in cars if isinstance(c['price'], int)]
    total_price = sum(known_prices) if known_prices else None
    price_coverage = len(known_prices)
    traced_count = sum(1 for c in cars if c.get('price_traced'))
    self_count = sum(1 for c in cars if c['is_self'])
    spouse_count = len(cars) - self_count

    people[name] = {
        'name': name,
        'title': title,
        'county': county,
        'region': region,
        'org': org,
        'party': party,
        'gender': gender,
        'date': date,
        'cars': cars,
        'car_count': len(cars),
        'luxury_count': luxury_count,
        'supercar_count': supercar_count,
        'total_price': total_price,
        'price_coverage': price_coverage,
        'traced_count': traced_count,
        'self_count': self_count,
        'spouse_count': spouse_count,
    }

result = sorted(people.values(), key=lambda x: (-x['luxury_count'], -x['car_count'], x['county']))

out_path = os.path.join(OUT_DIR, 'cars_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

print(f'匯出完成：{len(result)} 人 → {out_path}')
unknown_party = [p['name'] for p in result if p['party'] == '不明']
print(f'\n黨籍不明：{len(unknown_party)} 人')
if unknown_party:
    for nm in unknown_party:
        print(f'  {nm}')
county_counts = defaultdict(int)
for p in result:
    county_counts[p['county']] += 1
print('\n縣市人數:')
for c, n in sorted(county_counts.items(), key=lambda x: -x[1]):
    print(f'  {n:3d}  {c}')
