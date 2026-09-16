const form = document.querySelector("#scenario-form");
const statusMessage = document.querySelector("#status");
const result = document.querySelector("#result");
const metricsElement = document.querySelector("#metrics");

const money = (value) => new Intl.NumberFormat("en-IE", {
  style: "currency", currency: "EUR", minimumFractionDigits: 2,
}).format(value);

function metricValue(metric) {
  if (metric.unit === "percentage") return `${(metric.value * 100).toFixed(1)}%`;
  if (metric.unit === "currency") return money(metric.value);
  if (metric.unit === "ratio") return `${metric.value.toFixed(2)}x`;
  return `${metric.value.toFixed(2)} months`;
}

function showMetrics(metricDetails) {
  metricsElement.innerHTML = metricDetails.map((metric) => {
    const label = metric.acronym ? `${metric.name} (${metric.acronym})` : metric.name;
    return `<details class="metric metric--${metric.state} explanation">
      <summary>
        <span class="metric-name">${label}</span>
        <strong>${metricValue(metric)}</strong>
        <span class="metric-state">${metric.state}</span>
        <span class="metric-comparison">${metric.comparison}</span>
      </summary>
      <p>${metric.explanation}</p>
      <dl class="methodology">
        <div><dt>Formula</dt><dd>${metric.formula}</dd></div>
        <div><dt>Source</dt><dd>${metric.source}</dd></div>
        <div><dt>Assumptions</dt><dd>${metric.assumptions}</dd></div>
        <div><dt>Limits</dt><dd>${metric.limits}</dd></div>
      </dl>
    </details>`;
  }).join("");
}

function showResult(data) {
  const metrics = data.metrics;
  document.querySelector("#verdict").textContent = `${data.verdict} recommendation`;
  document.querySelector("#driver").textContent = `Decision driver: ${data.decided_by}`;
  document.querySelector("#trade-off").textContent = data.trade_off;
  document.querySelector("#reasons").innerHTML = data.reasons.map((reason) => `<li>${reason}</li>`).join("");
  document.querySelector("#assumptions").textContent =
    "Open a metric to see its business meaning, formula, source, assumptions, and limits.";
  document.querySelector("#data-quality").textContent = JSON.stringify(data.data_quality, null, 2);
  showMetrics(data.metric_details);
  result.hidden = false;
}

function setExplanations(open) {
  document.querySelectorAll(".explanation").forEach((detail) => { detail.open = open; });
}

document.querySelector("#expand-details").addEventListener("click", () => setExplanations(true));
document.querySelector("#collapse-details").addEventListener("click", () => setExplanations(false));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = true;
  statusMessage.textContent = "Calculating scenario…";
  const formData = new FormData(form);
  const request = {
    price: Number(formData.get("price")),
    channel: formData.get("channel"),
    month: Number(formData.get("month")),
    payback_horizon_months: Number(formData.get("payback_horizon_months")),
  };
  try {
    const response = await fetch("/api/scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.reason || payload.detail?.message || "Scenario unavailable.");
    showResult(payload);
    statusMessage.textContent = "Scenario evaluated.";
  } catch (error) {
    statusMessage.textContent = error.message;
  }
});

form.requestSubmit();
