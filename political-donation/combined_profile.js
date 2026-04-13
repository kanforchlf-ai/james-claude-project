'use strict';
// combined_profile.js — 產生多人政治履歷單一 HTML
// Usage: node combined_profile.js

const fs   = require('fs');
const path = require('path');

const TARGETS = ['蔡英文', '韓國瑜', '柯文哲', '柯建銘', '苗博雅', '蕭景田'];
const OUTPUT  = path.join(__dirname, '政治人物選舉紀錄.html');

// ── CSV helpers ───────────────────────────────────────────────────
function splitCSVLine(line) {
  const out = []; let cur = '', inQ = false;
  for (const ch of line) {
    if (ch === '"') { inQ = !inQ; }
    else if (ch === ',' && !inQ) { out.push(cur); cur = ''; }
    else { cur += ch; }
  }
  out.push(cur);
  return out;
}
function parseCSV(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const text = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const lines = text.split('\n');
  const headers = splitCSVLine(lines[0]);
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const cols = splitCSVLine(line);
    const row = {};
    headers.forEach((h, idx) => { row[h.trim()] = (cols[idx] || '').trim(); });
    rows.push(row);
  }
  return rows;
}

function normalizeParty(p) {
  if (!p) return '無黨籍';
  p = p.trim();
  if (p === '民主進步黨' || p === '中國民主進步黨') return '民進黨';
  if (p === '中國國民黨') return '國民黨';
  if (p === '台灣民眾黨' || p === '中國民眾黨') return '民眾黨';
  if (p === '無' || p === '無黨籍及未經政黨推薦') return '無黨籍';
  if (p === '綠黨社會民主黨聯盟') return '社民黨';
  return p;
}
function rocToWestern(n) { return isNaN(n) ? null : n + 1911; }
function electionYear(name) {
  const m = name.match(/^(\d+)年/);
  return m ? rocToWestern(parseInt(m[1], 10)) : null;
}
function formatBirth(s) {
  if (!s || s.startsWith('0')) return null;
  const parts = s.split('-');
  if (parts.length < 1) return null;
  const y = parseInt(parts[0]);
  if (isNaN(y) || y < 1900) return null;
  const m = parts[1] && parts[1] !== '00' ? parseInt(parts[1]) : null;
  const d = parts[2] && parts[2] !== '00' ? parseInt(parts[2]) : null;
  if (!m) return `${y} 年`;
  if (!d) return `${y} 年 ${m} 月`;
  return `${y} 年 ${m} 月 ${d} 日`;
}

// ── Load CSVs ─────────────────────────────────────────────────────
console.log('Loading CSVs...');
const allParties    = parseCSV(path.join(__dirname, 'parties.csv'));
const allSupplement = parseCSV(path.join(__dirname, 'supplement.csv'));
const allList       = parseCSV(path.join(__dirname, 'list.csv'));
const allSpouse     = parseCSV(path.join(__dirname, 'spouse.csv'));
const allIncomes    = parseCSV(path.join(__dirname, 'incomes.csv'));
const allCCM        = parseCSV(path.join(__dirname, 'ccm_search.csv'));
console.log(`  parties=${allParties.length}, list=${allList.length}, incomes=${allIncomes.length}, ccm=${allCCM.length}`);

