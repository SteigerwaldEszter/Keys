async function login(email, password) {
  const data = await api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

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
    // The session is cleared locally even if the API call fails.
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
