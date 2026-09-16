const form = document.querySelector("#scenario-form");
const scenariosElement = document.querySelector("#scenarios");
const statusMessage = document.querySelector("#status");
const result = document.querySelector("#result");
const metricsElement = document.querySelector("#metrics");
const comparison = document.querySelector("#comparison");
const comparisonResults = document.querySelector("#comparison-results");

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
    return `<details class="metric metric--${metric.state} explanation"><summary><span class="metric-name">${label}</span><strong>${metricValue(metric)}</strong><span class="metric-state">${metric.state}</span><span class="metric-comparison">${metric.comparison}</span></summary><p>${metric.explanation}</p><dl class="methodology"><div><dt>Formula</dt><dd>${metric.formula}</dd></div><div><dt>Source</dt><dd>${metric.source}</dd></div><div><dt>Assumptions</dt><dd>${metric.assumptions}</dd></div><div><dt>Limits</dt><dd>${metric.limits}</dd></div></dl></details>`;
  }).join("");
}

function showResult(data) {
  document.querySelector("#verdict").textContent = `${data.verdict} recommendation`;
  document.querySelector("#driver").textContent = `Decision driver: ${data.decided_by}`;
  document.querySelector("#trade-off").textContent = data.trade_off;
  document.querySelector("#positioning-summary").textContent = `${data.competitive_positioning.label}. ${data.competitive_positioning.summary}`;
  document.querySelector("#competitors").innerHTML = data.competitive_positioning.competitors.map((item) => `<li>${item.name}: EUR ${item.price_eur.toFixed(2)} (${item.positioning})</li>`).join("");
  for (const key of ["cmo", "cfo"]) {
    document.querySelector(`#${key}-title`).textContent = data.perspectives[key].title;
    document.querySelector(`#${key}-points`).innerHTML = data.perspectives[key].points.map((point) => `<li>${point}</li>`).join("");
  }
  document.querySelector("#reasons").innerHTML = data.reasons.map((reason) => `<li>${reason}</li>`).join("");
  document.querySelector("#assumptions").textContent = "Open a metric to see its business meaning, formula, source, assumptions, and limits.";
  document.querySelector("#data-quality").textContent = JSON.stringify(data.data_quality, null, 2);
  showMetrics(data.metric_details);
  result.hidden = false;
}

function scenarioFrom(fields) {
  const data = new FormData(fields);
  return { price: Number(data.get("price")), channel: data.get("channel"), month: Number(data.get("month")), payback_horizon_months: Number(data.get("payback_horizon_months")) };
}

function refreshScenarioLabels() {
  scenariosElement.querySelectorAll(".scenario-fields").forEach((fields, index) => {
    fields.querySelector("legend").textContent = `Scenario ${index + 1}`;
    const remove = fields.querySelector(".remove-scenario");
    if (remove) remove.hidden = scenariosElement.children.length === 1;
  });
  document.querySelector("#add-scenario").disabled = scenariosElement.children.length >= 3;
}

function addScenario(source = scenariosElement.lastElementChild) {
  if (scenariosElement.children.length >= 3) return;
  const copy = source.cloneNode(true);
  copy.querySelector(".remove-scenario")?.remove();
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "secondary remove-scenario";
  remove.textContent = "Remove scenario";
  remove.addEventListener("click", () => { copy.remove(); refreshScenarioLabels(); });
  copy.append(remove);
  scenariosElement.append(copy);
  refreshScenarioLabels();
}

function showComparison(payload) {
  comparison.hidden = payload.scenarios.length < 2;
  comparisonResults.innerHTML = payload.scenarios.map((item, index) => {
    const delta = payload.differences[index];
    const signedMoney = `${delta.monthly_contribution_eur >= 0 ? "+" : ""}${money(delta.monthly_contribution_eur)}`;
    const signedLtv = `${delta.lifetime_value_eur >= 0 ? "+" : ""}${money(delta.lifetime_value_eur)}`;
    return `<article><h3>Scenario ${index + 1}: ${item.verdict}</h3><p>${item.trade_off}</p><p>Monthly contribution vs scenario 1: ${signedMoney}. LTV vs scenario 1: ${signedLtv}.</p></article>`;
  }).join("");
}

function setExplanations(open) {
  document.querySelectorAll(".explanation").forEach((detail) => { detail.open = open; });
}

document.querySelector("#expand-details").addEventListener("click", () => setExplanations(true));
document.querySelector("#collapse-details").addEventListener("click", () => setExplanations(false));
document.querySelector("#add-scenario").addEventListener("click", () => addScenario());
document.querySelector("#compare-channels").addEventListener("click", () => {
  const first = scenariosElement.firstElementChild;
  while (scenariosElement.children.length > 1) scenariosElement.lastElementChild.remove();
  ["Retail/Grocery", "Gym & Office"].forEach((channel) => {
    addScenario(first);
    scenariosElement.lastElementChild.querySelector("[name=channel]").value = channel;
  });
  refreshScenarioLabels();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = true;
  statusMessage.textContent = "Calculating scenarios…";
  const scenarios = [...scenariosElement.querySelectorAll(".scenario-fields")].map(scenarioFrom);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch("/api/compare", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenarios }), signal: controller.signal });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.reason || payload.detail?.message || payload.detail || "Scenario unavailable.");
    showResult(payload.scenarios[0]);
    showComparison(payload);
    statusMessage.textContent = scenarios.length === 1 ? "Scenario evaluated." : "Scenarios compared.";
  } catch (error) {
    statusMessage.textContent = error.name === "AbortError" ? "Scenario request timed out. Try again." : error.message;
  } finally {
    clearTimeout(timeout);
  }
});

refreshScenarioLabels();
