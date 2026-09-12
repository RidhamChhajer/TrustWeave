// Experiment inputs are never relabelled as live observations.
const experimentButton = document.getElementById('experiment-run');
experimentButton.onclick = async () => {
  experimentButton.disabled = true;
  const status = document.getElementById('experiment-status');
  status.textContent = 'Running real TLS with simulated metadata and automatic MATCH responses…';
  try {
    const response = await fetch('/api/experiment/sudden', {
      method: 'POST', headers: {'X-Requested-With': 'adaptive-trust'}
    });
    if (!response.ok) throw new Error('Experiment failed; retry or inspect local diagnostics.');
    const result = await response.json();
    const anomaly = result.rows.find(row => row.anomaly);
    status.textContent = `SIMULATED metadata + OOB · Real TLS · Trust ${anomaly.before.toFixed(2)} → ${anomaly.score.toFixed(2)} · ΔS ${anomaly.delta.toFixed(2)} · ${anomaly.action} above threshold 50 · Fresh TLS session after MATCH.`;
    const body = document.getElementById('experiment-rows');
    body.replaceChildren();
    for (const row of result.rows) {
      const tr = document.createElement('tr');
      if (row.anomaly) tr.style.color = '#ff8495';
      for (const value of [row.tick, row.kind, row.score.toFixed(2), row.delta.toFixed(2), row.action, row.after.toFixed(2)]) {
        const td = document.createElement('td'); td.textContent = value; td.style.padding = '8px'; tr.append(td);
      }
      body.append(tr);
    }
  } catch (error) { status.textContent = error.message; }
  finally { experimentButton.disabled = false; }
};
