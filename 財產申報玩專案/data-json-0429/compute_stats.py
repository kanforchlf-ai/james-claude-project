"""
讀 cars_data.json，輸出 stats.json 給 index.html 使用
"""
import json, sys, os
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'car-watch', 'cars_data.json')

with open(DATA_PATH, encoding='utf-8') as f:
    people = json.load(f)

LUXURY = {'Lexus','Benz','BMW','Audi','Porsche','Volvo','Land Rover',
          'Maserati','Ferrari','Lamborghini','Bentley','McLaren','Jaguar','Rolls-Royce','Acura'}
SUPERCAR = {'Ferrari','Lamborghini','McLaren','Bentley','Maserati','Rolls-Royce'}
SIX = {'台北市','新北市','桃園市','台中市','台南市','高雄市'}

# ── 1. 品牌排行 ──────────────────────────────────────────────────────────────
brand_counter = Counter()
for p in people:
    for c in p['cars']:
        brand_counter[c['brand']] += 1

brands_ranking = [{'brand': b, 'count': c} for b, c in brand_counter.most_common(20)]

# ── 2. 縣市豪車率 ───────────────────────────────────────────────────────────
county_total = defaultdict(int)
county_luxury = defaultdict(int)
county_people = defaultdict(int)
for p in people:
    if not p['cars']:
        continue
    county_total[p['county']]  += len(p['cars'])
    county_luxury[p['county']] += p['luxury_count']
    county_people[p['county']] += 1

county_stats = []
for c in county_total:
    if c in ('立法院', '其他'):
        continue
    total = county_total[c]
    lux   = county_luxury[c]
    county_stats.append({
        'county': c,
        'total': total,
        'luxury': lux,
        'rate': round(lux / total * 100, 1) if total else 0,
        'people': county_people[c],
    })
county_stats.sort(key=lambda x: -x['rate'])

# ── 3. 超跑名人堂 ──────────────────────────────────────────────────────────
supercars_people = []
for p in people:
    sc = [c for c in p['cars'] if c['supercar']]
    if not sc:
        # Also include non-supercar luxury with Porsche
        sc = [c for c in p['cars'] if c['brand'] == 'Porsche']
    if sc:
        supercars_people.append({
            'name': p['name'],
            'title': p['title'],
            'county': p['county'],
            'party': p['party'],
            'gender': p['gender'],
            'car_count': p['car_count'],
            'supercars': sc,
            'all_cars': p['cars'],
        })
supercars_people.sort(key=lambda x: (-len(x['supercars']), -x['car_count']))

# ── 4. 政黨停車場 ──────────────────────────────────────────────────────────
party_total  = defaultdict(int)
party_luxury = defaultdict(int)
party_brands = defaultdict(Counter)

MAIN_PARTIES = {'國民黨','民進黨','民眾黨','時代力量','親民黨','無黨籍','新黨','台灣基進'}

for p in people:
    party = p['party']
    if party not in MAIN_PARTIES:
        continue
    for c in p['cars']:
        party_total[party]  += 1
        if c['luxury']:
            party_luxury[party] += 1
        party_brands[party][c['brand']] += 1

party_stats = []
for party in MAIN_PARTIES:
    tot = party_total[party]
    if tot < 5:
        continue
    lux = party_luxury[party]
    top_brands = [{'brand': b, 'count': c} for b, c in party_brands[party].most_common(5)]
    party_stats.append({
        'party': party,
        'total': tot,
        'luxury': lux,
        'rate': round(lux / tot * 100, 1) if tot else 0,
        'top_brands': top_brands,
    })
party_stats.sort(key=lambda x: -x['rate'])

# ── 5. 性別比較 ────────────────────────────────────────────────────────────
gender_brands = {'男': Counter(), '女': Counter()}
gender_total  = {'男': 0, '女': 0}
gender_luxury = {'男': 0, '女': 0}

for p in people:
    g = p['gender']
    if g not in ('男', '女'):
        continue
    for c in p['cars']:
        gender_brands[g][c['brand']] += 1
        gender_total[g]  += 1
        if c['luxury']:
            gender_luxury[g] += 1

