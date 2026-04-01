const fs = require('fs');
const path = require('path');

const CSV_PATH = path.join(__dirname, 'incomes.csv');
const PARTIES_PATH = path.join(__dirname, 'parties.csv');
const OUTPUT_PATH = path.join(__dirname, 'report.html');
const MIN_GROUP_SIZE = 10;

// Normalize party names to short form
function normalizeParty(p) {
  if (!p) return '無黨籍';
  p = p.trim();
  if (p === '民主進步黨' || p === '中國民主進步黨') return '民進黨';
  if (p === '中國國民黨') return '國民黨';
  if (p === '台灣民眾黨' || p === '中國民眾黨') return '民眾黨';
  if (p === '無' || p === '無黨籍及未經政黨推薦') return '無黨籍';
  return p;
}

// Load official party mapping: key = "選舉名稱|縣市|姓名" (precise) or "選舉名稱|姓名" (fallback)
const partyMapPrecise = new Map(); // election|county|name → party
const partyMapFallback = new Map(); // election|name → party (may be ambiguous)

const partyLines = fs.readFileSync(PARTIES_PATH, 'utf-8').replace(/^\uFEFF/, '').split('\n');
const partyHeaders = partyLines[0].split(',');
const pElecIdx = partyHeaders.indexOf('選舉名稱');
const pCountyIdx = partyHeaders.indexOf('縣市');
const pNameIdx = partyHeaders.indexOf('姓名');
const pPartyIdx = partyHeaders.indexOf('政黨');

for (let i = 1; i < partyLines.length; i++) {
  const cols = partyLines[i].split(',');
  const elec = (cols[pElecIdx] || '').trim();
  const county = (cols[pCountyIdx] || '').trim();
  const name = (cols[pNameIdx] || '').trim();
  const party = normalizeParty(cols[pPartyIdx]);
  if (!elec || !name) continue;
  partyMapPrecise.set(`${elec}|${county}|${name}`, party);
  // Only set fallback if not already set (first occurrence wins; ambiguous cases stay as first)
  const fbKey = `${elec}|${name}`;
  if (!partyMapFallback.has(fbKey)) partyMapFallback.set(fbKey, party);
}
console.log(`Official party mappings loaded: ${partyMapPrecise.size} (precise), ${partyMapFallback.size} (fallback)`);

// Lookup party for a candidate given election name and county from incomes data
function lookupParty(election, county, candidate) {
  return partyMapPrecise.get(`${election}|${county}|${candidate}`)
      || partyMapFallback.get(`${election}|${candidate}`)
      || '無黨籍';
}

// ── 1. Parse CSV ──────────────────────────────────────────────────────────────
function parseCSV(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.replace(/^\uFEFF/, '').split('\n');
  const headers = splitCSVLine(lines[0]);
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const cols = splitCSVLine(line);
    const row = {};
    headers.forEach((h, idx) => { row[h] = cols[idx] || ''; });
    rows.push(row);
  }
  return rows;
}

function splitCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') { inQuotes = !inQuotes; }
    else if (ch === ',' && !inQuotes) { result.push(current); current = ''; }
    else { current += ch; }
  }
  result.push(current);
  return result;
}

// ── 2. Load & filter ──────────────────────────────────────────────────────────
console.log('Loading CSV...');
const rows = parseCSV(CSV_PATH);
console.log(`Total rows: ${rows.length}`);

const VALID_SUBJECTS = new Set(['個人捐贈收入', '營利事業捐贈收入']);

// Only keep 立法委員選舉
const isLegislative = name => name.includes('立法委員');

// donorKey → Set of "election||county||candidate" strings
const donorMap = new Map();
// track donor type (個人 or 法人)
const donorType = new Map();
// tag → county (for party lookup)
const tagCounty = new Map();

let kept = 0;
for (const row of rows) {
  if (!isLegislative(row['選舉名稱'])) continue;
  const subject = row['收支科目'];
  if (!VALID_SUBJECTS.has(subject)) continue;

  const name = row['捐贈者／支出對象'].trim();
  const idRaw = row['身分證／統一編號'].trim();
  if (!name || name === '匿名') continue;

  const idPrefix = idRaw.slice(0, 3);
  const donorKey = `${name}|${idPrefix}`;

  const election = row['選舉名稱'].trim();
  const county = row['縣市'].trim();
  const candidate = row['擬參選人／政黨'].trim();
  if (!election || !candidate) continue;

  const tag = `${election}||${county}||${candidate}`;
  tagCounty.set(tag, { election, county, candidate });

  if (!donorMap.has(donorKey)) {
    donorMap.set(donorKey, new Set());
    donorType.set(donorKey, subject === '營利事業捐贈收入' ? '法人' : '個人');
  }
  donorMap.get(donorKey).add(tag);
  kept++;
}

