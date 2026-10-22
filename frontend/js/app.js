if (!requireAuth()) {
  throw new Error("Nincs bejelentkezve.");
}

const nameEl = document.getElementById("user-name");
const rolesEl = document.getElementById("user-roles");

document.getElementById("logout-button").addEventListener("click", () => {
  logout();
});

getMe()
  .then((user) => {
    nameEl.textContent = user.name || `Felhasználó #${user.id}`;
    rolesEl.textContent = (user.roles || []).join(", ") || "nincs szerepkör";
  })
  .catch(() => {
    clearToken();
    window.location.href = "login.html";
  });
