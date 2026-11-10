const REPORTS_BASE = "/api/reports";
const EXCLUDED_UTILIZATION_STATUSES = ["cancelled", "no-show"];

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

  const utilizationFrom = document.getElementById("utilization-from");
  const utilizationTo = document.getElementById("utilization-to");
  let utilizationRooms = [];
  let utilizationReservations = [];

  function toDateInput(date) {
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${date.getFullYear()}-${month}-${day}`;
  }


  function renderUtilization() {
    const tbody = document.getElementById("utilization-rows");
    tbody.innerHTML = "";

    if (!utilizationFrom.value || !utilizationTo.value || utilizationFrom.value > utilizationTo.value) {
      tbody.innerHTML = `<tr><td colspan="3">Adj meg érvényes időszakot.</td></tr>`;
      return;
    }
    if (!utilizationRooms.length) {
      tbody.innerHTML = `<tr><td colspan="3">Nincs megjeleníthető terem.</td></tr>`;
      return;
    }

    const start = new Date(`${utilizationFrom.value}T00:00:00`);
    const end = new Date(`${utilizationTo.value}T00:00:00`);
    end.setDate(end.getDate() + 1);

    const rows = utilizationRooms.map((room) => {
      let count = 0;
      let hours = 0;
      utilizationReservations.forEach((item) => {
        if (item.room_id !== room.id || EXCLUDED_UTILIZATION_STATUSES.includes(item.status)) return;
        const from = Math.max(new Date(item.start_time).getTime(), start.getTime());
        const to = Math.min(new Date(item.end_time).getTime(), end.getTime());
        if (to <= from) return;
        count += 1;
        hours += (to - from) / 3600000;
      });
      return { id: room.id, count, hours };
    });

    rows.sort((a, b) => b.hours - a.hours);
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(row.id)}</td>
        <td>${row.count}</td>
        <td>${row.hours.toFixed(1)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function loadUtilization() {
    const [roomData, reservationData] = await Promise.all([
      api("/api/classroom/list"),
      api("/api/reservation/list"),
    ]);
    utilizationRooms = roomData.classrooms || [];
    utilizationReservations = reservationData.reservations || [];
    renderUtilization();
  }

  const today = new Date();
  utilizationFrom.value = toDateInput(new Date(today.getFullYear(), today.getMonth(), 1));
  utilizationTo.value = toDateInput(new Date(today.getFullYear(), today.getMonth() + 1, 0));
  utilizationFrom.addEventListener("change", renderUtilization);
  utilizationTo.addEventListener("change", renderUtilization);

  function loadAll() {
    alertEl.classList.remove("visible");
    return Promise.all([loadUsage(), loadMissingKeys(), loadAuditLogs(), loadUtilization()]).catch((error) =>
      showAlert(error.message)
    );
  }

  document.getElementById("report-refresh").addEventListener("click", loadAll);
  loadAll();
}
