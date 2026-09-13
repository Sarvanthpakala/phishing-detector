// Populates the Analytics page: full model comparison table + confusion matrix
// for the selected best model, sourced from models/metadata.json via the API.
(function () {
  const tableBody = document.getElementById('metrics-body');
  const cmWrap = document.getElementById('confusion-matrix');
  const bestBadge = document.getElementById('best-model-badge');
  if (!tableBody) return;

  async function load() {
    try {
      const res = await fetch('/api/metadata');
      const meta = await res.json();
      if (!res.ok) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">${meta.error || 'Model not trained yet.'}</td></tr>`;
        return;
      }

      bestBadge.textContent = `Best model: ${meta.best_model}`;

      const rows = Object.entries(meta.metrics_by_model || {})
        .sort((a, b) => b[1].f1 - a[1].f1)
        .map(([name, m]) => {
          const isBest = name === meta.best_model;
          return `<tr style="${isBest ? 'background:var(--teal-dim);' : ''}">
            <td>${name}${isBest ? ' <span class="badge-soft">best</span>' : ''}</td>
            <td>${(m.accuracy * 100).toFixed(2)}%</td>
            <td>${(m.precision * 100).toFixed(2)}%</td>
            <td>${(m.recall * 100).toFixed(2)}%</td>
            <td>${(m.f1 * 100).toFixed(2)}%</td>
            <td>${(m.roc_auc * 100).toFixed(2)}%</td>
          </tr>`;
        })
        .join('');
      tableBody.innerHTML = rows;

      if (meta.confusion_matrix && cmWrap) {
        const [[tn, fp], [fn, tp]] = meta.confusion_matrix;
        cmWrap.innerHTML = `
          <div class="cm-grid">
            <div class="cm-cell safe"><div class="cm-val">${tn}</div><div class="cm-label">True Safe</div></div>
            <div class="cm-cell warn"><div class="cm-val">${fp}</div><div class="cm-label">False Phishing</div></div>
            <div class="cm-cell warn"><div class="cm-val">${fn}</div><div class="cm-label">False Safe</div></div>
            <div class="cm-cell danger"><div class="cm-val">${tp}</div><div class="cm-label">True Phishing</div></div>
          </div>`;
      }
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--danger);padding:24px;">Could not load model metadata.</td></tr>`;
    }
  }

  load();
})();