// ── Build profile for one person ──────────────────────────────────
function buildProfile(name) {
  // Elections
  function mapElec(r) {
    return {
      code    : r['選舉代碼'] || '',
      elName  : r['選舉名稱'] || '',
      year    : electionYear(r['選舉名稱']),
      county  : r['縣市'] || '',
      district: r['選區別'] || '',
      party   : normalizeParty(r['政黨']),
      won     : r['當選註記'] === '*',
      gender  : r['性別'] || '',
      birth   : r['出生日期'] || '',
      edu     : r['學歷'] || '',
    };
  }
  const fromParties = allParties.filter(r => r['姓名'] === name).map(mapElec);
  const fromSupp    = allSupplement.filter(r => r['姓名'] === name).map(mapElec);
  const seenCodes   = new Set(fromParties.map(e => e.code));
  const elections   = [...fromParties, ...fromSupp.filter(e => !seenCodes.has(e.code))]
    .sort((a, b) => {
      const ya = a.year || 9999, yb = b.year || 9999;
      return ya !== yb ? ya - yb : a.code.localeCompare(b.code);
    });

  // Positions from list.csv (財產申報 only)
  const rawPos = allList
    .filter(r => r['姓名'] === name && r['種類'] === '財產申報')
    .map(r => ({ date: r['申報日'] || '', org: r['服務機關'] || '', title: r['職稱'] || '' }))
    .sort((a, b) => a.date.localeCompare(b.date));
  const posMap = new Map();
  for (const p of rawPos) {
    const key = `${p.org}|${p.title}`;
    if (!posMap.has(key)) posMap.set(key, { ...p, dateEnd: p.date });
    else posMap.get(key).dateEnd = p.date;
  }
  const positions = [...posMap.values()].sort((a, b) => a.date.localeCompare(b.date));

  // Spouse
  const spouseRow  = allSpouse.find(r => r['姓名'] === name);
  const spouseName = spouseRow ? spouseRow['配偶'] : '';

  // Party history
  const partyHistory = [];
  let lastParty = null;
  for (const e of elections) {
    if (e.party !== lastParty) {
      partyHistory.push({ party: e.party, year: e.year, elName: e.elName });
      lastParty = e.party;
    }
  }
  const currentParty = partyHistory.length ? partyHistory[partyHistory.length - 1].party : '不明';

  // Donations breakdown
  const donRows = allIncomes.filter(r => {
    const cand = r['擬參選人／政黨'] || '';
    return cand === name;
  });
  const incomeByType = {};
  let totalIncome = 0;
  for (const r of donRows) {
    const amt = parseFloat(r['收入金額'] || '0');
    if (isNaN(amt) || amt <= 0) continue;
    const type = r['收支科目'] || '其他';
    incomeByType[type] = (incomeByType[type] || 0) + amt;
    totalIncome += amt;
  }
  const donationTypes = Object.entries(incomeByType)
    .sort((a, b) => b[1] - a[1])
    .map(([type, amt]) => ({ type, amt, pct: totalIncome > 0 ? (amt / totalIncome * 100) : 0 }));

  const ref     = elections[0] || {};
  const birthFmt = formatBirth(ref.birth || '');
  const wonCount = elections.filter(e => e.won).length;

  // Relatives from ccm_search.csv (readr-media curated)
  const relatives = allCCM
    .filter(r => r['議員'] === name && r['親屬姓名'])
    .map(r => ({ relation: r['關係'], relName: r['親屬姓名'], region: r['區域'] }));

  return {
    name, elections, positions, spouseName, partyHistory, currentParty,
    gender: ref.gender || '', birth: birthFmt,
    edu: elections.find(e => e.edu)?.edu || '',
    wonCount, lostCount: elections.length - wonCount,
    totalElections: elections.length,
    totalIncome, donationTypes, relatives,
  };
}

const profiles = TARGETS.map(buildProfile);
console.log('Profiles built:');
profiles.forEach(p => console.log(`  ${p.name}: ${p.totalElections} 選舉, ${p.positions.length} 職位, ${p.donationTypes.length} 獻金類型`));

// ── Helpers for HTML ──────────────────────────────────────────────
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function fmtMoney(n) {
  if (n >= 1e8) return (n / 1e8).toFixed(1).replace(/\.0$/, '') + ' 億';
  if (n >= 1e4) return Math.round(n / 1e4) + ' 萬';
  return n.toLocaleString();
}

const PARTY_COLORS = {
  '民進黨': '#1B7837', '國民黨': '#1954A6', '民眾黨': '#28C8C8',
  '時代力量': '#C8880A', '台灣基進': '#B22222', '社民黨': '#E06030',
  '社會民主黨': '#E06030', '親民黨': '#FF8C00', '新黨': '#DC143C',
  '無黨籍': '#888888', '不明': '#aaaaaa',
};
function partyColor(p) { return PARTY_COLORS[p] || '#888'; }
function initial(name) { return name ? name[0] : '?'; }

// ── Sidebar items ─────────────────────────────────────────────────
const sidebarHTML = profiles.map((p, i) => {
  const color = partyColor(p.currentParty);
  return `<div class="sidebar-item ${i === 0 ? 'active' : ''}" onclick="showProfile(${i})" data-idx="${i}">
  <div class="avatar" style="background:${color}">${esc(initial(p.name))}</div>
  <span>${esc(p.name)}</span>
</div>`;
}).join('\n');

