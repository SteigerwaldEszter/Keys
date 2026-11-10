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

  const masterBox = document.getElementById("master-box");
  const masterUserSelect = document.getElementById("master-user-select");
  const masterRoomSelect = document.getElementById("master-room-select");
  let masterKeyId = null;
  let masterUsers = null;
  let masterRooms = null;

  function fillSelect(select, items, emptyText) {
    select.innerHTML = "";
    if (!items.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = emptyText;
      select.appendChild(option);
    }
    items.forEach(([value, text]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      select.appendChild(option);
    });
    select.nextElementSibling.disabled = !items.length;
  }

  function fillRows(tbody, items, emptyText, onRemove) {
    tbody.innerHTML = "";
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="2">${emptyText}</td></tr>`;
      return;
    }
    items.forEach(([value, text]) => {
      const tr = document.createElement("tr");
      const label = document.createElement("td");
      label.textContent = text;
      const actions = document.createElement("td");
      const button = document.createElement("button");
      button.className = "btn-small btn-danger";
      button.type = "button";
      button.textContent = "Eltávolítás";
      button.addEventListener("click", () => onRemove(value));
      actions.appendChild(button);
      tr.append(label, actions);
      tbody.appendChild(tr);
    });
  }

  async function masterRequest(path, options) {
    try {
      const result = await keysRequest(`/${masterKeyId}/master-permissions${path}`, options);
      showAlert(result.message, true);
      await renderMaster();
    } catch (error) {
      showAlert(error.message);
    }
  }

  async function renderMaster() {
    if (!masterUsers) {
      const [userData, roomData] = await Promise.all([api("/api/user/list"), api("/api/classroom/list")]);
      masterUsers = userData.users || [];
      masterRooms = roomData.classrooms || [];
    }
    const details = await keysRequest(`/${masterKeyId}/master-permissions`);
    const userIds = details.users.map((item) => item.id);
    const roomIds = details.rooms.map((item) => item.id);

    fillRows(
      document.getElementById("master-user-rows"),
      details.users.map((item) => [item.id, item.name]),
      "Még senki nem jogosult.",
      (userId) => masterRequest(`/users/${userId}`, { method: "DELETE" })
    );
    fillRows(
      document.getElementById("master-room-rows"),
      details.rooms.map((item) => [item.id, `${item.id} (${item.capacity} fő)`]),
      "Még nincs hozzárendelt terem.",
      (roomId) => masterRequest(`/rooms/${encodeURIComponent(roomId)}`, { method: "DELETE" })
    );
    fillSelect(
      masterUserSelect,
      masterUsers
        .filter((item) => !userIds.includes(item.id))
        .map((item) => [item.id, `${item.name} (${(item.roles || []).join(", ")})`]),
      "Nincs több felhasználó"
    );
    fillSelect(
      masterRoomSelect,
      masterRooms
        .filter((room) => !roomIds.includes(room.id))
        .map((room) => [room.id, `${room.id} (${room.capacity} fő)`]),
      "Nincs több terem"
    );
  }

  async function openMaster(key) {
    masterKeyId = key.id;
    document.getElementById("master-key-name").textContent = key.name ?? `#${key.id}`;
    masterBox.classList.remove("hidden");
    try {
      await renderMaster();
    } catch (error) {
      showAlert(error.message);
    }
  }

  document.getElementById("master-user-form").addEventListener("submit", (event) => {
    event.preventDefault();
    masterRequest("/users", { method: "POST", body: JSON.stringify({ user_id: Number(masterUserSelect.value) }) });
  });

  document.getElementById("master-room-form").addEventListener("submit", (event) => {
    event.preventDefault();
    masterRequest("/rooms", { method: "POST", body: JSON.stringify({ room_id: masterRoomSelect.value }) });
  });

  document.getElementById("master-close").addEventListener("click", () => {
    masterKeyId = null;
    masterBox.classList.add("hidden");
  });

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
        if (key.is_master) {
          const masterButton = document.createElement("button");
          masterButton.className = "btn-small btn-secondary";
          masterButton.type = "button";
          masterButton.textContent = "Jogosultságok";
          masterButton.addEventListener("click", () => openMaster(key));
          actions.appendChild(masterButton);
        }
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

  const signatureRequestBtn = document.getElementById("signature-request");
  const signatureQrWrap = document.getElementById("signature-qr-wrap");
  const signatureQr = document.getElementById("signature-qr");
  const signatureStatus = document.getElementById("signature-status");
  const signaturePreviewWrap = document.getElementById("signature-preview-wrap");
  const signaturePreview = document.getElementById("signature-preview");
  let signatureTimer = null;
  let signatureSession = null;

  function stopSignaturePolling() {
    if (signatureTimer !== null) {
      clearInterval(signatureTimer);
      signatureTimer = null;
    }
    signatureSession = null;
    signatureQrWrap.classList.add("hidden");
    signatureQr.innerHTML = "";
  }

  function resetSignatureUi() {
    stopSignaturePolling();
    signaturePreview.removeAttribute("src");
    signaturePreviewWrap.classList.add("hidden");
  }

  function newSignatureToken() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }

  signatureRequestBtn.addEventListener("click", () => {
    if (!handoverForm.reportValidity()) return;

    resetSignatureUi();

    const token = newSignatureToken();
    const info =
      `Kulcs azonosító: ${document.getElementById("handover-key-id").value.trim()}` +
      ` · Foglalás: ${document.getElementById("handover-reservation-id").value.trim()}`;
    const url = new URL("sign.html", location.href);
    url.hash = new URLSearchParams({ t: token, i: info }).toString();

    const isLocal = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
    signatureStatus.textContent = isLocal
      ? "Figyelem: a localhost cím a telefonról nem érhető el. Nyisd meg az " +
        "alkalmazást a gép hálózati IP-címén (pl. http://192.168.1.20:8080)."
      : "Várakozás az aláírásra…";

    if (typeof qrcode === "function") {
      const qr = qrcode(0, "M");
      qr.addData(url.href);
      qr.make();
      signatureQr.innerHTML = qr.createImgTag(6, 8);
    } else {
      signatureQr.textContent = url.href;
      showAlert("A QR kód könyvtára nem töltődött be, a hivatkozást kézzel is megnyithatod.");
    }
    signatureQrWrap.classList.remove("hidden");

    const session = {};
    signatureSession = session;
    const deadline = Date.now() + 10 * 60 * 1000;
    let busy = false;

    signatureTimer = setInterval(async () => {
      if (busy) return;

      if (Date.now() > deadline) {
        stopSignaturePolling();
        showAlert("Az aláírási kérés lejárt. Kérj újat.");
        return;
      }

      busy = true;
      try {
        const result = await keysRequest(`/api/signature/${token}`);
        if (signatureSession !== session) return; 

        if (result && result.status === "ready") {
          stopSignaturePolling();
          document.getElementById("handover-format").value = result.format;
          document.getElementById("handover-payload").value = result.payload;
          signaturePreview.src = result.payload;
          signaturePreviewWrap.classList.remove("hidden");
          showAlert("Az aláírás megérkezett. Indítsd el a műveletet.", true);
        }
      } catch (error) {
        if (signatureSession === session) {
          stopSignaturePolling();
          showAlert(error.message);
        }
      } finally {
        busy = false;
      }
    }, 2000);
  });

  document.getElementById("signature-cancel").addEventListener("click", resetSignatureUi);

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

    // Kiadásnál az átvevő aláírása és a portás PIN-kódja is kötelező.
    if (action === "handover") {
      const pin = document.getElementById("handover-pin").value.trim();

      if (!payload.payload.startsWith("data:image/png;base64,")) {
        showAlert("A kiadáshoz az átvevő aláírása is szükséges. Kérj aláírást QR kóddal.");
        return;
      }
      if (!pin) {
        showAlert("A kiadáshoz add meg a PIN-kódodat.");
        return;
      }
      payload.pin = pin;
    }

    try {
      const result = await keysRequest(`/${keyId}/${action}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (action === "handover") {
        showAlert("A kulcs kiadva.", true);
      } else if (result && result.late) {
        showAlert(`${result.message}.`, false);
      } else {
        showAlert("A kulcs visszavéve.", true);
      }
      handoverForm.reset();
      resetSignatureUi();
      await loadKeys();
      loadOverdue();
    } catch (error) {
      showAlert(error.message);
    } finally {
      document.getElementById("handover-pin").value = "";
    }
  });

  
  const overdueEl = document.getElementById("key-overdue");

  async function loadOverdue() {
    if (!isReceptionist && !isAdmin) return;
    try {
      const items = (await keysRequest("/overdue")) || [];
      overdueEl.classList.toggle("visible", items.length > 0);
      if (!items.length) {
        overdueEl.textContent = "";
        return;
      }
      overdueEl.innerHTML =
        `<strong>Késve visszavett kulcsok (${items.length}):</strong><ul>` +
        items
          .map(
            (item) =>
              `<li>${escapeHtml(item.key_name)} (kulcs #${escapeHtml(item.key_id)}, ` +
              `terem: ${escapeHtml(item.room_id)}, foglalás #${escapeHtml(item.reservation_id)}) – ` +
              `${escapeHtml(item.minutes_late)} perce lejárt a foglalás</li>`,
          )
          .join("") +
        "</ul>";
    } catch {
      
    }
  }

  loadOverdue();
  setInterval(loadOverdue, 60000);

  loadKeys().catch((error) => showAlert(error.message));
}
