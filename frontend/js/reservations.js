function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("hu-HU");
}

function toApiDateTime(value) {
  if (!value) return value;
  return value.length === 16 ? `${value}:00` : value;
}

function initReservations(user) {
  const canCreate = hasAnyRole(user, ["Instructor", "Admin"]);
  const canStatus = hasAnyRole(user, ["Receptionist", "Admin"]);
  const canDelete = hasAnyRole(user, ["Instructor", "Admin"]);
  const alertEl = document.getElementById("reservation-alert");
  const tbody = document.getElementById("reservation-rows");
  const formBox = document.getElementById("reservation-form-box");
  const statusBox = document.getElementById("reservation-status-box");
  const form = document.getElementById("reservation-form");
  const statusForm = document.getElementById("reservation-status-form");

  if (canCreate) {
    formBox.classList.remove("hidden");
  }
  if (canStatus) {
    statusBox.classList.remove("hidden");
  }

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadReservations() {
    const data = await api("/api/reservation/list");
    const reservations = data.reservations || [];
    tbody.innerHTML = "";

    if (!reservations.length) {
      tbody.innerHTML = `<tr><td colspan="6">Nincs megjeleníthető foglalás.</td></tr>`;
      return;
    }

    reservations.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.room_id ?? ""}</td>
        <td>${item.user_id ?? ""}</td>
        <td>${formatDateTime(item.start_time)}</td>
        <td>${formatDateTime(item.end_time)}</td>
        <td><span class="badge">${item.status ?? ""}</span></td>
      `;

      if (canDelete) {
        const actions = document.createElement("td");
        actions.className = "actions";
        const button = document.createElement("button");
        button.className = "btn-small btn-danger";
        button.type = "button";
        button.textContent = "Törlés";
        button.addEventListener("click", async () => {
          if (!confirm(`Törlöd a(z) ${item.id} foglalást?`)) return;
          try {
            await api(`/api/reservation/delete/${item.id}`, { method: "DELETE" });
            showAlert("A foglalás törölve lett.", true);
            await loadReservations();
          } catch (error) {
            showAlert(error.message);
          }
        });
        actions.appendChild(button);
        tr.appendChild(actions);
      } else {
        tr.insertAdjacentHTML("beforeend", "<td></td>");
      }

      tbody.appendChild(tr);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      room_id: document.getElementById("reservation-room-id").value.trim(),
      start_time: toApiDateTime(document.getElementById("reservation-start").value),
      duration_slots: Number(document.getElementById("reservation-slots").value) || 1,
      recurring_weeks: Number(document.getElementById("reservation-weeks").value) || 1,
    };

    try {
      await api("/api/reservation/create", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("A foglalás létrejött.", true);
      form.reset();
      document.getElementById("reservation-slots").value = 1;
      document.getElementById("reservation-weeks").value = 1;
      await loadReservations();
    } catch (error) {
      showAlert(error.message);
    }
  });

  statusForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = document.getElementById("reservation-status-id").value.trim();
    const payload = {
      status: document.getElementById("reservation-status").value,
    };

    try {
      await api(`/api/reservation/status/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showAlert("A foglalás állapota frissítve lett.", true);
      statusForm.reset();
      await loadReservations();
    } catch (error) {
      showAlert(error.message);
    }
  });

  loadReservations().catch((error) => showAlert(error.message));
}
