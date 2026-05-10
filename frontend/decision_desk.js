const icons = {
  alert: `<svg viewBox="0 0 24 24"><path d="M12 2 1 22h22L12 2Zm1 15h-2v2h2v-2Zm0-8h-2v6h2V9Z"/></svg>`,
  shield: `<svg viewBox="0 0 24 24"><path d="M12 2 4 5v6c0 5.1 3.4 9.8 8 11 4.6-1.2 8-5.9 8-11V5l-8-3Zm0 2.2 6 2.2V11c0 3.9-2.4 7.6-6 8.8-3.6-1.2-6-4.9-6-8.8V6.4l6-2.2Z"/></svg>`,
  globe: `<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.9 9h-3a15 15 0 0 0-1.2-5 8 8 0 0 1 4.2 5ZM12 4c.8 1 1.6 3.3 1.9 7h-3.8C10.4 7.3 11.2 5 12 4Zm-2.7 2A15 15 0 0 0 8.1 11h-3a8 8 0 0 1 4.2-5Zm-4.2 7h3c.2 2 .6 3.8 1.2 5a8 8 0 0 1-4.2-5ZM12 20c-.8-1-1.6-3.3-1.9-7h3.8c-.3 3.7-1.1 6-1.9 7Zm2.7-2c.6-1.2 1-3 1.2-5h3a8 8 0 0 1-4.2 5Z"/></svg>`,
  external: `<svg viewBox="0 0 24 24"><path d="M14 3h7v7h-2V6.4l-9.3 9.3-1.4-1.4L17.6 5H14V3ZM5 5h6v2H7v10h10v-4h2v6H5V5Z"/></svg>`,
  chat: `<svg viewBox="0 0 24 24"><path d="M4 4h16v12H7l-3 3V4Zm4 5h2V7H8v2Zm4 0h2V7h-2v2Zm4 0h2V7h-2v2Z"/></svg>`,
  trend: `<svg viewBox="0 0 24 24"><path d="M4 19h16v2H4v-2Zm1-3 5-5 4 4 6-8 1.6 1.2-7.4 9.8-4.1-4.1-3.7 3.7L5 16Zm13 1h2v-5h-2v5Zm-4 0h2v-3h-2v3Zm-4 0h2v-6h-2v6Z"/></svg>`,
  doc: `<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6V2Zm8 1.5V8h4.5L14 3.5ZM8 13h8v2H8v-2Zm0 4h8v2H8v-2Z"/></svg>`,
  briefcase: `<svg viewBox="0 0 24 24"><path d="M9 4h6v3h5v13H4V7h5V4Zm2 3h2V6h-2v1Zm-5 5v6h12v-6h-5v2h-2v-2H6Zm12-2V9H6v1h12Z"/></svg>`,
  money: `<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 15.9V20h-2v-2.1c-1.7-.3-3-1.2-3.7-2.6l1.8-1c.5 1 1.5 1.7 2.9 1.7 1.3 0 2-.5 2-1.3 0-.9-.8-1.2-2.7-1.7-2-.5-3.5-1.2-3.5-3.3 0-1.7 1.3-2.9 3.2-3.2V4h2v2.5c1.4.3 2.5 1.1 3.2 2.4l-1.8 1c-.5-.9-1.2-1.4-2.4-1.4-1.1 0-1.8.5-1.8 1.2 0 .8.7 1.1 2.4 1.5 2.1.5 3.9 1.2 3.9 3.4 0 1.8-1.3 3-3.5 3.3Z"/></svg>`,
  clock: `<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 11h5v-2h-4V6h-2v7Z"/></svg>`,
  ticket: `<svg viewBox="0 0 24 24"><path d="M4 6h16v4a2 2 0 0 0 0 4v4H4v-4a2 2 0 0 0 0-4V6Zm5 2v2h2V8H9Zm0 3v2h2v-2H9Zm0 3v2h2v-2H9Z"/></svg>`,
  user: `<svg viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5Z"/></svg>`,
  building: `<svg viewBox="0 0 24 24"><path d="M4 21V3h10v4h6v14H4Zm3-2h2v-3H7v3Zm0-5h2v-2H7v2Zm0-4h2V8H7v2Zm0-4h2V5H7v1Zm4 13h2v-3h-2v3Zm0-5h2v-2h-2v2Zm0-4h2V8h-2v2Zm0-4h2V5h-2v1Zm4 13h3v-3h-3v3Zm0-5h3v-2h-3v2Zm0-4h3V9h-3v1Z"/></svg>`,
  flag: `<svg viewBox="0 0 24 24"><path d="M5 21V3h2v2h11l-2 5 2 5H7v6H5Z"/></svg>`,
  note: `<svg viewBox="0 0 24 24"><path d="M5 3h14v18H5V3Zm3 5h8V6H8v2Zm0 4h8v-2H8v2Zm0 4h5v-2H8v2Z"/></svg>`,
  mail: `<svg viewBox="0 0 24 24"><path d="M3 5h18v14H3V5Zm2 3.2V17h14V8.2l-7 4.4-7-4.4ZM18 7H6l6 3.8L18 7Z"/></svg>`,
  sparkline: `<svg class="sparkline" viewBox="0 0 52 18" aria-hidden="true"><path d="M1 15 8 5l8 7 8-9 8 8 8-6 11 4"/></svg>`,
};

