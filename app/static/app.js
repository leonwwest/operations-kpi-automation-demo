const formatNumber = new Intl.NumberFormat("de-DE");
const formatCurrency = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const elements = {
  orders: document.querySelector("#orders"),
  revenue: document.querySelector("#revenue"),
  onTime: document.querySelector("#on-time"),
  processing: document.querySelector("#processing"),
  dataQuality: document.querySelector("#data-quality"),
  monthChart: document.querySelector("#month-chart"),
  teamTable: document.querySelector("#team-table"),
  refreshButton: document.querySelector("#refresh-button"),
  runStatus: document.querySelector("#run-status"),
  pipelineSteps: [...document.querySelectorAll("#pipeline-steps li")],
};

function render(data) {
  const { summary, quality, months, teams } = data;
  elements.orders.textContent = formatNumber.format(summary.orders);
  elements.revenue.textContent = formatCurrency.format(summary.revenue_eur);
  elements.onTime.textContent = `${summary.on_time_rate.toFixed(1)} %`;
  elements.processing.textContent = `${summary.avg_processing_hours.toFixed(1)} h`;
  elements.dataQuality.textContent =
    `${quality.rows_processed} Zeilen · ${quality.validation_errors} Fehler`;

  const maxOrders = Math.max(...months.map((month) => month.orders));
  elements.monthChart.innerHTML = months
    .map((month) => {
      const height = Math.max(22, Math.round((month.orders / maxOrders) * 76));
      return `
        <article class="month" style="--height: ${height}%">
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
      <span>Termintreue</span><span>Ø Stunden</span>
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

async function refreshPipeline() {
  elements.refreshButton.disabled = true;
  elements.runStatus.textContent = "Läuft";
  elements.pipelineSteps.forEach((step) => step.classList.remove("done"));

  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    if (!response.ok) throw new Error("Refresh failed");
    const payload = await response.json();
    payload.trace.forEach((trace, index) => {
      const step = elements.pipelineSteps[index];
      step.classList.add("done");
      step.querySelector("small").textContent = trace.detail;
    });
    render(payload.result);
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