console.log(`Valid legislative donation records: ${kept}`);
console.log(`Unique donors: ${donorMap.size}`);

// ── 3. Only donors who donated to ≥2 DIFFERENT candidates ────────────────────
function getElection(tag) { return tag.split('||')[0]; }
function getCounty(tag) { return tag.split('||')[1]; }
function getCandidate(tag) { return tag.split('||')[2]; }
function getParty(tag) {
  const info = tagCounty.get(tag);
  if (!info) return '無黨籍';
  return lookupParty(info.election, info.county, info.candidate);
}

const multiCandidateDonors = new Map();
for (const [donorKey, tags] of donorMap) {
  const candidates = new Set([...tags].map(getCandidate));
  if (candidates.size >= 2) {
    multiCandidateDonors.set(donorKey, tags);
  }
}
console.log(`Donors who donated to ≥2 different candidates: ${multiCandidateDonors.size}`);

// ── 4. Build cross-candidate pair counts ──────────────────────────────────────
console.log('Computing cross-candidate pairs...');
const pairCounts = new Map(); // pairKey → Set of donorKeys

let dc = 0;
for (const [donorKey, tags] of multiCandidateDonors) {
  dc++;
  if (dc % 5000 === 0) process.stdout.write(`\r  Progress: ${dc}/${multiCandidateDonors.size}`);

  const tagArr = [...tags];
  for (let i = 0; i < tagArr.length; i++) {
    for (let j = i + 1; j < tagArr.length; j++) {
      const tagA = tagArr[i];
      const tagB = tagArr[j];
      // Skip same candidate (shouldn't happen given filter above, but safety check)
      if (getCandidate(tagA) === getCandidate(tagB)) continue;

      const pairKey = tagA < tagB ? `${tagA}:::${tagB}` : `${tagB}:::${tagA}`;
      if (!pairCounts.has(pairKey)) pairCounts.set(pairKey, new Set());
      pairCounts.get(pairKey).add(donorKey);
    }
  }
}
console.log(`\nDone. Total pairs evaluated: ${pairCounts.size}`);

// ── 5. Filter ≥ MIN_GROUP_SIZE ────────────────────────────────────────────────
const significantPairs = [];
for (const [pairKey, donors] of pairCounts) {
  if (donors.size < MIN_GROUP_SIZE) continue;
  const [tagA, tagB] = pairKey.split(':::');
  const elecA = getElection(tagA), candA = getCandidate(tagA), countyA = getCounty(tagA);
  const elecB = getElection(tagB), candB = getCandidate(tagB), countyB = getCounty(tagB);
  const isSameElection = elecA === elecB;

  // Count 個人 vs 法人 breakdown
  let indiv = 0, corp = 0;
  const donorArr = [...donors];
  for (const d of donorArr) {
    if (donorType.get(d) === '法人') corp++; else indiv++;
  }

  const partyA = getParty(tagA);
  const partyB = getParty(tagB);
  const crossParty = partyA !== partyB && partyA !== '無黨籍' && partyB !== '無黨籍';

  significantPairs.push({
    electionA: elecA, candidateA: candA, countyA, partyA,
    electionB: elecB, candidateB: candB, countyB, partyB,
    sameElection: isSameElection,
    crossParty,
    count: donors.size,
    indiv, corp,
    donors: donorArr.sort(),
  });
}

significantPairs.sort((a, b) => b.count - a.count);
console.log(`Significant cross-candidate pairs (≥${MIN_GROUP_SIZE}): ${significantPairs.length}`);

const sameElecPairs = significantPairs.filter(p => p.sameElection);
const crossElecPairs = significantPairs.filter(p => !p.sameElection);
const crossPartyPairs = significantPairs.filter(p => p.crossParty);
const dppKmtPairs = significantPairs.filter(p =>
  (p.partyA === '民進黨' && p.partyB === '國民黨') ||
  (p.partyA === '國民黨' && p.partyB === '民進黨')
);
// Same election + cross party (most meaningful)
const sameElecCrossPartyPairs = significantPairs.filter(p => p.sameElection && p.crossParty);
const sameElecDppKmtPairs = significantPairs.filter(p =>
  p.sameElection && (
    (p.partyA === '民進黨' && p.partyB === '國民黨') ||
    (p.partyA === '國民黨' && p.partyB === '民進黨')
  )
);
console.log(`DPP x KMT pairs (≥${MIN_GROUP_SIZE}): ${dppKmtPairs.length}`);
console.log(`Same election + cross party (≥${MIN_GROUP_SIZE}): ${sameElecCrossPartyPairs.length}`);
console.log(`Same election + DPP x KMT (≥${MIN_GROUP_SIZE}): ${sameElecDppKmtPairs.length}`);
sameElecDppKmtPairs.slice(0,10).forEach(p => console.log(`  [${p.count}] ${p.electionA} | ${p.candidateA}(${p.partyA}) x ${p.candidateB}(${p.partyB})`));
console.log(`  Same election: ${sameElecPairs.length}, Cross election: ${crossElecPairs.length}, Cross party: ${crossPartyPairs.length}`);

