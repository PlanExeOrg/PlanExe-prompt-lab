#!/usr/bin/env python3
"""
Flask app to visualize levers_chart_data.jsonl.
Run: /opt/homebrew/bin/python3.11 chart_dashboard/app.py
"""
import json
from pathlib import Path
from flask import Flask, jsonify, Response

app = Flask(__name__)

DATA_PATH = Path(__file__).parent / "levers_chart_data.jsonl"


def load_data():
    rows = []
    with open(DATA_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@app.route("/api/data")
def api_data():
    return jsonify(load_data())


@app.route("/")
def index():
    return Response(HTML, content_type="text/html")


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Levers Chart Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f1117; color: #e0e0e0; padding: 20px; }
h1 { font-size: 1.4rem; margin-bottom: 16px; color: #fff; }
h2 { font-size: 1.1rem; margin-bottom: 8px; color: #ccc; }
.controls { margin-bottom: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.controls label { font-size: 0.85rem; color: #aaa; }
.controls select { background: #1a1d28; color: #e0e0e0; border: 1px solid #333; padding: 4px 8px; border-radius: 4px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card { background: #1a1d28; border-radius: 8px; padding: 16px; }
.card canvas { width: 100% !important; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: #1a1d28; border-radius: 8px; padding: 14px; text-align: center; }
.stat-card .value { font-size: 1.6rem; font-weight: 700; color: #58a6ff; }
.stat-card .label { font-size: 0.8rem; color: #888; margin-top: 4px; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(2, 1fr); } }
</style>
</head>
<body>
<h1>identify_potential_levers &mdash; Dashboard</h1>

<div class="controls">
  <label>History group:
    <select id="groupSelect"><option value="all">All</option></select>
  </label>
  <label>Model:
    <select id="modelSelect"><option value="all">All</option></select>
  </label>
</div>

<div class="stats" id="stats"></div>

<div class="grid">
  <div class="card"><h2>Success Rate over Iterations</h2><canvas id="chartSuccess"></canvas></div>
  <div class="card"><h2>Avg Duration (seconds) over Iterations</h2><canvas id="chartDuration"></canvas></div>
  <div class="card"><h2>Success Rate over Time</h2><canvas id="chartSuccessTime"></canvas></div>
  <div class="card"><h2>Avg Duration over Time</h2><canvas id="chartDurationTime"></canvas></div>
  <div class="card"><h2>Duration by Model (box plot style)</h2><canvas id="chartModelDuration"></canvas></div>
  <div class="card"><h2>Success Rate by Model</h2><canvas id="chartModelSuccess"></canvas></div>
  <div class="card" style="grid-column: 1 / -1;"><h2>Per-Plan Durations over Iterations</h2><canvas id="chartPerPlan"></canvas></div>
</div>

<script>
const CHART_DEFAULTS = {
  borderWidth: 2,
  pointRadius: 3,
  tension: 0.3,
};

const COLORS = [
  '#58a6ff', '#f78166', '#3fb950', '#d2a8ff', '#f0e68c',
  '#79c0ff', '#ffa657', '#7ee787', '#bc8cff', '#e6db74',
];

const MODEL_COLORS = {};
let colorIdx = 0;
function modelColor(m) {
  if (!MODEL_COLORS[m]) MODEL_COLORS[m] = COLORS[colorIdx++ % COLORS.length];
  return MODEL_COLORS[m];
}

let allData = [];
let charts = {};

async function init() {
  const resp = await fetch('/api/data');
  allData = await resp.json();

  // Populate filters
  const groups = [...new Set(allData.map(r => r.history_group))].sort();
  const models = [...new Set(allData.map(r => r.model).filter(Boolean))].sort();

  const gs = document.getElementById('groupSelect');
  groups.forEach(g => { const o = document.createElement('option'); o.value = g; o.textContent = `Group ${g}`; gs.appendChild(o); });

  const ms = document.getElementById('modelSelect');
  models.forEach(m => { const o = document.createElement('option'); o.value = m; o.textContent = m; ms.appendChild(o); });

  // Assign stable colors
  models.forEach(m => modelColor(m));

  gs.addEventListener('change', render);
  ms.addEventListener('change', render);

  render();
}

function filtered() {
  const g = document.getElementById('groupSelect').value;
  const m = document.getElementById('modelSelect').value;
  return allData.filter(r =>
    (g === 'all' || String(r.history_group) === g) &&
    (m === 'all' || r.model === m)
  );
}

function renderStats(data) {
  const el = document.getElementById('stats');
  const total = data.length;
  const avgSuccess = total ? (data.reduce((s, r) => s + (r.success_rate ?? 0), 0) / total * 100).toFixed(1) : 0;
  const avgDur = total ? (data.reduce((s, r) => s + (r.avg_duration_seconds ?? 0), 0) / total).toFixed(1) : 0;
  const models = new Set(data.map(r => r.model).filter(Boolean)).size;
  el.innerHTML = `
    <div class="stat-card"><div class="value">${total}</div><div class="label">Total Runs</div></div>
    <div class="stat-card"><div class="value">${avgSuccess}%</div><div class="label">Avg Success Rate</div></div>
    <div class="stat-card"><div class="value">${avgDur}s</div><div class="label">Avg Duration</div></div>
    <div class="stat-card"><div class="value">${models}</div><div class="label">Distinct Models</div></div>
  `;
}

function makeOrUpdate(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), config);
}

function render() {
  const data = filtered();
  renderStats(data);

  // Group by model for iteration charts
  const byModel = {};
  data.forEach(r => {
    const m = r.model || 'unknown';
    if (!byModel[m]) byModel[m] = [];
    byModel[m].push(r);
  });

  // 1. Success rate over iterations (one line per model)
  makeOrUpdate('chartSuccess', {
    type: 'line',
    data: {
      datasets: Object.entries(byModel).map(([m, rows]) => ({
        label: m,
        data: rows.map(r => ({ x: r.history_group * 1000 + r.iteration, y: r.success_rate * 100 })),
        borderColor: modelColor(m),
        backgroundColor: modelColor(m) + '33',
        ...CHART_DEFAULTS,
      })),
    },
    options: {
      scales: { x: { title: { display: true, text: 'Iteration', color: '#888' }, ticks: { color: '#888' } }, y: { title: { display: true, text: 'Success %', color: '#888' }, min: 0, max: 100, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });

  // 2. Avg duration over iterations
  makeOrUpdate('chartDuration', {
    type: 'line',
    data: {
      datasets: Object.entries(byModel).map(([m, rows]) => ({
        label: m,
        data: rows.map(r => ({ x: r.history_group * 1000 + r.iteration, y: r.avg_duration_seconds })),
        borderColor: modelColor(m),
        backgroundColor: modelColor(m) + '33',
        ...CHART_DEFAULTS,
      })),
    },
    options: {
      scales: { x: { title: { display: true, text: 'Iteration', color: '#888' }, ticks: { color: '#888' } }, y: { title: { display: true, text: 'Seconds', color: '#888' }, min: 0, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });

  // 3. Success rate over time
  makeOrUpdate('chartSuccessTime', {
    type: 'line',
    data: {
      datasets: Object.entries(byModel).map(([m, rows]) => ({
        label: m,
        data: rows.map(r => ({ x: r.timestamp, y: r.success_rate * 100 })),
        borderColor: modelColor(m),
        backgroundColor: modelColor(m) + '33',
        ...CHART_DEFAULTS,
      })),
    },
    options: {
      scales: { x: { type: 'time', time: { unit: 'hour' }, title: { display: true, text: 'Time', color: '#888' }, ticks: { color: '#888' } }, y: { title: { display: true, text: 'Success %', color: '#888' }, min: 0, max: 100, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });

  // 4. Avg duration over time
  makeOrUpdate('chartDurationTime', {
    type: 'line',
    data: {
      datasets: Object.entries(byModel).map(([m, rows]) => ({
        label: m,
        data: rows.map(r => ({ x: r.timestamp, y: r.avg_duration_seconds })),
        borderColor: modelColor(m),
        backgroundColor: modelColor(m) + '33',
        ...CHART_DEFAULTS,
      })),
    },
    options: {
      scales: { x: { type: 'time', time: { unit: 'hour' }, title: { display: true, text: 'Time', color: '#888' }, ticks: { color: '#888' } }, y: { title: { display: true, text: 'Seconds', color: '#888' }, min: 0, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });

  // 5. Duration by model (bar: min, avg, max)
  const modelNames = Object.keys(byModel).sort();
  const avgDurs = modelNames.map(m => {
    const durs = byModel[m].map(r => r.avg_duration_seconds).filter(d => d != null && d > 0);
    return durs.length ? durs.reduce((a, b) => a + b, 0) / durs.length : 0;
  });
  const minDurs = modelNames.map(m => {
    const durs = byModel[m].map(r => r.min_duration_seconds).filter(d => d != null && d > 0);
    return durs.length ? Math.min(...durs) : 0;
  });
  const maxDurs = modelNames.map(m => {
    const durs = byModel[m].map(r => r.max_duration_seconds).filter(d => d != null && d > 0);
    return durs.length ? Math.max(...durs) : 0;
  });

  makeOrUpdate('chartModelDuration', {
    type: 'bar',
    data: {
      labels: modelNames,
      datasets: [
        { label: 'Min', data: minDurs, backgroundColor: '#3fb95088' },
        { label: 'Avg', data: avgDurs, backgroundColor: '#58a6ff88' },
        { label: 'Max', data: maxDurs, backgroundColor: '#f7816688' },
      ],
    },
    options: {
      scales: { x: { ticks: { color: '#888', maxRotation: 45 } }, y: { title: { display: true, text: 'Seconds', color: '#888' }, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });

  // 6. Success rate by model
  const modelSuccessRates = modelNames.map(m => {
    const rates = byModel[m].map(r => r.success_rate).filter(r => r != null);
    return rates.length ? (rates.reduce((a, b) => a + b, 0) / rates.length * 100) : 0;
  });

  makeOrUpdate('chartModelSuccess', {
    type: 'bar',
    data: {
      labels: modelNames,
      datasets: [{
        label: 'Success %',
        data: modelSuccessRates,
        backgroundColor: modelNames.map(m => modelColor(m) + 'aa'),
        borderColor: modelNames.map(m => modelColor(m)),
        borderWidth: 1,
      }],
    },
    options: {
      scales: { x: { ticks: { color: '#888', maxRotation: 45 } }, y: { title: { display: true, text: 'Success %', color: '#888' }, min: 0, max: 100, ticks: { color: '#888' } } },
      plugins: { legend: { display: false } },
    },
  });

  // 7. Per-plan durations over iterations
  const planNames = [...new Set(data.flatMap(r => r.plans.map(p => p.plan_name)))].sort();
  makeOrUpdate('chartPerPlan', {
    type: 'line',
    data: {
      datasets: planNames.map((pn, i) => ({
        label: pn,
        data: data.map(r => {
          const p = r.plans.find(pp => pp.plan_name === pn);
          return p ? { x: r.history_group * 1000 + r.iteration, y: p.duration_seconds } : null;
        }).filter(Boolean),
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: COLORS[i % COLORS.length] + '33',
        ...CHART_DEFAULTS,
      })),
    },
    options: {
      scales: { x: { title: { display: true, text: 'Iteration', color: '#888' }, ticks: { color: '#888' } }, y: { title: { display: true, text: 'Seconds', color: '#888' }, min: 0, ticks: { color: '#888' } } },
      plugins: { legend: { labels: { color: '#ccc', boxWidth: 12 } } },
    },
  });
}

init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=False, port=5001)
