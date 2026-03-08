let currentProblemId = window.__INITIAL_PROBLEM_ID__;
let monacoEditor = null;
let fallbackTextarea = null;
let stagedEditorValue = "";
let monacoInitPromise = null;
let hasLoadedSolution = false;
let lastLoadedContent = "";
let editorTouched = false;
let suppressEditorTouched = false;

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
const saveBtn = document.getElementById("save-btn");
const runBtn = document.getElementById("run-btn");
const logoutBtn = document.getElementById("logout-btn");

function setStatus(message) {
  statusEl.textContent = message;
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

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    if (res.status === 401) {
      window.location.href = "/login";
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

async function loadProblem(problemId) {
  try {
    currentProblemId = problemId;
    setActiveProblem(problemId);
    setStatus(`Loading problem ${problemId}...`);

    const data = await fetchJSON(`/api/problems/${problemId}`);
    const solution = await fetchJSON(`/api/solution/${problemId}`);
    statementTitleEl.textContent = data.problem.slug;
    editorTitleEl.textContent = `Solution: ${data.problem.slug}`;
    statementPathEl.textContent = data.statement_path;
    solutionPathEl.textContent = solution.path;
    statementContentEl.innerHTML = data.statement_html;
    const loadedContent = asEditorText(solution.content);
    lastLoadedContent = loadedContent;
    hasLoadedSolution = true;
    setEditorValue(loadedContent);
    outputEl.textContent = "";

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
  outputEl.textContent += chunk;
  outputEl.scrollTop = outputEl.scrollHeight;
}

async function refreshProblemList() {
  const data = await fetchJSON("/api/problems");
  for (const row of data.problems) {
    const btn = document.querySelector(`.problem-item[data-problem-id='${row.id}']`);
    if (!btn) {
      continue;
    }
    const statusNode = btn.querySelector(".status");
    const attemptsNode = btn.querySelector(".attempts");
    const lastRunNode = btn.querySelector(".last-run");
    statusNode.textContent = row.last_status.toUpperCase();
    statusNode.className = `status status-${row.last_status.toLowerCase()}`;
    attemptsNode.textContent = `${row.attempts}x`;
    lastRunNode.textContent = row.last_run || "-";
  }
}

async function runCurrent() {
  if (currentProblemId == null) {
    return;
  }

  try {
    outputEl.textContent = "";
    setStatus("Saving...");
    await saveCurrent();

    setStatus("Running doctests...");
    const result = await fetchJSON(`/api/run/${currentProblemId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    appendOutput(
      `[done] attempt=${result.attempt_id} status=${result.status} ` +
        `passed=${result.passed} failed=${result.failed} time=${result.time_ms}ms\n\n`,
    );
    appendOutput(result.output || "(no output)\n");
    setStatus(`Run complete: ${result.status.toUpperCase()}`);
    await refreshProblemList();
  } catch (err) {
    appendOutput(`[error] ${err.message}\n`);
    setStatus(`Run failed: ${err.message}`);
  }
}

document.querySelectorAll(".problem-item").forEach((el) => {
  el.addEventListener("click", () => {
    void loadProblem(Number(el.dataset.problemId));
  });
});

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

if (currentProblemId != null) {
  void loadProblem(currentProblemId);
}
