let currentProblemId = window.__INITIAL_PROBLEM_ID__;
let monacoEditor = null;
let fallbackTextarea = null;
let stagedEditorValue = "";
let monacoInitPromise = null;
let hasLoadedSolution = false;
let lastLoadedContent = "";
let editorTouched = false;
let suppressEditorTouched = false;
let sessionCheckTimer = null;
let isRedirectingToLogin = false;

const statusEl = document.getElementById("global-status");
const statementTitleEl = document.getElementById("statement-title");
const statementPathEl = document.getElementById("statement-path");
const statementContentEl = document.getElementById("statement-content");
const editorTitleEl = document.getElementById("editor-title");
const solutionPathEl = document.getElementById("solution-path");
const editorEl = document.getElementById("editor");
fallbackTextarea = document.getElementById("editor-fallback");
const monacoRootEl = document.getElementById("monaco-root");
const outputEl = document.getElementById("run-output");
const problemItemsEl = document.getElementById("problem-items");
const saveBtn = document.getElementById("save-btn");
const runBtn = document.getElementById("run-btn");
const submitBtn = document.getElementById("submit-btn");
const logoutBtn = document.getElementById("logout-btn");

function redirectToLogin() {
  if (isRedirectingToLogin) {
    return;
  }
  isRedirectingToLogin = true;
  if (sessionCheckTimer != null) {
    window.clearInterval(sessionCheckTimer);
    sessionCheckTimer = null;
  }
  window.location.href = "/login";
}

function setStatus(message) {
  statusEl.textContent = message;
}

function formatValue(value) {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "undefined") {
    return "(not provided)";
  }
  return JSON.stringify(value, null, 2);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderPublicExamples(examples) {
  if (!Array.isArray(examples) || examples.length === 0) {
    return "";
  }
  const blocks = examples.map((example, index) => {
    const id = example.id ? String(example.id) : `example-${index + 1}`;
    const input = example.input ?? example.args ?? "(not provided)";
    const output = example.output ?? example.expected ?? "(not provided)";
    const note = typeof example.note === "string" ? example.note : "";
    const inputText =
      typeof input === "string" ? input : JSON.stringify(input, null, 2);
    const outputText =
      typeof output === "string" ? output : JSON.stringify(output, null, 2);
    return (
      `<section class="public-example">` +
      `<h4>${escapeHtml(id)}</h4>` +
      `<div><strong>Input</strong></div>` +
      `<pre>${escapeHtml(inputText)}</pre>` +
      `<div><strong>Output</strong></div>` +
      `<pre>${escapeHtml(outputText)}</pre>` +
      (note ? `<p>${escapeHtml(note)}</p>` : "") +
      `</section>`
    );
  });
  return `<section class="public-examples"><h3>Public Examples</h3>${blocks.join("")}</section>`;
}