// ── 6. Generate HTML ──────────────────────────────────────────────────────────
console.log('Generating HTML report...');

function esc(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function donorDisplay(key) { return esc(key.split('|')[0]); }

const PARTY_COLORS = {
  '民進黨': '#1B7837',
  '國民黨': '#1954A6',
  '民眾黨': '#28C8C8',
  '時代力量': '#FBBE01',
  '台灣基進': '#B22222',
  '社會民主黨': '#E87722',
  '民國黨': '#888888',
  '無黨籍': '#999999',
};

function partyBadge(party) {
  const color = PARTY_COLORS[party] || '#999';
  return `<span class="party-badge" style="background:${color}">${esc(party)}</span>`;
}

function buildTableRows(pairs, limit = 150) {
  return pairs.slice(0, limit).map((p, idx) => {
    const donorList = p.donors.map(d => `<span class="donor">${donorDisplay(d)}</span>`).join(' ');
    const elecTag = p.sameElection ? '<span class="tag same">同屆</span>' : '<span class="tag cross">跨屆</span>';
    const cpTag = p.crossParty ? '<span class="tag xparty">跨黨派</span>' : '';
    const breakdown = `個人 ${p.indiv} / 法人 ${p.corp}`;
    return `
  <tr>
    <td class="rank">${idx + 1}</td>
    <td class="count">${p.count}<br><small>${breakdown}</small></td>
    <td>${elecTag}${cpTag}<br>${esc(p.electionA)}／${esc(p.countyA)}<br><strong>${esc(p.candidateA)}</strong><br>${partyBadge(p.partyA)}</td>
    <td>${esc(p.electionB)}／${esc(p.countyB)}<br><strong>${esc(p.candidateB)}</strong><br>${partyBadge(p.partyB)}</td>
    <td class="donors">${donorList}</td>
  </tr>`;
  }).join('');
}

const tableAll = buildTableRows(significantPairs);
const tableSame = buildTableRows(sameElecPairs);
const tableCross = buildTableRows(crossElecPairs);
const tableCrossParty = buildTableRows(crossPartyPairs);
const tableDppKmt = buildTableRows(dppKmtPairs);
const tableSameElecDppKmt = buildTableRows(sameElecDppKmtPairs);
const tableSameElecCrossParty = buildTableRows(sameElecCrossPartyPairs);

function section(title, desc, tableRows, count) {
  if (!tableRows) return `<p>無符合資料</p>`;
  return `
<h2>${esc(title)}</h2>
<p>${esc(desc)}（共 ${count} 組，下表顯示前 150 組）</p>
<table>
  <thead>
    <tr><th>#</th><th>共同捐款人數</th><th>候選人 A</th><th>候選人 B</th><th>捐款人名單</th></tr>
  </thead>
  <tbody>${tableRows}</tbody>
</table>`;
}

const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>立委選舉跨候選人共同捐款人分析</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #fff; color: #222;
    max-width: 1000px; margin: 0 auto;
    padding: 2rem 1.5rem; line-height: 1.75; font-size: 15px;
  }
  h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
  h2 { font-size: 1.15rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; margin-top: 2.5rem; }
  .meta { color: #666; font-size: 0.9rem; margin-bottom: 1rem; }
  blockquote {
    border-left: 4px solid #ccc; background: #f8f8f8;
    margin: 1rem 0; padding: 0.75rem 1rem; color: #444;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.87rem; margin-top: 1rem; }
  th { background: #f4f4f4; border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; white-space: nowrap; }
  td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; vertical-align: top; }
  td.rank { text-align: center; color: #aaa; width: 2.5rem; }
  td.count { text-align: center; font-weight: 700; color: #c00; width: 5rem; }
  td.count small { display: block; font-weight: 400; color: #888; font-size: 0.78rem; }
  td.donors { color: #555; font-size: 0.8rem; max-width: 350px; }
  span.donor { display: inline-block; background: #f0f0f0; border-radius: 3px; padding: 0 4px; margin: 1px 2px; }
  tr:hover td { background: #fafafa; }
  .tag { display: inline-block; border-radius: 3px; padding: 0 5px; font-size: 0.75rem; font-weight: 600; margin-bottom: 2px; }
  .tag.same { background: #e8f0fe; color: #1a56c4; }
  .tag.cross { background: #fef3e2; color: #b45309; }
  .tag.xparty { background: #fde8e8; color: #991b1b; }
  .party-badge { display: inline-block; border-radius: 3px; padding: 1px 6px; font-size: 0.75rem; color: #fff; font-weight: 600; margin-top: 3px; }
  .note { font-size: 0.83rem; color: #888; margin-top: 0.75rem; }
  .summary-grid { display: flex; gap: 2rem; margin: 1rem 0; flex-wrap: wrap; }
  .summary-item { }
  .summary-item .num { font-size: 1.8rem; font-weight: 700; color: #c00; }
  .summary-item .label { font-size: 0.85rem; color: #666; }
</style>
</head>
<body>
<h1>立委選舉跨候選人共同捐款人分析</h1>
<p class="meta">分析日期：2026-03-31 ｜ 分析範圍：歷屆立法委員選舉 ｜ 門檻：≥${MIN_GROUP_SIZE} 人</p>

<blockquote>
找出「同一批人同時捐款給不同立委候選人」的群體，揭示候選人之間可能存在的利益連結或共同政治背景。同一候選人的跨期捐款已排除。
</blockquote>

<h2>統計摘要</h2>
<div class="summary-grid">
  <div class="summary-item"><div class="num">${multiCandidateDonors.size.toLocaleString()}</div><div class="label">捐給 ≥2 位不同立委的捐款人</div></div>
  <div class="summary-item"><div class="num">${significantPairs.length.toLocaleString()}</div><div class="label">符合門檻的候選人配對組數</div></div>
  <div class="summary-item"><div class="num">${sameElecPairs.length.toLocaleString()}</div><div class="label">同屆選舉配對</div></div>
  <div class="summary-item"><div class="num">${crossElecPairs.length.toLocaleString()}</div><div class="label">跨屆選舉配對</div></div>
  <div class="summary-item"><div class="num">${crossPartyPairs.length.toLocaleString()}</div><div class="label">跨黨派配對</div></div>
  <div class="summary-item"><div class="num">${dppKmtPairs.length.toLocaleString()}</div><div class="label">民進黨 × 國民黨配對</div></div>
  <div class="summary-item"><div class="num">${sameElecDppKmtPairs.length.toLocaleString()}</div><div class="label">同屆民進黨 × 國民黨（最異常）</div></div>
</div>

${section('★★ 同屆選舉 × 民進黨 × 國民黨（最異常）', '在同一場選舉中，同一批人同時捐給民進黨和國民黨候選人——真正的藍綠通吃', tableSameElecDppKmt, sameElecDppKmtPairs.length)}
${section('★ 同屆選舉 × 跨黨派（所有黨）', '在同一場選舉中，同時捐給不同政黨候選人的群體', tableSameElecCrossParty, sameElecCrossPartyPairs.length)}
${section('民進黨 × 國民黨（含跨屆）', '包含跨屆選舉的藍綠通吃配對', tableDppKmt, dppKmtPairs.length)}
${section('全部配對（綜合排行）', '所有符合門檻的跨候選人共同捐款群體', tableAll, significantPairs.length)}
${section('同屆選舉配對', '同一場選舉中，同時捐給兩位不同候選人的群體（可能反映產業或派系連結）', tableSame, sameElecPairs.length)}
${section('跨屆選舉配對', '不同屆選舉之間，同一批人捐給不同候選人（可能反映政治立場轉移或跨期政治網絡）', tableCross, crossElecPairs.length)}

<p class="note">捐款人識別：姓名＋身分證前3碼（個人）或統一編號前3碼（法人）。匿名捐款已排除。</p>
</body>
</html>`;

fs.writeFileSync(OUTPUT_PATH, html, 'utf-8');
console.log(`\nReport saved: ${OUTPUT_PATH}`);
console.log('Top 5:');
significantPairs.slice(0, 5).forEach((p, i) => {
  console.log(`  ${i+1}. [${p.count}人] ${p.candidateA} × ${p.candidateB}  (${p.sameElection ? '同屆' : '跨屆'})`);
});
