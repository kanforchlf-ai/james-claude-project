'use strict';
// family_network.js — 政治家族網絡視覺化
// Usage: node family_network.js
// 目前固定輸出賴清海家族，作為 Route B 概念原型

const fs   = require('fs');
const path = require('path');

const OUTPUT = path.join(__dirname, '賴清海_家族網絡.html');

// ── 家族樹定義（手動） ────────────────────────────────────────────
// relation: 從父節點看子節點的關係
const FAMILY_TREE = {
  name: '賴清海', relation: null,
  children: [
    {
      name: '賴誠吉', relation: '兒子',
      sideLinks: [{ name: '林柏榕', relation: '姻親' }],
      children: [
        { name: '賴順仁', relation: '兒子', children: [] }
      ]
    }
  ]
};

// 所有成員列表（含側連）
const MEMBERS = ['賴清海', '賴誠吉', '賴順仁', '林柏榕'];

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
    const line = lines[i].trim(); if (!line) continue;
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
  if (p === '台灣民眾黨') return '民眾黨';
  if (p === '無' || p === '無黨籍及未經政黨推薦') return '無黨籍';
  return p;
}
function rocToWestern(n) { return isNaN(n) ? null : n + 1911; }
function electionYear(name) {
  const m = (name || '').match(/^(\d+)年/);
  return m ? rocToWestern(parseInt(m[1], 10)) : null;
}
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const PARTY_COLORS = {
  '民進黨': '#1B7837', '國民黨': '#1954A6', '民眾黨': '#28C8C8',
  '時代力量': '#C8880A', '社民黨': '#E06030', '親民黨': '#FF8C00',
  '無黨籍': '#888888', '不明': '#aaaaaa',
};
function partyColor(p) { return PARTY_COLORS[p] || '#888'; }

// ── 載入資料 ──────────────────────────────────────────────────────
const allParties    = parseCSV(path.join(__dirname, 'parties.csv'));
const allSupplement = parseCSV(path.join(__dirname, 'supplement.csv'));

// ── 建立每人資料 ──────────────────────────────────────────────────
function buildPerson(name) {
  function mapElec(r) {
    return {
      year    : electionYear(r['選舉名稱']),
      elName  : r['選舉名稱'] || '',
      county  : r['縣市'] || '',
      district: r['選區別'] || '',
      party   : normalizeParty(r['政黨']),
      won     : r['當選註記'] === '*',
    };
  }
  const fromP    = allParties.filter(r => r['姓名'] === name).map(mapElec);
  const fromS    = allSupplement.filter(r => r['姓名'] === name).map(mapElec);
  const seen     = new Set(fromP.map(e => `${e.year}|${e.elName}`));
  const elections = [...fromP, ...fromS.filter(e => !seen.has(`${e.year}|${e.elName}`))]
    .sort((a, b) => (a.year || 0) - (b.year || 0));

  const won     = elections.filter(e => e.won);
  const current = elections.length ? elections[elections.length - 1].party : '不明';

  // 主要選區
  const distCount = {};
  for (const e of won) {
    const k = [e.county, e.district].filter(Boolean).join(' ');
    if (k) distCount[k] = (distCount[k] || 0) + 1;
  }
  const mainDist = Object.entries(distCount).sort((a, b) => b[1] - a[1])[0]?.[0] || '';
  const firstYear = elections[0]?.year;
  const lastYear  = elections[elections.length - 1]?.year;

  return { name, elections, wins: won.length, total: elections.length,
           currentParty: current, mainDist, firstYear, lastYear };
}

const persons = Object.fromEntries(MEMBERS.map(n => [n, buildPerson(n)]));

