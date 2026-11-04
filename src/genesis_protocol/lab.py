"""Generate a self-contained interactive HTML viewer for an ecology run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_lab(experiment: dict[str, Any], output: str | Path = "genesis-lab.html") -> Path:
    """Write an offline viewer with generation navigation and species filtering."""
    payload = json.dumps(experiment, separators=(",", ":")).replace("</", "<\\/")
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Genesis Protocol — Evolutionary Laboratory</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif;background:#0b1020;color:#e8edf8}
body{margin:0;padding:24px;max-width:1100px;margin-inline:auto}h1{margin-bottom:4px}
.muted{color:#9eacc6}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.card{background:#151e33;border:1px solid #293754;border-radius:12px;padding:16px}
.metric{font-size:1.7rem;font-weight:700}.controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:18px 0}
input,select{accent-color:#8bb7ff;background:#151e33;color:#e8edf8;padding:8px;border:1px solid #415274;border-radius:8px}
canvas{width:100%;height:280px;background:#10182b;border-radius:12px;margin-top:12px}
table{border-collapse:collapse;width:100%;margin-top:12px}td,th{text-align:left;padding:9px;border-bottom:1px solid #293754}
</style></head><body>
<h1>Genesis Protocol</h1><div class="muted">Evolutionary laboratory · deterministic experiment record</div>
<div class="controls"><label>Generation <input id="generation" type="range" min="0" value="0"></label><span id="generation-label"></span>
<label>Species <select id="species"><option value="all">All species</option></select></label></div>
<div class="grid"><div class="card"><div class="muted">Population</div><div class="metric" id="population">—</div></div>
<div class="card"><div class="muted">Mean resources</div><div class="metric" id="resources">—</div></div>
<div class="card"><div class="muted">Mean survival energy</div><div class="metric" id="survival">—</div></div>
<div class="card"><div class="muted">Genotype diversity</div><div class="metric" id="diversity">—</div></div></div>
<canvas id="chart" width="1000" height="280" aria-label="Evolution metrics chart"></canvas>
<h2>Species populations</h2><table><thead><tr><th>Species</th><th>Population</th></tr></thead><tbody id="species-table"></tbody></table>
<h2>Lineage records</h2><p class="muted">The run contains <strong id="lineage-count">0</strong> organism lineage records. Export the source JSON for full parent-child reconstruction.</p>
<script>
const data=__DATA__;
const reports=data.reports||[];const species=data.species||[];
const slider=document.getElementById('generation'),filter=document.getElementById('species');
slider.max=Math.max(0,reports.length-1);
for(const s of species){const o=document.createElement('option');o.value=String(s.species_id);o.textContent=s.name;filter.append(o)}
document.getElementById('lineage-count').textContent=(data.lineage||[]).length;
function draw(){const i=Number(slider.value),r=reports[i];if(!r)return;
document.getElementById('generation-label').textContent='Generation '+r.generation;
document.getElementById('population').textContent=Object.values(r.species_population).reduce((a,b)=>a+b,0);
document.getElementById('resources').textContent=Number(r.mean_resources).toFixed(2);
document.getElementById('survival').textContent=Number(r.mean_survival).toFixed(2);
document.getElementById('diversity').textContent=r.genotype_diversity;
const body=document.getElementById('species-table');body.replaceChildren();
for(const [name,count] of Object.entries(r.species_population)){const row=document.createElement('tr');
const a=document.createElement('td'),b=document.createElement('td');a.textContent=name;b.textContent=count;
if(filter.value==='all'||species.find(s=>s.name===name)?.species_id===Number(filter.value)){row.append(a,b);body.append(row)}}
const canvas=document.getElementById('chart'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
const values=reports.map(x=>x.mean_resources),max=Math.max(1,...values);
ctx.strokeStyle='#8bb7ff';ctx.lineWidth=3;ctx.beginPath();
values.forEach((v,n)=>{const x=40+n*(canvas.width-80)/Math.max(1,values.length-1),y=canvas.height-30-(v/max)*(canvas.height-60);if(n===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});
ctx.stroke();ctx.fillStyle='#aab8d0';ctx.font='14px system-ui';ctx.fillText('Mean resources gathered per organism',40,20);
ctx.strokeStyle='#445574';ctx.beginPath();ctx.moveTo(40,canvas.height-30);ctx.lineTo(canvas.width-40,canvas.height-30);ctx.stroke();
}
slider.addEventListener('input',draw);filter.addEventListener('change',draw);draw();
</script></body></html>"""
    target = Path(output)
    target.write_text(html.replace("__DATA__", payload), encoding="utf-8")
    return target
