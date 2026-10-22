let keysBase = "/api/keys";

async function keysRequest(path, options) {
  try {
    return await api(`${keysBase}${path}`, options);
  } catch (error) {
    if (keysBase === "/api/keys" && /404|Not Found|nem található/i.test(error.message)) {
      keysBase = "/api/keys/api/keys";
      return api(`${keysBase}${path}`, options);
    }
    throw error;
  }
}

function initKeys(user) {
  const isAdmin = hasRole(user, "Admin");
  const isReceptionist = hasRole(user, "Receptionist");
  const alertEl = document.getElementById("key-alert");
  const tbody = document.getElementById("key-rows");
  const formBox = document.getElementById("key-form-box");
  const handoverBox = document.getElementById("key-handover-box");
  const form = document.getElementById("key-form");
  const handoverForm = document.getElementById("key-handover-form");

  if (isAdmin) {
    formBox.classList.remove("hidden");
  }
  if (isReceptionist) {
    handoverBox.classList.remove("hidden");
  }

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadKeys() {
    const keys = (await keysRequest("")) || [];
    tbody.innerHTML = "";

    if (!keys.length) {
      tbody.innerHTML = `<tr><td colspan="5">Nincs megjeleníthető kulcs.</td></tr>`;
      return;
    }

    keys.forEach((key) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${key.id}</td>
        <td>${key.room_id ?? ""}</td>
        <td>${key.name ?? ""}</td>
        <td><span class="badge">${key.status ?? ""}</span></td>
        <td>${key.is_master ? "igen" : "nem"}</td>
      `;

      if (isAdmin) {
        const actions = document.createElement("td");
        actions.className = "actions";
        actions.innerHTML = `
          <button class="btn-small btn-secondary" type="button" data-edit>Szerkesztés</button>
          <button class="btn-small btn-danger" type="button" data-delete>Törlés</button>
        `;
        actions.querySelector("[data-edit]").addEventListener("click", () => {
          document.getElementById("key-id").value = key.id;
          document.getElementById("key-room-id").value = key.room_id ?? "";
          document.getElementById("key-name").value = key.name ?? "";
          document.getElementById("key-status").value = key.status || "available";
          document.getElementById("key-master").checked = Boolean(key.is_master);
          document.getElementById("key-submit").textContent = "Kulcs mentése";
        });
        actions.querySelector("[data-delete]").addEventListener("click", async () => {
          if (!confirm(`Törlöd a(z) ${key.id} azonosítójú kulcsot?`)) return;
          try {
            await keysRequest(`/${key.id}`, { method: "DELETE" });
            showAlert("A kulcs törölve lett.", true);
            await loadKeys();
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
    const keyId = document.getElementById("key-id").value.trim();
    const payload = {
      room_id: document.getElementById("key-room-id").value.trim(),
      name: document.getElementById("key-name").value.trim(),
      status: document.getElementById("key-status").value,
      is_master: document.getElementById("key-master").checked,
    };

    try {
      if (keyId) {
        await keysRequest(`/${keyId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showAlert("A kulcs frissítve lett.", true);
      } else {
        await keysRequest("/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        showAlert("A kulcs létrejött.", true);
      }
      form.reset();
      document.getElementById("key-submit").textContent = "Kulcs létrehozása";
      await loadKeys();
    } catch (error) {
      showAlert(error.message);
    }
  });

  document.getElementById("key-reset").addEventListener("click", () => {
    form.reset();
    document.getElementById("key-submit").textContent = "Kulcs létrehozása";
  });

  handoverForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const keyId = document.getElementById("handover-key-id").value.trim();
    const action = document.getElementById("handover-action").value;
    const payload = {
      reservation_id: Number(document.getElementById("handover-reservation-id").value),
      receiver_id: Number(document.getElementById("handover-receiver-id").value),
      format: document.getElementById("handover-format").value.trim() || "SIGNATURE",
      payload: document.getElementById("handover-payload").value.trim() || "OK",
    };

    try {
      await keysRequest(`/${keyId}/${action}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert(action === "handover" ? "A kulcs kiadva." : "A kulcs visszavéve.", true);
      handoverForm.reset();
      await loadKeys();
    } catch (error) {
      showAlert(error.message);
    }
  });

  loadKeys().catch((error) => showAlert(error.message));
}