function asEditorText(value) {
  return typeof value === "string" ? value : "";
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

async function initMonacoEditor() {
  if (monacoInitPromise) {
    return monacoInitPromise;
  }
  monacoInitPromise = (async () => {
    if (!window.require || typeof window.require.config !== "function") {
      await loadScript("/static/vendor/monaco/min/vs/loader.js");
    }
    window.require.config({
      paths: {
        vs: "/static/vendor/monaco/min/vs",
      },
    });
    await new Promise((resolve, reject) => {
      window.require(["vs/editor/editor.main"], resolve, reject);
    });
    if (!monacoRootEl) {
      throw new Error("Missing Monaco container (#monaco-root)");
    }
    monacoRootEl.style.display = "block";
    monacoEditor = window.monaco.editor.create(monacoRootEl, {
      value: stagedEditorValue,
      language: "python",
      theme: "vs",
      automaticLayout: true,
      minimap: { enabled: false },
      lineNumbers: "on",
      autoIndent: "advanced",
      tabSize: 4,
      insertSpaces: true,
      detectIndentation: false,
      scrollBeyondLastLine: false,
      bracketPairColorization: { enabled: true },
    });
    monacoEditor.onDidChangeModelContent(() => {
      if (suppressEditorTouched) {
        return;
      }
      editorTouched = true;
      stagedEditorValue = monacoEditor.getValue();
    });
    monacoEditor.layout();
    window.addEventListener("resize", () => {
      if (monacoEditor) {
        monacoEditor.layout();
      }
    });
    if (fallbackTextarea) {
      fallbackTextarea.style.display = "none";
    }
  })();
  return monacoInitPromise;
}

function setEditorValue(content) {
  const safeContent = asEditorText(content);
  stagedEditorValue = safeContent;
  suppressEditorTouched = true;
  editorTouched = false;
  if (monacoEditor) {
    monacoEditor.setValue(safeContent);
    monacoEditor.layout();
    suppressEditorTouched = false;
    return;
  }
  if (fallbackTextarea) {
    fallbackTextarea.style.display = "block";
    fallbackTextarea.value = safeContent;
  }
  suppressEditorTouched = false;
}

function getEditorValue() {
  if (monacoEditor) {
    return monacoEditor.getValue();
  }
  if (fallbackTextarea) {
    return asEditorText(fallbackTextarea.value);
  }
  return asEditorText(stagedEditorValue);
}

function setActiveProblem(problemId) {
  document.querySelectorAll(".problem-item").forEach((el) => {
    el.classList.toggle("active", Number(el.dataset.problemId) === problemId);
  });
}

function problemItemMarkup(row, isActive) {
  const label = row.display_name || row.slug || row.title || `problem-${row.id}`;
  return (
    `<button class="problem-item${isActive ? " active" : ""}" data-problem-id="${escapeHtml(row.id)}" type="button">` +
    `<span class="slug">${escapeHtml(label)}</span>` +
    `<span class="meta">` +
    `<span class="status status-${escapeHtml(String(row.last_status || "never").toLowerCase())}">` +
    `${escapeHtml(String(row.last_status || "never").toUpperCase())}` +
    `</span>` +
    `<span class="attempts">${escapeHtml(row.attempts ?? 0)}x</span>` +
    `</span>` +
    `<span class="last-run">${escapeHtml(row.last_run || "-")}</span>` +
    `</button>`
  );
}

function bindProblemItemListeners() {
  document.querySelectorAll(".problem-item").forEach((el) => {
    el.addEventListener("click", () => {
      void loadProblem(Number(el.dataset.problemId));
    });
  });
}

function renderProblemList(rows) {
  if (!problemItemsEl) {
    return;
  }
  const safeRows = Array.isArray(rows) ? rows : [];
  if (safeRows.length === 0) {
    problemItemsEl.innerHTML = "";
    currentProblemId = null;
    return;
  }

  const availableIds = new Set(safeRows.map((row) => Number(row.id)));
  if (currentProblemId == null || !availableIds.has(Number(currentProblemId))) {
    currentProblemId = Number(safeRows[0].id);
  }

  problemItemsEl.innerHTML = safeRows
    .map((row) => problemItemMarkup(row, Number(row.id) === Number(currentProblemId)))
    .join("");
  bindProblemItemListeners();
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    if (res.status === 401) {
      redirectToLogin();
      throw new Error("Unauthorized");
    }
    let message = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data?.detail) && data.detail.length > 0) {
        const first = data.detail[0];
        if (typeof first?.msg === "string") {
          message = first.msg;
        }
      }
    } catch (_err) {
      // Keep default message when response is not JSON.
    }
    throw new Error(message);
  }
  return await res.json();
}