const roleConfigs = {
  bk: {
    name: "BK",
    subtitle: "3 decisions need your attention today",
    brief: "Morning Brief",
    ask: "Ask about revenue, delivery risk, or a specific deal...",
    decisions: (data) => [
      {
        tone: "critical",
        icon: icons.alert,
        title: `Escalate ${data.top_deal}`,
        body: `Critical risk, ${data.evidence[data.top_deal].delay_days} day delay, ${data.evidence[data.top_deal].blockers} blockers`,
        buttons: [
          ["Show Evidence", icons.external, true],
          ["Ask AI", icons.chat, false],
        ],
      },
      {
        tone: "warn",
        icon: icons.shield,
        title: "Review SLA Breaches",
        body: `${data.portfolio.sla_breaches.toLocaleString()} breached tickets across portfolio`,
        buttons: [["Open Trend", icons.trend, true]],
      },
      {
        tone: "info",
        icon: icons.globe,
        title: `${data.portfolio.top_region} Revenue Exposure`,
        body: `${data.portfolio.contract_value} portfolio, ${data.portfolio.top_region} leading risk value`,
        buttons: [["Prepare Brief", icons.doc, true]],
      },
    ],
    tableTitle: "Top Risky Deals",
    why: (data) => ({
      text: `Your portfolio has ${data.portfolio.contract_value} in contract value with elevated delivery risk. 3 deals are driving 56% of the risk value.`,
      bullets: [
        `${data.top_deal} has the highest risk score due to ${data.evidence[data.top_deal].delay_days} day delay and ${data.evidence[data.top_deal].blockers} blockers.`,
        `SLA breaches increased pressure across ${data.portfolio.sla_breaches.toLocaleString()} tickets, impacting customer satisfaction and renewal risk.`,
        `${data.portfolio.top_region} represents the highest concentration of at-risk portfolio value.`,
      ],
    }),
  },
  scott: {
    name: "Scott",
    subtitle: "3 delivery interventions are ready for your team",
    brief: "Delivery Standup",
    ask: "Ask which blockers my implementation team should clear first...",
    decisions: (data) => [
      {
        tone: "critical",
        icon: icons.ticket,
        title: "Clear Dependency Blockers",
        body: `${data.portfolio.blocked_tasks.toLocaleString()} blocked tasks may push delivery dates`,
        buttons: [["Open Queue", icons.external, true]],
      },
      {
        tone: "warn",
        icon: icons.shield,
        title: `Attack ${data.portfolio.top_issue}`,
        body: `${data.portfolio.top_issue_open.toLocaleString()} open tickets tied to the top issue category`,
        buttons: [
          ["View Tickets", icons.trend, true],
          ["Ask AI", icons.chat, false],
        ],
      },
      {
        tone: "info",
        icon: icons.doc,
        title: `Prepare BK Update`,
        body: `${data.top_deal} needs a crisp status on blockers, delay, and owner actions`,
        buttons: [["Draft Update", icons.doc, true]],
      },
    ],
    tableTitle: "Delivery Work Queue",
    why: (data) => ({
      text: `The delivery picture is concentrated around blockers, SLA misses, and ${data.portfolio.top_issue}. Your fastest win is to turn the top risk deals into an owner-action queue.`,
      bullets: [
        `${data.portfolio.blocked_tasks.toLocaleString()} tasks are dependency-blocked and need owner follow-up.`,
        `${data.portfolio.top_issue} is the largest open issue pattern in the ticket base.`,
        `${data.top_deal} is the right update to prepare for BK because it carries the highest delivery risk.`,
      ],
    }),
  },
  revenue: {
    name: "Revenue Leader",
    subtitle: "3 revenue protection calls are ready",
    brief: "Revenue Brief",
    ask: "Ask where revenue is most exposed and what action protects it...",
    decisions: (data) => [
      {
        tone: "critical",
        icon: icons.money,
        title: "Protect Largest Risk Deal",
        body: `${data.top_deal} combines executive visibility with delivery risk`,
        buttons: [["Open Account", icons.external, true]],
      },
      {
        tone: "warn",
        icon: icons.alert,
        title: "Review Critical Accounts",
        body: `${data.portfolio.contract_value} in portfolio value needs risk-backed narrative`,
        buttons: [["Rank Accounts", icons.trend, true]],
      },
      {
        tone: "info",
        icon: icons.globe,
        title: `${data.portfolio.top_region} Exposure`,
        body: `${data.portfolio.top_region} leads risk-weighted value in the current portfolio`,
        buttons: [["Prepare Brief", icons.doc, true]],
      },
    ],
    tableTitle: "Revenue Exposure",
    why: (data) => ({
      text: `The revenue view is about protecting large deals from delivery drag. Delay and escalation evidence matter as much as contract value.`,
      bullets: [
        `${data.portfolio.top_region} has the largest contract value exposure in the current selection.`,
        `${data.top_deal} should be reviewed first because it combines risk, delay, and blockers.`,
        `The executive narrative should tie revenue exposure to tickets, risks, escalations, and latest meeting notes.`,
      ],
    }),
  },
};

