if (!requireAuth()) {
  throw new Error("Nincs bejelentkezve.");
}

const nameEl = document.getElementById("user-name");
const rolesEl = document.getElementById("user-roles");

document.getElementById("logout-button").addEventListener("click", () => {
  logout();
});

function activateTab(tab) {
  const target = tab?.dataset.tab;
  document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${target}`);
  });
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab));
});

const TAB_INITS = {
  classrooms: initClassrooms,
  keys: initKeys,
  reservations: initReservations,
  maintenance: initMaintenance,
  tools: initTools,
  issues: initIssues,
  users: initUsers,
  reports: initReports,
};

getMe()
  .then((user) => {
    nameEl.textContent = user.name || `Felhasználó #${user.id}`;
    rolesEl.textContent = (user.roles || []).join(", ") || "nincs szerepkör";
    document.querySelectorAll(".tab[data-roles]").forEach((tab) => {
      const allowed = hasAnyRole(user, tab.dataset.roles.split(","));
      tab.classList.toggle("hidden", !allowed);
    });
    activateTab(document.querySelector(".tab:not(.hidden)"));
    document.querySelectorAll(".tab:not(.hidden)").forEach((tab) => TAB_INITS[tab.dataset.tab](user));
  })
  .catch(() => {
    clearToken();
    window.location.href = "login.html";
  });
