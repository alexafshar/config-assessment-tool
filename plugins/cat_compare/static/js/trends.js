// compare-plugin/static/js/trends.js

/**
 * trends.js
 * ---------
 * This module manages the rendering, layout, and updates of trend-related charts in the application.
 * It uses Chart.js to create and manipulate charts, ensuring proper responsiveness and layout.
 *
 * Purpose:
 * - Initializes and updates charts for visualizing trends.
 * - Ensures charts are properly wrapped and styled to avoid layout issues.
 * - Manages chart instances and prevents overlapping renders.
 * - Handles dynamic resizing and responsiveness of charts.
 *
 * Key Features:
 * - `ensureTrendBox(canvas, heightPx)`:
 *   - Ensures that the `<canvas>` element used by Chart.js is wrapped in a fixed-height container.
 *   - Prevents layout issues caused by Chart.js's responsive behavior.
 * - Chart Instances:
 *   - Manages trend chart instances to avoid redundant renders.
 * - Request Sequence Management:
 *   - Tracks asynchronous requests with `trendsReqSeq` to ensure only the latest data is used for rendering.
 * - Dynamic Chart Resizing:
 *   - Adjusts chart dimensions dynamically to fit the UI layout.
 *
 * Usage:
 * - This file is included in the application's frontend to manage trend-related charts.
 * - Functions are called to initialize, update, and manage charts dynamically based on user interactions or data updates.
 */

// Hold chart instances and a request sequence to avoid overlapping renders.
let overallLineChart = null;
let countsStackedChart = null;
let trendsReqSeq = 0;

/**
 * Ensure the canvas has a fixed-height wrapper that Chart.js will respect.
 * This avoids growth caused by responsive: true + maintainAspectRatio: false.
 */
function ensureTrendBox(canvas, heightPx) {
  if (!canvas) return null;

  // If already wrapped from a previous call, just update the height.
  if (canvas.parentElement && canvas.parentElement.classList.contains('trendbox')) {
    canvas.parentElement.style.height = heightPx + 'px';
    return canvas.parentElement;
  }

  // Create a wrapper right before the canvas and move the canvas inside it.
  const wrapper = document.createElement('div');
  wrapper.className = 'trendbox';
  wrapper.style.height = heightPx + 'px';
  wrapper.style.width = '100%';
  wrapper.style.position = 'relative';

  const parent = canvas.parentElement;
  parent.insertBefore(wrapper, canvas);
  wrapper.appendChild(canvas);

  // Let Chart.js use 100% to fill the wrapper height.
  canvas.style.height = '100%';
  canvas.style.width  = '100%';

  return wrapper;
}

function projectedNextValue(values) {
  const nums = values.map(v => Number(v)).filter(v => Number.isFinite(v));
  if (nums.length < 3) return null;
  const n = nums.length;
  const avgX = (n - 1) / 2;
  const avgY = nums.reduce((sum, value) => sum + value, 0) / n;
  let numerator = 0;
  let denominator = 0;
  nums.forEach((value, index) => {
    numerator += (index - avgX) * (value - avgY);
    denominator += (index - avgX) ** 2;
  });
  if (!denominator) return null;
  const slope = numerator / denominator;
  const intercept = avgY - slope * avgX;
  return Math.round(intercept + slope * n);
}

const chartTextColor = '#e8eef7';
const chartMutedColor = '#b8c7d8';
const chartGridColor = 'rgba(232,238,247,0.12)';
const chartZeroGridColor = 'rgba(232,238,247,0.26)';
const chartVerticalGridColor = 'rgba(232,238,247,0.05)';

function chartAxisTitle(text) {
  return {
    display: true,
    text,
    color: chartTextColor,
    font: { size: 12, weight: '600' }
  };
}

function chartTickOptions() {
  return {
    color: chartMutedColor,
    font: { size: 11 }
  };
}

/**
 * Desktop-only context menu to delete the currently selected snapshot.
 * Creates the menu dynamically and wires events to the Snapshot selector.
 */
