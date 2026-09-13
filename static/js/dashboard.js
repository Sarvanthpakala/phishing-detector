// Populates the Dashboard page: KPI summary cards + recent scan history table.
(function () {
  const historyBody = document.getElementById('history-body');
  const kpiTotal = document.getElementById('kpi-total');
  const kpiPhishing = document.getElementById('kpi-phishing');
  const kpiSafe = document.getElementById('kpi-safe');
  const kpiAcc = document.getElementById('kpi-acc');
  if (!historyBody) return;

  async function load() {
    try {
      const [histRes, metaRes] = await Promise.all([
        fetch('/api/history?limit=25'),
        fetch('/api/metadata'),
      ]);
      const hist = await histRes.json();
      const meta = await metaRes.json();

      const items = hist.history || [];
      const phishingCount = items.filter((i) => i.prediction === 'Phishing').length;
      const safeCount = items.length - phishingCount;

      kpiTotal.textContent = hist.total ?? items.length;
      kpiPhishing.textContent = phishingCount;
      kpiSafe.textContent = safeCount;
      kpiAcc.textContent = meta.best_metrics ? (meta.best_metrics.accuracy * 100).toFixed(2) + '%' : '—';

      if (!items.length) {
        historyBody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-dim);padding:28px;">No scans yet — run a URL through the Scanner to populate this table.</td></tr>`;
        return;
      }

      historyBody.innerHTML = items
        .map(
          (i) => `<tr>
            <td>${escapeHtml(i.timestamp)}</td>
            <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(i.url)}</td>
            <td><span class="tag ${i.prediction.toLowerCase()}">${i.prediction}</span></td>
            <td>${i.confidence}%</td>
            <td><span class="tag ${i.threat_level.toLowerCase()}">${i.threat_level}</span></td>
          </tr>`
        )
        .join('');
    } catch (e) {
      historyBody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--danger);padding:28px;">Could not load dashboard data.</td></tr>`;
    }
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  load();
  setInterval(load, 15000);
})();
