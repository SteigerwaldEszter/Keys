if (!requireAuth()) {
  throw new Error("Nincs bejelentkezve.");
}

const nameEl = document.getElementById("user-name");
const rolesEl = document.getElementById("user-roles");

document.getElementById("logout-button").addEventListener("click", () => {
  logout();
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
    document.querySelectorAll(".panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `panel-${target}`);
    });
  });
});

getMe()
  .then((user) => {
    nameEl.textContent = user.name || `Felhasználó #${user.id}`;
    rolesEl.textContent = (user.roles || []).join(", ") || "nincs szerepkör";
    document.querySelectorAll(".tab[data-roles]").forEach((tab) => {
      const allowed = hasAnyRole(user, tab.dataset.roles.split(","));
      tab.classList.toggle("hidden", !allowed);
    });
    initClassrooms(user);
    initKeys(user);
    initReservations(user);
    initMaintenance(user);
    initTools(user);
    initIssues(user);
    initUsers(user);
    initReports(user);
  })
  .catch(() => {
    clearToken();
    window.location.href = "login.html";
  });