function initSnapshotDeleteMenu() {
  const domainSel = document.getElementById('domain');
  const snapshotSel = document.getElementById('snapshot');
  if (!domainSel || !snapshotSel) return;

  // Inject lightweight styles for the context menu (once).
  if (!document.getElementById('snapshotMenuStyles')) {
    const style = document.createElement('style');
    style.id = 'snapshotMenuStyles';
    style.textContent = `
      .contextmenu{position:fixed;background:#0f1620;border:1px solid rgba(255,255,255,0.12);
        border-radius:8px;padding:6px;display:none;min-width:220px;box-shadow:0 8px 24px rgba(0,0,0,0.4);z-index:1000}
      .contextmenu .item{padding:8px 10px;cursor:pointer;font-size:13px;color:#e8eef7}
      .contextmenu .item:hover{background:rgba(255,255,255,0.06)}
      .contextmenu .item.danger:hover{background:rgba(192,0,0,0.15);color:#ffd7d7}
    `;
    document.head.appendChild(style);
  }

  // Build the menu once and attach to body.
  const menu = document.createElement('div');
  menu.id = 'snapshotMenu';
  menu.className = 'contextmenu';
  menu.setAttribute('role', 'menu');
  menu.setAttribute('aria-hidden', 'true');

  const btnDelete = document.createElement('div');
  btnDelete.className = 'item danger';
  btnDelete.id = 'menuDelete';
  btnDelete.textContent = 'Delete snapshot…';

  const btnCancel = document.createElement('div');
  btnCancel.className = 'item';
  btnCancel.id = 'menuCancel';
  btnCancel.textContent = 'Cancel';

  menu.appendChild(btnDelete);
  menu.appendChild(btnCancel);
  document.body.appendChild(menu);

  let menuOpen = false;

  function hideMenu() {
    if (!menuOpen) return;
    menu.style.display = 'none';
    menu.setAttribute('aria-hidden', 'true');
    menuOpen = false;
  }

  function showMenuAt(x, y) {
    menu.style.display = 'block';
    menu.setAttribute('aria-hidden', 'false');
    // Clamp within viewport
    const margin = 8;
    const w = menu.offsetWidth;
    const h = menu.offsetHeight;
    let left = x;
    let top = y;
    if (left + w > window.innerWidth - margin) left = window.innerWidth - w - margin;
    if (top + h > window.innerHeight - margin) top = window.innerHeight - h - margin;
    menu.style.left = left + 'px';
    menu.style.top = top + 'px';
    menuOpen = true;
  }

  // Right-click on Snapshot selector opens the menu (except for LATEST).
  snapshotSel.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const file = snapshotSel.value;
    if (!file || file === 'LATEST') return;
    showMenuAt(e.clientX, e.clientY);
  });

  // Close on outside click or Escape.
  document.addEventListener('click', (e) => {
    if (menuOpen && !menu.contains(e.target)) hideMenu();
  });
  document.addEventListener('keydown', (e) => {
    if (menuOpen && e.key === 'Escape') hideMenu();
    // Optional: open via Shift+F10 when snapshot select is focused.
    if (document.activeElement === snapshotSel && e.shiftKey && e.key === 'F10') {
      e.preventDefault();
      const rect = snapshotSel.getBoundingClientRect();
      showMenuAt(rect.left + 10, rect.top + 10);
    }
  });

  btnCancel.addEventListener('click', hideMenu);

  // Delete handler posts to backend and refreshes UI if globals exist.
  btnDelete.addEventListener('click', async () => {
    const domain = (domainSel.value || '').toLowerCase();
    const file = snapshotSel.value;
    if (!file || file === 'LATEST') { hideMenu(); return; }

    const ok = window.confirm(`Delete snapshot:\n${file}\n\nThis will remove it from history and trends.`);
    if (!ok) return;

    try {
      const res = await fetch('/api/history/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, file })
      });
      if (!res.ok) {
        alert(`Delete failed (status ${res.status}).`);
        return;
      }
      hideMenu();

      // Refresh UI safely if functions are available.
      if (typeof loadHistory === 'function') await loadHistory();
      if (typeof loadApps === 'function') await loadApps();
      if (typeof loadInsights === 'function') await loadInsights();
      if (typeof triggerTrendsRefresh === 'function') triggerTrendsRefresh();
    } catch (err) {
      alert('Delete failed: ' + err);
    }
  });
}

// Initialize the desktop menu after DOM is ready.
document.addEventListener('DOMContentLoaded', initSnapshotDeleteMenu);

/**
 * Load and render controller trends for a domain.
 * Safe against concurrent calls and reuses existing Chart instances.
 */
