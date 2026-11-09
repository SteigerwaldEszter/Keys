redirectIfLoggedIn();

const form = document.getElementById("login-form");
const alertBox = document.getElementById("login-alert");
const submitButton = document.getElementById("login-submit");

function showError(message) {
  alertBox.textContent = message;
  alertBox.classList.add("visible");
}

const roleStep = document.getElementById("role-step");
const roleOptions = document.getElementById("role-options");

function showRoleStep(roles, email, password) {
  roleOptions.innerHTML = "";

  roles.forEach((role) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "full";
    button.style.marginBottom = "8px";
    button.textContent = role;
    button.addEventListener("click", async () => {
      alertBox.classList.remove("visible");
      roleOptions.querySelectorAll("button").forEach((b) => (b.disabled = true));
      try {
        await login(email, password, role);
        window.location.href = "app.html";
      } catch (error) {
        showError(error.message || "Sikertelen bejelentkezés.");
        roleOptions.querySelectorAll("button").forEach((b) => (b.disabled = false));
      }
    });
    roleOptions.appendChild(button);
  });

  form.classList.add("hidden");
  roleStep.classList.remove("hidden");
}

document.getElementById("role-back").addEventListener("click", () => {
  roleOptions.innerHTML = "";
  roleStep.classList.add("hidden");
  form.classList.remove("hidden");
  alertBox.classList.remove("visible");
  document.getElementById("password").value = "";
  submitButton.disabled = false;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  alertBox.classList.remove("visible");
  submitButton.disabled = true;

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    const data = await login(email, password);

    if (data && data.role_selection_required) {
      showRoleStep(data.roles || [], email, password);
      return;
    }

    window.location.href = "app.html";
  } catch (error) {
    showError(error.message || "Sikertelen bejelentkezés.");
    submitButton.disabled = false;
  }
});