// ── Per-person panel HTML ─────────────────────────────────────────
function buildDonationBar(p) {
  if (p.donationTypes.length === 0) return `<p class="no-data">無政治獻金申報資料</p>`;
  const topType = p.donationTypes[0];
  let html = `<div class="don-summary">
    <span class="don-total">總計 <strong>${fmtMoney(p.totalIncome)}</strong> 元</span>
    <span class="don-top-label">最多來源：<strong style="color:#1B7837">${esc(topType.type)}</strong>（${topType.pct.toFixed(1)}%）</span>
  </div>
  <div class="don-bars">`;
  for (const d of p.donationTypes) {
    html += `<div class="don-row">
      <div class="don-label">${esc(d.type)}</div>
      <div class="don-bar-wrap">
        <div class="don-bar" style="width:${d.pct.toFixed(1)}%;background:${partyColor(p.currentParty)}"></div>
      </div>
      <div class="don-pct">${d.pct.toFixed(1)}%</div>
      <div class="don-amt">${fmtMoney(d.amt)}</div>
    </div>`;
  }
  html += `</div>`;
  return html;
}

function buildElectionRows(p) {
  if (p.elections.length === 0) return `<p class="no-data">無參選紀錄</p>`;
  let html = `<table class="el-table"><thead><tr>
    <th>年份</th><th>選舉</th><th>縣市／選區</th><th>政黨</th><th>結果</th>
  </tr></thead><tbody>`;
  for (const e of p.elections) {
    const place = [e.county, e.district].filter(Boolean).join(' ');
    const color = partyColor(e.party);
    const won = e.won
      ? `<span class="won">✓ 當選</span>`
      : `<span class="lost">落選</span>`;
    html += `<tr>
      <td>${e.year || '?'}</td>
      <td>${esc(e.elName)}</td>
      <td>${esc(place)}</td>
      <td><span class="party-badge" style="background:${color}">${esc(e.party)}</span></td>
      <td>${won}</td>
    </tr>`;
  }
  html += `</tbody></table>`;
  return html;
}

function buildPositionList(p) {
  if (p.positions.length === 0) return `<p class="no-data">無廉政專刊財產申報職位紀錄</p>`;
  let html = `<ul class="pos-list">`;
  for (const pos of p.positions) {
    const dateStr = pos.date === pos.dateEnd ? pos.date : `${pos.date} ～ ${pos.dateEnd}`;
    html += `<li>
      <div class="pos-dot"></div>
      <div class="pos-body">
        <strong>${esc(pos.org)}</strong>　${esc(pos.title)}
        <span class="pos-date">${esc(dateStr)}</span>
      </div>
    </li>`;
  }
  html += `</ul>`;
  return html;
}

function buildRelativesSection(p) {
  if (!p.relatives || p.relatives.length === 0)
    return `<p class="no-data">ccm_search.csv 中無此人親屬記錄（資料以縣市議員為主）</p>`;
  const rows = p.relatives.map(r =>
    `<tr><td>${esc(r.relation)}</td><td><strong>${esc(r.relName)}</strong></td><td style="color:#888;font-size:0.85rem;">${esc(r.region)}</td></tr>`
  ).join('');
  return `<table class="el-table">
  <thead><tr><th>關係</th><th>姓名</th><th>區域</th></tr></thead>
  <tbody>${rows}</tbody>
</table>
<p style="font-size:0.78rem;color:#aaa;margin-top:0.6rem;">資料來源：readr-media ccm_search.csv</p>`;
}

function buildPartyHistory(p) {
  if (p.partyHistory.length <= 1) {
    return `<p>自紀錄以來始終為 <span class="party-badge" style="background:${partyColor(p.currentParty)}">${esc(p.currentParty)}</span></p>`;
  }
  return `<ul class="party-hist">` + p.partyHistory.map(ph =>
    `<li>${ph.year || '?'} 年 → <span class="party-badge" style="background:${partyColor(ph.party)}">${esc(ph.party)}</span></li>`
  ).join('') + `</ul>`;
}

