const form = document.querySelector("#scenario-form");
const scenariosElement = document.querySelector("#scenarios");
const statusMessage = document.querySelector("#status");
const result = document.querySelector("#result");
const metricsElement = document.querySelector("#metrics");
const comparison = document.querySelector("#comparison");
const comparisonResults = document.querySelector("#comparison-results");
const analysis = document.querySelector("#analysis");
const showAnalysisButton = document.querySelector("#show-analysis");
const adjustments = document.querySelector("#adjustments");
let analysisRequested = false;

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
  const value = (name) => fields.elements.namedItem(name).value;
  return { price: Number(value("price")), channel: value("channel"), month: Number(value("month")), payback_horizon_months: Number(value("payback_horizon_months")) };
}

function refreshScenarioLabels() {
  scenariosElement.querySelectorAll(".scenario-fields").forEach((fields, index) => {
    fields.querySelector(".scenario-title").textContent = `Scenario ${index + 1}`;
    const baseline = fields.querySelector("[name=baseline]");
    baseline.value = index;
    fields.classList.toggle("scenario-fields--selected", baseline.checked);
    fields.querySelector(".baseline-badge").hidden = !baseline.checked;
    const remove = fields.querySelector(".remove-scenario");
    if (remove) remove.hidden = scenariosElement.children.length === 1;
  });
  document.querySelector("#add-scenario").disabled = scenariosElement.children.length >= 3;
}

function selectedBaselineIndex() {
  return [...scenariosElement.querySelectorAll("[name=baseline]")].findIndex((input) => input.checked);
}

function addScenario(source = scenariosElement.lastElementChild) {
  if (scenariosElement.children.length >= 3) return;
  const copy = source.cloneNode(true);
  copy.querySelector(".remove-scenario")?.remove();
  copy.querySelector("[name=baseline]").checked = false;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "secondary remove-scenario";
  remove.textContent = "Remove scenario";
  remove.addEventListener("click", () => {
    const removedBaseline = copy.querySelector("[name=baseline]").checked;
    copy.remove();
    if (removedBaseline) scenariosElement.querySelector("[name=baseline]").checked = true;
    refreshScenarioLabels();
    if (!result.hidden) form.requestSubmit();
  });
  copy.append(remove);
  scenariosElement.append(copy);
  refreshScenarioLabels();
}

function showComparison(payload) {
  comparison.hidden = payload.scenarios.length < 2;
  comparisonResults.innerHTML = payload.scenarios.map((item, index) => {
    const delta = payload.differences[index];
    const isBaseline = index === payload.baseline_index;
    const signedMoney = `${delta.monthly_contribution_eur >= 0 ? "+" : ""}${money(delta.monthly_contribution_eur)}`;
    const signedLtv = `${delta.lifetime_value_eur >= 0 ? "+" : ""}${money(delta.lifetime_value_eur)}`;
    const difference = isBaseline ? "Selected baseline. Differences are zero." : `Monthly contribution vs selected baseline: ${signedMoney}. LTV vs selected baseline: ${signedLtv}.`;
    return `<article class="comparison-card${isBaseline ? " comparison-card--selected" : ""}"><h3>Scenario ${index + 1}: ${item.verdict}</h3><p>${item.trade_off}</p><p>${difference}</p></article>`;
  }).join("");
}