function startSessionCheck() {
  if (!document.getElementById("logout-btn")) {
    return;
  }
  if (sessionCheckTimer != null) {
    return;
  }
  let inFlight = false;
  const check = async () => {
    if (inFlight || isRedirectingToLogin) {
      return;
    }
    inFlight = true;
    try {
      const res = await fetch("/api/me", {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (res.status === 401) {
        redirectToLogin();
      }
    } catch (_err) {
      // Ignore transient network errors; other API calls still handle auth failures.
    } finally {
      inFlight = false;
    }
  };
  void check();
  sessionCheckTimer = window.setInterval(check, 5000);
  window.addEventListener(
    "beforeunload",
    () => {
      if (sessionCheckTimer != null) {
        window.clearInterval(sessionCheckTimer);
        sessionCheckTimer = null;
      }
    },
    { once: true },
  );
}

async function loadProblem(problemId) {
  try {
    currentProblemId = problemId;
    setActiveProblem(problemId);
    setStatus(`Loading problem ${problemId}...`);

    const data = await fetchJSON(`/api/problems/${problemId}`);
    const solution = await fetchJSON(`/api/solution/${problemId}`);
    const label = data.problem.display_name || data.problem.slug;
    statementTitleEl.textContent = label;
    editorTitleEl.textContent = `Solution: ${label}`;
    statementPathEl.textContent = data.statement_path;
    solutionPathEl.textContent = solution.path;
    const publicExamplesHtml = renderPublicExamples(data.public_examples);
    statementContentEl.innerHTML = data.statement_html + publicExamplesHtml;
    const loadedContent = asEditorText(solution.content);
    lastLoadedContent = loadedContent;
    hasLoadedSolution = true;
    setEditorValue(loadedContent);
    clearOutput();

    setStatus("Ready");
  } catch (err) {
    setStatus(`Load failed: ${err.message}`);
    appendOutput(`[error] ${err.message}\n`);
  }
}

async function saveCurrent() {
  if (currentProblemId == null) {
    return;
  }
  if (!hasLoadedSolution) {
    throw new Error("Editor is not ready yet. Please wait for the solution to load.");
  }
  const content = getEditorValue();
  if (content === "" && lastLoadedContent.trim() !== "" && !editorTouched) {
    throw new Error("Blocked empty save to protect existing code. Edit the content first, then save again.");
  }
  const result = await fetchJSON(`/api/solution/${currentProblemId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (result.ok !== true) {
    throw new Error("Save failed: backend did not confirm success.");
  }
  lastLoadedContent = content;
  editorTouched = false;
  solutionPathEl.textContent = result.path;
}

function appendOutput(chunk) {
  outputEl.innerHTML += `<pre>${escapeHtml(chunk)}</pre>`;
  outputEl.scrollTop = outputEl.scrollHeight;
}

function clearOutput() {
  outputEl.innerHTML = "";
}

function renderLegacyOutput(result) {
  const summary =
    `[done] attempt=${result.attempt_id} status=${result.status} ` +
    `passed=${result.passed} failed=${result.failed} time=${result.time_ms}ms`;
  const body = result.output || "(no output)";
  outputEl.innerHTML =
    `<section class="result-block">` +
    `<div class="result-summary">${escapeHtml(summary)}</div>` +
    `<pre>${escapeHtml(body)}</pre>` +
    `</section>`;
}

function renderRunResult(result) {
  if (!Array.isArray(result.public_examples)) {
    renderLegacyOutput(result);
    return;
  }
  const summary = result.summary || {};
  const cards = result.public_examples.map((example) => {
    const message = example.message ? `<div><strong>Message</strong>: ${escapeHtml(example.message)}</div>` : "";
    return (
      `<section class="result-card ${example.passed ? "result-pass" : "result-fail"}">` +
      `<h4>${escapeHtml(example.id || "example")}</h4>` +
      `<div><strong>Status</strong>: ${example.passed ? "PASS" : "FAIL"}</div>` +
      `<div><strong>Input</strong></div>` +
      `<pre>${escapeHtml(formatValue(example.input))}</pre>` +
      `<div><strong>Expected</strong></div>` +
      `<pre>${escapeHtml(formatValue(example.expected))}</pre>` +
      `<div><strong>Actual</strong></div>` +
      `<pre>${escapeHtml(formatValue(example.actual))}</pre>` +
      message +
      `</section>`
    );
  });
  outputEl.innerHTML =
    `<section class="result-block">` +
    `<div class="result-summary">` +
    `Public examples: ${escapeHtml(summary.passed ?? 0)} / ${escapeHtml(summary.total ?? 0)} passed` +
    `</div>` +
    `${cards.join("")}` +
    `</section>`;
}

function renderSubmitResult(result) {
  if (!result.summary || !Object.prototype.hasOwnProperty.call(result.summary, "total_hidden")) {
    renderLegacyOutput(result);
    return;
  }
  const summary = result.summary;
  const failure = result.first_failure;
  let failureHtml = `<div class="result-note">All hidden tests passed.</div>`;
  if (failure) {
    const failureType = failure.failure_type || "Failure";
    const actualHtml = Object.prototype.hasOwnProperty.call(failure, "actual")
      ? `<div><strong>Actual</strong></div><pre>${escapeHtml(formatValue(failure.actual))}</pre>`
      : "";
    const expectedHtml = Object.prototype.hasOwnProperty.call(failure, "expected")
      ? `<div><strong>Expected</strong></div><pre>${escapeHtml(formatValue(failure.expected))}</pre>`
      : "";
    const inputSummaryHtml = failure.input_summary
      ? `<div><strong>Input summary</strong>: ${escapeHtml(failure.input_summary)}</div>`
      : "";
    failureHtml =
      `<section class="result-card result-fail">` +
      `<h4>First Hidden Failure</h4>` +
      `<div><strong>${escapeHtml(failure.case_label || failure.case_id || "Hidden case")}</strong></div>` +
      `<div><strong>Failure type</strong>: ${escapeHtml(failureType)}</div>` +
      `<div><strong>Message</strong>: ${escapeHtml(failure.message || "Failure")}</div>` +
      `${actualHtml}` +
      `${expectedHtml}` +
      `${inputSummaryHtml}` +
      `</section>`;
  }
  outputEl.innerHTML =
    `<section class="result-block">` +
    `<div class="result-summary">` +
    `Hidden tests: ${escapeHtml(summary.passed_hidden ?? 0)} / ${escapeHtml(summary.total_hidden ?? 0)} passed` +
    `</div>` +
    `${failureHtml}` +
    `</section>`;
}

function renderResult(result, action) {
  if (result && typeof result.error === "string" && result.error !== "") {
    renderError(result.error);
    return;
  }
  if (action === "submit") {
    renderSubmitResult(result);
    return;
  }
  renderRunResult(result);
}

function renderError(message) {
  outputEl.innerHTML =
    `<section class="result-block">` +
    `<div class="result-summary result-fail">Error</div>` +
    `<pre>${escapeHtml(message)}</pre>` +
    `</section>`;
}

async function refreshProblemList() {
  const data = await fetchJSON("/api/problems");
  renderProblemList(data.problems || []);
}

async function runCurrent() {
  if (currentProblemId == null) {
    return;
  }

  try {
    clearOutput();
    setStatus("Saving...");
    await saveCurrent();

    setStatus("Running tests...");
    const result = await fetchJSON(`/api/run/${currentProblemId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    renderResult(result, "run");
    setStatus(`Run complete: ${result.status.toUpperCase()}`);
    await refreshProblemList();
  } catch (err) {
    renderError(err.message);
    setStatus(`Run failed: ${err.message}`);
  }
}

async function submitCurrent() {
  if (currentProblemId == null) {
    return;
  }

  try {
    clearOutput();
    setStatus("Saving...");
    await saveCurrent();

    setStatus("Submitting...");
    const result = await fetchJSON(`/api/submit/${currentProblemId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    renderResult(result, "submit");
    setStatus(`Submit complete: ${result.status.toUpperCase()}`);
    await refreshProblemList();
  } catch (err) {
    renderError(err.message);
    setStatus(`Submit failed: ${err.message}`);
  }
}

bindProblemItemListeners();

saveBtn.addEventListener("click", () => {
  void saveCurrent()
    .then(() => setStatus("Saved"))
    .catch((err) => {
      appendOutput(`[error] ${err.message}\n`);
      setStatus(`Save failed: ${err.message}`);
    });
});

runBtn.addEventListener("click", () => {
  void runCurrent();
});

if (submitBtn) {
  submitBtn.addEventListener("click", () => {
    void submitCurrent();
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    void fetchJSON("/api/auth/logout", { method: "POST" })
      .finally(() => {
        window.location.href = "/login";
      });
  });
}

if (fallbackTextarea) {
  fallbackTextarea.addEventListener("input", () => {
    if (suppressEditorTouched) {
      return;
    }
    editorTouched = true;
    stagedEditorValue = fallbackTextarea.value;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  startSessionCheck();
});

void initMonacoEditor()
  .catch((err) => {
    if (monacoRootEl) {
      monacoRootEl.style.display = "none";
    }
    if (fallbackTextarea) {
      fallbackTextarea.style.display = "block";
    }
    setStatus(`Monaco unavailable, using basic editor (${err.message})`);
    appendOutput(`[warn] Monaco failed to load; fallback editor enabled: ${err.message}\n`);
  })

void refreshProblemList()
  .then(() => {
    if (currentProblemId != null) {
      return loadProblem(currentProblemId);
    }
    return undefined;
  })
  .catch((err) => {
    setStatus(`Problem list failed: ${err.message}`);
    appendOutput(`[error] ${err.message}\n`);
  });
