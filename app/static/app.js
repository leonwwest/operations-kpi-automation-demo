const formatNumber = new Intl.NumberFormat("de-DE");
const formatCurrency = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});
const ON_TIME_TARGET = 95;

const elements = {
  orders: document.querySelector("#orders"),
  revenue: document.querySelector("#revenue"),
  onTime: document.querySelector("#on-time"),
  onTimeBadge: document.querySelector("#on-time-badge"),
  processing: document.querySelector("#processing"),
  dataQuality: document.querySelector("#data-quality"),
  monthChart: document.querySelector("#month-chart"),
  teamTable: document.querySelector("#team-table"),
  refreshButton: document.querySelector("#refresh-button"),
  runStatus: document.querySelector("#run-status"),
  runMeta: document.querySelector("#run-meta"),
  pipelineSteps: [...document.querySelectorAll("#pipeline-steps li")],
};

function formatSignedPoints(value) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1).replace(".", ",")} PP`;
}

function renderOnTimeBadge(summary, months) {
  const met = summary.on_time_rate >= ON_TIME_TARGET;
  let text = met ? "Ziel erreicht" : "Unter Ziel";
  if (months.length >= 2) {
    const [previous, current] = months.slice(-2);
    const delta = current.on_time_rate - previous.on_time_rate;
    const arrow = Math.abs(delta) < 0.05 ? "→" : delta > 0 ? "▲" : "▼";
    text += ` · ${arrow} ${formatSignedPoints(delta)}`;
  }
  elements.onTimeBadge.textContent = text;
  elements.onTimeBadge.classList.toggle("badge-ok", met);
  elements.onTimeBadge.classList.toggle("badge-bad", !met);
}

function render(data) {
  const { summary, quality, months, teams } = data;
  elements.orders.textContent = formatNumber.format(summary.orders);
  elements.revenue.textContent = formatCurrency.format(summary.revenue_eur);
  elements.onTime.textContent = `${summary.on_time_rate.toFixed(1)} %`;
  elements.processing.textContent = `${summary.avg_processing_hours.toFixed(1)} h`;
  renderOnTimeBadge(summary, months);
  elements.dataQuality.textContent =
    `${quality.rows_processed} Zeilen · ${quality.validation_errors} Fehler`;

  const maxOrders = Math.max(...months.map((month) => month.orders));
  elements.monthChart.innerHTML = months
    .map((month) => {
      const height = Math.max(22, Math.round((month.orders / maxOrders) * 76));
      return `
        <article class="month" style="--height: ${height}%"
          title="${month.month}: ${formatNumber.format(month.orders)} Aufträge, ${formatCurrency.format(month.revenue_eur)}">
          <span>${month.month}</span>
          <strong>${formatNumber.format(month.orders)}</strong>
          <small>${formatCurrency.format(month.revenue_eur)}</small>
        </article>
      `;
    })
    .join("");

  elements.teamTable.innerHTML = `
    <div class="team-row header" role="row">
      <span>Team</span><span>Aufträge</span><span>Umsatz</span>
      <span>Termintreue</span><span>Ø Stunden</span><span>Störungen</span>
    </div>
    ${teams
      .map(
        (team) => `
          <div class="team-row" role="row">
            <strong>${team.team}</strong>
            <span>${formatNumber.format(team.orders)}</span>
            <span>${formatCurrency.format(team.revenue_eur)}</span>
            <span>${team.on_time_rate.toFixed(1)} %</span>
            <span>${team.avg_processing_hours.toFixed(1)} h</span>
            <span>${formatNumber.format(team.incidents)}</span>
          </div>
        `,
      )
      .join("")}
  `;
}

async function loadKpis() {
  const response = await fetch("/api/kpis");
  if (!response.ok) throw new Error("KPI data could not be loaded");
  render(await response.json());
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function refreshPipeline() {
  elements.refreshButton.disabled = true;
  elements.runStatus.textContent = "Läuft";
  elements.runMeta.hidden = true;
  elements.pipelineSteps.forEach((step) => step.classList.remove("done"));

  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    if (!response.ok) throw new Error("Refresh failed");
    const payload = await response.json();
    for (const [index, trace] of payload.trace.entries()) {
      await wait(400);
      const step = elements.pipelineSteps[index];
      step.classList.add("done");
      step.querySelector("small").textContent = trace.detail;
    }
    render(payload.result);
    const finishedAt = new Date(payload.finished_at).toLocaleString("de-DE");
    elements.runMeta.textContent = `${payload.run_id} · ${finishedAt}`;
    elements.runMeta.hidden = false;
    elements.runStatus.textContent = "Abgeschlossen";
  } catch (error) {
    elements.runStatus.textContent = "Fehler";
  } finally {
    elements.refreshButton.disabled = false;
  }
}

elements.refreshButton.addEventListener("click", refreshPipeline);
loadKpis().catch(() => {
  elements.dataQuality.textContent = "API nicht erreichbar";
  elements.runStatus.textContent = "Fehler";
});
