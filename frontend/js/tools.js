function initTools(user) {
  const isAdmin = hasRole(user, "Admin");
  const alertEl = document.getElementById("tool-alert");
  const tbody = document.getElementById("tool-rows");
  const formBox = document.getElementById("tool-form-box");
  const form = document.getElementById("tool-form");

  if (isAdmin) {
    formBox.classList.remove("hidden");
  }

  function showAlert(message, ok = false) {
    alertEl.textContent = message;
    alertEl.classList.add("visible");
    alertEl.classList.toggle("ok", ok);
  }

  async function loadTools() {
    const data = await api("/api/tool/list");
    const tools = data.tools || [];
    tbody.innerHTML = "";

    if (!tools.length) {
      tbody.innerHTML = `<tr><td colspan="3">Nincs megjeleníthető eszköz.</td></tr>`;
      return;
    }

    tools.forEach((tool) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${tool.id}</td>
        <td>${escapeHtml(tool.name)}</td>
      `;

      const actions = document.createElement("td");
      actions.className = "actions";
      if (isAdmin) {
        const button = document.createElement("button");
        button.className = "btn-small btn-danger";
        button.type = "button";
        button.textContent = "Törlés";
        button.addEventListener("click", async () => {
          if (!confirm(`Törlöd a(z) "${tool.name}" eszközt?`)) return;
          try {
            await api(`/api/tool/delete/${tool.id}`, { method: "DELETE" });
            showAlert("Az eszköz törölve lett.", true);
            await loadTools();
          } catch (error) {
            showAlert(error.message);
          }
        });
        actions.appendChild(button);
      }
      tr.appendChild(actions);

      tbody.appendChild(tr);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = { name: document.getElementById("tool-name").value.trim() };

    try {
      await api("/api/tool/create", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("Az eszköz létrejött.", true);
      form.reset();
      await loadTools();
    } catch (error) {
      showAlert(error.message);
    }
  });

  loadTools().catch((error) => showAlert(error.message));
}