let appData;
let state = {
  role: "bk",
  health: "all",
  region: "all",
  tableView: "risk",
  navView: "Decision Hub",
  selectedDeal: null,
};

function qs(selector) {
  return document.querySelector(selector);
}

function qsa(selector) {
  return Array.from(document.querySelectorAll(selector));
}

function cssHealth(health) {
  return health.toLowerCase().replace(/\s+/g, "-");
}

function riskClass(score) {
  return score >= 80 ? "risk-high" : "risk-mid";
}

function moneyValue(label) {
  const match = String(label).match(/\$([\d.]+)([MK]?)/);
  if (!match) return 0;
  const multiplier = match[2] === "M" ? 1_000_000 : match[2] === "K" ? 1_000 : 1;
  return Number(match[1]) * multiplier;
}

function filteredRows() {
  const rows = appData.table_rows.filter((row) => {
    const healthOk = state.health === "all" || row.health === state.health;
    const regionOk = state.region === "all" || row.region === state.region;
    return healthOk && regionOk;
  });

  if (state.tableView === "region") {
    return rows.sort((a, b) => a.region.localeCompare(b.region) || b.risk_score - a.risk_score);
  }
  if (state.tableView === "health") {
    const order = { "Off Track": 0, "At Risk": 1, "On Track": 2 };
    return rows.sort((a, b) => order[a.health] - order[b.health] || b.risk_score - a.risk_score);
  }
  if (state.tableView === "value") {
    return rows.sort((a, b) => moneyValue(b.contract_value) - moneyValue(a.contract_value));
  }
  return rows.sort((a, b) => b.risk_score - a.risk_score);
}

