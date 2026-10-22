function initClassrooms(user) {
  const isAdmin = hasRole(user, "Admin");
  const alertEl = document.getElementById("classroom-alert");
  const tbody = document.getElementById("classroom-rows");
  const formBox = document.getElementById("classroom-form-box");
  const form = document.getElementById("classroom-form");
  const idInput = document.getElementById("classroom-id");
  const modeInput = document.getElementById("classroom-mode");

  if (isAdmin) {
    formBox.classList.remove("hidden");
  }

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadClassrooms() {
    const data = await api("/api/classroom/list");
    const classrooms = data.classrooms || [];
    tbody.innerHTML = "";

    if (!classrooms.length) {
      tbody.innerHTML = `<tr><td colspan="5">Nincs megjeleníthető terem.</td></tr>`;
      return;
    }

    classrooms.forEach((room) => {
      const tools = Array.isArray(room.tools) ? room.tools.join(", ") : "";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${room.id}</td>
        <td>${room.capacity ?? ""}</td>
        <td>${room.room_type ?? ""}</td>
        <td>${room.is_active ? "igen" : "nem"}</td>
        <td>${tools}</td>
      `;

      if (isAdmin) {
        const actions = document.createElement("td");
        actions.className = "actions";
        actions.innerHTML = `
          <button class="btn-small btn-secondary" type="button" data-edit>Szerkesztés</button>
          <button class="btn-small btn-danger" type="button" data-delete>Törlés</button>
        `;
        actions.querySelector("[data-edit]").addEventListener("click", () => {
          modeInput.value = "update";
          idInput.value = room.id;
          idInput.readOnly = true;
          document.getElementById("classroom-capacity").value = room.capacity ?? "";
          document.getElementById("classroom-type-id").value = "";
          document.getElementById("classroom-type-id").required = false;
          document.getElementById("classroom-active").checked = Boolean(room.is_active);
          document.getElementById("classroom-submit").textContent = "Terem mentése";
        });
        actions.querySelector("[data-delete]").addEventListener("click", async () => {
          if (!confirm(`Törlöd a(z) ${room.id} termet?`)) return;
          try {
            await api(`/api/classroom/${encodeURIComponent(room.id)}`, { method: "DELETE" });
            showAlert("A terem törölve lett.", true);
            await loadClassrooms();
          } catch (error) {
            showAlert(error.message);
          }
        });
        tr.appendChild(actions);
      } else {
        tr.insertAdjacentHTML("beforeend", "<td></td>");
      }

      tbody.appendChild(tr);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const mode = modeInput.value;
    const roomId = idInput.value.trim();
    const payload = {
      capacity: Number(document.getElementById("classroom-capacity").value),
    };

    try {
      if (mode === "create") {
        payload.id = roomId;
        payload.type_id = Number(document.getElementById("classroom-type-id").value);
        await api("/api/classroom/create", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        showAlert("A terem létrejött.", true);
      } else {
        payload.is_active = document.getElementById("classroom-active").checked;
        const typeId = document.getElementById("classroom-type-id").value;
        if (typeId) {
          payload.room_type_id = Number(typeId);
        }
        await api(`/api/classroom/update/${encodeURIComponent(roomId)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showAlert("A terem frissítve lett.", true);
      }
      form.reset();
      modeInput.value = "create";
      idInput.readOnly = false;
      document.getElementById("classroom-type-id").required = true;
      document.getElementById("classroom-submit").textContent = "Terem létrehozása";
      await loadClassrooms();
    } catch (error) {
      showAlert(error.message);
    }
  });

  document.getElementById("classroom-reset").addEventListener("click", () => {
    form.reset();
    modeInput.value = "create";
    idInput.readOnly = false;
    document.getElementById("classroom-type-id").required = true;
    document.getElementById("classroom-submit").textContent = "Terem létrehozása";
  });

  loadClassrooms().catch((error) => showAlert(error.message));
}