function showAnalysis(data) {
  if (!data) return;
  const sensitivity = data.price_sensitivity;
  const interval = sensitivity.contiguous_interval;
  const changes = sensitivity.nearest_verdict_changes.map((change) => `${money(change.from.price_eur)} ${change.from.verdict} to ${money(change.to.price_eur)} ${change.to.verdict}`).join("; ") || "No adjacent verdict change in observed support.";
  document.querySelector("#price-sensitivity").innerHTML = `<h3>Price sensitivity</h3><p>${interval.verdict} from ${money(interval.from_price_eur)} to ${money(interval.to_price_eur)} around selected price. Grid resolution: ${money(sensitivity.grid_step_eur)}; ${sensitivity.evaluation_count} of ${sensitivity.max_evaluations} allowed price evaluations.</p><p>Nearest verdict changes: ${changes}</p><p>${sensitivity.method} ${sensitivity.limit}</p>`;
  const timing = data.launch_timing;
  const selected = timing.selected_month;
  const window = timing.most_favorable_window;
  const payback = Number.isFinite(selected.payback_months) ? `${selected.payback_months.toFixed(2)} months` : "Not recoverable";
  const paybackChange = timing.payback_change_to_best_months === null ? "not available" : `${timing.payback_change_to_best_months.toFixed(2)} months`;
  document.querySelector("#launch-timing").innerHTML = `<h3>Launch month</h3><p>${selected.name} has seasonal index ${selected.seasonality_index} and ranks ${selected.rank_of_12} of 12. Monthly contribution: ${money(selected.monthly_contribution_eur)}. Payback: ${payback}.</p><p>Most favourable supplied window: ${window.months.join(", ")} (index ${window.seasonality_index}). At the same price and channel, monthly contribution changes by ${money(timing.monthly_contribution_change_to_best_eur)} and payback changes by ${paybackChange}.</p><p>${timing.limit}</p>`;
  analysis.hidden = false;
}

function showAdjustments(data) {
  if (!data) return;
  document.querySelector("#adjustments-summary").textContent = data.summary;
  document.querySelector("#adjustment-results").innerHTML = data.alternatives.map((item) => `<article class="comparison-card"><h3>${item.verdict}: ${item.change}</h3><p><strong>Improves:</strong> ${item.improvements.join("; ") || "No approved decision metric improves."}</p><p><strong>Trade-offs:</strong> ${item.trade_offs.join("; ") || "No approved decision metric worsens."}</p><p>${item.held_constant}</p></article>`).join("");
  adjustments.hidden = false;
}

function setExplanations(open) {
  document.querySelectorAll(".explanation").forEach((detail) => { detail.open = open; });
}

document.querySelector("#expand-details").addEventListener("click", () => setExplanations(true));
document.querySelector("#collapse-details").addEventListener("click", () => setExplanations(false));
document.querySelector("#add-scenario").addEventListener("click", () => addScenario());
scenariosElement.addEventListener("change", (event) => {
  if (event.target.name !== "baseline") return;
  refreshScenarioLabels();
  if (!result.hidden) form.requestSubmit();
});
document.querySelector("#compare-channels").addEventListener("click", () => {
  const first = scenariosElement.firstElementChild;
  while (scenariosElement.children.length > 1) scenariosElement.lastElementChild.remove();
  first.querySelector("[name=baseline]").checked = true;
  ["Retail/Grocery", "Gym & Office"].forEach((channel) => {
    addScenario(first);
    scenariosElement.lastElementChild.querySelector("[name=channel]").value = channel;
  });
  refreshScenarioLabels();
});
showAnalysisButton.addEventListener("click", () => {
  analysisRequested = true;
  form.requestSubmit();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = true;
  analysis.hidden = true;
  adjustments.hidden = true;
  statusMessage.textContent = "Calculating scenarios…";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const scenarios = [...scenariosElement.querySelectorAll(".scenario-fields")].map(scenarioFrom);
    const response = await fetch("/api/compare", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenarios, baseline_index: selectedBaselineIndex(), include_analysis: analysisRequested }), signal: controller.signal });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.reason || payload.detail?.message || payload.detail || "Scenario unavailable.");
    showResult(payload.scenarios[payload.baseline_index]);
    showComparison(payload);
    showAnalysis(payload.analysis);
    showAdjustments(payload.model_adjustments);
    showAnalysisButton.hidden = false;
    statusMessage.textContent = scenarios.length === 1 ? "Scenario evaluated." : "Scenarios compared.";
  } catch (error) {
    statusMessage.textContent = error.name === "AbortError" ? "Scenario request timed out. Try again." : error.message;
  } finally {
    clearTimeout(timeout);
  }
});

refreshScenarioLabels();