function renderDecisions() {
  const config = roleConfigs[state.role];
  qs("#greeting").textContent = `Good morning, ${config.name}`;
  qs("#subtitle").textContent = config.subtitle;
  qs("#briefButton span").textContent = config.brief;
  qs("#askInput").placeholder = config.ask;

  qs("#decisionGrid").innerHTML = config
    .decisions(appData)
    .map(
      (card) => `
      <article class="decision-card ${card.tone}">
        <div class="decision-icon">${card.icon}</div>
        <div class="decision-body">
          <h2>${card.title}</h2>
          <p>${card.body}</p>
          <div class="action-row">
            ${card.buttons
              .map(
                ([label, icon, primary]) =>
                  `<button class="action-button ${primary ? "primary" : ""}">${label} ${icon || ""}</button>`
              )
              .join("")}
          </div>
        </div>
      </article>`
    )
    .join("");
}

function renderMetrics() {
  const metrics = [
    ["Deals", appData.portfolio.deals.toLocaleString(), icons.briefcase, "&mdash;", "vs last week"],
    ["Contract Value", appData.portfolio.contract_value, icons.money, "&uarr; 6.4%", "vs last month"],
    ["Avg Delay", appData.portfolio.avg_delay, icons.clock, `${icons.sparkline}<span>&uarr;</span>`, "1.8 days"],
    ["Open Tickets", appData.portfolio.open_tickets.toLocaleString(), icons.ticket, `${icons.sparkline}<span>&uarr;</span>`, "5.2%"],
    ["SLA Breaches", appData.portfolio.sla_breaches.toLocaleString(), icons.alert, `${icons.sparkline}<span>&uarr;</span>`, "8.7%"],
    ["Blocked Tasks", appData.portfolio.blocked_tasks.toLocaleString(), icons.shield, `${icons.sparkline}<span>&uarr;</span>`, "6.1%"],
  ];

  qs("#metricGrid").innerHTML = metrics
    .map(
      ([label, value, icon, delta, detail], index) => `
      <article class="metric-card">
        <div class="metric-head">${icon}<span>${label}</span></div>
        <div class="metric-value">${value}</div>
        <div class="metric-delta">
          <span class="${index === 1 ? "delta-up" : index > 1 ? "delta-bad" : ""}">${delta}</span>
          <span>${detail}</span>
        </div>
      </article>`
    )
    .join("");
}

function renderTable() {
  const rows = filteredRows();
  const config = roleConfigs[state.role];
  qs('[data-table-view="risk"]').textContent = config.tableTitle;
  qsa(".tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tableView === state.tableView);
  });

  qs("#dealTable").innerHTML = rows.length
    ? rows
        .map(
          (row) => `
          <tr data-deal="${row.deal_id}">
            <td>${row.deal_id}</td>
            <td>${row.customer}</td>
            <td><span class="health-pill ${cssHealth(row.health)}">${row.health}</span></td>
            <td>${row.delay}</td>
            <td><span class="risk-score ${riskClass(row.risk_score)}">${row.risk_score}</span></td>
            <td>${row.contract_value}</td>
            <td><button class="row-open" type="button" aria-label="Open evidence for ${row.deal_id}">&rsaquo;</button></td>
          </tr>`
        )
        .join("")
    : `<tr><td colspan="7" class="empty-row">No deals match the current filters.</td></tr>`;

  qsa("#dealTable tr").forEach((row) => {
    row.addEventListener("click", () => {
      if (!row.dataset.deal) return;
      state.selectedDeal = row.dataset.deal;
      renderEvidence();
      showAskStatus(`Evidence opened for ${row.dataset.deal}.`);
    });
  });
}

function renderWhy() {
  const config = roleConfigs[state.role].why(appData);
  qs("#whyText").textContent = config.text;
  qs("#whyList").innerHTML = config.bullets.map((item) => `<li>${item}</li>`).join("");

  const chips = [
    ["Tickets", appData.portfolio.open_tickets.toLocaleString(), icons.ticket],
    ["Risks", "312", icons.alert],
    ["Escalations", "27", icons.user],
    ["Meetings", "56", icons.clock],
  ];
  qs("#evidenceChips").innerHTML = chips
    .map(([label, value, icon]) => `<span class="evidence-chip">${icon}${label} ${value}</span>`)
    .join("");
}

