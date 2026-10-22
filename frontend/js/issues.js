const ISSUE_STATUSES = {
  open: "Nyitott",
  in_progress: "Folyamatban",
  resolved: "Megoldva",
  closed: "Lezárva",
};

function initIssues(user) {
  const alertEl = document.getElementById("issue-alert");
  const tbody = document.getElementById("issue-rows");
  const form = document.getElementById("issue-form");
  const roomSelect = document.getElementById("issue-room-id");

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadRooms() {
    const data = await api("/api/classroom/list");
    roomSelect.innerHTML = "";
    (data.classrooms || []).forEach((room) => {
      const option = document.createElement("option");
      option.value = room.id;
      option.textContent = room.id;
      roomSelect.appendChild(option);
    });
  }

  function statusSelect(issue) {
    const select = document.createElement("select");
    select.className = "inline-select";
    Object.entries(ISSUE_STATUSES).forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      select.appendChild(option);
    });
    if (!(issue.status in ISSUE_STATUSES)) {
      const option = document.createElement("option");
      option.value = issue.status;
      option.textContent = issue.status;
      select.appendChild(option);
    }
    select.value = issue.status;

    select.addEventListener("change", async () => {
      try {
        await api(`/api/issues/${issue.id}`, {
          method: "PUT",
          body: JSON.stringify({ status: select.value }),
        });
        showAlert(`A(z) #${issue.id} hibajegy állapota frissítve.`, true);
        issue.status = select.value;
      } catch (error) {
        select.value = issue.status;
        showAlert(error.message);
      }
    });
    return select;
  }

  async function loadIssues() {
    const issues = (await api("/api/issues")) || [];
    issues.sort((a, b) => b.id - a.id);
    tbody.innerHTML = "";

    if (!issues.length) {
      tbody.innerHTML = `<tr><td colspan="6">Nincs bejelentett hiba.</td></tr>`;
      return;
    }

    issues.forEach((issue) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${issue.id}</td>
        <td>${escapeHtml(issue.room_id)}</td>
        <td>
          <strong>${escapeHtml(issue.title)}</strong>
          <div class="muted">${escapeHtml(issue.description)}</div>
        </td>
        <td>${issue.user_id ?? ""}</td>
        <td>${formatDateTime(issue.created_at)}</td>
      `;
      const statusCell = document.createElement("td");
      statusCell.appendChild(statusSelect(issue));
      tr.appendChild(statusCell);
      tbody.appendChild(tr);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      room_id: roomSelect.value,
      title: document.getElementById("issue-title").value.trim(),
      description: document.getElementById("issue-description").value.trim(),
    };

    try {
      await api("/api/issues", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("A hibajegy rögzítve.", true);
      form.reset();
      await loadIssues();
    } catch (error) {
      showAlert(error.message);
    }
  });

  loadRooms().catch((error) => showAlert(error.message));
  loadIssues().catch((error) => showAlert(error.message));
}
