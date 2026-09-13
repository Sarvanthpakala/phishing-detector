// Drives the URL Scanner page: submits to /api/predict, animates the
// threat gauge, and renders the explainable-AI reason list + feature table.

(function () {
  const form = document.getElementById('scan-form');
  const input = document.getElementById('url-input');
  const resultPanel = document.getElementById('result-panel');
  const loader = document.getElementById('scan-loader');
  const chips = document.querySelectorAll('.chip');

  if (!form) return;

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      input.value = chip.getAttribute('data-url');
      form.dispatchEvent(new Event('submit'));
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = input.value.trim();
    if (!url) return;

    loader.style.display = 'flex';
    resultPanel.style.opacity = '0.35';

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      loader.style.display = 'none';
      resultPanel.style.opacity = '1';

      if (!res.ok) {
        renderError(data.error || 'Something went wrong.');
        return;
      }
      renderResult(data);
    } catch (err) {
      loader.style.display = 'none';
      resultPanel.style.opacity = '1';
      renderError('Could not reach the prediction service.');
    }
  });

  function renderError(msg) {
    resultPanel.innerHTML = `<div class="reason-list"><li class="risk" style="list-style:none;display:flex;padding:12px;border-radius:8px;">⚠️ ${escapeHtml(msg)}</li></div>`;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderResult(data) {
    const isPhishing = data.label === 'phishing';
    const pct = isPhishing ? data.probability.phishing : data.probability.safe;
    const gaugeColor = isPhishing ? 'var(--danger)' : 'var(--teal)';

    const reasonsHtml = data.reasons
      .map(
        (r) => `<li class="${r.type}">${r.type === 'risk' ? '⚠️' : '✅'} ${escapeHtml(r.text)}</li>`
      )
      .join('');

    const featureRows = Object.entries(data.features)
      .map(([k, v]) => `<tr><td>${escapeHtml(k.replace(/_/g, ' '))}</td><td>${v}</td></tr>`)
      .join('');

    resultPanel.innerHTML = `
      <div class="flex-between" style="margin-bottom:20px;">
        <span class="result-badge ${data.label}">${isPhishing ? '🚨' : '🛡️'} ${data.prediction}</span>
        <span class="badge-soft">Model: ${escapeHtml(data.model_used)}</span>
      </div>
      <div class="console-body" style="margin-top:0;">
        <div class="gauge-wrap">
          <div class="gauge" id="result-gauge" style="--pct:0; background:conic-gradient(${gaugeColor} 0%, var(--surface-2) 0);">
            <div class="gauge-value">
              <div class="pct">${data.confidence}%</div>
              <div class="tag">confidence</div>
            </div>
          </div>
          <span class="tag ${data.threat_level.toLowerCase()}">${data.threat_level} threat</span>
        </div>
        <div class="console-readout">
          <div class="readout-row"><span class="k">Safe probability</span><span class="v">${data.probability.safe}%</span></div>
          <div class="readout-row"><span class="k">Phishing probability</span><span class="v danger">${data.probability.phishing}%</span></div>
          <div class="readout-row"><span class="k">Scanned URL</span><span class="v" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(data.url)}</span></div>
        </div>
      </div>
      <h4 style="margin-top:26px;">Why this verdict</h4>
      <ul class="reason-list">${reasonsHtml}</ul>
      <h4 style="margin-top:26px;">Extracted features</h4>
      <div style="max-height:260px;overflow-y:auto;">
        <table class="feature-table"><thead><tr><th>Feature</th><th>Value</th></tr></thead><tbody>${featureRows}</tbody></table>
      </div>
    `;

    requestAnimationFrame(() => {
      const gaugeEl = document.getElementById('result-gauge');
      if (gaugeEl) {
        gaugeEl.style.transition = 'background 1.1s cubic-bezier(.16,.84,.44,1)';
        gaugeEl.style.background = `conic-gradient(${gaugeColor} ${pct}%, var(--surface-2) 0)`;
      }
    });
  }
})();
