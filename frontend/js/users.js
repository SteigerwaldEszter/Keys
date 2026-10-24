const ALL_ROLES = ["Admin", "Instructor", "Director", "Receptionist"];

function initUsers(user) {
  if (!hasRole(user, "Admin")) return;

  const alertEl = document.getElementById("user-alert");
  const tbody = document.getElementById("user-rows");
  const form = document.getElementById("user-form");
  const roleBox = document.getElementById("user-role-box");
  const roleForm = document.getElementById("user-role-form");
  const roleChecks = document.getElementById("user-role-checks");
  let editedUserId = null;

  ALL_ROLES.forEach((role) => {
    const row = document.createElement("div");
    row.className = "checkbox-row";
    row.innerHTML = `
      <input id="role-check-${role}" type="checkbox" value="${role}" />
      <label for="role-check-${role}">${role}</label>
    `;
    roleChecks.appendChild(row);
  });

  const roleSelect = document.getElementById("new-user-role");
  const pinRow = document.getElementById("new-user-pin-row");
  const pinInput = document.getElementById("new-user-pin");
  function syncPinField() {
    const needsPin = roleSelect.value === "Receptionist";
    pinRow.classList.toggle("hidden", !needsPin);
    pinInput.required = needsPin;
  }
  roleSelect.addEventListener("change", syncPinField);
  syncPinField();

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  function openRoleEditor(target) {
    editedUserId = target.id;
    document.getElementById("user-role-name").textContent = `${target.name} (#${target.id})`;
    ALL_ROLES.forEach((role) => {
      document.getElementById(`role-check-${role}`).checked = (target.roles || []).includes(role);
    });
    roleBox.classList.remove("hidden");
  }

  async function loadUsers() {
    const data = await api("/api/user/list");
    const users = data.users || [];
    tbody.innerHTML = "";

    if (!users.length) {
      tbody.innerHTML = `<tr><td colspan="4">Nincs felhasználó.</td></tr>`;
      return;
    }

    users.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${escapeHtml(item.name)}</td>
        <td>${(item.roles || []).map((r) => `<span class="badge">${escapeHtml(r)}</span>`).join(" ")}</td>
      `;

      const actions = document.createElement("td");
      actions.className = "actions";
      actions.innerHTML = `
        <button class="btn-small btn-secondary" type="button" data-roles>Szerepkörök</button>
        <button class="btn-small btn-danger" type="button" data-delete>Törlés</button>
      `;
      actions.querySelector("[data-roles]").addEventListener("click", () => openRoleEditor(item));
      const deleteButton = actions.querySelector("[data-delete]");
      if (item.id === user.id) {
        deleteButton.disabled = true;
        deleteButton.title = "Saját fiók nem törölhető";
      }
      deleteButton.addEventListener("click", async () => {
        if (!confirm(`Törlöd ${item.name} felhasználót?`)) return;
        try {
          await api(`/api/auth/delete/${item.id}`, { method: "DELETE" });
          showAlert("A felhasználó törölve lett.", true);
          await loadUsers();
        } catch (error) {
          showAlert(error.message);
        }
      });
      tr.appendChild(actions);

      tbody.appendChild(tr);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const role = document.getElementById("new-user-role").value;
    const pin = document.getElementById("new-user-pin").value.trim();
    const payload = {
      name: document.getElementById("new-user-name").value.trim(),
      email: document.getElementById("new-user-email").value.trim(),
      password: document.getElementById("new-user-password").value,
      role,
    };
    if (pin) {
      payload.pin = pin;
    }

    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("A felhasználó létrejött.", true);
      form.reset();
      syncPinField();
      await loadUsers();
    } catch (error) {
      showAlert(error.message);
    }
  });

  roleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const roleNames = ALL_ROLES.filter((role) => document.getElementById(`role-check-${role}`).checked);

    try {
      await api(`/api/user/update/${editedUserId}`, {
        method: "PUT",
        body: JSON.stringify({ role_names: roleNames }),
      });
      showAlert("A szerepkörök frissítve lettek.", true);
      roleBox.classList.add("hidden");
      await loadUsers();
    } catch (error) {
      showAlert(error.message);
    }
  });

  document.getElementById("user-role-cancel").addEventListener("click", () => {
    roleBox.classList.add("hidden");
  });

  loadUsers().catch((error) => showAlert(error.message));
}