// ── HTML 元件 ─────────────────────────────────────────────────────
function personCard(name) {
  const p = persons[name];
  const color = partyColor(p.currentParty);
  const yearRange = p.firstYear && p.lastYear
    ? (p.firstYear === p.lastYear ? `${p.firstYear}` : `${p.firstYear}–${p.lastYear}`)
    : null;
  const noData = p.total === 0;

  return `<div class="p-card" id="card-${esc(name)}" style="border-left:4px solid ${color}">
  <div class="p-name">${esc(name)}</div>
  <span class="p-badge" style="background:${color}">${esc(p.currentParty)}</span>
  ${p.mainDist ? `<div class="p-dist">${esc(p.mainDist)}</div>` : ''}
  ${noData
    ? `<div class="p-stat muted">歷史資料不足</div>`
    : `<div class="p-stat"><strong>${p.wins}</strong> 次當選 <span class="muted">／ ${p.total} 次參選</span></div>`}
  ${yearRange ? `<div class="p-years muted">${yearRange}</div>` : ''}
</div>`;
}

function electionTable(name) {
  const p = persons[name];
  if (p.total === 0) return `<p class="no-data">parties.csv 中無此人選舉紀錄（資料可能早於資料庫涵蓋範圍）</p>`;
  const rows = p.elections.map(e => {
    const place = [e.county, e.district].filter(Boolean).join(' ');
    const color = partyColor(e.party);
    const result = e.won
      ? `<span class="badge-won">✓ 當選</span>`
      : `<span class="badge-lost">落選</span>`;
    return `<tr>
      <td>${e.year || '?'}</td>
      <td>${esc(e.elName)}</td>
      <td>${esc(place)}</td>
      <td><span class="p-badge" style="background:${color}">${esc(e.party)}</span></td>
      <td>${result}</td>
    </tr>`;
  }).join('');
  return `<table class="el-table">
    <thead><tr><th>年份</th><th>選舉</th><th>選區</th><th>政黨</th><th>結果</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

// ── 家族樹 HTML ───────────────────────────────────────────────────
// 結構：每一代一個 .gen 橫列，中間用 .connector 連接
const treeHTML = `
<div class="tree-wrap">

  <!-- 第一代 -->
  <div class="gen">
    <div class="node-wrap">
      ${personCard('賴清海')}
    </div>
  </div>

  <!-- 連接線：兒子 -->
  <div class="v-connector">
    <div class="v-line"></div>
    <span class="v-label">兒子</span>
    <div class="v-line"></div>
  </div>

  <!-- 第二代：賴誠吉 + 姻親 林柏榕 -->
  <div class="gen gen-row">
    <div class="node-wrap">
      ${personCard('賴誠吉')}
    </div>
    <div class="h-connector">
      <div class="h-line"></div>
      <span class="h-label">姻親</span>
      <div class="h-line"></div>
    </div>
    <div class="node-wrap">
      ${personCard('林柏榕')}
    </div>
  </div>

  <!-- 連接線：兒子（賴誠吉 → 賴順仁，左對齊於賴誠吉） -->
  <div class="v-connector">
    <div class="v-line"></div>
    <span class="v-label">兒子</span>
    <div class="v-line"></div>
  </div>

  <!-- 第三代 -->
  <div class="gen">
    <div class="node-wrap">
      ${personCard('賴順仁')}
    </div>
  </div>

</div>`;

// ── 詳細選舉資料 ─────────────────────────────────────────────────
const detailHTML = MEMBERS.map(name => `
<section class="detail-section">
  <h3><span class="detail-dot" style="background:${partyColor(persons[name].currentParty)}"></span>${esc(name)} 選舉明細</h3>
  ${electionTable(name)}
</section>`).join('');

// ── 完整 HTML ─────────────────────────────────────────────────────
const today = new Date().toISOString().slice(0, 10);
const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>賴清海 家族政治網絡</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans TC', -apple-system, sans-serif;
  background: #f4f6f9; color: #222; font-size: 15px; line-height: 1.7;
  padding: 2rem;
}

/* ── Page header ── */
.page-header {
  max-width: 860px; margin: 0 auto 2rem;
}
.page-header h1 { font-size: 1.6rem; font-weight: 700; color: #1b2a3b; }
.page-header p  { color: #666; font-size: 0.9rem; margin-top: 0.3rem; }

/* ── Tree wrap ── */
.tree-wrap {
  max-width: 860px; margin: 0 auto 2.5rem;
  background: #fff; border-radius: 14px;
  padding: 2.5rem 2rem;
  box-shadow: 0 2px 12px rgba(0,0,0,.08);
  display: flex; flex-direction: column; align-items: center; gap: 0;
}

/* ── Person card ── */
.node-wrap { display: flex; }
.p-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 1rem 1.2rem; min-width: 160px; max-width: 200px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  transition: box-shadow .15s;
}
.p-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,.12); }
.p-name  { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.35rem; }
.p-badge {
  display: inline-block; padding: 1px 8px; border-radius: 4px;
  color: #fff; font-size: 0.75rem; font-weight: 600;
}
.p-dist  { font-size: 0.8rem; color: #555; margin-top: 0.3rem; }
.p-stat  { font-size: 0.85rem; margin-top: 0.4rem; }
.p-years { font-size: 0.78rem; margin-top: 0.2rem; }
.muted   { color: #999; }

/* ── Gen row (horizontal) ── */
.gen { display: flex; justify-content: center; }
.gen-row { display: flex; align-items: center; gap: 0; }

/* ── Vertical connector ── */
.v-connector {
  display: flex; flex-direction: column; align-items: center; padding: 0;
}
.v-line { width: 2px; height: 22px; background: #d1d5db; }
.v-label {
  background: #f3f4f6; border: 1px solid #d1d5db;
  border-radius: 12px; padding: 1px 10px;
  font-size: 0.75rem; color: #6b7280; white-space: nowrap;
}

/* ── Horizontal connector (姻親) ── */
.h-connector {
  display: flex; align-items: center; padding: 0 4px;
  margin-top: -1.5rem; /* align with middle of cards */
}
.h-line  { height: 2px; width: 28px; background: #d1d5db; }
.h-label {
  background: #fef9c3; border: 1px solid #fde047;
  border-radius: 12px; padding: 1px 10px;
  font-size: 0.75rem; color: #854d0e; white-space: nowrap;
}

/* ── Detail sections ── */
.detail-wrap { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.2rem; }
.detail-section {
  background: #fff; border-radius: 10px; padding: 1.3rem 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.detail-section h3 {
  font-size: 1rem; font-weight: 600; color: #1b2a3b;
  display: flex; align-items: center; gap: 0.5rem;
  border-bottom: 1px solid #eee; padding-bottom: 0.5rem; margin-bottom: 1rem;
}
.detail-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}

/* ── Election table ── */
.el-table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
.el-table th {
  background: #f6f8fa; border: 1px solid #e8e8e8;
  padding: 0.45rem 0.7rem; text-align: left; font-weight: 600;
}
.el-table td { border: 1px solid #e8e8e8; padding: 0.45rem 0.7rem; vertical-align: middle; }
.badge-won  { color: #166534; font-weight: 700; }
.badge-lost { color: #bbb; }
.no-data    { color: #aaa; font-size: 0.87rem; font-style: italic; }

/* ── Footer ── */
.page-footer {
  max-width: 860px; margin: 2rem auto 0;
  font-size: 0.78rem; color: #aaa; text-align: right;
}
</style>
</head>
<body>

<div class="page-header">
  <h1>賴清海 家族政治網絡</h1>
  <p>三代政治世家・臺中市・國民黨　｜　資料來源：中選會開放資料、readr-media ccm_search.csv</p>
</div>

${treeHTML}

<div class="detail-wrap">
  ${detailHTML}
</div>

<div class="page-footer">產生日期：${today}</div>

</body>
</html>`;

fs.writeFileSync(OUTPUT, html, 'utf-8');
console.log(`Saved: ${OUTPUT}`);
