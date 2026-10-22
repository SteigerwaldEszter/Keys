redirectIfLoggedIn();

const form = document.getElementById("login-form");
const alertBox = document.getElementById("login-alert");
const submitButton = document.getElementById("login-submit");

function showError(message) {
  alertBox.textContent = message;
  alertBox.classList.add("visible");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  alertBox.classList.remove("visible");
  submitButton.disabled = true;

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    await login(email, password);
    window.location.href = "app.html";
  } catch (error) {
    showError(error.message || "Sikertelen bejelentkezés.");
    submitButton.disabled = false;
  }
});
