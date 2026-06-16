"""
Build index.html — single-page app with landing + 7 feature views
"""
import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE  = os.path.join(os.path.dirname(__file__), '..', 'car-watch')
OUT   = os.path.join(BASE, 'index.html')

with open(os.path.join(BASE, 'cars_data.json'), encoding='utf-8') as f:
    cars_raw = f.read()
with open(os.path.join(BASE, 'stats.json'), encoding='utf-8') as f:
    stats_raw = f.read()

# ─── HTML ─────────────────────────────────────────────────────────────────────
html = r'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🚗 民代車庫</title>
<style>
/* ── Reset & Base ── */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif;background:#f5f5f0;color:#222;overflow-x:hidden}

/* ── Nav ── */
nav{
  position:sticky;top:0;z-index:200;
  background:#fff;border-bottom:2px solid #eee;
  display:flex;align-items:center;gap:0;overflow-x:auto;
  scrollbar-width:none;
}
nav::-webkit-scrollbar{display:none}
.nav-logo{
  flex-shrink:0;padding:.6rem 1.2rem;font-weight:900;font-size:1.05rem;
  color:#1a1a2e;cursor:pointer;white-space:nowrap;border-right:2px solid #eee;
}
.nav-logo:hover{background:#f0f0f0}
.nav-btn{
  flex-shrink:0;padding:.65rem .9rem;font-size:.82rem;font-weight:700;
  color:#555;cursor:pointer;white-space:nowrap;transition:all .15s;
  border-bottom:3px solid transparent;
}
.nav-btn:hover{color:#1a1a2e;background:#fafafa}
.nav-btn.active{color:#e63946;border-bottom-color:#e63946}
.scope-toggle{display:flex;gap:.25rem;padding:.35rem .8rem;border-right:2px solid #eee;flex-shrink:0;align-items:center}
.scope-btn{padding:.28rem .7rem;font-size:.75rem;font-weight:800;border-radius:99px;cursor:pointer;border:2px solid #ddd;background:#fff;color:#666;transition:all .15s;white-space:nowrap;line-height:1}
.scope-btn:hover{border-color:#1a1a2e;color:#1a1a2e}
.scope-btn.active{background:#1a1a2e;color:#fff;border-color:#1a1a2e}
.scope-btn.s-law.active{background:#1565c0;border-color:#1565c0}
.scope-btn.s-council.active{background:#2e7d32;border-color:#2e7d32}

/* ── Views ── */
.view{display:none;min-height:90vh}
.view.active{display:block}

/* ═══════════════════════════════════════════════════════════
   LANDING
═══════════════════════════════════════════════════════════ */
.hero{
  background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
  color:#fff;text-align:center;padding:5rem 2rem 4rem;
}
.hero-emoji{font-size:4rem;display:block;margin-bottom:1rem}
.hero h1{font-size:clamp(2rem,6vw,3.5rem);font-weight:900;letter-spacing:.04em;line-height:1.15}
.hero h1 span{color:#ffd700}
.hero p{margin-top:1rem;font-size:1.05rem;opacity:.8;max-width:580px;margin-left:auto;margin-right:auto;line-height:1.7}

.hero-stats{
  display:flex;justify-content:center;flex-wrap:wrap;gap:2rem;
  margin-top:3rem;padding:2rem;
  background:rgba(255,255,255,.08);border-radius:16px;max-width:700px;margin-left:auto;margin-right:auto;
}
.hero-stat{text-align:center}
.hero-stat-num{font-size:2.5rem;font-weight:900;color:#ffd700;display:block}
.hero-stat-label{font-size:.85rem;opacity:.75;margin-top:.25rem}

.features{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:1.2rem;padding:2.5rem;max-width:1200px;margin:0 auto;
}
.feature-card{
  background:#fff;border-radius:16px;padding:1.8rem 1.5rem;
  box-shadow:0 2px 12px rgba(0,0,0,.08);cursor:pointer;
  transition:transform .15s,box-shadow .15s;
  border-top:4px solid var(--fc,#ccc);
  display:flex;flex-direction:column;gap:.6rem;
}
.feature-card:hover{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,0,0,.15)}
.feature-card .icon{font-size:2.2rem}
.feature-card h3{font-size:1.15rem;font-weight:900}
.feature-card p{font-size:.88rem;color:#666;line-height:1.6}
.feature-card .tag{
  margin-top:auto;display:inline-block;font-size:.75rem;font-weight:700;
  padding:.25rem .7rem;border-radius:99px;background:#f0f0f0;color:#666;
}

.tagline{text-align:center;padding:1.5rem;color:#888;font-size:.85rem}

/* ═══════════════════════════════════════════════════════════
   SHARED PAGE CHROME
═══════════════════════════════════════════════════════════ */
.page-header{
  background:linear-gradient(135deg,#1a1a2e,#0f3460);
  color:#fff;padding:2.5rem 2rem 2rem;
}
.page-header .back{font-size:.82rem;opacity:.6;cursor:pointer;margin-bottom:.8rem;display:inline-block}
.page-header .back:hover{opacity:1}
.page-header h2{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900}
.page-header p{margin-top:.5rem;opacity:.75;font-size:.95rem}

.section-body{padding:2rem;max-width:1100px;margin:0 auto}

/* ═══════════════════════════════════════════════════════════
   1 BRANDS — 品牌排行榜
═══════════════════════════════════════════════════════════ */
.bar-chart{display:flex;flex-direction:column;gap:.7rem;margin-top:1.5rem}
.bar-row{display:flex;align-items:center;gap:.8rem}
.bar-rank{width:1.6rem;font-weight:900;color:#aaa;font-size:.88rem;text-align:right;flex-shrink:0}
.bar-label{width:90px;font-weight:700;font-size:.92rem;flex-shrink:0;text-align:right}
.bar-track{flex:1;background:#eee;border-radius:99px;height:28px;overflow:hidden}
.bar-fill{
  height:100%;border-radius:99px;
  display:flex;align-items:center;padding-left:.7rem;
  font-size:.8rem;font-weight:700;color:#fff;white-space:nowrap;
  transition:width 1s cubic-bezier(.25,.46,.45,.94);
  width:0%;
}
.bar-count{font-size:.82rem;color:#555;flex-shrink:0;width:3rem;text-align:right}
.bar-emoji{width:1.5rem;flex-shrink:0}
.luxury-mark{
  font-size:.7rem;font-weight:900;padding:.15rem .45rem;border-radius:99px;
  background:#ffd700;color:#333;flex-shrink:0;
}

/* ═══════════════════════════════════════════════════════════
   2 MAP — 縣市豪車率
═══════════════════════════════════════════════════════════ */
.map-legend{display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;font-size:.85rem}
.legend-grad{
  width:180px;height:16px;border-radius:8px;
  background:linear-gradient(to right,#fff5e0,#ff6b00);border:1px solid #ddd;
}
.map-grid{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  grid-template-rows:repeat(10,auto);
  gap:.5rem;max-width:520px;
}
.tile{
  border-radius:10px;padding:.6rem .4rem;
  text-align:center;font-size:.78rem;font-weight:700;
  cursor:pointer;transition:transform .1s;border:2px solid transparent;
  min-height:52px;display:flex;flex-direction:column;justify-content:center;
}
.tile:hover{transform:scale(1.06);border-color:#333}
.tile-name{font-size:.8rem}
.tile-rate{font-size:1rem;font-weight:900;margin-top:.15rem}
.tile-empty{opacity:0;pointer-events:none}

.county-list{margin-top:2rem}
.county-row{
  display:flex;align-items:center;gap:.8rem;padding:.6rem 0;
  border-bottom:1px solid #eee;
}
.county-row .cname{width:72px;font-weight:700;font-size:.9rem}
.county-track{flex:1;background:#eee;border-radius:99px;height:22px;overflow:hidden}
.county-fill{height:100%;border-radius:99px;transition:width 1s ease}
.county-rate{width:52px;text-align:right;font-weight:900;font-size:.9rem}
.county-note{font-size:.75rem;color:#aaa;flex-shrink:0}
.rural-badge{
  font-size:.68rem;padding:.15rem .4rem;border-radius:4px;
  background:#888;color:#fff;font-weight:700;flex-shrink:0;
}
.rural-badge.six{background:#1565c0}

/* ═══════════════════════════════════════════════════════════
   3 SUPERCARS — 超跑名人堂
═══════════════════════════════════════════════════════════ */
.hall{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.2rem;margin-top:1.5rem}
.hall-card{
  background:#fff;border-radius:14px;overflow:hidden;
  box-shadow:0 2px 12px rgba(0,0,0,.1);
}
.hall-top{
  padding:1.2rem 1.2rem .8rem;
  background:linear-gradient(135deg,#1a1a2e,#2d2d44);
  color:#fff;
}
.hall-name{font-size:1.3rem;font-weight:900}
.hall-badges{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.5rem}
.hall-badge{font-size:.72rem;font-weight:700;padding:.2rem .55rem;border-radius:99px}
.hb-party{color:#fff}
.hb-title{background:rgba(255,255,255,.2);color:#fff}
.hb-county{background:rgba(255,255,255,.15);color:#eee}

.hall-cars{padding:.8rem 1.2rem 1.2rem}
.hcar{
  display:flex;align-items:center;gap:.6rem;
  padding:.4rem .5rem;border-radius:8px;margin-bottom:.3rem;
  font-size:.9rem;
}
.hcar.sc{background:#fff0eb;border:1px solid #ff6b35}
.hcar.lux{background:#fffbea;border:1px solid #ffd700}
.hcar.reg{background:#fafafa}
.hcar-em{font-size:1.2rem;width:1.6rem;text-align:center}
.hcar-brand{font-weight:700}
.hcar-raw{color:#999;font-size:.78rem;margin-left:.3rem}
.hcar-cc{margin-left:auto;color:#bbb;font-size:.78rem}
.hcar-date{color:#bbb;font-size:.75rem;margin-left:.4rem;white-space:nowrap}

/* ═══════════════════════════════════════════════════════════
   4 SEARCH — 查選區
═══════════════════════════════════════════════════════════ */
.controls{
  background:#fff;padding:1rem 2rem;display:flex;flex-wrap:wrap;
  gap:.6rem;align-items:center;border-bottom:2px solid #eee;
  position:sticky;top:54px;z-index:90;
}
.controls select,.controls input{
  border:2px solid #ddd;border-radius:8px;padding:.5rem .8rem;
  font-size:.92rem;outline:none;transition:border-color .2s;font-family:inherit;
}
.controls select:focus,.controls input:focus{border-color:#0f3460}
.controls input{flex:1;min-width:160px}
.mini-stats{
  background:#1a1a2e;color:#fff;padding:.55rem 2rem;
  display:flex;flex-wrap:wrap;gap:1.2rem;font-size:.85rem;
  position:sticky;top:109px;z-index:89;
}
.mini-stat span{font-weight:900;color:#ffd700}
.search-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));
  gap:1rem;padding:1.2rem 2rem;
}
.s-card{
  background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.08);
  overflow:hidden;border-top:4px solid var(--pc,#ccc);
  transition:transform .15s;
}
.s-card:hover{transform:translateY(-3px)}
.s-header{padding:.8rem 1rem .6rem;display:flex;justify-content:space-between;align-items:flex-start}
.s-name{font-size:1.2rem;font-weight:900}
.s-meta{display:flex;gap:.35rem;flex-wrap:wrap;margin-top:.3rem}
.badge{display:inline-block;font-size:.7rem;font-weight:700;padding:.18rem .5rem;border-radius:99px;white-space:nowrap}
.b-party{color:#fff}
.b-title{background:#eee;color:#555}
.b-county{background:#e8f4fd;color:#1a6faf}
.b-date{background:#f0f0f0;color:#999;font-weight:400}
.s-sp{font-size:.68rem;font-weight:900;padding:.25rem .5rem;border-radius:7px;white-space:nowrap;text-align:center;line-height:1.3;flex-shrink:0;margin-left:.4rem}
.sp-sc{background:linear-gradient(135deg,#ff6b35,#f7c59f);color:#fff}
.sp-lux{background:linear-gradient(135deg,#ffd700,#ffaa00);color:#333}
.sp-many{background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff}
.s-cars{padding:0 1rem 1rem}
.ci{display:flex;align-items:center;gap:.45rem;padding:.3rem .45rem;border-radius:7px;margin-bottom:.2rem;font-size:.86rem;background:#fafafa}
.ci.lux{background:#fffbea;border:1px solid #ffd700}
.ci.sc{background:#fff0eb;border:1px solid #ff6b35}
.ci-em{font-size:1rem;width:1.3rem;flex-shrink:0;text-align:center}
.ci-left{flex:1;min-width:0;display:flex;align-items:center;gap:.35rem;overflow:hidden}
.ci-brand{font-weight:700;white-space:nowrap;flex-shrink:0}
.ci-raw{color:#aaa;font-size:.76rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.ci-right{flex-shrink:0;display:flex;align-items:center;gap:.3rem;margin-left:.4rem}
.ci-cc{color:#bbb;font-size:.76rem;white-space:nowrap}
.ci-price{color:#e67e22;font-weight:700;font-size:.82rem;white-space:nowrap}
.ci-over5{color:#aaa;font-size:.76rem;white-space:nowrap}
.ci-traced{color:#bbb;font-size:.68rem}
.ci-date{color:#aaa;font-size:.74rem;white-space:nowrap}
.s-total{display:flex;align-items:center;gap:.5rem;padding:.5rem .75rem;border-top:1px solid #f0f0f0;margin-top:.4rem;flex-wrap:wrap}
.s-total-label{font-size:.76rem;color:#999}
.s-total-val{font-size:1rem;font-weight:900;color:#e67e22}
.s-total-note{font-size:.74rem;color:#bbb}
.no-res{text-align:center;padding:4rem;color:#aaa;font-size:1.1rem;grid-column:1/-1}

/* ═══════════════════════════════════════════════════════════
   5 ECO
═══════════════════════════════════════════════════════════ */
  background:#e8f8ee;border-radius:12px;padding:1.2rem;
  border-left:4px solid #27ae60;margin-bottom:1.5rem;font-size:.9rem;line-height:1.7;
}

/* ═══════════════════════════════════════════════════════════
   6 PARTY — 政黨停車場
═══════════════════════════════════════════════════════════ */
.party-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;margin-top:1.5rem}
.party-card{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.09)}
.party-head{padding:1.2rem;color:#fff;font-weight:900}
.party-head h3{font-size:1.3rem}
.party-head p{font-size:.85rem;opacity:.8;margin-top:.2rem}
.party-body{padding:1rem 1.2rem 1.2rem}
.p-stat-row{display:flex;justify-content:space-between;margin-bottom:.8rem}
.p-stat{text-align:center}
.p-stat-n{font-size:1.5rem;font-weight:900}
.p-stat-l{font-size:.76rem;color:#888;margin-top:.1rem}
.p-bars{margin-top:1rem}
.p-bar-row{display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem;font-size:.82rem}
.p-bar-label{width:90px;text-align:right;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0}
.p-bar-track{flex:1;background:#eee;border-radius:99px;height:20px;overflow:hidden}
.p-bar-fill{height:100%;border-radius:99px;min-width:4px;transition:width 1s ease}
.p-bar-n{width:2rem;font-size:.78rem;color:#888}
.lot-wrap{margin-top:1.2rem}
.lot-title{font-size:.8rem;color:#888;margin-bottom:.5rem;font-weight:700}
.parking-lot{display:flex;flex-wrap:wrap;gap:3px}
.parking-space{
  width:20px;height:14px;border-radius:3px;
  transition:transform .1s;cursor:default;
  border:1px solid rgba(0,0,0,.1);
}
.parking-space.luxury{border:1.5px solid rgba(0,0,0,.3)}
.parking-space:hover{transform:scale(1.3)}

/* ═══════════════════════════════════════════════════════════
   7 GENDER
═══════════════════════════════════════════════════════════ */
.gender-wrap{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:1.5rem}
@media(max-width:560px){.gender-wrap{grid-template-columns:1fr}}
.gender-card{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.09)}
.g-head{padding:1.2rem;color:#fff;font-weight:900;font-size:1.4rem;text-align:center}
.g-head-m{background:linear-gradient(135deg,#1565c0,#1e88e5)}
.g-head-f{background:linear-gradient(135deg,#c2185b,#e91e63)}
.g-body{padding:1.2rem}
.g-big{font-size:3rem;font-weight:900;text-align:center;margin:1rem 0}
.g-sub{text-align:center;font-size:.85rem;color:#888;margin-bottom:1.5rem}
.g-bar-section{margin-bottom:.5rem;font-size:.85rem;font-weight:700;color:#888}
.g-br{display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem;font-size:.85rem}
.g-br-label{width:80px;text-align:right;font-weight:600}
.g-br-track{flex:1;background:#eee;border-radius:99px;height:22px;overflow:hidden}
.g-br-fill{height:100%;border-radius:99px;transition:width 1s ease}
.g-br-n{width:2.2rem;font-size:.8rem;color:#888}

.insight-box{
  background:#1a1a2e;color:#fff;border-radius:14px;padding:1.5rem;
  margin-top:1.5rem;font-size:.95rem;line-height:1.8;
}
.insight-box strong{color:#ffd700}

/* ═══════════════════════════════════════════════════════════
   8 RICHEST — 最貴車庫
═══════════════════════════════════════════════════════════ */
.rich-card{
  background:#fff;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.09);
  margin-bottom:1rem;overflow:hidden;
  border-left:6px solid var(--pc,#ffd700);
}
.rich-top{
  padding:1rem 1.2rem .7rem;display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;
}
.rich-rank{
  font-size:2rem;font-weight:900;color:#bbb;width:2.5rem;flex-shrink:0;line-height:1;
}
.rich-rank.gold{color:#f9a825}
.rich-rank.silver{color:#9e9e9e}
.rich-rank.bronze{color:#a1601c}
.rich-info{flex:1}
.rich-name{font-size:1.25rem;font-weight:900}
.rich-meta{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.35rem}
.rich-price-block{text-align:right;flex-shrink:0}
.rich-total{font-size:1.6rem;font-weight:900;color:#e67e22;white-space:nowrap}
.rich-total-label{font-size:.72rem;color:#aaa;margin-top:.1rem}
.rich-coverage{font-size:.72rem;color:#aaa}
.rich-cars{padding:.5rem 1.2rem 1rem;display:flex;flex-wrap:wrap;gap:.4rem}
.rcar{
  display:inline-flex;align-items:center;gap:.35rem;
  padding:.3rem .6rem;border-radius:8px;font-size:.83rem;background:#fafafa;
  border:1px solid #eee;
}
.rcar.lux{background:#fffbea;border-color:#ffd700}
.rcar.sc{background:#fff0eb;border-color:#ff6b35}
.rcar-price{font-weight:700;color:#e67e22;margin-left:.25rem}
.rcar-date{color:#bbb;font-size:.74rem;margin-left:.3rem;white-space:nowrap}
.rcar-over5{color:#bbb;font-style:italic}

/* ── Footer ── */
footer{text-align:center;padding:2.5rem;color:#aaa;font-size:.8rem;border-top:1px solid #eee;margin-top:2rem}

/* ── Brands split layout ── */
.brands-layout{display:flex;gap:1.5rem;align-items:flex-start}
.brands-layout .bar-chart{flex:1;min-width:0}
.brand-panel{
  width:280px;flex-shrink:0;position:sticky;top:4.5rem;
  background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.1);
  max-height:calc(100vh - 6rem);overflow-y:auto;
}
.brand-panel-empty{padding:2.5rem 1.2rem;text-align:center;color:#bbb;font-size:.9rem;line-height:1.8}
.brand-panel-header{padding:.8rem 1rem .5rem;border-bottom:1px solid #f0f0f0;position:sticky;top:0;background:#fff;z-index:1}
.brand-panel-title{font-size:1.1rem;font-weight:900;display:flex;align-items:center;gap:.4rem}
.brand-panel-sub{font-size:.78rem;color:#999;margin-top:.2rem}
.brand-owners{padding:.5rem .6rem;display:flex;flex-direction:column;gap:.25rem}
.bo-row{display:flex;align-items:center;gap:.35rem;flex-wrap:wrap;padding:.3rem .4rem;border-radius:6px;font-size:.83rem}
.bo-row:hover{background:#f8f8f8}
.bo-name{font-weight:700;min-width:3.5rem}
.br-clickable{cursor:pointer}
.br-clickable:hover{background:#f5f5f5}
.br-clickable.active{background:#fff8f0;border-left:3px solid #e67e22}

/* ── Party layout ── */
.party-layout{display:flex;gap:1.5rem;align-items:flex-start}
.party-layout .party-grid{flex:1;min-width:0}
.party-card{cursor:pointer;transition:box-shadow .15s}
.party-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.15)}
.party-card.active{outline:3px solid #e67e22}
@media(max-width:640px){.party-layout{flex-direction:column}}
@media(max-width:640px){
  .brands-layout{flex-direction:column}
  .brand-panel{width:100%;position:static;max-height:none}
}

/* ── Owner page ── */
.stat-block{background:#f9f9f9;border-radius:12px;padding:1.2rem 1rem;text-align:center}
.stat-num{font-size:2.2rem;font-weight:900;line-height:1}
.stat-label{font-size:.85rem;color:#555;margin-top:.35rem;font-weight:600}
.ow-row{display:flex;align-items:center;gap:.5rem;height:2rem}
.ow-label{width:60px;font-size:.85rem;flex-shrink:0}
.ow-bar-wrap{flex:1;background:#eee;border-radius:3px;height:14px;overflow:hidden}
.ow-pct{width:42px;font-size:.82rem;font-weight:700;color:#555;text-align:right;flex-shrink:0}
.ow-detail{font-size:.75rem;color:#aaa;width:56px;flex-shrink:0}
</style>
</head>
<body>

<!-- ── NAV ── -->
<nav id="main-nav">
  <div class="nav-logo" onclick="showView('landing')">🚗 民代車庫</div>
  <div class="scope-toggle">
    <button class="scope-btn active"   data-scope="all"        onclick="setScope('all')">全部</button>
    <button class="scope-btn s-law"    data-scope="legislator" onclick="setScope('legislator')">立委</button>
    <button class="scope-btn s-council"data-scope="councilor"  onclick="setScope('councilor')">議員</button>
  </div>
  <div class="nav-btn" data-view="brands"   onclick="showView('brands')">🏆 品牌排行</div>
  <div class="nav-btn" data-view="map"      onclick="showView('map')">🗺️ 縣市豪車</div>
  <div class="nav-btn" data-view="supercars"onclick="showView('supercars')">🔥 超跑名人堂</div>
  <div class="nav-btn" data-view="search"   onclick="showView('search')">🚗 查選區</div>
  <div class="nav-btn" data-view="party"    onclick="showView('party')">🎯 政黨停車場</div>
  <div class="nav-btn" data-view="gender"   onclick="showView('gender')">📊 男女比較</div>
  <div class="nav-btn" data-view="richest"  onclick="showView('richest')">💰 最貴車庫</div>
  <div class="nav-btn" data-view="owner"    onclick="showView('owner')">👫 配偶名下</div>
</nav>

<!-- ══════════════════════════ LANDING ══════════════════════════ -->
<div class="view active" id="view-landing">
  <div class="hero">
    <span class="hero-emoji">🚗</span>
    <h1>你的民代家<span>車庫</span>有哪些車？</h1>
    <p>
      台灣公職人員每年申報財產，包含汽車。
      我們把 <strong>__TOTAL_PEOPLE__ 位</strong>現任立委和縣市議員的申報資料整理出來，
      用最直白的方式問一個問題：<br>
      <em>你選的人，開什麼車？</em>
    </p>
    <p style="margin-top:.6rem;font-size:.85rem;opacity:.65">
      📋 依財產申報規定，申報範圍涵蓋本人及配偶的財產，<br>
      因此每位民代的車輛資料反映的是<strong>整個家庭</strong>的申報車輛。
    </p>
    <p style="margin-top:.5rem;font-size:.8rem;opacity:.5">
      📄 本站資料取自<strong>廉政專刊第 291 期起</strong>（2023 年下半年）的財產申報公開資料，291 期以前的資料不納入。
    </p>
    <div class="hero-stats" id="hero-stats"></div>
  </div>

  <div class="features">
    <div class="feature-card" style="--fc:#e67e22" onclick="showView('brands')">
      <div class="icon">🏆</div>
      <h3>品牌排行榜</h3>
      <p>Toyota 遙遙領先、Lexus 和 Benz 並駕齊驅，誰是民代最愛？</p>
      <div class="tag">看動態排行 →</div>
    </div>
    <div class="feature-card" style="--fc:#e74c3c" onclick="showView('map')">
      <div class="icon">🗺️</div>
      <h3>各縣市豪車率排行</h3>
      <p>__TOP_COUNTY__議員豪車率達 __TOP_COUNTY_RATE__%，各縣市差異懸殊。</p>
      <div class="tag">看縣市地圖 →</div>
    </div>
    <div class="feature-card" style="--fc:#c0392b" onclick="showView('supercars')">
      <div class="icon">🔥</div>
      <h3>超跑名人堂</h3>
      <p>McLaren、Lamborghini、Bentley⋯⋯那些申報超跑的民代都是誰？</p>
      <div class="tag">進入名人堂 →</div>
    </div>
    <div class="feature-card" style="--fc:#2980b9" onclick="showView('search')">
      <div class="icon">🔍</div>
      <h3>查你的選區民代</h3>
      <p>選縣市、選政黨、直接搜尋，看你投票給的人開什麼車。</p>
      <div class="tag">查我的民代 →</div>
    </div>
    <div class="feature-card" style="--fc:#8e44ad" onclick="showView('party')">
      <div class="icon">🎯</div>
      <h3>政黨停車場</h3>
      <p>國民黨豪車率 24%、時代力量 8%，每個停車格都是一台申報的車。</p>
      <div class="tag">進停車場 →</div>
    </div>
    <div class="feature-card" style="--fc:#d35400" onclick="showView('gender')">
      <div class="icon">📊</div>
      <h3>男女開車習慣</h3>
      <p>男女民代的豪車率、品牌偏好有差異嗎？數據說話。</p>
      <div class="tag">看性別比較 →</div>
    </div>
    <div class="feature-card" style="--fc:#b7950b" onclick="showView('richest')">
      <div class="icon">💰</div>
      <h3>最貴車庫排行榜</h3>
      <p>誰的申報車輛總價最高？彰化縣議員黃正盛近 3,200 萬，第二名也超過 2,800 萬。</p>
      <div class="tag">看排行榜 →</div>
    </div>
    <div class="feature-card" style="--fc:#16a085" onclick="showView('owner')">
      <div class="icon">👫</div>
      <h3>配偶名下</h3>
      <p>申報車輛中 42% 登記在配偶名下。誰家的車幾乎都掛在另一半名下？</p>
      <div class="tag">看分析 →</div>
    </div>
  </div>

  <div class="tagline">
    資料來源：廉政專刊財產申報公開資料 · 申報範圍依法包含本人及配偶 · 僅顯示各人最近一次申報 · 本站僅供公益資訊用途
  </div>
</div>

<!-- ══════════════════════════ 1 BRANDS ══════════════════════════ -->
<div class="view" id="view-brands">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>🏆 品牌排行榜</h2>
    <p>__TOTAL_PEOPLE__ 位現任立委 + 議員，共 __TOTAL_CARS__ 台車（含配偶申報），誰最多？</p>
  </div>
  <div class="section-body">
    <div class="brands-layout">
      <div class="bar-chart" id="brands-chart"></div>
      <div class="brand-panel" id="brand-panel">
        <div class="brand-panel-empty">← 點選左側品牌<br>查看擁有者</div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════ 2 MAP ══════════════════════════ -->
<div class="view" id="view-map">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>🗺️ 各縣市豪車率排行</h2>
    <p>各縣市議員豪車品牌比例排行（含配偶申報車輛）</p>
  </div>
  <div class="section-body">
    <div class="map-legend">
      <span>低</span>
      <div class="legend-grad"></div>
      <span>高</span>
      <span style="margin-left:1rem;color:#aaa;font-size:.82rem">豪車率 = 豪華品牌車輛佔該縣市議員總申報車輛比例</span>
    </div>
    <div class="county-list" id="county-list"></div>
  </div>
</div>

<!-- ══════════════════════════ 3 SUPERCARS ══════════════════════════ -->
<div class="view" id="view-supercars">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>🔥 超跑名人堂</h2>
    <p>申報 McLaren、Lamborghini、Bentley、Maserati、Ferrari、Porsche 的民代（含配偶名下車輛）</p>
  </div>
  <div class="section-body">
    <div class="hall" id="hall-grid"></div>
  </div>
</div>

<!-- ══════════════════════════ 4 SEARCH ══════════════════════════ -->
<div class="view" id="view-search">
  <div class="page-header" style="padding-bottom:1rem">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>🔍 查你的選區民代</h2>
  </div>
  <div class="controls">
    <select id="sel-county">
      <option value="">全部縣市</option>
      <option value="立法院">🏛️ 立法院（立委）</option>
      <optgroup label="六都">
        <option>台北市</option><option>新北市</option><option>桃園市</option>
        <option>台中市</option><option>台南市</option><option>高雄市</option>
      </optgroup>
      <optgroup label="北部">
        <option>基隆市</option><option>新竹市</option><option>新竹縣</option><option>宜蘭縣</option>
      </optgroup>
      <optgroup label="中部">
        <option>苗栗縣</option><option>彰化縣</option><option>南投縣</option><option>雲林縣</option>
      </optgroup>
      <optgroup label="南部">
        <option>嘉義市</option><option>嘉義縣</option><option>屏東縣</option>
      </optgroup>
      <optgroup label="東部">
        <option>花蓮縣</option><option>台東縣</option>
      </optgroup>
      <optgroup label="離島">
        <option>澎湖縣</option><option>金門縣</option><option>連江縣</option>
      </optgroup>
    </select>
    <select id="sel-party">
      <option value="">全部政黨</option>
      <option>國民黨</option><option>民進黨</option><option>民眾黨</option>
      <option>時代力量</option><option>親民黨</option><option>無黨籍</option>
      <option>台灣基進</option><option>新黨</option>
    </select>
    <select id="sel-sort">
      <option value="luxury">豪車數 ↓</option>
      <option value="price">總車價 ↓</option>
      <option value="cars">車輛數 ↓</option>
      <option value="name">姓名</option>
    </select>
    <input id="s-search" type="text" placeholder="🔍 搜尋姓名 / 車款…">
  </div>
  <div class="mini-stats" id="mini-stats">
    篩選 <span id="ms-people">—</span> 人 &nbsp;·&nbsp;
    共 <span id="ms-cars">—</span> 台 &nbsp;·&nbsp;
    豪車 <span id="ms-lux">—</span> 台 &nbsp;·&nbsp;
    超跑 <span id="ms-sc">—</span> 台
  </div>
  <div class="search-grid" id="search-grid"></div>
</div>

<!-- ══════════════════════════ 5 ECO ══════════════════════════ -->
<!-- ══════════════════════════ 6 PARTY ══════════════════════════ -->
<div class="view" id="view-party">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>🎯 政黨停車場</h2>
    <p>每個停車格 = 一台申報車輛（含配偶），金色 = 豪車。點選政黨卡片查看成員。</p>
  </div>
  <div class="section-body">
    <div class="party-layout">
      <div class="party-grid" id="party-grid"></div>
      <div class="brand-panel" id="party-panel">
        <div class="brand-panel-empty">← 點選政黨卡片<br>查看該黨民代</div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════════════════ 7 GENDER ══════════════════════════ -->
<div class="view" id="view-gender">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>📊 男女開車習慣</h2>
    <p>現任民代申報車輛的性別分析（含配偶名下車輛）</p>
  </div>
  <div class="section-body">
    <div class="gender-wrap" id="gender-wrap"></div>
    <div class="insight-box">
      💡 <strong>數據觀察</strong>：女性民代豪車率 __FEMALE_RATE__%，男性 __MALE_RATE__%，差距 <strong>__GENDER_DIFF__ 個百分點</strong>。<br><br>
      女性民代 Top 品牌同樣是 Toyota、Benz、中華三菱，品牌偏好與男性高度相似；
      差異在 <strong>Benz 比例較高</strong>（女性第 2 名，男性第 4 名）。
    </div>
  </div>
</div>

<!-- ══════════════════════════ 8 RICHEST ══════════════════════════ -->
<div class="view" id="view-richest">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>💰 最貴車庫排行榜</h2>
    <p>以申報取得價格加總排行，包含本人及配偶名下車輛（僅計算有填價格的車）</p>
  </div>
  <div class="section-body">
    <div class="insight-box" style="margin-bottom:1.5rem">
      ⚠️ <strong>資料限制說明</strong>：依法規定，取得超過五年的車輛不需申報價格，約 <strong>43%</strong> 的車填「超過五年」。
      以下排行只計算有填入價格的車輛，實際總價可能更高。
      部分標「超過五年」的車輛，系統已從該民代<strong>歷史申報記錄</strong>中回溯到原始購買價格（標有 ✱ 符號）。
      每台車旁的 <strong>民國年月</strong> 為申報的登記取得時間，可看出這台車是新購還是舊車。
    </div>
    <div id="richest-list"></div>
  </div>
</div>

<!-- ══════════════════════════ 9 OWNER ══════════════════════════ -->
<div class="view" id="view-owner">
  <div class="page-header">
    <div class="back" onclick="showView('landing')">← 回首頁</div>
    <h2>👫 配偶名下車輛分析</h2>
    <p>依法申報範圍涵蓋本人與配偶財產。分析每位民代的車輛中，有幾台登記在配偶（或其他家屬）名下。</p>
  </div>
  <div class="section-body">
    <div class="insight-box" style="margin-bottom:1.5rem" id="owner-summary-box">
    </div>
    <div id="owner-charts"></div>
    <h3 style="margin:2rem 0 1rem;font-size:1.1rem;color:#333">配偶名下車輛最多的民代</h3>
    <p style="color:#666;font-size:.88rem;margin-bottom:1rem">依配偶名下車輛數排序，點選民代可展開查看全部車輛</p>
    <div id="owner-list"></div>
  </div>
</div>

<footer>
  資料來源：廉政專刊財產申報 · 僅顯示各人最近一次申報 · 本站僅供公益資訊用途
</footer>

<script>
// ─── DATA ───────────────────────────────────────────────────────────────────
const CARS  = ''' + cars_raw  + ''';
const STATS = ''' + stats_raw + ''';

const PARTY_COLOR = {
  '國民黨':'#003f88','民進黨':'#1b9431','民眾黨':'#28c0c8',
  '時代力量':'#f9c80e','親民黨':'#f47920','無黨籍':'#888',
  '台灣基進':'#d0021b','新黨':'#c0392b','台聯':'#f39c12',
  '綠黨':'#27ae60','不明':'#bbb',
};
const BRAND_EMOJI = {
  'Toyota':'🚗','Lexus':'✨','Benz':'⭐','BMW':'🔵','Audi':'🔴','Porsche':'🏎️',
  'Volvo':'🇸🇪','Land Rover':'🦁','Ferrari':'🔥','Lamborghini':'🔥',
  'McLaren':'🔥','Bentley':'👑','Maserati':'🔱','Rolls-Royce':'👸',
  'Tesla':'⚡','Honda':'🚗','Nissan':'🚙','Ford':'🚗','Mazda':'🌀',
  'VW':'🇩🇪','Suzuki':'🛵','中華三菱':'🚗','Luxgen':'🇹🇼',
  'MINI':'🎀','Austin Mini':'🇬🇧','三陽SYM':'🛵','Subaru':'⭕','Skoda':'✅',
  'Jeep':'🪖','Jaguar':'🐆','Harley-Davidson':'🏍️','Acura':'🔷',
};
const LUXURY_BRANDS = new Set(['Lexus','Benz','BMW','Audi','Porsche','Volvo','Land Rover',
  'Maserati','Ferrari','Lamborghini','Bentley','McLaren','Jaguar','Rolls-Royce','Acura','MINI','Tesla']);
const SUPERCAR_BRANDS = new Set(['Ferrari','Lamborghini','McLaren','Bentley','Maserati','Rolls-Royce']);

function em(brand){ return BRAND_EMOJI[brand]||'🚗'; }
function pc(party){ return PARTY_COLOR[party]||'#bbb'; }
function fmtDate(s){
  // 民國年 "95年06月" → "民95.06"；西元 "2022-11-01" → "2022"
  if(!s) return '';
  const m = s.match(/^(\d+)年(\d+)月/);
  if(m) return `民${m[1]}.${m[2]}`;
  const m2 = s.match(/^(\d{4})/);
  if(m2) return m2[1];
  return s.substring(0,7);
}

// ─── ROUTING ─────────────────────────────────────────────────────────────────
function showView(id){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  const v = document.getElementById('view-'+id);
  if(v){ v.classList.add('active'); window.scrollTo(0,0); }
  const b = document.querySelector(`[data-view="${id}"]`);
  if(b){ b.classList.add('active'); }
  // lazy render
  if(id==='brands'   && !rendered.brands)   { renderBrands();    rendered.brands=true;   }
  if(id==='map'      && !rendered.map)       { renderMap();       rendered.map=true;      }
  if(id==='supercars'&& !rendered.supercars) { renderSupercars(); rendered.supercars=true;}
  if(id==='search'   && !rendered.search)    { renderSearch();    rendered.search=true;   }
  if(id==='party'    && !rendered.party)     { renderParty();     rendered.party=true;    }
  if(id==='gender'   && !rendered.gender)    { renderGender();    rendered.gender=true;   }
  if(id==='richest'  && !rendered.richest)   { renderRichest();   rendered.richest=true;  }
  if(id==='owner'    && !rendered.owner)     { renderOwner();     rendered.owner=true;    }
  // trigger animations after DOM paint
  setTimeout(()=>{ triggerAnimations(id); }, 60);
}
const rendered = {};

// ─── SCOPE ───────────────────────────────────────────────────────────────────
let currentScope = 'all';

function setScope(scope){
  if(currentScope === scope) return;
  currentScope = scope;
  Object.keys(rendered).forEach(k=>{ rendered[k]=false; });
  document.querySelectorAll('.scope-btn').forEach(b=>{
    b.classList.toggle('active', b.dataset.scope === scope);
  });
  // 議員模式：隱藏「立法院」選項；立委模式：只保留「立法院」
  const lyOpt = document.querySelector('#sel-county option[value="立法院"]');
  if(lyOpt){
    if(scope === 'councilor'){
      lyOpt.hidden = true;
      if(document.getElementById('sel-county').value === '立法院')
        document.getElementById('sel-county').value = '';
    } else {
      lyOpt.hidden = false;
    }
  }
  renderHeroStats();
  const id = document.querySelector('.view.active')?.id?.replace('view-','');
  if(id && id !== 'landing') showView(id);
}

function scopedPeople(){
  if(currentScope==='all') return CARS;
  if(currentScope==='legislator') return CARS.filter(p=>p.title==='立法委員');
  return CARS.filter(p=>p.title!=='立法委員');
}

// ─── COMPUTE HELPERS ─────────────────────────────────────────────────────────
function computeBrands(pp){
  const c={};
  pp.forEach(p=>p.cars.forEach(car=>{ c[car.brand]=(c[car.brand]||0)+1; }));
  return Object.entries(c).sort((a,b)=>b[1]-a[1]).slice(0,20).map(([brand,count])=>({brand,count}));
}
function computeCounties(pp){
  const tot={},lux={};
  pp.forEach(p=>{
    if(!p.cars.length||!p.county||p.county==='立法院'||p.county==='其他') return;
    tot[p.county]=(tot[p.county]||0)+p.car_count;
    lux[p.county]=(lux[p.county]||0)+p.luxury_count;
  });
  return Object.keys(tot).map(c=>({
    county:c,total:tot[c],luxury:lux[c]||0,
    rate:tot[c]?Math.round((lux[c]||0)/tot[c]*1000)/10:0,
  })).sort((a,b)=>b.rate-a.rate);
}
function computeParties(pp){
  const MAIN=['國民黨','民進黨','民眾黨','時代力量','親民黨','無黨籍','新黨','台灣基進'];
  const tot={},lux={},brd={};
  pp.forEach(p=>{
    if(!MAIN.includes(p.party)) return;
    p.cars.forEach(c=>{
      tot[p.party]=(tot[p.party]||0)+1;
      if(c.luxury) lux[p.party]=(lux[p.party]||0)+1;
      if(!brd[p.party]) brd[p.party]={};
      brd[p.party][c.brand]=(brd[p.party][c.brand]||0)+1;
    });
  });
  return MAIN.filter(pt=>(tot[pt]||0)>=5).map(pt=>{
    const t=tot[pt]||0,l=lux[pt]||0;
    const top_brands=Object.entries(brd[pt]||{}).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([brand,count])=>({brand,count}));
    return {party:pt,total:t,luxury:l,rate:t?Math.round(l/t*1000)/10:0,top_brands};
  }).sort((a,b)=>b.rate-a.rate);
}
function computeGender(pp){
  const res={};
  ['男','女'].forEach(sex=>{
    const brd={};let tot=0,lux=0;
    pp.filter(p=>p.gender===sex).forEach(p=>p.cars.forEach(c=>{
      tot++;if(c.luxury)lux++;
      brd[c.brand]=(brd[c.brand]||0)+1;
    }));
    const top_brands=Object.entries(brd).sort((a,b)=>b[1]-a[1]).slice(0,8).map(([brand,count])=>({brand,count}));
    res[sex]={total:tot,luxury:lux,rate:tot?Math.round(lux/tot*1000)/10:0,top_brands};
  });
  return res;
}
function computeSupercars(pp){
  return pp.filter(p=>p.cars.some(c=>c.supercar||c.brand==='Porsche'))
    .map(p=>({...p,supercars:p.cars.filter(c=>c.supercar||c.brand==='Porsche'),all_cars:p.cars}))
    .sort((a,b)=>b.supercars.length-a.supercars.length||b.car_count-a.car_count);
}
function computeRichest(pp){
  return pp.filter(p=>p.total_price!=null).sort((a,b)=>b.total_price-a.total_price).slice(0,50);
}

// ─── LANDING ─────────────────────────────────────────────────────────────────
function renderHeroStats(){
  const pp=scopedPeople();
  const allCars=pp.flatMap(p=>p.cars);
  document.getElementById('hero-stats').innerHTML = [
    {n: pp.length.toLocaleString(),                              l:'位民代'},
    {n: allCars.length.toLocaleString(),                         l:'台申報車輛'},
    {n: allCars.filter(c=>c.luxury).length.toLocaleString(),     l:'台豪車'},
    {n: allCars.filter(c=>c.supercar).length.toLocaleString(),        l:'台超跑 🏎️'},
    {n: pp.reduce((s,p)=>s+p.spouse_count,0).toLocaleString(),        l:'台配偶名下 👫'},
  ].map(x=>`<div class="hero-stat"><span class="hero-stat-num">${x.n}</span><div class="hero-stat-label">${x.l}</div></div>`).join('');
}
renderHeroStats();

// ─── 1 BRANDS ────────────────────────────────────────────────────────────────
let _brandPeopleMap = {};  // brand → [{name,party,county,title,count}]

function renderBrands(){
  const pp = scopedPeople();

  // build brand→people index
  _brandPeopleMap = {};
  pp.forEach(p=>{
    const cnt = {};
    p.cars.forEach(c=>{ cnt[c.brand]=(cnt[c.brand]||0)+1; });
    Object.entries(cnt).forEach(([brand,n])=>{
      if(!_brandPeopleMap[brand]) _brandPeopleMap[brand]=[];
      _brandPeopleMap[brand].push({name:p.name,party:p.party,county:p.county,title:p.title,count:n});
    });
  });
  const _COUNTY_ORDER = ['立法院','台北市','新北市','基隆市','宜蘭縣','桃園市','新竹市','新竹縣','苗栗縣','台中市','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','台南市','高雄市','屏東縣','花蓮縣','台東縣','澎湖縣','金門縣','連江縣','其他'];
  const _countyRank = c => { const i=_COUNTY_ORDER.indexOf(c); return i<0?99:i; };
  Object.values(_brandPeopleMap).forEach(arr=>arr.sort((a,b)=>b.count-a.count||_countyRank(a.county)-_countyRank(b.county)||a.name.localeCompare(b.name)));

  // compute ALL brands sorted by count
  const allBrands = Object.entries(
    pp.reduce((c,p)=>{ p.cars.forEach(car=>{ c[car.brand]=(c[car.brand]||0)+1; }); return c; }, {})
  ).sort((a,b)=>b[1]-a[1]).map(([brand,count])=>({brand,count}));

  if(!allBrands.length){document.getElementById('brands-chart').innerHTML='<div class="no-res">無資料</div>';return;}
  const top20 = allBrands.slice(0,20);
  const rest  = allBrands.slice(20);
  const otherCount = rest.reduce((s,b)=>s+b.count,0);
  const max = top20[0].count;
  const LUXURY_B = LUXURY_BRANDS;

  const makeRow = (b, rank)=>{
    const pct = (b.count/max*100).toFixed(1);
    const isLux = LUXURY_B.has(b.brand);
    const color = isLux ? '#e67e22' : '#3498db';
    const brandEsc = b.brand.replace(/'/g,"\\'");
    return `<div class="bar-row br-clickable" onclick="selectBrand('${brandEsc}',this)">
      <div class="bar-rank">${rank}</div>
      <div class="bar-emoji">${em(b.brand)}</div>
      <div class="bar-label">${b.brand}</div>
      <div class="bar-track">
        <div class="bar-fill" data-pct="${pct}" style="background:${color};width:0%">
          ${b.count >= 30 ? b.count+'台' : ''}
        </div>
      </div>
      <div class="bar-count">${b.count}台</div>
      ${isLux ? '<div class="luxury-mark">豪車</div>' : ''}
    </div>`;
  };

  const rows = top20.map((b,i)=>makeRow(b,i+1));

  if(otherCount > 0){
    const restRows = rest.map((b,i)=>makeRow(b,20+i+1)).join('');
    const pct = (otherCount/max*100).toFixed(1);
    rows.push(`
      <div class="bar-row other-toggle" onclick="toggleOtherBrands(this)" style="cursor:pointer;opacity:.7">
        <div class="bar-rank">—</div>
        <div class="bar-emoji">🚗</div>
        <div class="bar-label" style="color:#999">其他品牌 <span class="ot-arrow" style="font-size:.75rem">▼</span></div>
        <div class="bar-track">
          <div class="bar-fill" data-pct="${pct}" style="background:#bbb;width:0%"></div>
        </div>
        <div class="bar-count" style="color:#999">${otherCount}台</div>
      </div>
      <div class="other-brands-list" style="display:none">${restRows}</div>`);
  }
  document.getElementById('brands-chart').innerHTML = rows.join('');
}

function selectBrand(brand, rowEl){
  // highlight active row
  document.querySelectorAll('#brands-chart .br-clickable').forEach(r=>r.classList.remove('active'));
  rowEl.classList.add('active');

  const people = _brandPeopleMap[brand] || [];
  const panel  = document.getElementById('brand-panel');
  panel.innerHTML = `
    <div class="brand-panel-header">
      <div class="brand-panel-title">${em(brand)} ${brand}</div>
      <div class="brand-panel-sub">${people.length} 位民代・共 ${people.reduce((s,p)=>s+p.count,0)} 台</div>
    </div>
    <div class="brand-owners">
      ${people.map(p=>{
        const c = pc(p.party);
        const countTxt = p.count>1 ? `<span style="color:#e67e22;font-weight:700;margin-left:auto">${p.count}台</span>` : '';
        return `<div class="bo-row">
          <span class="bo-name">${p.name}</span>
          <span class="badge b-party" style="background:${c};color:#fff">${p.party}</span>
          <span class="badge b-county">${p.county}</span>
          ${countTxt}
        </div>`;
      }).join('')}
    </div>`;
  panel.scrollTop = 0;
}

function toggleOtherBrands(el){
  const list = el.nextElementSibling;
  const open = list.style.display !== 'none';
  list.style.display = open ? 'none' : 'block';
  el.querySelector('.ot-arrow').textContent = open ? '▼' : '▲';
  if(!open){
    list.querySelectorAll('.bar-fill[data-pct]').forEach(f=>{ f.style.width=f.dataset.pct+'%'; });
  }
}

// ─── 2 MAP ───────────────────────────────────────────────────────────────────
function renderMap(){
  const data = computeCounties(scopedPeople());
  if(!data.length){document.getElementById('county-list').innerHTML='<div class="no-res">立委依選區在立法院，不分縣市，請切換為「全部」或「議員」</div>';return;}
  const maxRate = data[0].rate;

  function rateColor(rate){
    const t = rate / 65;
    const r = Math.round(255 * Math.min(1, t*1.5));
    const g = Math.round(220 * Math.max(0, 1 - t));
    const b = 30;
    return `rgb(${r},${g},${b})`;
  }

  const SIX = new Set(['台北市','新北市','桃園市','台中市','台南市','高雄市']);
  const rows = data.map((c,i)=>{
    const color = rateColor(c.rate);
    const isSix = SIX.has(c.county);
    return `<div class="county-row">
      <div class="cname">${c.county}</div>
      <div class="county-track">
        <div class="county-fill" data-pct="${(c.rate/maxRate*100).toFixed(1)}"
             style="background:${color};width:0%"></div>
      </div>
      <div class="county-rate" style="color:${color}">${c.rate}%</div>
      ${!isSix ? '<div class="rural-badge">縣市</div>' : '<div class="rural-badge six">直轄市</div>'}
      <div class="county-note">(${c.luxury}/${c.total})</div>
    </div>`;
  }).join('');
  document.getElementById('county-list').innerHTML = rows;
}

// ─── 3 SUPERCARS ─────────────────────────────────────────────────────────────
function renderSupercars(){
  const html = computeSupercars(scopedPeople()).map(p=>{
    const color = pc(p.party);
    const carsHtml = p.all_cars.map(c=>{
      const cls = c.supercar ? 'hcar sc' : c.luxury ? 'hcar lux' : 'hcar reg';
      const cc  = c.cc>0 ? c.cc.toLocaleString()+'cc' : '';
      const raw = (c.raw&&c.raw!==c.brand) ? `<span class="hcar-raw">${c.raw}</span>` : '';
      const dt  = c.acquired ? `<span class="hcar-date">${fmtDate(c.acquired)}</span>` : '';
      return `<div class="${cls}">
        <span class="hcar-em">${em(c.brand)}</span>
        <span class="hcar-brand">${c.brand}</span>
        ${raw}
        ${dt}
        <span class="hcar-cc">${cc}</span>
      </div>`;
    }).join('');
    return `<div class="hall-card">
      <div class="hall-top">
        <div class="hall-name">${p.name}</div>
        <div class="hall-badges">
          <span class="hall-badge hb-party" style="background:${color}">${p.party}</span>
          <span class="hall-badge hb-title">${p.title}</span>
          <span class="hall-badge hb-county">${p.county}</span>
        </div>
      </div>
      <div class="hall-cars">${carsHtml}</div>
    </div>`;
  }).join('');
  document.getElementById('hall-grid').innerHTML = html;
}

// ─── 4 SEARCH ────────────────────────────────────────────────────────────────
function renderSearch(){ doSearch(); }

function doSearch(){
  const county = document.getElementById('sel-county').value;
  const party  = document.getElementById('sel-party').value;
  const sortBy = document.getElementById('sel-sort').value;
  const q      = document.getElementById('s-search').value.trim().toLowerCase();

  let list = scopedPeople().filter(p=>{
    if(county && p.county!==county) return false;
    if(party  && p.party !==party)  return false;
    if(q){
      const hay = (p.name+p.county+p.party+p.cars.map(c=>c.brand+c.raw).join('')).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
  list.sort((a,b)=>{
    if(sortBy==='luxury') return (b.luxury_count-a.luxury_count)||(b.car_count-a.car_count);
    if(sortBy==='price')  return (b.total_price||0)-(a.total_price||0);
    if(sortBy==='cars')   return b.car_count-a.car_count;
    return a.name.localeCompare(b.name,'zh-TW');
  });

  const tCars=list.reduce((s,p)=>s+p.car_count,0);
  const tLux =list.reduce((s,p)=>s+p.luxury_count,0);
  const tSC  =list.reduce((s,p)=>s+p.supercar_count,0);
  document.getElementById('ms-people').textContent = list.length;
  document.getElementById('ms-cars').textContent   = tCars;
  document.getElementById('ms-lux').textContent    = tLux;
  document.getElementById('ms-sc').textContent     = tSC;

  if(!list.length){
    const _NO_DATA_COUNTIES = new Set(['基隆市','新竹市','嘉義市','花蓮縣','台東縣','澎湖縣','金門縣','連江縣']);
    const _msg = (county && _NO_DATA_COUNTIES.has(county))
      ? `<div class="no-res">📋 ${county}的議員申報資料僅收錄於廉政專刊第 291 期以前，<br>超出本站資料範圍，無法顯示。</div>`
      : '<div class="no-res">🤷 找不到符合條件的民代</div>';
    document.getElementById('search-grid').innerHTML = _msg;
    return;
  }
  const color = pc;
  document.getElementById('search-grid').innerHTML = list.map(p=>{
    const c = color(p.party);
    const sc = p.supercar_count>0;
    const lx = p.luxury_count>0;
    const mn = p.car_count>=5;
    let sp = '';
    if(sc)     sp=`<div class="s-sp sp-sc">🔥 超跑<br>${p.supercar_count}台</div>`;
    else if(lx)sp=`<div class="s-sp sp-lux">✨ 豪車<br>${p.luxury_count}台</div>`;
    else if(mn)sp=`<div class="s-sp sp-many">🚗 ${p.car_count}台</div>`;
    const cars = p.cars.map(car=>{
      const cls = car.supercar?'ci sc':car.luxury?'ci lux':'ci';
      const cc  = car.cc>0?car.cc.toLocaleString()+'cc':'';
      const raw = (car.raw&&car.raw!==car.brand)?`<span class="ci-raw" title="${car.raw}">${car.raw}</span>`:'';
      const priceEl = typeof car.price==='number'
        ? `<span class="ci-price">${(car.price/10000).toFixed(0)}萬${car.price_traced?'<span class="ci-traced" title="從歷史申報回溯">✱</span>':''}</span>`
        : car.price==='over5' ? `<span class="ci-over5">5年+</span>` : (cc?`<span class="ci-cc">${cc}</span>`:'');
      const dateEl = car.acquired ? `<span class="ci-date">${fmtDate(car.acquired)}</span>` : '';
      return `<div class="${cls}"><span class="ci-em">${em(car.brand)}</span><span class="ci-left"><span class="ci-brand">${car.brand}</span>${raw}</span><span class="ci-right">${dateEl}${priceEl}</span></div>`;
    }).join('');
    const dt = p.date?p.date.substring(0,7):'';
    function fmtPrice(n){ return n>=10000000?(n/10000000).toFixed(2)+'億':(n/10000).toFixed(0)+'萬'; }
    const totalEl = p.total_price
      ? `<div class="s-total">
           <span class="s-total-label">已知總車價</span>
           <span class="s-total-val">${fmtPrice(p.total_price)}</span>
           ${p.price_coverage<p.car_count?`<span class="s-total-note">（${p.price_coverage}/${p.car_count} 台有價格）</span>`:''}
         </div>` : '';
    return `<div class="s-card" style="--pc:${c}">
      <div class="s-header">
        <div>
          <div class="s-name">${p.name}</div>
          <div class="s-meta">
            <span class="badge b-party" style="background:${c}">${p.party||'不明'}</span>
            <span class="badge b-title">${p.title}</span>
            <span class="badge b-county">${p.county}</span>
            ${dt?`<span class="badge b-date">${dt}</span>`:''}
          </div>
        </div>${sp}
      </div>
      <div class="s-cars">${cars||'<div style="color:#aaa;font-size:.82rem;padding:.3rem .5rem">無汽車申報</div>'}</div>
      ${totalEl}
    </div>`;
  }).join('');
}

['sel-county','sel-party','sel-sort'].forEach(id=>
  document.getElementById(id).addEventListener('change', doSearch)
);
let st;
document.getElementById('s-search').addEventListener('input',()=>{
  clearTimeout(st); st=setTimeout(doSearch,200);
});

// ─── 5 ECO ───────────────────────────────────────────────────────────────────
// ─── 6 PARTY ─────────────────────────────────────────────────────────────────
let _partyPeopleMap = {};

function renderParty(){
  const pp = scopedPeople();

  // build party→people index (sorted by luxury_count desc)
  _partyPeopleMap = {};
  pp.forEach(p=>{
    if(!_partyPeopleMap[p.party]) _partyPeopleMap[p.party]=[];
    _partyPeopleMap[p.party].push(p);
  });
  const _COUNTY_ORDER2 = ['立法院','台北市','新北市','基隆市','宜蘭縣','桃園市','新竹市','新竹縣','苗栗縣','台中市','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','台南市','高雄市','屏東縣','花蓮縣','台東縣','澎湖縣','金門縣','連江縣','其他'];
  const _countyRank2 = c => { const i=_COUNTY_ORDER2.indexOf(c); return i<0?99:i; };
  Object.values(_partyPeopleMap).forEach(arr=>
    arr.sort((a,b)=>b.luxury_count-a.luxury_count||b.car_count-a.car_count||_countyRank2(a.county)-_countyRank2(b.county))
  );

  const html = computeParties(pp).map(p=>{
    const c    = pc(p.party);
    const maxB = p.top_brands[0]?.count||1;
    const bars = p.top_brands.map(b=>`<div class="p-bar-row">
      <div class="p-bar-label">${em(b.brand)} ${b.brand}</div>
      <div class="p-bar-track">
        <div class="p-bar-fill" data-pct="${(b.count/maxB*100).toFixed(1)}"
             style="background:${c};width:0%"></div>
      </div>
      <div class="p-bar-n">${b.count}</div>
    </div>`).join('');

    const spaces = Array(p.total).fill(0).map((_,i)=>{
      const isLux = i < p.luxury;
      return `<div class="parking-space${isLux?' luxury':''}"
        style="background:${isLux?'#e67e22':c+'88'};border-color:${isLux?'#c0580a':c}"
        title="${isLux?'豪車':'一般車'}"></div>`;
    }).join('');

    const partyEsc = p.party.replace(/'/g,"\\'");
    return `<div class="party-card" onclick="selectParty('${partyEsc}',this)">
      <div class="party-head" style="background:${c}">
        <h3>${p.party}</h3>
        <p>豪車率 ${p.rate}%</p>
      </div>
      <div class="party-body">
        <div class="p-stat-row">
          <div class="p-stat"><div class="p-stat-n">${p.total}</div><div class="p-stat-l">申報車輛</div></div>
          <div class="p-stat"><div class="p-stat-n" style="color:#e67e22">${p.luxury}</div><div class="p-stat-l">豪車</div></div>
          <div class="p-stat"><div class="p-stat-n" style="color:${c}">${p.rate}%</div><div class="p-stat-l">豪車率</div></div>
        </div>
        <div class="p-bars">${bars}</div>
        <div class="lot-wrap">
          <div class="lot-title">停車場（<span style="color:#e67e22">■</span> 橘色=豪車）</div>
          <div class="parking-lot">${spaces}</div>
        </div>
      </div>
    </div>`;
  }).join('');
  document.getElementById('party-grid').innerHTML = html;
}

function selectParty(party, cardEl){
  document.querySelectorAll('#party-grid .party-card').forEach(c=>c.classList.remove('active'));
  cardEl.classList.add('active');

  const people = _partyPeopleMap[party] || [];
  const color  = pc(party);
  const panel  = document.getElementById('party-panel');
  panel.innerHTML = `
    <div class="brand-panel-header">
      <div class="brand-panel-title" style="color:${color}">${party}</div>
      <div class="brand-panel-sub">${people.length} 位民代</div>
    </div>
    <div class="brand-owners">
      ${people.map(p=>{
        const luxTag = p.luxury_count>0
          ? `<span style="color:#e67e22;font-size:.75rem;margin-left:auto">${p.luxury_count}豪</span>` : '';
        const carTag = `<span style="color:#aaa;font-size:.75rem">${p.car_count}台</span>`;
        return `<div class="bo-row">
          <span class="bo-name">${p.name}</span>
          <span class="badge b-title">${p.title}</span>
          <span class="badge b-county">${p.county}</span>
          ${carTag}${luxTag}
        </div>`;
      }).join('')}
    </div>`;
  panel.scrollTop = 0;
}

// ─── 7 GENDER ────────────────────────────────────────────────────────────────
function renderGender(){
  const g = computeGender(scopedPeople());
  function card(sex, data, headCls, color){
    const maxB = data.top_brands[0]?.count||1;
    const bars = data.top_brands.map(b=>`<div class="g-br">
      <div class="g-br-label">${em(b.brand)} ${b.brand}</div>
      <div class="g-br-track">
        <div class="g-br-fill" data-pct="${(b.count/maxB*100).toFixed(1)}"
             style="background:${color};width:0%"></div>
      </div>
      <div class="g-br-n">${b.count}</div>
    </div>`).join('');
    return `<div class="gender-card">
      <div class="g-head ${headCls}">${sex === '男' ? '👨 男性民代' : '👩 女性民代'}</div>
      <div class="g-body">
        <div class="g-big" style="color:${color}">${data.rate}%</div>
        <div class="g-sub">豪車率（共 ${data.luxury} / ${data.total} 台）</div>
        <div class="g-bar-section">Top 8 品牌</div>
        ${bars}
      </div>
    </div>`;
  }
  document.getElementById('gender-wrap').innerHTML =
    card('男', g['男'], 'g-head-m', '#1565c0') +
    card('女', g['女'], 'g-head-f', '#c2185b');
}

// ─── 8 RICHEST ───────────────────────────────────────────────────────────────
function renderRichest(){
  const RANK_CLASS = ['gold','silver','bronze'];
  function fmt(n){ return n>=10000000 ? (n/10000000).toFixed(2)+'億' : (n/10000).toFixed(0)+'萬'; }

  const html = computeRichest(scopedPeople()).map((p,i)=>{
    const rankCls = RANK_CLASS[i] || '';
    const color = pc(p.party);
    const carsHtml = p.cars.map(c=>{
      const cls = c.supercar ? 'rcar sc' : c.luxury ? 'rcar lux' : 'rcar';
      const tracedMark = c.price_traced ? '<span title="從歷史申報回溯" style="color:#aaa;font-size:.72rem;margin-left:.15rem">✱</span>' : '';
      const priceStr = typeof c.price === 'number'
        ? `<span class="rcar-price">${c.price.toLocaleString()}${tracedMark}</span>`
        : c.price === 'over5'
          ? '<span class="rcar-over5">超過五年</span>'
          : '';
      const dateEl = c.acquired ? `<span class="rcar-date">${fmtDate(c.acquired)}</span>` : '';
      return `<div class="${cls}">${em(c.brand)} ${c.brand}${dateEl}${priceStr}</div>`;
    }).join('');
    const covNote = p.price_coverage < p.car_count
      ? `（${p.price_coverage}/${p.car_count} 台有填價格）` : '';
    return `<div class="rich-card" style="--pc:${color}">
      <div class="rich-top">
        <div class="rich-rank ${rankCls}">${i+1}</div>
        <div class="rich-info">
          <div class="rich-name">${p.name}</div>
          <div class="rich-meta">
            <span class="badge b-party" style="background:${color};color:#fff">${p.party}</span>
            <span class="badge b-title">${p.title}</span>
            <span class="badge b-county">${p.county}</span>
          </div>
        </div>
        <div class="rich-price-block">
          <div class="rich-total">${fmt(p.total_price)}</div>
          <div class="rich-total-label">申報總車價</div>
          <div class="rich-coverage">${covNote}</div>
        </div>
      </div>
      <div class="rich-cars">${carsHtml}</div>
    </div>`;
  }).join('');
  document.getElementById('richest-list').innerHTML = html;
}

// ─── OWNER PAGE ──────────────────────────────────────────────────────────────
function renderOwner(){
  const people = scopedPeople();
  const totalCars   = people.reduce((s,p)=>s+p.car_count,0);
  const totalSelf   = people.reduce((s,p)=>s+p.self_count,0);
  const totalSpouse = people.reduce((s,p)=>s+p.spouse_count,0);
  const selfPct     = totalCars ? (totalSelf/totalCars*100).toFixed(1) : 0;
  const spousePct   = totalCars ? (totalSpouse/totalCars*100).toFixed(1) : 0;

  // luxury breakdown
  const allCars = people.flatMap(p=>p.cars);
  const selfLux   = allCars.filter(c=>c.is_self && c.luxury).length;
  const spouseLux = allCars.filter(c=>!c.is_self && c.luxury).length;
  const selfTotal   = allCars.filter(c=>c.is_self).length;
  const spouseTotal = allCars.filter(c=>!c.is_self).length;
  const selfLuxPct   = selfTotal   ? (selfLux/selfTotal*100).toFixed(1)   : 0;
  const spouseLuxPct = spouseTotal ? (spouseLux/spouseTotal*100).toFixed(1) : 0;

  // people with any spouse car
  const hasSpouse = people.filter(p=>p.spouse_count>0).length;
  const allSpouse = people.filter(p=>p.car_count>0 && p.self_count===0).length;

  document.getElementById('owner-summary-box').innerHTML =
    `<strong>👫 整體概況（${people.length} 位民代 / ${totalCars} 台車）</strong><br>
    本人名下：<strong>${totalSelf} 台（${selfPct}%）</strong>　配偶名下：<strong>${totalSpouse} 台（${spousePct}%）</strong><br>
    豪車率 — 本人：${selfLuxPct}%　配偶：${spouseLuxPct}%<br>
    ${hasSpouse} 位民代有配偶名下車輛（佔 ${people.length ? (hasSpouse/people.length*100).toFixed(0) : 0}%），其中 ${allSpouse} 位所有申報車輛全數登記在配偶名下。`;

  // ── party breakdown ──
  const MAIN = ['國民黨','民進黨','民眾黨','無黨籍','時代力量','新黨','親民黨','台灣基進'];
  const partyData = {};
  MAIN.forEach(pt=>{
    const pp = people.filter(p=>p.party===pt);
    const tc = pp.reduce((s,p)=>s+p.car_count,0);
    const sc = pp.reduce((s,p)=>s+p.spouse_count,0);
    if(tc>=5) partyData[pt] = {total:tc, spouse:sc, rate: tc ? (sc/tc*100).toFixed(1) : 0};
  });
  const partyRows = Object.entries(partyData)
    .sort((a,b)=>b[1].rate-a[1].rate)
    .map(([pt,d])=>{
      const pct = +d.rate;
      const color = pc(pt);
      return `<div class="ow-row">
        <div class="ow-label" style="color:${color};font-weight:700">${pt}</div>
        <div class="ow-bar-wrap">
          <div class="ow-fill" data-pct="${pct}" style="background:${color};width:0;height:100%;border-radius:3px;transition:width .7s ease"></div>
        </div>
        <div class="ow-pct">${d.rate}%</div>
        <div class="ow-detail">(${d.spouse}/${d.total})</div>
      </div>`;
    }).join('');

  // ── gender breakdown ──
  const gData = {};
  ['男','女'].forEach(g=>{
    const pp = people.filter(p=>p.gender===g);
    const tc = pp.reduce((s,p)=>s+p.car_count,0);
    const sc = pp.reduce((s,p)=>s+p.spouse_count,0);
    gData[g] = {total:tc, spouse:sc, rate: tc ? (sc/tc*100).toFixed(1) : 0};
  });

  document.getElementById('owner-charts').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:2rem">
      <div class="stat-block">
        <div class="stat-num" style="color:#16a085">${spousePct}%</div>
        <div class="stat-label">配偶名下比例</div>
        <div style="font-size:.82rem;color:#888;margin-top:.3rem">${totalSpouse} 台 / 共 ${totalCars} 台</div>
      </div>
      <div class="stat-block">
        <div class="stat-num" style="color:#c0392b">${allSpouse}</div>
        <div class="stat-label">全數登記配偶</div>
        <div style="font-size:.82rem;color:#888;margin-top:.3rem">有申報車輛中，所有車都掛在配偶名下</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin-bottom:2rem">
      <div>
        <h4 style="margin-bottom:.8rem;color:#555;font-size:.95rem">各黨配偶名下比例</h4>
        <div style="font-size:.8rem;color:#999;margin-bottom:.5rem">（配偶名下車輛 / 該黨總車輛）</div>
        <div style="display:flex;flex-direction:column;gap:.5rem">${partyRows}</div>
      </div>
      <div>
        <h4 style="margin-bottom:.8rem;color:#555;font-size:.95rem">性別比較</h4>
        <div style="font-size:.8rem;color:#999;margin-bottom:.5rem">配偶名下車輛比例</div>
        <div style="display:flex;flex-direction:column;gap:.8rem">
          ${['男','女'].map(g=>{
            const d = gData[g];
            if(!d || d.total<5) return '';
            const pct = +d.rate;
            return `<div>
              <div style="display:flex;justify-content:space-between;margin-bottom:.3rem">
                <span style="font-weight:700">${g}性民代</span>
                <span style="color:#16a085;font-weight:700">${d.rate}%</span>
              </div>
              <div style="background:#eee;border-radius:4px;height:10px;overflow:hidden">
                <div class="ow-fill" data-pct="${pct}" style="background:#16a085;width:0;height:100%;border-radius:4px;transition:width .7s ease"></div>
              </div>
              <div style="font-size:.78rem;color:#888;margin-top:.2rem">${d.spouse} 台配偶 / ${d.total} 台總計</div>
            </div>`;
          }).join('')}
        </div>
        <div style="margin-top:1.5rem;padding:1rem;background:#f9f9f9;border-radius:8px;font-size:.85rem;color:#555;line-height:1.7">
          💡 豪車率：本人名下 <strong>${selfLuxPct}%</strong>，配偶名下 <strong>${spouseLuxPct}%</strong><br>
          兩者差異不大，豪車並未特別集中在某一方名下。
        </div>
      </div>
    </div>`;

  // ── top spouse list ──
  const topSpouse = [...people]
    .filter(p=>p.spouse_count>0)
    .sort((a,b)=>b.spouse_count-a.spouse_count || b.car_count-a.car_count)
    .slice(0,50);

  document.getElementById('owner-list').innerHTML = topSpouse.map((p,i)=>{
    const color = pc(p.party);
    const carsHtml = p.cars.map(c=>{
      const ownerTag = c.is_self
        ? `<span style="font-size:.72rem;color:#888;margin-left:.3rem">本人</span>`
        : `<span style="font-size:.72rem;color:#16a085;font-weight:700;margin-left:.3rem">配偶</span>`;
      const cls = c.supercar ? 'rcar sc' : c.luxury ? 'rcar lux' : 'rcar';
      const tracedMark = c.price_traced ? '<span title="從歷史申報回溯" style="color:#aaa;font-size:.72rem;margin-left:.15rem">✱</span>' : '';
      const priceStr = typeof c.price === 'number'
        ? `<span class="rcar-price">${(c.price/10000).toFixed(0)}萬${tracedMark}</span>`
        : c.price === 'over5' ? '<span class="rcar-over5">5年+</span>' : '';
      const dateEl = c.acquired ? `<span class="rcar-date">${fmtDate(c.acquired)}</span>` : '';
      return `<div class="${cls}">${em(c.brand)} ${c.brand}${ownerTag}${dateEl}${priceStr}</div>`;
    }).join('');
    const spousePct2 = p.car_count ? Math.round(p.spouse_count/p.car_count*100) : 0;
    return `<div class="rich-card" style="--pc:${color}">
      <div class="rich-top">
        <div class="rich-rank" style="background:#16a085;color:#fff;font-size:.95rem">${i+1}</div>
        <div class="rich-info">
          <div class="rich-name">${p.name}</div>
          <div class="rich-meta">
            <span class="badge b-party" style="background:${color};color:#fff">${p.party}</span>
            <span class="badge b-title">${p.title}</span>
            <span class="badge b-county">${p.county}</span>
          </div>
        </div>
        <div class="rich-price-block">
          <div class="rich-total" style="color:#16a085">${p.spouse_count}<span style="font-size:.9rem"> 台</span></div>
          <div class="rich-total-label">配偶名下</div>
          <div style="font-size:.78rem;color:#888">共 ${p.car_count} 台・配偶佔 ${spousePct2}%</div>
        </div>
      </div>
      <div class="rich-cars">${carsHtml}</div>
    </div>`;
  }).join('');
}

// ─── ANIMATIONS ──────────────────────────────────────────────────────────────
function triggerAnimations(id){
  if(id==='brands'){
    document.querySelectorAll('.bar-fill[data-pct]').forEach(el=>{
      el.style.width = el.dataset.pct+'%';
    });
  }
  if(id==='map'){
    document.querySelectorAll('.county-fill[data-pct]').forEach(el=>{
      el.style.width = el.dataset.pct+'%';
    });
  }
  if(id==='party'||id==='gender'){
    document.querySelectorAll('.p-bar-fill[data-pct],.g-br-fill[data-pct]').forEach(el=>{
      el.style.width = el.dataset.pct+'%';
    });
  }
  if(id==='owner'){
    document.querySelectorAll('.ow-fill[data-pct]').forEach(el=>{
      el.style.width = el.dataset.pct+'%';
    });
  }
}

// ─── HASH ROUTING ────────────────────────────────────────────────────────────
(function(){
  const h = location.hash.replace('#','');
  if(h && document.getElementById('view-'+h)) showView(h);
})();
</script>
</body>
</html>'''

# ─── 動態填入首頁文案數字（避免寫死過時）──────────────────────────────────────
_people = json.loads(cars_raw)
_total_people = len(_people)
_total_cars = sum(len(p.get('cars', [])) for p in _people)

# 性別豪車率（與前端 computeGender 一致：以每台車的 luxury flag 計）
def _gender_rate(sex):
    cs = [c for p in _people if p.get('gender') == sex for c in p.get('cars', [])]
    if not cs:
        return 0.0
    return round(sum(1 for c in cs if c.get('luxury')) / len(cs) * 1000) / 10
_f_rate = _gender_rate('女')
_m_rate = _gender_rate('男')
_g_diff = round(abs(_m_rate - _f_rate) * 10) / 10

# 縣市豪車率冠軍（與前端 computeCounties 一致：排除立法院/其他）
_tot, _lux = {}, {}
for p in _people:
    c = p.get('county')
    if not p.get('cars') or not c or c in ('立法院', '其他'):
        continue
    _tot[c] = _tot.get(c, 0) + p.get('car_count', 0)
    _lux[c] = _lux.get(c, 0) + p.get('luxury_count', 0)
_county_rates = sorted(
    ((c, round((_lux.get(c, 0) / _tot[c]) * 1000) / 10) for c in _tot if _tot[c]),
    key=lambda x: -x[1])
_top_county, _top_rate = _county_rates[0] if _county_rates else ('', 0)

html = (html
    .replace('__TOTAL_PEOPLE__', f'{_total_people:,}')
    .replace('__TOTAL_CARS__', f'{_total_cars:,}')
    .replace('__FEMALE_RATE__', f'{_f_rate:g}')
    .replace('__MALE_RATE__', f'{_m_rate:g}')
    .replace('__GENDER_DIFF__', f'{_g_diff:g}')
    .replace('__TOP_COUNTY__', _top_county)
    .replace('__TOP_COUNTY_RATE__', f'{_top_rate:g}'))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
size = os.path.getsize(OUT)/1024
print(f'Done → {OUT}  ({size:.0f} KB)')