gender_stats = {
    '男': {
        'total': gender_total['男'],
        'luxury': gender_luxury['男'],
        'rate': round(gender_luxury['男'] / gender_total['男'] * 100, 1) if gender_total['男'] else 0,
        'top_brands': [{'brand': b, 'count': c} for b, c in gender_brands['男'].most_common(8)],
    },
    '女': {
        'total': gender_total['女'],
        'luxury': gender_luxury['女'],
        'rate': round(gender_luxury['女'] / gender_total['女'] * 100, 1) if gender_total['女'] else 0,
        'top_brands': [{'brand': b, 'count': c} for b, c in gender_brands['女'].most_common(8)],
    },
}

# ── 6. Tesla / EV ─────────────────────────────────────────────────────────
tesla_people = []
for p in people:
    ev = [c for c in p['cars'] if c['brand'] == 'Tesla']
    if ev:
        tesla_people.append({
            'name': p['name'],
            'title': p['title'],
            'county': p['county'],
            'party': p['party'],
            'gender': p['gender'],
            'ev_count': len(ev),
            'all_cars': p['cars'],
        })
tesla_people.sort(key=lambda x: -x['ev_count'])

# ── 7. 最貴車庫排行 ───────────────────────────────────────────────────────
richest = []
for p in people:
    if p.get('total_price') is None:
        continue
    richest.append({
        'name': p['name'],
        'title': p['title'],
        'county': p['county'],
        'party': p['party'],
        'gender': p.get('gender', ''),
        'total_price': p['total_price'],
        'price_coverage': p.get('price_coverage', 0),
        'car_count': p['car_count'],
        'cars': [
            {
                'brand': c['brand'],
                'raw': c['raw'],
                'cc': c['cc'],
                'luxury': c['luxury'],
                'supercar': c['supercar'],
                'price': c.get('price'),
                'price_traced': c.get('price_traced', False),
                'acquired': c.get('acquired', ''),
            }
            for c in p['cars']
        ],
    })
richest.sort(key=lambda x: -x['total_price'])

# also: single most expensive car
priciest_cars = []
for p in people:
    for c in p['cars']:
        if isinstance(c.get('price'), int):
            priciest_cars.append({
                'name': p['name'],
                'title': p['title'],
                'county': p['county'],
                'party': p['party'],
                'brand': c['brand'],
                'raw': c['raw'],
                'cc': c['cc'],
                'price': c['price'],
                'luxury': c['luxury'],
                'supercar': c['supercar'],
            })
priciest_cars.sort(key=lambda x: -x['price'])

# ── 8. 全體摘要 ────────────────────────────────────────────────────────────
all_cars = [c for p in people for c in p['cars']]
all_prices = [c['price'] for p in people for c in p['cars'] if isinstance(c.get('price'), int)]
summary = {
    'total_people': len(people),
    'total_cars': len(all_cars),
    'luxury_cars': sum(1 for c in all_cars if c['luxury']),
    'supercar_cars': sum(1 for c in all_cars if c['supercar']),
    'tesla_cars': sum(1 for c in all_cars if c['brand'] == 'Tesla'),
    'porsche_cars': sum(1 for c in all_cars if c['brand'] == 'Porsche'),
    'cars_with_price': len(all_prices),
    'max_single_price': max(all_prices) if all_prices else 0,
}

stats = {
    'summary': summary,
    'brands': brands_ranking,
    'counties': county_stats,
    'supercars': supercars_people,
    'parties': party_stats,
    'gender': gender_stats,
    'tesla': tesla_people,
    'richest': richest[:50],
    'priciest_cars': priciest_cars[:30],
}

OUT = os.path.join(os.path.dirname(__file__), '..', 'car-watch', 'stats.json')
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, separators=(',', ':'))
print('stats.json written')
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(f'\n縣市豪車率 Top 5:')
for c in county_stats[:5]:
    print(f"  {c['county']:6s}  {c['rate']}%  ({c['luxury']}/{c['total']})")
print(f'\n超跑人數: {len(supercars_people)}')
print(f'Tesla 人數: {len(tesla_people)}')
