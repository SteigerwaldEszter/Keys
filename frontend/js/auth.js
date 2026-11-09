async function login(email, password, role = null) {
  const body = { email, password };
  if (role) body.role = role;

  const data = await api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

  
  if (data && data.role_selection_required) {
    return data;
  }

  if (!data || !data.token) {
    throw new Error("A bejelentkezés nem adott vissza tokent.");
  }

  setToken(data.token);
  return data;
}

async function getMe() {
  return api("/api/auth/me");
}

async function logout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch {
    
  }
  clearToken();
  window.location.href = "login.html";
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function redirectIfLoggedIn() {
  if (getToken()) {
    window.location.href = "app.html";
  }
}

function hasRole(user, role) {
  return (user.roles || []).includes(role);
}

function hasAnyRole(user, roles) {
  return roles.some((role) => hasRole(user, role));
}
