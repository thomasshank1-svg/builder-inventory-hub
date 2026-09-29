let state = { projects: [], units: [], statuses: [], states: [], brokers: [], totals: {} };

function optionList(values, selected) {
  return values.map((value) => `<option ${value === selected ? "selected" : ""}>${esc(value)}</option>`).join("");
}

function renderControls() {
  $("#stateFilter").innerHTML = '<option value="">All states</option>' + state.states.map((s) => `<option>${esc(s)}</option>`).join("");
  $("#newProjectState").innerHTML = optionList(state.states);
  $("#statusSelect").innerHTML = optionList(state.statuses, "Available");
  $("#brokerSelect").innerHTML = optionList(state.brokers, "Unassigned");
  $("#projectSelect").innerHTML = state.projects.map((project) => `<option value="${project.id}">${esc(project.name)} · ${esc(project.city)}</option>`).join("");
}

function renderStats() {
  $("#stats").innerHTML = state.statuses.map((status) => `<div class="stat"><strong>${state.totals[status] || 0}</strong><span>${esc(status)}</span></div>`).join("");
}

function renderUnits() {
  const selectedState = $("#stateFilter").value;
  const units = selectedState ? state.units.filter((unit) => unit.state === selectedState) : state.units;
  $("#units").innerHTML = units.map((unit) => `
    <article class="item unit">
      <div>
        <span class="pill">${esc(unit.state)}</span>
        <h3>${esc(unit.project_name)} · ${esc(unit.unit_code)}</h3>
        <p>${esc(unit.city)} · ${esc(unit.unit_type)} · ${unit.bedrooms} bed · floor ${esc(unit.floor)}</p>
        <p><strong>${money(unit.price_cents)}</strong> · ${unit.inquiries} broker inquiries</p>
      </div>
      <div class="stack">
        <select data-status="${unit.id}">${optionList(state.statuses, unit.status)}</select>
        <select data-broker="${unit.id}">${optionList(state.brokers, unit.broker)}</select>
        <label class="small">Inquiries <input data-inquiries="${unit.id}" type="number" min="0" value="${unit.inquiries}"></label>
        <textarea data-notes="${unit.id}">${esc(unit.notes)}</textarea>
        <button data-save="${unit.id}">Save unit</button>
      </div>
    </article>
  `).join("") || '<p class="muted">No inventory matches this filter.</p>';
  document.querySelectorAll("[data-save]").forEach((button) => button.addEventListener("click", () => action(button, async () => {
    const id = button.dataset.save;
    await api("/api/update-unit", {
      id: Number(id),
      status: document.querySelector(`[data-status="${id}"]`).value,
      broker: document.querySelector(`[data-broker="${id}"]`).value,
      inquiries: Number(document.querySelector(`[data-inquiries="${id}"]`).value || 0),
      notes: document.querySelector(`[data-notes="${id}"]`).value,
    });
    await refresh();
    toast("Inventory updated.");
  })));
}

async function refresh() {
  state = await api("/api/state");
  renderControls();
  renderStats();
  renderUnits();
}

$("#stateFilter").addEventListener("change", renderUnits);
$("#unitForm").addEventListener("submit", (event) => {
  event.preventDefault();
  action(event.submitter, async () => {
    await api("/api/units", Object.fromEntries(new FormData(event.currentTarget)));
    event.currentTarget.reset();
    await refresh();
  });
});
$("#projectForm").addEventListener("submit", (event) => {
  event.preventDefault();
  action(event.submitter, async () => {
    await api("/api/projects", Object.fromEntries(new FormData(event.currentTarget)));
    event.currentTarget.reset();
    await refresh();
  });
});
refresh().catch((error) => toast(error.message));
