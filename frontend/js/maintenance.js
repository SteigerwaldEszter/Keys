function initMaintenance(user) {
  if (!hasRole(user, "Admin")) return;

  const alertEl = document.getElementById("maintenance-alert");
  const tbody = document.getElementById("maintenance-rows");
  const form = document.getElementById("maintenance-form");
  const roomSelect = document.getElementById("maintenance-room-id");
  const startInput = document.getElementById("maintenance-start");
  const endInput = document.getElementById("maintenance-end");
  const submitBtn = document.getElementById("maintenance-submit");
  const conflictBox = document.getElementById("maintenance-conflict-box");
  const conflictTitle = document.getElementById("maintenance-conflict-title");
  const conflictRows = document.getElementById("maintenance-conflict-rows");
  const confirmBtn = document.getElementById("maintenance-confirm");
  const cancelBtn = document.getElementById("maintenance-cancel");


  let pendingPayload = null;
  let rooms = [];
  const reservationsById = new Map();

  function showAlert(message, kind = "error") {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", kind === "ok");
    alertEl.classList.toggle("warn", kind === "warn");
  }

  function hideAlert() {
    alertEl.classList.remove("visible");
  }

  function timeRange(start, end) {
    return `${formatDateTime(start)} – ${formatDateTime(end)}`;
  }

  function ownerHtml(item) {
    const name = escapeHtml(item.user_name || `#${item.user_id}`);
    const email = item.user_email
      ? `<div class="muted">${escapeHtml(item.user_email)}</div>`
      : "";
    return `${name}${email}`;
  }

  function conflictRowHtml(item, withAction) {
    const action = withAction
      ? `<td><div class="actions">
          <button class="btn-small" type="button" data-action="edit-reservation"
            data-id="${escapeHtml(item.id)}">Módosítás</button>
          <button class="btn-small btn-danger" type="button"
            data-action="delete-reservation" data-id="${escapeHtml(item.id)}">
            Foglalás törlése</button>
        </div></td>`
      : "";
    return `
      <tr>
        <td>#${escapeHtml(item.id)}</td>
        <td>${ownerHtml(item)}</td>
        <td>${escapeHtml(timeRange(item.start_time, item.end_time))}</td>
        <td><span class="badge">${escapeHtml(item.status)}</span></td>
        ${action}
      </tr>`;
  }

  function windowRowsHtml(windows) {
    reservationsById.clear();
    if (!windows.length) {
      return `<tr><td colspan="5">Nincs kijelölt karbantartási idősáv.</td></tr>`;
    }

    return windows
      .map((item) => {
        const conflicts = item.conflicts || [];
+        conflicts.forEach((reservation) => reservationsById.set(String(reservation.id), reservation));
        let status = `<span class="badge">nincs ütközés</span>`;
        if (conflicts.length) {
          status = `<span class="badge badge-warn">${conflicts.length} foglalás</span>`;
        } else if (item.is_past) {
          status = `<span class="badge badge-muted">lejárt</span>`;
        }

        const row = `
          <tr class="${item.is_past ? "past" : ""}">
            <td>${escapeHtml(item.room_id)}</td>
            <td>${escapeHtml(formatDateTime(item.start_time))}</td>
            <td>${escapeHtml(formatDateTime(item.end_time))}</td>
            <td>${status}</td>
            <td>
              <div class="actions">
                <button class="btn-small btn-danger" type="button"
                  data-action="delete-window" data-id="${escapeHtml(item.id)}"
                  data-label="${escapeHtml(item.room_id)}">Törlés</button>
              </div>
            </td>
          </tr>`;

        if (!conflicts.length) return row;

        return `${row}
          <tr class="conflict-row">
            <td colspan="5">
              <strong>Kezelendő foglalások</strong>
              <span class="muted">
                – módosítsd a terem/időpont adatait, vagy töröld a foglalást.
              </span>
              <table class="conflict-list">
                <thead><tr><th>Foglalás</th><th>Foglaló</th><th>Időpont</th><th>Állapot</th><th>Műveletek</th></tr></thead>
                <tbody>${conflicts.map((c) => conflictRowHtml(c, true)).join("")}</tbody>
              </table>
            </td>
          </tr>`;
      })
      .join("");
  }

  function localDateTimeValue(value) {
    return String(value || "").slice(0, 16);
  }

  function reservationEditorRow(item) {
    const row = document.createElement("tr");
    row.className = "reservation-edit-row";
    const roomOptions = rooms.map((room) =>
      `<option value="${escapeHtml(room.id)}" ${String(room.id) === String(item.room_id) ? "selected" : ""}>${escapeHtml(room.id)}</option>`,
    ).join("");
    row.innerHTML = `
      <td colspan="5">
        <form class="reservation-edit-form" data-reservation-edit="${escapeHtml(item.id)}">
          <label>Terem
            <select name="room_id" required>${roomOptions}</select>
          </label>
          <label>Kezdete
            <input name="start_time" type="datetime-local" value="${escapeHtml(localDateTimeValue(item.start_time))}" required />
          </label>
          <label>Vége
            <input name="end_time" type="datetime-local" value="${escapeHtml(localDateTimeValue(item.end_time))}" required />
          </label>
          <div class="actions">
            <button class="btn-small" type="submit">Módosítás mentése</button>
            <button class="btn-small btn-secondary" type="button" data-action="cancel-edit">Mégse</button>
          </div>
        </form>
      </td>`;
    return row;
  }

  async function loadWindows() {
    const data = await api("/api/maintenance/list");
    tbody.innerHTML = windowRowsHtml((data && data.windows) || []);
  }

  async function loadRooms() {
    const data = await api("/api/classroom/list");
    rooms = (data && data.classrooms) || [];
    roomSelect.innerHTML =
      `<option value="" disabled selected>Válassz termet</option>` +
      rooms
        .map(
          (room) =>
            `<option value="${escapeHtml(room.id)}">${escapeHtml(room.id)}</option>`,
        )
        .join("");
  }

  function hideConflicts() {
    pendingPayload = null;
    conflictBox.classList.add("hidden");
    conflictRows.innerHTML = "";
  }

  function showConflicts(conflicts) {
    conflictTitle.textContent =
      `Figyelem: a karbantartás ${conflicts.length} meglévő foglalással ütközik`;
    conflictRows.innerHTML = conflicts.map((c) => conflictRowHtml(c, false)).join("");
    conflictBox.classList.remove("hidden");
    if (conflictBox.scrollIntoView) conflictBox.scrollIntoView({ block: "nearest" });
  }

  function setBusy(busy) {
    submitBtn.disabled = busy;
    confirmBtn.disabled = busy;
  }

  async function submitWindow(payload, confirmed) {
    setBusy(true);
    try {
      const result = await api("/api/maintenance/create", {
        method: "POST",
        body: JSON.stringify({ ...payload, confirm_conflicts: confirmed }),
      });

      hideConflicts();
      form.reset();

      const count = ((result && result.conflicts) || []).length;
      if (count) {
        showAlert(
          `A karbantartási idősáv kijelölve. Figyelem: ${count} meglévő foglalással ` +
            `ütközik, kezeld őket az alábbi listában (törlés vagy áthelyezés).`,
          "warn",
        );
      } else {
        showAlert("A karbantartási idősáv kijelölve.", "ok");
      }
      await loadWindows();
    } catch (error) {
      const detail = error.data && error.data.detail;
      if (error.status === 409 && detail && Array.isArray(detail.conflicts)) {
      
        hideAlert();
        pendingPayload = payload;
        showConflicts(detail.conflicts);
      } else {
        showAlert(error.message);
      }
    } finally {
      setBusy(false);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    hideAlert();
    hideConflicts();
    submitWindow(
      {
        room_id: roomSelect.value,
        start_time: toApiDateTime(startInput.value),
        end_time: toApiDateTime(endInput.value),
      },
      false,
    );
  });

  form.addEventListener("input", () => {
    if (pendingPayload) hideConflicts();
  });

  confirmBtn.addEventListener("click", () => {
    if (!pendingPayload) return;
    submitWindow(pendingPayload, true);
  });

  cancelBtn.addEventListener("click", hideConflicts);

  tbody.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    const id = button.dataset.id;

    try {
      if (button.dataset.action === "edit-reservation") {
        const reservation = reservationsById.get(String(id));
        if (!reservation) throw new Error("A foglalás adatai nem találhatók. Frissítsd a listát.");
        tbody.querySelectorAll(".reservation-edit-row").forEach((row) => row.remove());
        button.closest("tr").insertAdjacentElement("afterend", reservationEditorRow(reservation));
        return;
      } else if (button.dataset.action === "cancel-edit") {
        button.closest(".reservation-edit-row").remove();
        return;
      } else if (button.dataset.action === "delete-window") {
        if (!confirm(`Törlöd a(z) ${button.dataset.label} terem karbantartási idősávját?`)) {
          return;
        }
        await api(`/api/maintenance/delete/${id}`, { method: "DELETE" });
        showAlert("A karbantartási idősáv törölve lett.", "ok");
      } else if (button.dataset.action === "delete-reservation") {
        if (!confirm(`Törlöd a(z) #${id} foglalást?`)) return;
        await api(`/api/reservation/delete/${id}`, { method: "DELETE" });
        document.dispatchEvent(new CustomEvent("reservations-changed"));
        showAlert("A foglalás törölve lett.", "ok");
      }
      await loadWindows();
    } catch (error) {
      showAlert(error.message);
    }
  });

  tbody.addEventListener("submit", async (event) => {
    const editForm = event.target.closest("form[data-reservation-edit]");
    if (!editForm) return;
    event.preventDefault();
    const reservationId = editForm.dataset.reservationEdit;
    const formData = new FormData(editForm);
    const payload = {
      room_id: formData.get("room_id"),
      start_time: toApiDateTime(formData.get("start_time")),
      end_time: toApiDateTime(formData.get("end_time")),
    };
    try {
      await api(`/api/maintenance/reservation/${reservationId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showAlert(`A #${reservationId} foglalás módosítva lett.`, "ok");
      document.dispatchEvent(new CustomEvent("reservations-changed"));
      await loadWindows();
    } catch (error) {
      showAlert(error.message);
    }
  });

  // Fülváltáskor frissítjük a listát, mert közben változhattak a foglalások.
  const tab = document.querySelector('.tab[data-tab="maintenance"]');
  if (tab) {
    tab.addEventListener("click", () => {
      loadWindows().catch((error) => showAlert(error.message));
    });
  }

  loadRooms().catch((error) => showAlert(error.message));
  loadWindows().catch((error) => showAlert(error.message));
}