const panelsHTML = profiles.map((p, i) => {
  const color = partyColor(p.currentParty);
  const partyBadge = `<span class="party-badge-lg" style="background:${color}">${esc(p.currentParty)}</span>`;
  const basicInfo = [
    p.gender ? `${p.gender}` : '',
    p.birth ? `${p.birth}` : '',
  ].filter(Boolean).join('　');

  return `<div class="panel ${i === 0 ? 'active' : ''}" id="panel-${i}">

  <div class="person-header">
    <div class="avatar-lg" style="background:${color}">${esc(initial(p.name))}</div>
    <div class="person-info">
      <h1>${esc(p.name)} ${partyBadge}</h1>
      ${basicInfo ? `<p class="person-sub">${esc(basicInfo)}</p>` : ''}
      ${p.edu ? `<p class="person-sub">${esc(p.edu)}</p>` : ''}
      ${p.spouseName ? `<p class="person-sub">配偶：${esc(p.spouseName)}</p>` : ''}
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">參選次數</div>
      <div class="stat-value">${p.totalElections} 次</div>
      <div class="stat-sub">當選 ${p.wonCount}・未當選 ${p.lostCount}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">職位紀錄</div>
      <div class="stat-value">${p.positions.length} 筆</div>
      <div class="stat-sub">廉政專刊財產申報</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">政黨歷程</div>
      <div class="stat-value">${p.partyHistory.length} 個政黨</div>
      <div class="stat-sub">目前：${esc(p.currentParty)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">獻金申報總額</div>
      <div class="stat-value" style="color:${color}">${p.totalIncome > 0 ? fmtMoney(p.totalIncome) : '—'}</div>
      <div class="stat-sub">${p.totalIncome > 0 ? p.donationTypes[0]?.type + ' 為最大宗' : '無申報資料'}</div>
    </div>
  </div>

  <section>
    <h2>政黨歷程</h2>
    ${buildPartyHistory(p)}
  </section>

  <section>
    <h2>參選紀錄（${p.totalElections} 筆）</h2>
    ${buildElectionRows(p)}
  </section>

  <section>
    <h2>職位時間軸（${p.positions.length} 筆）</h2>
    ${buildPositionList(p)}
  </section>

  <section>
    <h2>政治獻金收入</h2>
    ${buildDonationBar(p)}
  </section>

  <section>
    <h2>親屬關係（${p.relatives.length} 筆）</h2>
    ${buildRelativesSection(p)}
  </section>

</div>`;
}).join('\n');

// ── Full HTML ─────────────────────────────────────────────────────
const today = new Date().toISOString().slice(0, 10);
const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>政治人物選舉紀錄</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans TC', -apple-system, sans-serif;
  font-size: 15px; line-height: 1.7; color: #222;
  background: #f0f2f5; display: flex; min-height: 100vh;
}

