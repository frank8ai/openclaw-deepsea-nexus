const { execFileSync, execSync } = require("child_process");
const { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } = require("fs");
const { createHash } = require("crypto");
const { join } = require("path");

function resolveSkillPath() {
  const home = process.env.HOME || "";
  const candidates = [
    process.env.NEXUS_SKILL_PATH,
    join(home, ".openclaw", "workspace", "skills", "deepsea-nexus"),
    join(home, ".openclaw", "skills", "deepsea-nexus"),
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return candidates[0] || "";
}

function resolvePythonBin() {
  const candidates = [
    process.env.NEXUS_PYTHON_PATH,
    "/Users/yizhi/.openclaw/workspace/.venv-nexus/bin/python3",
    "/Users/yizhi/.openclaw/workspace/.venv-nexus/bin/python",
    "/Users/yizhi/miniconda3/envs/openclaw-nexus/bin/python",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (candidate && existsSync(candidate)) {
      return candidate;
    }
  }

  try {
    const found = execSync("command -v python3", { encoding: "utf-8" }).trim();
    if (found) {
      return found;
    }
  } catch (_) {
    // ignore
  }
  return "python3";
}

const RUNTIME = {
  skillPath: resolveSkillPath(),
  pythonBin: resolvePythonBin(),
};

const CONFIG = {
  enabled: true,
  timeout: 30000,
  minResponseChars: 24,
  dedupeWindowMs: 10 * 60 * 1000,
  statusPath: join(process.env.HOME || "", ".openclaw", "state", "nexus-auto-save-status.json"),
};

function logDebug(payload) {
  try {
    const logPath = "/tmp/nexus-auto-save-debug.jsonl";
    appendFileSync(logPath, JSON.stringify(payload) + "\n", "utf-8");
  } catch (_) {
    // ignore
  }
}

function readJson(path) {
  try {
    if (!existsSync(path)) {
      return {};
    }
    const raw = readFileSync(path, "utf-8");
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function writeJson(path, payload) {
  try {
    const dir = path.replace(/\/[^/]+$/, "");
    if (dir && !existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    writeFileSync(path, JSON.stringify(payload, null, 2), "utf-8");
  } catch (_) {
    // ignore
  }
}

function firstNonEmpty(candidates) {
  for (const candidate of candidates || []) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }
  return "";
}

function hasSummaryMarker(text) {
  const source = String(text || "");
  return (
    source.includes("## 📋 总结") ||
    source.includes("=== Context Policy v2 ===") ||
    source.includes("=== Session Handoff Summary ===")
  );
}

function getSummaryHint(event) {
  const ctx = event?.context || {};
  const data = event?.data || {};
  const candidates = [
    ctx?.sessionSummary?.content,
    data?.sessionSummary?.content,
    ctx?.sessionSummary,
    data?.sessionSummary,
    ctx?._contextOptimizer?.summary,
    data?._contextOptimizer?.summary,
    data?.policyV2?.lastSummary,
  ];
  return firstNonEmpty(candidates);
}

function isNonTrivialResponse(text, summaryHint) {
  const source = String(text || "").trim();
  if (hasSummaryMarker(source) || hasSummaryMarker(summaryHint)) {
    return true;
  }
  return source.length >= CONFIG.minResponseChars;
}

function digestPayload(response, summaryHint) {
  const h = createHash("sha1");
  h.update(String(response || ""));
  h.update("\n---\n");
  h.update(String(summaryHint || ""));
  return h.digest("hex");
}

function clipOutput(text, maxLen = 600) {
  const value = String(text || "").trim();
  if (!value) {
    return "";
  }
  if (value.length <= maxLen) {
    return value;
  }
  const half = Math.floor(maxLen / 2);
  return `${value.slice(0, half)}\n...<truncated>...\n${value.slice(-half)}`;
}

function shouldSkipByDedupe(conversationId, digest) {
  const key = conversationId || "global";
  const store = readJson(CONFIG.statusPath);
  const prev = store[key];
  if (!prev || typeof prev !== "object") {
    return false;
  }
  const age = Date.now() - Number(prev.updatedAtMs || 0);
  return prev.digest === digest && age >= 0 && age < CONFIG.dedupeWindowMs;
}

function markSaved(conversationId, digest) {
  const key = conversationId || "global";
  const store = readJson(CONFIG.statusPath);
  store[key] = {
    digest,
    updatedAtMs: Date.now(),
    updatedAt: new Date().toISOString(),
  };
  writeJson(CONFIG.statusPath, store);
}

function runAutoSave(response, conversationId, userQuery, summaryHint = "", extra = {}) {
  const hookScript = join(RUNTIME.skillPath, "hooks", "post-response", "auto_save_summary.py");
  if (!existsSync(hookScript)) {
    return { ok: false, error: `missing_hook_script:${hookScript}` };
  }

  const ctx = {
    response: response || "",
    summary_hint: summaryHint || "",
    user_query: userQuery || "",
    conversation_id: conversationId || new Date().toISOString().replace(/[:.]/g, "-"),
    source: "nexus-auto-save/message:sent",
    ...extra,
  };

  const env = {
    ...process.env,
    NEXUS_HOOK_CONTEXT: JSON.stringify(ctx),
    NEXUS_PYTHON_PATH: RUNTIME.pythonBin,
    NEXUS_SKILL_PATH: RUNTIME.skillPath,
    NEXUS_HOOK_TS: new Date().toISOString(),
    PYTHONWARNINGS: process.env.PYTHONWARNINGS || "ignore::FutureWarning",
  };

  try {
    const stdout = execFileSync(RUNTIME.pythonBin, [hookScript], {
      encoding: "utf-8",
      timeout: CONFIG.timeout,
      env,
    });
    return { ok: true, stdout: clipOutput(stdout) };
  } catch (error) {
    return {
      ok: false,
      error: error.message,
      stdout: clipOutput(error?.stdout),
      stderr: clipOutput(error?.stderr),
    };
  }
}

async function handleMessageSent(event) {
  const ctx = event?.context || {};
  const data = event?.data || {};
  const response = ctx.content || ctx.message || "";
  const conversationId = ctx.conversationId || event?.sessionKey || data?.sessionKey || ctx.messageId || "";
  const userQuery = ctx.userQuery || ctx.prompt || "";
  const summaryHint = getSummaryHint(event);
  const digest = digestPayload(response, summaryHint);

  logDebug({
    ts: new Date().toISOString(),
    eventType: event?.type,
    action: event?.action,
    hasResponse: Boolean(response),
    responseLength: response ? String(response).length : 0,
    hasSummaryHint: Boolean(summaryHint),
    summaryHintLength: summaryHint.length,
  });

  if (!CONFIG.enabled || (!response && !summaryHint)) {
    return event;
  }

  if (!isNonTrivialResponse(response, summaryHint)) {
    logDebug({
      ts: new Date().toISOString(),
      conversationId,
      skipped: "short_non_trivial",
      responseLength: String(response || "").length,
    });
    return event;
  }

  if (shouldSkipByDedupe(conversationId, digest)) {
    logDebug({
      ts: new Date().toISOString(),
      conversationId,
      skipped: "dedupe_window",
    });
    return event;
  }

  const result = runAutoSave(response, conversationId, userQuery, summaryHint, {
    event_type: event?.type || "",
    event_action: event?.action || "",
  });
  if (!result.ok) {
    logDebug({
      ts: new Date().toISOString(),
      conversationId,
      error: result.error,
      hookStdout: result.stdout || "",
      hookStderr: result.stderr || "",
    });
    return event;
  }
  if (result.stdout) {
    logDebug({
      ts: new Date().toISOString(),
      conversationId,
      hookStdout: result.stdout,
    });
  }
  markSaved(conversationId, digest);
  return event;
}

async function main(event) {
  const eventType = event?.type || event?.event?.type || "unknown";
  const action = event?.action || "";

  if (eventType === "message:sent" || (eventType === "message" && action === "sent")) {
    return await handleMessageSent(event);
  }

  return event;
}

const handler = async (event) => main(event);
module.exports = handler;
module.exports.main = main;