async function loadTrends(domain, controller) {
  // Sequence guard: ignore stale responses.
  const seq = ++trendsReqSeq;

  try {
    const q = new URLSearchParams({ domain, controller, limit: 20, baseline: 'earliestprev' });
    const res = await fetch(`/api/trends/runs?${q.toString()}`);
    const data = await res.json();

    // If a newer call superseded this one, abort.
    if (seq !== trendsReqSeq) return;

    const items    = Array.isArray(data.items) ? data.items : [];
    const baseline = data.baselineDate || (items[0]?.previousDate || 'baseline');
    const labels = items.map(i => i.currentDate || i.compareDate || 'Run');
    const fullLabels = items.map(i => `${i.previousDate || baseline} → ${i.currentDate || 'Current'}`);
    const improved = items.map(i => Number(i.improved ?? 0));
    const degraded = items.map(i => Number(i.degraded ?? 0));
    const net = improved.map((value, index) => value - degraded[index]);
    const projectedNet = projectedNextValue(net);
    const hasProjection = projectedNet !== null && net.length >= 3;
    const chartLabels = hasProjection ? labels.concat('Projected') : labels;
    const chartFullLabels = hasProjection ? fullLabels.concat('Projected direction') : fullLabels;
    const actualImproved = hasProjection ? improved.concat(null) : improved;
    const actualDegraded = hasProjection ? degraded.concat(null) : degraded;
    const actualNet = hasProjection ? net.concat(null) : net;
    const projectedNetData = hasProjection
      ? Array(Math.max(0, net.length - 1)).fill(null).concat([net[net.length - 1], projectedNet])
      : [];
    let netMin = Math.min(0, ...net, ...(hasProjection ? [projectedNet] : []));
    let netMax = Math.max(0, ...net, ...(hasProjection ? [projectedNet] : []));
    if (netMin === netMax) {
      netMin -= 1;
      netMax += 1;
    }

    const overallCanvas = document.getElementById('overallLine');
    const countsCanvas  = document.getElementById('countsStacked');
    if (!overallCanvas) return;
    if (countsCanvas) {
      try { Chart.getChart(countsCanvas)?.destroy(); } catch {}
      countsStackedChart = null;
    }

    ensureTrendBox(overallCanvas, 240);

    // Update-or-create: combined counts + net movement chart.
    const existingOverall = Chart.getChart ? Chart.getChart(overallCanvas) : null;
    if (existingOverall && existingOverall.config?.type === 'line' && existingOverall.data?.datasets?.length >= 3) {
      existingOverall.data.labels = chartLabels;
      existingOverall.data.datasets[0].label = 'Improved';
      existingOverall.data.datasets[0].data = actualImproved;
      existingOverall.data.datasets[0].borderColor = '#35c56d';
      existingOverall.data.datasets[0].backgroundColor = 'rgba(53,197,109,0.15)';
      existingOverall.data.datasets[1].label = 'Degraded';
      existingOverall.data.datasets[1].data = actualDegraded;
      existingOverall.data.datasets[1].borderColor = '#c00000';
      existingOverall.data.datasets[1].backgroundColor = 'rgba(192,0,0,0.15)';
      existingOverall.data.datasets[2].label = 'Net Movement';
      existingOverall.data.datasets[2].data = actualNet;
      existingOverall.data.datasets[2].borderColor = '#00bceb';
      existingOverall.data.datasets[2].backgroundColor = 'rgba(0,188,235,0.15)';
      if (hasProjection) {
        if (!existingOverall.data.datasets[3]) {
          existingOverall.data.datasets.push({
            label: 'Projected net',
            yAxisID: 'yNet',
            borderColor: '#f1c40f',
            backgroundColor: 'rgba(241,196,15,0.15)',
            pointBackgroundColor: '#f1c40f',
            pointRadius: 3,
            borderDash: [2, 4],
            tension: 0.15,
            fill: false
          });
        }
        existingOverall.data.datasets[3].data = projectedNetData;
      } else if (existingOverall.data.datasets[3]) {
        existingOverall.data.datasets.splice(3, 1);
      }
      if (existingOverall.options?.scales?.yNet) {
        existingOverall.options.scales.yNet.min = netMin;
        existingOverall.options.scales.yNet.max = netMax;
        existingOverall.options.scales.x.title = chartAxisTitle(`Current assessment date (baseline ${baseline})`);
        existingOverall.options.scales.x.ticks = chartTickOptions();
        existingOverall.options.scales.x.grid = { color: chartVerticalGridColor };
        existingOverall.options.scales.y.title = chartAxisTitle('Application count');
        existingOverall.options.scales.y.ticks = chartTickOptions();
        existingOverall.options.scales.y.grid = {
          color: (ctx) => ctx.tick?.value === 0 ? chartZeroGridColor : chartGridColor,
          lineWidth: (ctx) => ctx.tick?.value === 0 ? 1.4 : 1
        };
        existingOverall.options.scales.yNet.title = chartAxisTitle('Net movement (improved - degraded)');
        existingOverall.options.scales.yNet.ticks = chartTickOptions();
        existingOverall.options.scales.yNet.grid = {
          drawOnChartArea: true,
          color: (ctx) => ctx.tick?.value === 0 ? chartZeroGridColor : 'rgba(0,188,235,0.06)',
          borderDash: [3, 5],
          lineWidth: (ctx) => ctx.tick?.value === 0 ? 1.4 : 1
        };
      }
      if (existingOverall.options?.plugins?.legend?.labels) {
        existingOverall.options.plugins.legend.labels.color = chartTextColor;
      }
      existingOverall.update();
      overallLineChart = existingOverall;
    } else {
      try { existingOverall?.destroy(); } catch {}
      overallLineChart = new Chart(overallCanvas, {
        type: 'line',
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: 'Improved',
              data: actualImproved,
              borderColor: '#35c56d',
              backgroundColor: 'rgba(53,197,109,0.15)',
              pointBackgroundColor: '#35c56d',
              pointRadius: 2,
              tension: 0.25,
              fill: false
            },
            {
              label: 'Degraded',
              data: actualDegraded,
              borderColor: '#c00000',
              backgroundColor: 'rgba(192,0,0,0.15)',
              pointBackgroundColor: '#c00000',
              pointRadius: 2,
              tension: 0.25,
              fill: false
            },
            {
              label: 'Net Movement',
              data: actualNet,
              yAxisID: 'yNet',
              borderColor: '#00bceb',
              backgroundColor: 'rgba(0,188,235,0.15)',
              pointBackgroundColor: '#00bceb',
              pointRadius: 3,
              borderDash: [6, 4],
              tension: 0.25,
              fill: false
            },
            ...(hasProjection ? [{
              label: 'Projected net',
              data: projectedNetData,
              yAxisID: 'yNet',
              borderColor: '#f1c40f',
              backgroundColor: 'rgba(241,196,15,0.15)',
              pointBackgroundColor: '#f1c40f',
              pointRadius: 3,
              borderDash: [2, 4],
              tension: 0.15,
              fill: false
            }] : [])
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // fill wrapper height
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'bottom', labels: { color: chartTextColor } },
            tooltip: {
              callbacks: {
                title: (items) => chartFullLabels[items[0]?.dataIndex] || '',
                label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}`
              }
            }
          },
          scales: {
            x: {
              title: chartAxisTitle(`Current assessment date (baseline ${baseline})`),
              ticks: chartTickOptions(),
              grid: { color: chartVerticalGridColor }
            },
            y: {
              beginAtZero: true,
              title: chartAxisTitle('Application count'),
              ticks: chartTickOptions(),
              grid: {
                color: (ctx) => ctx.tick?.value === 0 ? chartZeroGridColor : chartGridColor,
                lineWidth: (ctx) => ctx.tick?.value === 0 ? 1.4 : 1
              }
            },
            yNet: {
              position: 'right',
              min: netMin,
              max: netMax,
              title: chartAxisTitle('Net movement (improved - degraded)'),
              ticks: chartTickOptions(),
              grid: {
                drawOnChartArea: true,
                color: (ctx) => ctx.tick?.value === 0 ? chartZeroGridColor : 'rgba(0,188,235,0.06)',
                borderDash: [3, 5],
                lineWidth: (ctx) => ctx.tick?.value === 0 ? 1.4 : 1
              }
            }
          }
        }
      });
    }
  } catch (err) {
    console.error('loadTrends failed:', err);
  }
}

// Expose for insights.html to call.
window.loadTrends = loadTrends;
window.getOverallTrendChart = () => overallLineChart;

// Optional cleanup on page unload.
window.addEventListener('beforeunload', () => {
  try { overallLineChart?.destroy(); } catch {}
  try { countsStackedChart?.destroy(); } catch {}
});
