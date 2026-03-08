const statusEl = document.getElementById("login-status");
const tabRegister = document.getElementById("tab-register");
const tabLogin = document.getElementById("tab-login");
const registerPanel = document.getElementById("register-panel");
const loginPanel = document.getElementById("login-panel");

const tabLoginPassword = document.getElementById("tab-login-password");
const tabLoginCode = document.getElementById("tab-login-code");
const loginPasswordPanel = document.getElementById("login-password-panel");
const loginCodePanel = document.getElementById("login-code-panel");

const registerEmail = document.getElementById("register-email");
const registerPassword = document.getElementById("register-password");
const registerCode = document.getElementById("register-code");
const registerSendCodeBtn = document.getElementById("register-send-code-btn");
const registerVerifyBtn = document.getElementById("register-verify-btn");

const loginPasswordEmail = document.getElementById("login-password-email");
const loginPasswordValue = document.getElementById("login-password-value");
const loginPasswordBtn = document.getElementById("login-password-btn");

const loginCodeEmail = document.getElementById("login-code-email");
const loginCodeValue = document.getElementById("login-code-value");
const loginCodeSendBtn = document.getElementById("login-code-send-btn");
const loginCodeVerifyBtn = document.getElementById("login-code-verify-btn");

function setStatus(message) {
  statusEl.textContent = message;
}

function setTopTab(mode) {
  const registerMode = mode === "register";
  tabRegister.classList.toggle("is-active", registerMode);
  tabLogin.classList.toggle("is-active", !registerMode);
  registerPanel.hidden = !registerMode;
  loginPanel.hidden = registerMode;
  setStatus("");
}

function setLoginMethod(mode) {
  const passwordMode = mode === "password";
  tabLoginPassword.classList.toggle("is-active", passwordMode);
  tabLoginCode.classList.toggle("is-active", !passwordMode);
  loginPasswordPanel.hidden = !passwordMode;
  loginCodePanel.hidden = passwordMode;
  setStatus("");
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (_err) {
    data = {};
  }
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : `Request failed: ${res.status}`;
    throw new Error(detail);
  }
  return data;
}

tabRegister.addEventListener("click", () => setTopTab("register"));
tabLogin.addEventListener("click", () => setTopTab("login"));
tabLoginPassword.addEventListener("click", () => setLoginMethod("password"));
tabLoginCode.addEventListener("click", () => setLoginMethod("code"));

registerSendCodeBtn.addEventListener("click", () => {
  const email = registerEmail.value.trim();
  setStatus("Sending registration code...");
  void postJSON("/api/auth/register/request_code", { email })
    .then(() => setStatus("Code sent. Check your inbox."))
    .catch((err) => setStatus(`Error: ${err.message}`));
});

registerVerifyBtn.addEventListener("click", () => {
  const email = registerEmail.value.trim();
  const password = registerPassword.value;
  const code = registerCode.value.trim();
  setStatus("Creating account...");
  void postJSON("/api/auth/register/verify", { email, password, code })
    .then(() => {
      setStatus("Account created. Redirecting...");
      window.location.href = "/";
    })
    .catch((err) => setStatus(`Error: ${err.message}`));
});

loginPasswordBtn.addEventListener("click", () => {
  const email = loginPasswordEmail.value.trim();
  const password = loginPasswordValue.value;
  setStatus("Logging in...");
  void postJSON("/api/auth/login/password", { email, password })
    .then(() => {
      setStatus("Logged in. Redirecting...");
      window.location.href = "/";
    })
    .catch((err) => setStatus(`Error: ${err.message}`));
});

loginCodeSendBtn.addEventListener("click", () => {
  const email = loginCodeEmail.value.trim();
  setStatus("Sending login code...");
  void postJSON("/api/auth/login/request_code", { email })
    .then(() => setStatus("Code sent. Check your inbox."))
    .catch((err) => setStatus(`Error: ${err.message}`));
});

loginCodeVerifyBtn.addEventListener("click", () => {
  const email = loginCodeEmail.value.trim();
  const code = loginCodeValue.value.trim();
  setStatus("Verifying login...");
  void postJSON("/api/auth/login/verify", { email, code })
    .then(() => {
      setStatus("Logged in. Redirecting...");
      window.location.href = "/";
    })
    .catch((err) => setStatus(`Error: ${err.message}`));
});