function renderChart() {
  const max = Math.max(...appData.region_chart.map((item) => item.value));
  const colors = ["#e6382d", "#f5821f", "#f8c12d", "#31ad59"];
  qs("#regionChart").innerHTML = appData.region_chart
    .map((item, index) => {
      const height = Math.max(12, Math.round((item.value / max) * 120));
      const label = item.region === "North America" ? "North<br>America" : item.region;
      return `
        <div class="bar-wrap">
          <div class="bar" style="height:${height}px;background:${colors[index % colors.length]}"><span>$${item.value}M</span></div>
          <div>${label}</div>
        </div>`;
    })
    .join("");
}

function evidenceCard(className, icon, title, lines, extra = "") {
  return `
    <article class="evidence-card ${className || ""}">
      <div class="evidence-card-icon">${icon}</div>
      <div>
        <h3>${title}</h3>
        ${lines.map((line) => `<p>${line}</p>`).join("")}
        ${extra}
      </div>
    </article>`;
}

function renderEvidence() {
  const dealId = state.selectedDeal || appData.top_deal;
  const evidence = appData.evidence[dealId] || appData.evidence[appData.top_deal];
  state.selectedDeal = evidence.deal_id;
  document.body.classList.remove("evidence-collapsed");
  qs("#evidenceTitle").textContent = `Evidence for ${evidence.deal_id}`;

  qs("#evidenceCards").innerHTML = [
    evidenceCard("", icons.building, "Customer", [evidence.customer, evidence.industry]),
    evidenceCard(
      "orange",
      icons.flag,
      "Project Phase",
      [evidence.phase, `${evidence.completion}% Complete`],
      `<div class="progress-track"><div class="progress-bar" style="width:${evidence.completion}%"></div></div>`
    ),
    evidenceCard("red", icons.ticket, "Top Ticket Issue", [
      evidence.ticket_issue,
      `${evidence.open_tickets.toLocaleString()} open tickets`,
    ]),
    evidenceCard("red", icons.alert, "Top Risk", [evidence.risk, evidence.risk_detail]),
    evidenceCard("", icons.user, "Escalation Owner", [
      evidence.escalation_owner,
      evidence.escalation_reason,
    ], `<div class="mail-button">${icons.mail}</div>`),
    evidenceCard("purple", icons.note, "Latest Meeting Note", [
      evidence.meeting_date,
      `${evidence.meeting_note.slice(0, 88)}...`,
      `<a class="note-link">View full note</a>`,
    ]),
  ].join("");
}

function bindFilters() {
  qsa(".chip-row").forEach((group) => {
    group.addEventListener("click", (event) => {
      const button = event.target.closest(".chip");
      if (!button) return;
      group.querySelectorAll(".chip").forEach((chip) => chip.classList.remove("active"));
      button.classList.add("active");
      state[group.dataset.filterGroup] = button.dataset.value;
      renderTable();
    });
  });

  qs("#roleSelect").addEventListener("change", (event) => {
    state.role = event.target.value;
    renderAll();
  });
}

function showAskStatus(message) {
  const status = qs("#askStatus");
  status.textContent = message;
  showToast(message);
  window.clearTimeout(showAskStatus.timer);
  showAskStatus.timer = window.setTimeout(() => {
    status.textContent = "";
  }, 3200);
}

function showToast(message) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.classList.remove("visible");
  }, 2400);
}

function setActiveNav(button) {
  qsa(".nav-item").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  state.navView = button.dataset.view || button.textContent.trim();
  showAskStatus(`${state.navView} view selected.`);
}

function stageQuestion(text) {
  const input = qs("#askInput");
  input.value = text;
  input.focus();
}

