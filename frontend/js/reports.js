const REPORTS_BASE = "/api/reports";

function initReports(user) {
  if (!hasRole(user, "Director")) return;

  const alertEl = document.getElementById("report-alert");

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadUsage() {
    const data = await api(`${REPORTS_BASE}/reports/usage`);
    document.getElementById("stat-total").textContent = data.total_keys ?? "–";
    document.getElementById("stat-issued").textContent = data.handed_out_keys ?? "–";
    document.getElementById("stat-available").textContent = data.available_keys ?? "–";
  }

  async function loadMissingKeys() {
    const rows = (await api(`${REPORTS_BASE}/reports/missing-keys`)) || [];
    const tbody = document.getElementById("missing-key-rows");
    tbody.innerHTML = "";

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="5">Nincs lejárt, vissza nem hozott kulcs.</td></tr>`;
      return;
    }

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.key_id}</td>
        <td>${escapeHtml(row.room_id)}</td>
        <td>${row.reservation_id ?? ""}</td>
        <td>${formatDateTime(row.end_time)}</td>
        <td>${row.handler_id ?? ""}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function loadAuditLogs() {
    const rows = (await api(`${REPORTS_BASE}/audit-logs`)) || [];
    rows.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const tbody = document.getElementById("audit-rows");
    tbody.innerHTML = "";

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="6">Nincs naplóbejegyzés.</td></tr>`;
      return;
    }

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${formatDateTime(row.timestamp)}</td>
        <td>${row.user_id ?? ""}</td>
        <td><span class="badge">${escapeHtml(row.action)}</span></td>
        <td>${escapeHtml(row.entity_name)} ${escapeHtml(row.entity_value)}</td>
        <td class="mono">${escapeHtml(row.old_value)}</td>
        <td class="mono">${escapeHtml(row.new_value)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function loadAll() {
    alertEl.classList.remove("visible");
    return Promise.all([loadUsage(), loadMissingKeys(), loadAuditLogs()]).catch((error) =>
      showAlert(error.message)
    );
  }

  document.getElementById("report-refresh").addEventListener("click", loadAll);
  loadAll();
}