/* ── Sidebar ── */
.sidebar {
  width: 220px; min-height: 100vh; background: #1b2a3b;
  display: flex; flex-direction: column; flex-shrink: 0;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
}
.sidebar-title {
  padding: 1.5rem 1.2rem 0.5rem;
  font-size: 0.72rem; font-weight: 600; color: #7a9ab8;
  letter-spacing: 0.08em; text-transform: uppercase;
}
.sidebar-item {
  display: flex; align-items: center; gap: 0.85rem;
  padding: 0.75rem 1.2rem; cursor: pointer; transition: background .15s;
  border-left: 3px solid transparent;
}
.sidebar-item:hover { background: rgba(255,255,255,0.06); }
.sidebar-item.active {
  background: rgba(255,255,255,0.1);
  border-left-color: #4fc3f7;
}
.sidebar-item span { color: #d4e3f0; font-size: 0.95rem; font-weight: 500; }
.sidebar-item.active span { color: #fff; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 1rem; color: #fff; flex-shrink: 0;
}
.sidebar-footer {
  margin-top: auto; padding: 1rem 1.2rem;
  font-size: 0.72rem; color: #4a6a88; line-height: 1.6;
}

/* ── Main ── */
.main { flex: 1; padding: 2rem; max-width: 900px; }

/* ── Panel ── */
.panel { display: none; }
.panel.active { display: block; }

/* ── Person header ── */
.person-header {
  display: flex; align-items: center; gap: 1.2rem;
  background: #fff; border-radius: 12px;
  padding: 1.5rem; margin-bottom: 1.2rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.avatar-lg {
  width: 64px; height: 64px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 1.6rem; color: #fff; flex-shrink: 0;
}
.person-info h1 { font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.person-sub { color: #666; font-size: 0.88rem; margin-top: 0.2rem; }
.party-badge-lg {
  display: inline-block; padding: 2px 10px; border-radius: 4px;
  color: #fff; font-size: 0.82rem; font-weight: 600;
}
.party-badge {
  display: inline-block; padding: 1px 7px; border-radius: 3px;
  color: #fff; font-size: 0.78rem; font-weight: 600; white-space: nowrap;
}

/* ── Stats grid ── */
.stats-grid {
  display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  background: #fff; border-radius: 10px;
  padding: 1.1rem 1rem; box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.stat-label { font-size: 0.78rem; color: #888; margin-bottom: 0.3rem; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #1b2a3b; line-height: 1.2; }
.stat-sub { font-size: 0.78rem; color: #999; margin-top: 0.25rem; }

/* ── Sections ── */
section {
  background: #fff; border-radius: 10px;
  padding: 1.3rem 1.5rem; margin-bottom: 1.2rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
section h2 {
  font-size: 1rem; font-weight: 600; color: #1b2a3b;
  border-bottom: 1px solid #eee; padding-bottom: 0.5rem; margin-bottom: 1rem;
}

/* ── Election table ── */
.el-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
.el-table th {
  background: #f6f8fa; border: 1px solid #e8e8e8;
  padding: 0.45rem 0.7rem; text-align: left; font-weight: 600; white-space: nowrap;
}
.el-table td { border: 1px solid #e8e8e8; padding: 0.45rem 0.7rem; vertical-align: middle; }
.won  { color: #1B7837; font-weight: 700; }
.lost { color: #bbb; }

/* ── Position list ── */
.pos-list { list-style: none; }
.pos-list li {
  display: flex; align-items: flex-start; gap: 0.8rem;
  padding: 0.6rem 0; border-bottom: 1px solid #f0f0f0;
}
.pos-list li:last-child { border-bottom: none; }
.pos-dot {
  width: 9px; height: 9px; border-radius: 50%; background: #b0c4d8;
  flex-shrink: 0; margin-top: 0.55rem;
}
.pos-body { flex: 1; font-size: 0.9rem; }
.pos-date { display: block; font-size: 0.77rem; color: #999; margin-top: 0.1rem; }

/* ── Party history ── */
.party-hist { list-style: none; display: flex; gap: 0.5rem; flex-wrap: wrap; padding: 0.3rem 0; }
.party-hist li { font-size: 0.9rem; color: #444; }

/* ── Donation bars ── */
.don-summary { display: flex; gap: 1.5rem; margin-bottom: 0.8rem; font-size: 0.9rem; color: #555; }
.don-bars { display: flex; flex-direction: column; gap: 0.55rem; }
.don-row { display: flex; align-items: center; gap: 0.7rem; font-size: 0.85rem; }
.don-label { min-width: 130px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.don-bar-wrap { flex: 1; background: #f0f0f0; border-radius: 3px; height: 10px; overflow: hidden; }
.don-bar { height: 100%; border-radius: 3px; transition: width .3s; }
.don-pct { min-width: 42px; text-align: right; color: #888; }
.don-amt { min-width: 65px; text-align: right; color: #444; font-weight: 500; }

.no-data { color: #aaa; font-size: 0.88rem; font-style: italic; }

@media (max-width: 680px) {
  .stats-grid { grid-template-columns: repeat(2,1fr); }
  .sidebar { width: 180px; }
}
</style>
</head>
<body>

<nav class="sidebar">
  <div class="sidebar-title">候選人</div>
  ${sidebarHTML}
  <div class="sidebar-footer">
    資料來源：中選會、廉政專刊<br>
    產生日期：${today}
  </div>
</nav>

<main class="main">
${panelsHTML}
</main>

<script>
function showProfile(idx) {
  document.querySelectorAll('.sidebar-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });
  document.querySelectorAll('.panel').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });
}
</script>
</body>
</html>`;

fs.writeFileSync(OUTPUT, html, 'utf-8');
console.log(`\nSaved: ${OUTPUT}`);