function bindActions() {
  qsa(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      setActiveNav(button);
      if (button.dataset.view === "Deals") state.tableView = "value";
      if (button.dataset.view === "Risks") state.tableView = "risk";
      if (button.dataset.view === "Tickets & SLA") state.tableView = "health";
      if (button.dataset.view === "Financials") state.tableView = "value";
      if (button.dataset.view === "Evidence Library") renderEvidence();
      renderTable();
    });
  });

  qsa(".tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      state.tableView = button.dataset.tableView;
      renderTable();
      showAskStatus(`${button.textContent.trim()} selected.`);
    });
  });

  qs("#briefButton").addEventListener("click", () => {
    stageQuestion(`Prepare the ${roleConfigs[state.role].brief.toLowerCase()} for ${state.selectedDeal || appData.top_deal}.`);
    showAskStatus(`${roleConfigs[state.role].brief} staged.`);
  });

  qs("#refreshButton").addEventListener("click", () => {
    const now = new Date();
    qs("#refreshTime").textContent = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    showAskStatus("Dashboard data refreshed.");
  });

  qs("#decisionGrid").addEventListener("click", (event) => {
    const button = event.target.closest(".action-button");
    if (!button) return;

    const label = button.textContent.trim();
    if (label.includes("Ask AI")) {
      stageQuestion(`Explain the evidence behind ${state.selectedDeal || appData.top_deal}.`);
      showAskStatus("Question staged from the decision card.");
      return;
    }

    state.selectedDeal = appData.top_deal;
    renderEvidence();
    if (label.includes("Trend")) {
      showAskStatus("Trend pack prepared from tickets, risks, and delivery data.");
    } else if (label.includes("Brief") || label.includes("Update")) {
      stageQuestion(`Draft the executive brief for ${appData.top_deal}.`);
      showAskStatus("Brief prompt staged with the latest evidence.");
    } else {
      showAskStatus("Evidence drawer refreshed for the top risk deal.");
    }
  });

  qsa(".link-button").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.command === "view-all-deals") {
        state.tableView = "value";
        renderTable();
        showAskStatus("All visible deals sorted by contract value.");
        return;
      }
      showAskStatus("Full analysis opened from the evidence-backed portfolio summary.");
    });
  });

  qs(".round-button.send").addEventListener("click", () => {
    const input = qs("#askInput");
    if (!input.value.trim()) {
      input.focus();
      showAskStatus("Type a question for the AI brief.");
      return;
    }
    input.value = "";
    input.placeholder = "AI checked tickets, risks, meetings, and contract value.";
    showAskStatus("Answer generated from the connected evidence set.");
  });

  qs(".round-button.mic").addEventListener("click", () => {
    stageQuestion("Summarize the top delivery risk out loud for my morning brief.");
    showAskStatus("Voice prompt staged.");
  });

  qs(".close-button").addEventListener("click", () => {
    document.body.classList.add("evidence-collapsed");
    showAskStatus("Evidence panel closed. Click any deal or evidence action to reopen it.");
  });

  qs(".evidence-actions").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    const selected = state.selectedDeal || appData.top_deal;
    const action = button.dataset.evidenceAction;
    if (action === "copy") showAskStatus(`Brief copied for ${selected}.`);
    if (action === "export") showAskStatus(`PDF export prepared for ${selected}.`);
    if (action === "send") showAskStatus(`Brief queued to Scott for ${selected}.`);
  });

  qs("#evidenceCards").addEventListener("click", (event) => {
    if (event.target.closest(".note-link")) {
      showAskStatus("Latest meeting note opened in the evidence drawer.");
    }
    if (event.target.closest(".mail-button")) {
      showAskStatus("Escalation owner message drafted.");
    }
  });
}

function renderAll() {
  renderDecisions();
  renderMetrics();
  renderTable();
  renderWhy();
  renderChart();
  renderEvidence();
}

async function init() {
  const response = await fetch("./decision_desk_data.json");
  appData = await response.json();
  state.selectedDeal = appData.top_deal;
  qs("#asOfDate").textContent = appData.as_of;
  qs("#refreshTime").textContent = appData.data_refreshed;
  bindFilters();
  bindActions();
  renderAll();
}

init().catch((error) => {
  document.body.innerHTML = `<pre style="padding:24px;color:#b42318">Failed to load decision desk: ${error.message}</pre>`;
});
