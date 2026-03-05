/**
 * Context Optimizer Hook
 *
 * 目标：在不改变既有行为预期的前提下，简化上下文压缩逻辑，
 * 将触发判断与压缩执行统一到单一路径。
 */

const { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } = require("fs");
const { join } = require("path");
const { createHash } = require("crypto");

const RUNTIME_DEFAULTS = {
  preserveRecent: 8,
  compressionThreshold: 20,
  compressAfterRounds: 35,
  tokenTriggerEstimate: 8000,
  triggerSoftRatio: 0.7,
  triggerHardRatio: 0.85,
  mode: "auto",
  enabled: true,
  verbose: false,
};

const DEFAULT_OVERRIDE_PATH = join(
  process.env.HOME || "",
  ".openclaw",
  "state",
  "context-optimizer-single-source.json"
);

const DEFAULT_DEEPSEA_CONFIG_PATH = join(
  process.env.HOME || "",
  ".openclaw",
  "workspace",
  "skills",
  "deepsea-nexus",
  "config.json"
);
const AGENTS_ROOT = join(process.env.HOME || "", ".openclaw", "agents");
const SESSION_FALLBACK_MAX_MESSAGES = toPositiveInt(
  process.env.OPENCLAW_CONTEXT_OPTIMIZER_SESSION_FALLBACK_MAX_MESSAGES,
  320
);
const SESSION_FALLBACK_MAX_SCAN_LINES = toPositiveInt(
  process.env.OPENCLAW_CONTEXT_OPTIMIZER_SESSION_FALLBACK_MAX_SCAN_LINES,
  2000
);
const RUNTIME_STATE_TTL_MS = toPositiveInt(
  process.env.OPENCLAW_CONTEXT_OPTIMIZER_RUNTIME_TTL_SEC,
  24 * 60 * 60
) * 1000;
const MAX_L2_RECORDS = toPositiveInt(
  process.env.OPENCLAW_CONTEXT_OPTIMIZER_MAX_L2_RECORDS,
  120
);

function toPositiveInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.floor(parsed);
}

function toRatio(value, fallback, min = 0, max = 1) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  if (parsed < min || parsed > max) {
    return fallback;
  }
  return parsed;
}

function toNonEmptyString(value, fallback) {
  if (typeof value !== "string") {
    return fallback;
  }
  const text = value.trim();
  return text || fallback;
}

function readJson(path) {
  try {
    if (!path || !existsSync(path)) {
      return null;
    }
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch (_error) {
    return null;
  }
}

function loadRuntimeConfig() {
  const overridePath = process.env.OPENCLAW_CONTEXT_OPTIMIZER_CONFIG || DEFAULT_OVERRIDE_PATH;
  const deepseaPath = process.env.OPENCLAW_DEEPSEA_CONFIG_PATH || DEFAULT_DEEPSEA_CONFIG_PATH;
  const override = readJson(overridePath);

  const normalizeRuntimeConfig = (raw, source) => {
    const preserveRecent = toPositiveInt(raw.preserveRecent, RUNTIME_DEFAULTS.preserveRecent);
    const compressionThreshold = toPositiveInt(raw.compressionThreshold, RUNTIME_DEFAULTS.compressionThreshold);
    const compressAfterRaw = toPositiveInt(
      raw.compressAfterRounds,
      Math.max(compressionThreshold + 8, RUNTIME_DEFAULTS.compressAfterRounds)
    );
    const triggerSoftRatio = toRatio(raw.triggerSoftRatio, RUNTIME_DEFAULTS.triggerSoftRatio, 0.55, 0.9);
    const triggerHardRatio = toRatio(
      raw.triggerHardRatio,
      RUNTIME_DEFAULTS.triggerHardRatio,
      Math.max(triggerSoftRatio + 0.05, 0.65),
      0.98
    );
    const mode = toNonEmptyString(raw.mode, RUNTIME_DEFAULTS.mode).toLowerCase();

    return {
      preserveRecent,
      compressionThreshold,
      compressAfterRounds: Math.max(compressionThreshold + 6, compressAfterRaw),
      tokenTriggerEstimate: toPositiveInt(raw.tokenTriggerEstimate, RUNTIME_DEFAULTS.tokenTriggerEstimate),
      triggerSoftRatio,
      triggerHardRatio,
      mode: mode === "coding" || mode === "general" || mode === "auto" ? mode : RUNTIME_DEFAULTS.mode,
      enabled: raw.enabled !== false,
      verbose: Boolean(raw.verbose),
      source,
    };
  };

  if (override && typeof override === "object") {
    return normalizeRuntimeConfig(
      {
        preserveRecent: override.preserveRecent,
        compressionThreshold: override.compressionThreshold,
        compressAfterRounds: override.compressAfterRounds,
        tokenTriggerEstimate: override.tokenTriggerEstimate,
        triggerSoftRatio: override.triggerSoftRatio,
        triggerHardRatio: override.triggerHardRatio,
        mode: override.mode,
        enabled: override.enabled,
        verbose: override.verbose,
      },
      "single-source-override"
    );
  }

  const deepsea = readJson(deepseaPath);
  const smart = deepsea && typeof deepsea.smart_context === "object" ? deepsea.smart_context : null;

  if (smart) {
    return normalizeRuntimeConfig(
      {
        preserveRecent: smart.full_rounds,
        compressionThreshold: smart.summary_rounds,
        compressAfterRounds: smart.compress_after_rounds,
        tokenTriggerEstimate: smart.full_tokens_max,
        triggerSoftRatio: smart.trigger_soft_ratio,
        triggerHardRatio: smart.trigger_hard_ratio,
        mode: smart.mode,
        enabled: true,
        verbose: false,
      },
      "deepsea-config"
    );
  }

  return { ...RUNTIME_DEFAULTS, source: "runtime-default" };
}

const CONFIG = loadRuntimeConfig();

function roundsToMessageCount(rounds) {
  return toPositiveInt(rounds, RUNTIME_DEFAULTS.preserveRecent) * 2;
}

function getPreserveRecentMessageCount() {
  return roundsToMessageCount(CONFIG.preserveRecent);
}

function readUsageRatio(event) {
  const data = event?.data || {};
  const ratioCandidates = [
    data.contextUsedRatio,
    data.context_ratio,
    data.contextRatio,
    data.percentUsed != null ? Number(data.percentUsed) / 100 : null,
    data.remainingTokens != null && data.contextTokens
      ? 1 - Number(data.remainingTokens) / Number(data.contextTokens)
      : null,
  ];
  for (const candidate of ratioCandidates) {
    const v = Number(candidate);
    if (Number.isFinite(v) && v > 0 && v <= 2) {
      return v;
    }
  }
  return null;
}


const METRICS_LOG =
  process.env.OPENCLAW_SMART_CONTEXT_METRICS_LOG ||
  join(process.env.HOME || "", ".openclaw", "workspace", "logs", "smart_context_metrics.log");
const STATUS_STORE_PATH =
  process.env.OPENCLAW_SMART_CONTEXT_STATUS_PATH ||
  join(process.env.HOME || "", ".openclaw", "state", "smart-context-status.json");

const PHASE = {
  NONE: "none",
  SUMMARY: "summary",
  COMPRESSED: "compressed",
};

const MODE = {
  GENERAL: "general",
  CODING: "coding",
};

const MODE_PROFILE_OFFSETS = {
  [MODE.GENERAL]: {
    preserveRecent: -1,
    summaryRounds: -3,
    compressAfterRounds: -4,
    tokenTriggerScale: 0.9,
    triggerSoftDelta: -0.02,
    triggerHardDelta: -0.03,
  },
  [MODE.CODING]: {
    preserveRecent: 2,
    summaryRounds: 6,
    compressAfterRounds: 8,
    tokenTriggerScale: 1.15,
    triggerSoftDelta: 0.04,
    triggerHardDelta: 0.05,
  },
};

const CODING_SIGNAL_RULES = [
  { name: "code_block", regex: /```[\s\S]{0,1200}?```/m, weight: 4 },
  { name: "stack_trace", regex: /\b(traceback|exception|error:|stack trace|panic:|line \d+)\b/i, weight: 3 },
  {
    name: "path_or_file",
    regex: /(?:^|[\s(])[~/.][\w./-]+|[\w./-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|json|ya?ml|toml|sh|md)(?::\d+)?/i,
    weight: 2,
  },
  {
    name: "tooling",
    regex: /\b(pytest|npm|pnpm|yarn|pip|poetry|uv|cargo|go test|go build|make|cmake|gradle|mvn|ruff|eslint|git)\b/i,
    weight: 2,
  },
  {
    name: "diff_patch",
    regex: /\b(\+\+\+|---|@@|begin patch|end patch|apply_patch)\b/i,
    weight: 2,
  },
  {
    name: "engineering_intent",
    regex: /\b(implement|refactor|debug|fix|optimi[sz]e|测试|报错|修复|编译|重构|上线|回归)\b/i,
    weight: 1,
  },
];

const CODING_MIN_SCORE = 4;
const MODE_RECENT_MESSAGES = 12;

const SUMMARY_PATTERNS = {
  decision: /(^|\s)(decision|decided|决定|结论|方案|trade-off|取舍)[:：-]/i,
  next: /(^|\s)(next(\s+step|\s+action)?|todo|行动项|下一步|待办|follow[-\s]?up)[:：-]/i,
  risk: /(^|\s)(risk|blocked?|阻塞|卡住|故障|失败|异常|告警|注意)[:：-]/i,
  keep: /(^|\s)(\[keep\]|#keep|keep[:：-])/i,
  verify: /\b(pass(?:ed)?|success|ok|验证通过|回归通过|测试通过)\b/i,
  blocker: /\b(block(?:ed|er)?|阻塞|卡住|pending|待处理|failed?|失败)\b/i,
  env: /\b(env|环境变量|配置|config|开关|flag|token|key|secret|权限|proxy|代理)\b/i,
  error: /\b(error|failed?|traceback|exception|unauthorized|timeout|429|401|403|500)\b/i,
  file: /(?:^|[\s(])[~/.][\w./-]+|[\w./-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|json|ya?ml|toml|sh|md)(?::\d+)?/i,
  command: /^\s*(?:[$>#]\s*)?(?:npm|pnpm|yarn|python3?|pytest|ruff|eslint|git|openclaw|codex|bash|zsh)\b/i,
};

function getEventType(event) {
  return String(event?.type || event?.event?.type || "unknown").toLowerCase();
}

function resolveEffectiveEventType(event) {
  const explicitType = getEventType(event);
  if (explicitType !== "unknown") {
    return explicitType;
  }

  // before_prompt_build payload may omit `type` and only provide prompt/messages.
  if (Array.isArray(event?.messages) && event.messages.length > 0) {
    return "before_prompt_build";
  }

  return explicitType;
}

function trimText(text, maxChars = 1600) {
  if (!text || typeof text !== "string") {
    return "";
  }
  if (text.length <= maxChars) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxChars - 15))}\n...[truncated]`;
}

function writeMetric(event, payload = {}) {
  try {
    appendFileSync(
      METRICS_LOG,
      `${JSON.stringify({
        event,
        component: "context_optimizer_hook",
        schema_version: "4.6.0",
        ...payload,
        ts: new Date().toISOString(),
      })}\n`,
      "utf-8"
    );
  } catch (_error) {
    // ignore metrics write failures
  }
}

function extractSessionKey(event) {
  const data = event?.data || {};
  const candidates = [
    event?.sessionKey,
    event?.event?.sessionKey,
    data?.sessionKey,
    data?.session_key,
    data?.session?.key,
    data?.requesterSessionKey,
    data?.callerSessionKey,
    event?.context?.sessionKey,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }
  return null;
}

function readStatusStore() {
  const store = readJson(STATUS_STORE_PATH);
  if (!store || typeof store !== "object") {
    return {};
  }
  return store;
}

function writeStatusStore(store) {
  const dir = STATUS_STORE_PATH.replace(/\/[^/]+$/, "");
  if (dir && !existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(STATUS_STORE_PATH, JSON.stringify(store, null, 2), "utf-8");
}

function stableHash(payload) {
  const text = typeof payload === "string" ? payload : JSON.stringify(payload);
  return createHash("sha1").update(String(text || "")).digest("hex").slice(0, 14);
}

function nowMs() {
  return Date.now();
}

function toIso(ms) {
  if (!Number.isFinite(ms)) {
    return "";
  }
  return new Date(ms).toISOString();
}

function normalizeSessionStateShape(entry) {
  const state = entry && typeof entry === "object" ? entry : {};
  const policy = state.policyV2 && typeof state.policyV2 === "object" ? state.policyV2 : {};
  return {
    sessionKey: state.sessionKey || "",
    lastSummary: typeof policy.lastSummary === "string" ? policy.lastSummary : "",
    lastEventSignature: typeof policy.lastEventSignature === "string" ? policy.lastEventSignature : "",
    l1: policy.l1 && typeof policy.l1 === "object" ? policy.l1 : null,
    l2Records: Array.isArray(policy.l2Records) ? policy.l2Records : [],
    l1ExpiresAtMs: Number(policy.l1ExpiresAtMs || 0),
    updatedAtMs: Number(policy.updatedAtMs || 0),
  };
}

function getSessionPolicyState(store, sessionKey) {
  if (!sessionKey) {
    return normalizeSessionStateShape(null);
  }
  const entry = store && typeof store === "object" ? store[sessionKey] : null;
  const state = normalizeSessionStateShape(entry);
  const now = nowMs();
  if (state.l1ExpiresAtMs > 0 && now > state.l1ExpiresAtMs) {
    state.l1 = null;
    state.l1ExpiresAtMs = 0;
  }
  return state;
}

function writeSmartContextStatus(event, result, hookPhase) {
  try {
    const sessionKey = extractSessionKey(event);
    if (!sessionKey || !result?.ok) {
      return;
    }

    const compressed = result.compressed || {};
    const trigger = result.trigger || {};
    const recentMessages = Array.isArray(compressed.recent) ? compressed.recent.length : 0;
    const keepRounds = Math.floor(recentMessages / 2);

    const store = readStatusStore();
    const prev = getSessionPolicyState(store, sessionKey);
    const policy = compressed.policy_v2 && typeof compressed.policy_v2 === "object" ? compressed.policy_v2 : null;
    const mergedL2 = Array.isArray(prev.l2Records) ? [...prev.l2Records] : [];
    if (policy?.l2_record && typeof policy.l2_record === "object") {
      mergedL2.push(policy.l2_record);
    }
    const compactedL2 = mergedL2.slice(-MAX_L2_RECORDS);

    const l1ExpiresAtMs =
      Number(policy?.l1_expires_at_ms || 0) > 0
        ? Number(policy.l1_expires_at_ms)
        : Number(prev.l1ExpiresAtMs || 0);

    store[sessionKey] = {
      sessionKey,
      hookPhase,
      phase: trigger.phase || PHASE.NONE,
      reason: trigger.reason || "unknown",
      mode: trigger.mode || MODE.GENERAL,
      historyMessages: Number(trigger.historyLength || 0),
      historyRounds: Math.max(1, Math.ceil(Number(trigger.historyLength || 0) / 2)),
      tokenEstimate: Number(trigger.tokenEstimate || 0),
      tokensSaved: Number(compressed.tokens_saved || 0),
      keepMessages: recentMessages,
      keepRounds,
      effectiveRules: compressed.effective_rules || trigger.effectiveRules || null,
      detectedSignals: compressed.mode_signals || [],
      policyV2: {
        version: "2.0",
        updatedAtMs: nowMs(),
        updatedAt: new Date().toISOString(),
        l1: policy?.l1 || prev.l1 || null,
        l1ExpiresAtMs,
        l1ExpiresAt: toIso(l1ExpiresAtMs),
        l2Records: compactedL2,
        lastEventSignature: policy?.event_signature || prev.lastEventSignature || "",
        lastSummary:
          typeof compressed.summary === "string" && compressed.summary.trim()
            ? compressed.summary
            : prev.lastSummary || "",
        lastReplayCommand: policy?.replay || "",
        lastEvents: Array.isArray(policy?.events) ? policy.events : [],
      },
      updatedAt: new Date().toISOString(),
      updatedAtMs: Date.now(),
    };

    writeStatusStore(store);
  } catch (_error) {
    // best-effort only
  }
}

function listAgentNames() {
  try {
    if (!existsSync(AGENTS_ROOT)) {
      return [];
    }
    return readdirSync(AGENTS_ROOT, { withFileTypes: true })
      .filter((entry) => entry?.isDirectory?.())
      .map((entry) => entry.name)
      .filter(Boolean);
  } catch (_error) {
    return [];
  }
}

function resolveSessionFileFromSessionKey(sessionKey) {
  if (typeof sessionKey !== "string" || !sessionKey.trim()) {
    return null;
  }

  const key = sessionKey.trim();
  const agentMatch = key.match(/^agent:([^:]+):/i);
  const agentCandidates = [];

  if (agentMatch?.[1]) {
    agentCandidates.push(agentMatch[1]);
  }

  for (const name of listAgentNames()) {
    if (!agentCandidates.includes(name)) {
      agentCandidates.push(name);
    }
  }

  for (const agentName of agentCandidates) {
    const indexPath = join(AGENTS_ROOT, agentName, "sessions", "sessions.json");
    const index = readJson(indexPath);
    if (!index || typeof index !== "object") {
      continue;
    }
    const entry = index[key];
    const sessionFile = typeof entry?.sessionFile === "string" ? entry.sessionFile.trim() : "";
    if (!sessionFile || !existsSync(sessionFile)) {
      continue;
    }
    return sessionFile;
  }

  return null;
}

function parseSessionMessageRecord(record) {
  if (!record || typeof record !== "object" || record.type !== "message") {
    return null;
  }
  const message = record.message;
  const role = typeof message?.role === "string" ? message.role.trim().toLowerCase() : "";
  if (!role || message?.content == null) {
    return null;
  }
  return {
    role,
    content: message.content,
  };
}

function loadSessionHistoryFromFile(sessionFile) {
  if (!sessionFile || !existsSync(sessionFile)) {
    return [];
  }

  let raw = "";
  try {
    raw = readFileSync(sessionFile, "utf-8");
  } catch (_error) {
    return [];
  }
  if (!raw) {
    return [];
  }

  const lines = raw.split("\n");
  const start = Math.max(0, lines.length - SESSION_FALLBACK_MAX_SCAN_LINES);
  const recent = [];

  for (let i = lines.length - 1; i >= start; i -= 1) {
    const line = lines[i]?.trim();
    if (!line || line[0] !== "{") {
      continue;
    }

    let record = null;
    try {
      record = JSON.parse(line);
    } catch (_error) {
      continue;
    }

    const parsed = parseSessionMessageRecord(record);
    if (!parsed) {
      continue;
    }
    recent.push(parsed);
    if (recent.length >= SESSION_FALLBACK_MAX_MESSAGES) {
      break;
    }
  }

  return recent.reverse();
}

function normalizeMessages(messages) {
  if (!Array.isArray(messages)) {
    return [];
  }

  return messages
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const role = String(item.role || "unknown").toLowerCase();
      let content = item.content || "";

      if (Array.isArray(content)) {
        content = content
          .map((part) => {
            if (typeof part === "string") {
              return part;
            }
            if (part && typeof part === "object") {
              if (typeof part.text === "string") {
                return part.text;
              }
              if (typeof part.content === "string") {
                return part.content;
              }
            }
            return "";
          })
          .filter(Boolean)
          .join("\n");
      }

      if (typeof content !== "string") {
        content = JSON.stringify(content);
      }

      content = content.trim();
      if (!content) {
        return null;
      }

      return { role, content };
    })
    .filter(Boolean);
}

function toModelSafeMessages(messages) {
  return normalizeMessages(messages)
    .map((m) => {
      const role = String(m.role || "assistant").toLowerCase();
      let safeRole = "assistant";
      if (role === "system" || role === "user" || role === "assistant") {
        safeRole = role;
      }
      return {
        role: safeRole,
        content: String(m.content || "").trim(),
      };
    })
    .filter((m) => m.content.length > 0);
}

function estimateTokens(messages) {
  const rows = typeof messages === "string" ? [{ content: messages }] : messages;
  let total = 0;

  for (const row of rows || []) {
    const raw = row?.content || "";
    const text = typeof raw === "string" ? raw : JSON.stringify(raw);

    const english = (text.match(/[a-zA-Z0-9]/g) || []).length;
    const chinese = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const other = text.length - english - chinese;

    total += english / 4 + chinese / 2 + other / 4;
  }

  return Math.floor(total);
}

function clampNumber(value, min, max) {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.max(min, Math.min(max, value));
}

function sanitizeSensitiveText(text) {
  let safe = String(text || "");
  safe = safe.replace(/(sk-[a-z0-9_-]{10,})/gi, "<SECRET_REF:sk>");
  safe = safe.replace(
    /\b(api[_-]?key|secret|token|passphrase|private[_-]?key|authorization)\b\s*[:=]\s*([^\s,;]+)/gi,
    "$1=<SECRET_REF>"
  );
  safe = safe.replace(/\b[A-Fa-f0-9]{32,}\b/g, "<SECRET_REF:hex>");
  safe = safe.replace(/\b[A-Za-z0-9+/=]{48,}\b/g, "<SECRET_REF:blob>");
  return safe;
}

function normalizeSummaryLine(line, maxChars = 220) {
  const compact = String(line || "")
    .replace(/^[\s>*-]+/, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!compact) {
    return "";
  }
  return sanitizeSensitiveText(trimText(compact, maxChars));
}

function dedupeLines(lines, maxItems) {
  const seen = new Set();
  const out = [];
  for (const line of lines || []) {
    const normalized = normalizeSummaryLine(line);
    if (!normalized) {
      continue;
    }
    const key = normalized.toLowerCase();
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    out.push(normalized);
    if (out.length >= maxItems) {
      break;
    }
  }
  return out;
}

function extractFileHints(text, maxItems = 4) {
  const source = String(text || "");
  const matches = source.match(/(?:~\/|\/)[\w./-]+|[\w./-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|json|ya?ml|toml|sh|md)(?::\d+)?/gi) || [];
  return dedupeLines(matches, maxItems);
}

function detectConversationMode(messages) {
  if (CONFIG.mode === MODE.CODING || CONFIG.mode === MODE.GENERAL) {
    return {
      mode: CONFIG.mode,
      score: CONFIG.mode === MODE.CODING ? 99 : 0,
      matchedSignals: [`forced:${CONFIG.mode}`],
      source: "config",
    };
  }

  const normalized = normalizeMessages(messages);
  const recent = normalized.slice(-MODE_RECENT_MESSAGES);
  let score = 0;
  const matchedSignals = [];

  for (const msg of recent) {
    const content = String(msg.content || "");
    for (const rule of CODING_SIGNAL_RULES) {
      if (rule.regex.test(content)) {
        score += Number(rule.weight || 1);
        if (!matchedSignals.includes(rule.name)) {
          matchedSignals.push(rule.name);
        }
      }
    }
  }

  return {
    mode: score >= CODING_MIN_SCORE ? MODE.CODING : MODE.GENERAL,
    score,
    matchedSignals: matchedSignals.slice(0, 8),
    source: "auto",
  };
}

function resolveEffectiveRules(modeContext) {
  const mode = modeContext?.mode === MODE.CODING ? MODE.CODING : MODE.GENERAL;
  const offsets = MODE_PROFILE_OFFSETS[mode] || MODE_PROFILE_OFFSETS[MODE.GENERAL];

  const preserveRecent = Math.floor(clampNumber(CONFIG.preserveRecent + offsets.preserveRecent, 4, 28));
  const summaryRounds = Math.floor(
    clampNumber(CONFIG.compressionThreshold + offsets.summaryRounds, preserveRecent + 4, 72)
  );
  const compressAfterRounds = Math.floor(
    clampNumber(CONFIG.compressAfterRounds + offsets.compressAfterRounds, summaryRounds + 6, 120)
  );
  const tokenTriggerEstimate = Math.max(1200, Math.floor(CONFIG.tokenTriggerEstimate * offsets.tokenTriggerScale));
  const triggerSoftRatio = clampNumber(CONFIG.triggerSoftRatio + offsets.triggerSoftDelta, 0.55, 0.92);
  const triggerHardRatio = clampNumber(CONFIG.triggerHardRatio + offsets.triggerHardDelta, triggerSoftRatio + 0.08, 0.98);

  return {
    mode,
    preserveRecent,
    summaryRounds,
    compressAfterRounds,
    tokenTriggerEstimate,
    triggerSoftRatio,
    triggerHardRatio,
  };
}

function pickFirstNonEmpty(values, fallback = "") {
  for (const item of values || []) {
    const text = normalizeSummaryLine(item, 220);
    if (text) {
      return text;
    }
  }
  return fallback;
}

function detectLifecycleStatus(handoff) {
  const hasVerification = Array.isArray(handoff.verification) && handoff.verification.length > 0;
  const hasBlocker = Array.isArray(handoff.blockers) && handoff.blockers.length > 0;
  const hasProgress = Array.isArray(handoff.progress) && handoff.progress.length > 0;
  const hasIntent = Array.isArray(handoff.taskIntent) && handoff.taskIntent.length > 0;

  if (hasBlocker) {
    return "blocked";
  }
  if (hasVerification && !hasBlocker) {
    return "validated";
  }
  if (hasProgress) {
    return "in-progress";
  }
  if (hasIntent) {
    return "start";
  }
  return "unknown";
}

function detectRiskLevel(handoff, status) {
  if (status === "blocked") {
    return "H";
  }
  const riskText = [...(handoff.risks || []), ...(handoff.blockers || [])].join(" ").toLowerCase();
  if (/\b(no risk|none|n\/a|无风险|无)\b/.test(riskText)) {
    return "L";
  }
  if (/\b(401|403|429|500|timeout|unauthorized|panic|exception|failed)\b/.test(riskText)) {
    return "H";
  }
  if ((handoff.risks || []).length > 0) {
    return "M";
  }
  return "L";
}

function extractOwnerAndEta(handoff, sessionKey) {
  const fromText = [...(handoff.keep || []), ...(handoff.constraints || []), ...(handoff.progress || [])];
  let owner = "";
  let eta = "";

  for (const line of fromText) {
    if (!owner) {
      const m = line.match(/\b(owner|assignee|负责人)\s*[:：-]\s*([a-zA-Z0-9._-]{2,64})/i);
      if (m?.[2]) {
        owner = m[2].trim();
      }
    }
    if (!eta) {
      const m = line.match(/\b(eta|deadline|预计|完成时间)\s*[:：-]\s*([^\s,;]{2,40})/i);
      if (m?.[2]) {
        eta = m[2].trim();
      }
    }
    if (owner && eta) {
      break;
    }
  }

  if (!owner && typeof sessionKey === "string") {
    const agent = sessionKey.match(/^agent:([^:]+):/i)?.[1];
    if (agent) {
      owner = agent;
    }
  }
  if (!owner) {
    owner = "unknown";
  }
  if (!eta) {
    eta = "unknown";
  }

  return { owner, eta };
}

function buildEvidencePointers(handoff, historyInfo) {
  const pointers = [];
  for (const file of handoff.files || []) {
    pointers.push(file);
    if (pointers.length >= 5) {
      break;
    }
  }
  for (const cmd of handoff.commands || []) {
    pointers.push(`cmd:${cmd}`);
    if (pointers.length >= 8) {
      break;
    }
  }
  if (historyInfo?.sessionFile) {
    pointers.push(`session:${historyInfo.sessionFile}`);
  }
  return dedupeLines(pointers, 8);
}

function buildReplayCommand(handoff, historyInfo, sessionKey) {
  const cmd = pickFirstNonEmpty(handoff.commands || [], "");
  if (cmd) {
    return cmd;
  }
  if (historyInfo?.sessionFile) {
    return `tail -n 200 "${historyInfo.sessionFile}"`;
  }
  if (sessionKey) {
    return `rg -n "${sessionKey}" ~/.openclaw/logs/gateway.err.log | tail -n 120`;
  }
  return `tail -n 120 ~/.openclaw/logs/gateway.err.log`;
}

function buildL2Candidate(handoff, evidencePointers) {
  const decision = pickFirstNonEmpty([...(handoff.keep || []), ...(handoff.progress || [])], "");
  const why = pickFirstNonEmpty(handoff.risks || [], "not explicitly stated");
  const constraint = pickFirstNonEmpty(handoff.constraints || [], "none");
  const evidence = pickFirstNonEmpty(evidencePointers || [], "");
  const reversal = pickFirstNonEmpty(handoff.nextSteps || [], "revisit when blocker clears");
  return {
    decision,
    why,
    constraint,
    evidence,
    reversal,
  };
}

function scoreL2Candidate(candidate, previousRecords) {
  if (!candidate || !candidate.decision) {
    return { score: 0, reasons: [] };
  }
  let score = 0;
  const reasons = [];
  const text = `${candidate.decision} ${candidate.why} ${candidate.constraint}`.toLowerCase();

  if (/\b(architecture|provider|model|transformer|framework|接口|链路|策略|方案)\b/.test(text)) {
    score += 2;
    reasons.push("+2 architecture/tool-choice impact");
  }

  const prev = Array.isArray(previousRecords) ? previousRecords : [];
  if (prev.some((x) => String(x?.decision || "").toLowerCase() === text.toLowerCase())) {
    score += 1;
    reasons.push("+1 repeated decision");
  }

  if (/\b(prevent|fix|guard|risk|401|403|timeout|故障|风险|修复|防止)\b/.test(text)) {
    score += 1;
    reasons.push("+1 risk prevention");
  }

  if (/\b(prefer|must|禁止|偏好|约束|required)\b/.test(text)) {
    score += 1;
    reasons.push("+1 stable preference/constraint");
  }

  if (/\b(temp|temporary|today|once|临时|一次性)\b/.test(text)) {
    score -= 1;
    reasons.push("-1 likely stale");
  }

  if (!candidate.evidence) {
    score -= 1;
    reasons.push("-1 missing evidence");
  }

  return { score, reasons };
}

function buildEventSignature(payload) {
  return stableHash({
    status: payload.status,
    decision: payload.decisions?.[0] || "",
    blocker: payload.blocker || "",
    verification: payload.verification || "",
    next: payload.next || "",
  });
}

function detectPolicyEvents(previousState, currentState, triggerReason) {
  const events = [];
  const currentSignature = buildEventSignature(currentState);
  const hasPrevious = Boolean(previousState && previousState.lastEventSignature);
  if (!hasPrevious) {
    events.push("status_changed:start");
  } else if (previousState?.l1?.status !== currentState.status) {
    events.push(`status_changed:${previousState?.l1?.status || "none"}->${currentState.status}`);
  }
  if (
    hasPrevious &&
    previousState?.l1?.blocker !== currentState.blocker &&
    currentState.blocker &&
    currentState.blocker !== "none"
  ) {
    events.push("new_blocker");
  }
  if (hasPrevious && previousState?.l1?.decisionTop1 !== currentState.decisionTop1) {
    events.push("decision_changed");
  }
  if (
    hasPrevious &&
    previousState?.l1?.verification !== currentState.verification &&
    currentState.verification !== "none"
  ) {
    events.push("validation_result");
  }
  if (/compress-after-rounds|hard-ratio/.test(String(triggerReason || ""))) {
    events.push("phase_complete");
  }
  if (hasPrevious && previousState.lastEventSignature !== currentSignature) {
    events.push("state_changed");
  }
  if (events.length === 0) {
    events.push("none");
  }
  return dedupeLines(events, 6);
}

function shouldForceSummaryRefresh(triggerReason, hasPreviousSummary) {
  if (!hasPreviousSummary) {
    return true;
  }
  const reason = String(triggerReason || "");
  return /token:hard-ratio|smart:compress-after-rounds/.test(reason);
}

function compactLine(text, maxChars = 220) {
  return normalizeSummaryLine(text, maxChars) || "none";
}

function buildPolicyV2Summary(payload) {
  const decisions = (payload.decisions || []).slice(0, 3).map((x, idx) => `${idx + 1}) ${compactLine(x, 90)}`);
  const evidence = (payload.evidence || []).slice(0, 3).map((x) => compactLine(x, 72));
  const events = (payload.events || []).slice(0, 3).join(", ") || "none";
  const replay = compactLine(payload.replay || "", 180);
  const next = compactLine(payload.next || "", 180);

  const lines = [
    "=== Context Policy v2 ===",
    `State: ${compactLine(payload.state, 180)}`,
    `Decisions: ${decisions.length ? decisions.join(" | ") : "none"}`,
    `Blocker: ${compactLine(payload.blocker || "none", 180)}`,
    `Replay: ${replay}`,
    `Next: ${next}`,
    `L1: Goal=${compactLine(payload.goal, 64)} | Now=${compactLine(payload.now, 64)} | Owner=${compactLine(payload.owner, 48)} | ETA=${compactLine(payload.eta, 48)} | Risk=${compactLine(payload.risk, 8)}`,
    `L2: ${compactLine(payload.l2, 220)}`,
    `Evidence: ${evidence.length ? evidence.join(" | ") : "none"}`,
    `Events: ${events}; Trigger=${compactLine(payload.triggerReason || "none", 64)}; Mode=${compactLine(payload.mode || MODE.GENERAL, 16)}`,
    `TTL: L1 expires ${compactLine(payload.ttl || "unknown", 48)}; session=${compactLine(payload.sessionKey || "n/a", 72)}`,
    "=== End Context Policy v2 ===",
  ];

  return lines.slice(0, 12).join("\n");
}

function extractHandoffData(messages) {
  const taskIntent = [];
  const progress = [];
  const constraints = [];
  const risks = [];
  const keep = [];
  const verification = [];
  const blockers = [];
  const files = [];
  const commands = [];
  const nextSteps = [];

  for (const msg of messages || []) {
    const role = String(msg?.role || "").toLowerCase();
    const content = String(msg?.content || "");
    const cleanedContent = sanitizeSensitiveText(content);
    const lines = cleanedContent
      .split("\n")
      .map((line) => normalizeSummaryLine(line, 260))
      .filter(Boolean);

    if (role === "user" && cleanedContent.trim().length > 24) {
      taskIntent.push(`User request: ${normalizeSummaryLine(cleanedContent, 220)}`);
    }

    for (const line of lines) {
      if (SUMMARY_PATTERNS.keep.test(line)) {
        keep.push(line.replace(/\[keep\]|#keep|keep[:：-]/gi, "").trim());
      }
      if (SUMMARY_PATTERNS.next.test(line)) {
        nextSteps.push(line);
      }
      if (SUMMARY_PATTERNS.risk.test(line) || SUMMARY_PATTERNS.error.test(line)) {
        risks.push(line);
      }
      if (SUMMARY_PATTERNS.verify.test(line)) {
        verification.push(line);
      }
      if (SUMMARY_PATTERNS.blocker.test(line)) {
        blockers.push(line);
      }
      if (SUMMARY_PATTERNS.env.test(line)) {
        constraints.push(line);
      }
      if (SUMMARY_PATTERNS.decision.test(line) || /\b(done|completed|implemented|fixed|updated|已完成|已修复|已更新)\b/i.test(line)) {
        progress.push(line);
      }
      if (SUMMARY_PATTERNS.command.test(line)) {
        commands.push(line);
      }
      if (SUMMARY_PATTERNS.file.test(line)) {
        files.push(...extractFileHints(line, 2));
      }
    }
  }

  const normalizedIntent = dedupeLines(taskIntent, 3);
  const normalizedProgress = dedupeLines(progress, 6);
  const normalizedConstraints = dedupeLines(constraints, 5);
  const normalizedRisks = dedupeLines(risks, 5);
  const normalizedKeep = dedupeLines(keep, 6);
  const normalizedVerification = dedupeLines(verification, 4);
  const normalizedBlockers = dedupeLines(blockers, 4);
  const normalizedFiles = dedupeLines(files, 8);
  const normalizedCommands = dedupeLines(commands, 6);
  const normalizedNext = dedupeLines(nextSteps, 5);

  const keyPointCount =
    normalizedIntent.length +
    normalizedProgress.length +
    normalizedConstraints.length +
    normalizedRisks.length +
    normalizedKeep.length +
    normalizedVerification.length +
    normalizedBlockers.length +
    normalizedFiles.length +
    normalizedCommands.length +
    normalizedNext.length;

  return {
    taskIntent: normalizedIntent,
    progress: normalizedProgress,
    constraints: normalizedConstraints,
    risks: normalizedRisks,
    keep: normalizedKeep,
    verification: normalizedVerification,
    blockers: normalizedBlockers,
    files: normalizedFiles,
    commands: normalizedCommands,
    nextSteps: normalizedNext,
    keyPointCount,
  };
}

function appendSection(lines, title, entries, fallback) {
  lines.push(`${title}:`);
  if (!entries || entries.length === 0) {
    lines.push(`- ${fallback}`);
    lines.push("");
    return;
  }
  for (const entry of entries) {
    lines.push(`- ${entry}`);
  }
  lines.push("");
}

function buildSummary(totalCompressedRounds, handoff, modeContext, effectiveRules, options = {}) {
  const sessionKey = options.sessionKey || "unknown";
  const previousState = options.previousPolicyState || null;
  const historyInfo = options.historyInfo || null;
  const triggerReason = options.triggerReason || "unknown";
  const status = detectLifecycleStatus(handoff);
  const risk = detectRiskLevel(handoff, status);
  const ownerEta = extractOwnerAndEta(handoff, sessionKey);
  const goal = pickFirstNonEmpty([...(handoff.keep || []), ...(handoff.taskIntent || [])], "none");
  const now = pickFirstNonEmpty([...(handoff.progress || []), ...(handoff.taskIntent || [])], "none");
  const blocker = pickFirstNonEmpty([...(handoff.blockers || []), ...(handoff.risks || [])], "none");
  const next = pickFirstNonEmpty([...(handoff.nextSteps || []), ...(handoff.commands || [])], "none");
  const evidencePointers = buildEvidencePointers(handoff, historyInfo);
  const replay = buildReplayCommand(handoff, historyInfo, sessionKey);
  const l2Candidate = buildL2Candidate(handoff, evidencePointers);
  const l2Score = scoreL2Candidate(l2Candidate, previousState?.l2Records || []);
  const ttlMs = nowMs() + RUNTIME_STATE_TTL_MS;
  const stateLine = `${status}; blocker=${blocker}; risk=${risk}`;

  const currentEventPayload = {
    status,
    decisions: [l2Candidate.decision].filter(Boolean),
    blocker,
    verification: pickFirstNonEmpty(handoff.verification || [], "none"),
    next,
  };
  const eventSignature = buildEventSignature(currentEventPayload);
  const events = detectPolicyEvents(previousState, {
    ...currentEventPayload,
    decisionTop1: l2Candidate.decision || "none",
  }, triggerReason);
  const hasEvent = events.some((x) => x !== "none");
  const forceRefresh = shouldForceSummaryRefresh(triggerReason, Boolean(previousState?.lastSummary));
  const shouldRefreshSummary = hasEvent || forceRefresh;

  const l2RecordEligible = l2Score.score >= 3 && Boolean(l2Candidate.evidence);
  const l2Record = l2RecordEligible && hasEvent
    ? {
        id: `${new Date().toISOString()}-${stableHash({ eventSignature, decision: l2Candidate.decision })}`,
        ts: new Date().toISOString(),
        score: l2Score.score,
        score_reasons: l2Score.reasons,
        decision: l2Candidate.decision,
        why: l2Candidate.why,
        constraint: l2Candidate.constraint,
        evidence: l2Candidate.evidence,
        reversal_condition: l2Candidate.reversal,
        event: events[0] || "none",
      }
    : null;

  const summaryPayload = {
    state: stateLine,
    decisions: dedupeLines(
      [
        ...(handoff.keep || []).slice(0, 1),
        l2Candidate.decision,
        ...(handoff.progress || []).slice(0, 2),
      ],
      3
    ),
    blocker,
    replay,
    next,
    goal,
    now,
    owner: ownerEta.owner,
    eta: ownerEta.eta,
    risk,
    l2:
      l2RecordEligible && l2Record
        ? `${l2Record.decision} | why=${l2Record.why} | evidence=${l2Record.evidence} | reversal=${l2Record.reversal_condition}`
        : "No durable decision record (score < 3 or no evidence).",
    evidence: evidencePointers,
    events,
    triggerReason,
    mode: modeContext?.mode || MODE.GENERAL,
    ttl: toIso(ttlMs),
    sessionKey,
  };
  const generatedSummary = buildPolicyV2Summary(summaryPayload);
  const summary =
    shouldRefreshSummary || !previousState?.lastSummary
      ? generatedSummary
      : previousState.lastSummary;

  return {
    summary,
    policy: {
      version: "2.0",
      totalCompressedRounds,
      state: summaryPayload.state,
      events,
      event_signature: eventSignature,
      refreshed: shouldRefreshSummary,
      replay,
      l1: {
        goal,
        now,
        blocker,
        next,
        owner: ownerEta.owner,
        eta: ownerEta.eta,
        risk,
        status,
        decisionTop1: l2Candidate.decision || "none",
        verification: currentEventPayload.verification,
      },
      l1_expires_at_ms: ttlMs,
      l2_score: l2Score.score,
      l2_record: l2Record,
      evidence: evidencePointers,
      one_change_one_record: l2Record ? true : false,
      no_evidence_no_memory: Boolean(l2Record && l2Record.evidence),
    },
  };
}

function compressHistory(messages, preserveRecent = CONFIG.preserveRecent, options = {}) {
  const normalized = normalizeMessages(messages);
  const totalMessages = normalized.length;
  const preserveRecentMessages = roundsToMessageCount(preserveRecent);

  if (totalMessages <= preserveRecentMessages) {
    return {
      success: true,
      compressed: {
        type: PHASE.NONE,
        original_count: totalMessages,
        compressed_count: totalMessages,
        recent: normalized,
        summary: null,
        tokens_saved: 0,
        compression_ratio: 0,
      },
    };
  }

  const recent = normalized.slice(-preserveRecentMessages);
  const toCompress = normalized.slice(0, -preserveRecentMessages);
  const handoff = extractHandoffData(toCompress);
  const summaryBuild = buildSummary(
    Math.max(1, Math.ceil(toCompress.length / 2)),
    handoff,
    options.modeContext || { mode: MODE.GENERAL, matchedSignals: [] },
    options.effectiveRules || resolveEffectiveRules({ mode: MODE.GENERAL }),
    options
  );
  const summary = summaryBuild.summary;

  const originalTokens = estimateTokens(toCompress);
  const summaryTokens = estimateTokens(summary);
  const tokensSaved = originalTokens - summaryTokens;

  return {
    success: true,
    compressed: {
      type: PHASE.COMPRESSED,
      original_count: toCompress.length,
      compressed_count: 1,
      recent,
      summary,
      key_points_count: handoff.keyPointCount,
      original_tokens: originalTokens,
      summary_tokens: summaryTokens,
      tokens_saved: tokensSaved,
      compression_ratio: originalTokens > 0 ? tokensSaved / originalTokens : 0,
      mode: options.modeContext?.mode || MODE.GENERAL,
      mode_signals: options.modeContext?.matchedSignals || [],
      effective_rules: options.effectiveRules || null,
      policy_v2: summaryBuild.policy || null,
    },
  };
}

function getHistoryFromData(data) {
  if (Array.isArray(data?.sessionHistory) && data.sessionHistory.length > 0) {
    return data.sessionHistory;
  }
  if (Array.isArray(data?.last_messages) && data.last_messages.length > 0) {
    return data.last_messages;
  }
  if (Array.isArray(data?.messages) && data.messages.length > 0) {
    return data.messages;
  }
  return [];
}

function getHistoryFromEvent(event) {
  if (Array.isArray(event?.messages) && event.messages.length > 0) {
    return event.messages;
  }
  if (Array.isArray(event?.historyMessages) && event.historyMessages.length > 0) {
    return event.historyMessages;
  }
  if (Array.isArray(event?.last_messages) && event.last_messages.length > 0) {
    return event.last_messages;
  }
  return getHistoryFromData(event?.data || {});
}

function getHistoryForCompression(event, hookPhase) {
  const directHistory = getHistoryFromEvent(event);
  const directCount = normalizeMessages(directHistory).length;
  const minMessagesForCompression = getPreserveRecentMessageCount() + 1;
  const phase = String(hookPhase || "").toLowerCase();
  const allowSessionFallback = phase === "before_prompt_build" || phase === "agent:input" || phase === "input";

  if (!allowSessionFallback || directCount >= minMessagesForCompression) {
    return {
      history: directHistory,
      source: "event",
      fallbackUsed: false,
      directCount,
      resolvedCount: directCount,
    };
  }

  const sessionKey = extractSessionKey(event);
  if (!sessionKey) {
    return {
      history: directHistory,
      source: "event",
      fallbackUsed: false,
      directCount,
      resolvedCount: directCount,
    };
  }

  const sessionFile = resolveSessionFileFromSessionKey(sessionKey);
  if (!sessionFile) {
    return {
      history: directHistory,
      source: "event",
      fallbackUsed: false,
      directCount,
      resolvedCount: directCount,
      sessionKey,
    };
  }

  const fallbackHistory = loadSessionHistoryFromFile(sessionFile);
  const fallbackCount = normalizeMessages(fallbackHistory).length;
  if (fallbackCount <= directCount) {
    return {
      history: directHistory,
      source: "event",
      fallbackUsed: false,
      directCount,
      resolvedCount: directCount,
      sessionKey,
      sessionFile,
    };
  }

  return {
    history: fallbackHistory,
    source: "session-file",
    fallbackUsed: true,
    directCount,
    resolvedCount: fallbackCount,
    sessionKey,
    sessionFile,
  };
}

function evaluateTrigger(event, messages, effectiveRules, modeContext) {
  const normalized = normalizeMessages(messages);
  const historyLength = normalized.length;
  const tokenEstimate = estimateTokens(normalized);
  const preserveRecentMessages = roundsToMessageCount(effectiveRules.preserveRecent);

  if (historyLength <= preserveRecentMessages) {
    return {
      shouldCompress: false,
      phase: PHASE.NONE,
      reason: "below-preserve-recent",
      mode: effectiveRules.mode,
      historyLength,
      tokenEstimate,
      messages: normalized,
      effectiveRules,
      modeScore: Number(modeContext?.score || 0),
      modeSignals: modeContext?.matchedSignals || [],
    };
  }

  // 0) Token-waterline fallback (70/85). Apply even before rounds rules.
  // Keep preserveRecent semantics: we compress older history, not the most recent turns.
  const usageRatio = readUsageRatio(event);
  if (usageRatio != null) {
    if (usageRatio >= Number(effectiveRules.triggerHardRatio || 0.85)) {
      return {
        shouldCompress: true,
        phase: PHASE.COMPRESSED,
        reason: "token:hard-ratio",
        mode: effectiveRules.mode,
        historyLength,
        tokenEstimate,
        messages: normalized,
        effectiveRules,
        modeScore: Number(modeContext?.score || 0),
        modeSignals: modeContext?.matchedSignals || [],
      };
    }
    if (usageRatio >= Number(effectiveRules.triggerSoftRatio || 0.7)) {
      return {
        shouldCompress: true,
        phase: PHASE.SUMMARY,
        reason: "token:soft-ratio",
        mode: effectiveRules.mode,
        historyLength,
        tokenEstimate,
        messages: normalized,
        effectiveRules,
        modeScore: Number(modeContext?.score || 0),
        modeSignals: modeContext?.matchedSignals || [],
      };
    }
  }


  // 1) Smart Context tier rules first.
  // NOTE: historyLength counts messages, not turns. We approximate turns as message pairs.
  const estimatedRounds = Math.max(1, Math.ceil(historyLength / 2));
  if (effectiveRules.compressAfterRounds > 0 && estimatedRounds > effectiveRules.compressAfterRounds) {
    return {
      shouldCompress: true,
      phase: PHASE.COMPRESSED,
      reason: "smart:compress-after-rounds",
      mode: effectiveRules.mode,
      historyLength,
      tokenEstimate,
      messages: normalized,
      effectiveRules,
      modeScore: Number(modeContext?.score || 0),
      modeSignals: modeContext?.matchedSignals || [],
    };
  }
  if (effectiveRules.summaryRounds > 0 && estimatedRounds > effectiveRules.summaryRounds) {
    return {
      shouldCompress: true,
      phase: PHASE.COMPRESSED,
      reason: "smart:intelligent-compress-rounds",
      mode: effectiveRules.mode,
      historyLength,
      tokenEstimate,
      messages: normalized,
      effectiveRules,
      modeScore: Number(modeContext?.score || 0),
      modeSignals: modeContext?.matchedSignals || [],
    };
  }
  if (effectiveRules.preserveRecent > 0 && estimatedRounds > effectiveRules.preserveRecent) {
    return {
      shouldCompress: true,
      phase: PHASE.SUMMARY,
      reason: "smart:summary-window-rounds",
      mode: effectiveRules.mode,
      historyLength,
      tokenEstimate,
      messages: normalized,
      effectiveRules,
      modeScore: Number(modeContext?.score || 0),
      modeSignals: modeContext?.matchedSignals || [],
    };
  }

  // 2) Fallback triggers (token estimate thresholds).
  const byHistory = estimatedRounds > effectiveRules.summaryRounds;
  const byToken = tokenEstimate >= Number(effectiveRules.tokenTriggerEstimate || 0);

  if (!byHistory && !byToken) {
    return {
      shouldCompress: false,
      phase: PHASE.NONE,
      reason: "below-threshold",
      mode: effectiveRules.mode,
      historyLength,
      tokenEstimate,
      messages: normalized,
      effectiveRules,
      modeScore: Number(modeContext?.score || 0),
      modeSignals: modeContext?.matchedSignals || [],
    };
  }

  return {
    shouldCompress: true,
    phase: byHistory ? PHASE.COMPRESSED : PHASE.SUMMARY,
    reason: byHistory ? "history-threshold" : "token-threshold",
    mode: effectiveRules.mode,
    historyLength,
    tokenEstimate,
    messages: normalized,
    effectiveRules,
    modeScore: Number(modeContext?.score || 0),
    modeSignals: modeContext?.matchedSignals || [],
  };
}

function buildSnapshot(compressed) {
  if (!compressed?.summary) {
    return "";
  }

  const recent = Array.isArray(compressed.recent) ? compressed.recent : [];
  const recentDigest = recent
    .slice(-3)
    .map((m) => `[${m.role}] ${trimText(m.content, 180)}`)
    .join("\n");

  return [
    "=== Smart Context Snapshot ===",
    trimText(String(compressed.summary), 1200),
    recentDigest ? `\n=== Recent Turns Digest ===\n${recentDigest}` : "",
    "=== End Snapshot ===",
  ]
    .filter(Boolean)
    .join("\n");
}

function runCompression(event, messages, context = {}) {
  const modeContext = detectConversationMode(messages);
  const effectiveRules = resolveEffectiveRules(modeContext);
  const trigger = evaluateTrigger(event, messages, effectiveRules, modeContext);
  const sessionKey = extractSessionKey(event) || context.sessionKey || "";
  const store = readStatusStore();
  const previousPolicyState = getSessionPolicyState(store, sessionKey);
  if (!trigger.shouldCompress) {
    return { ok: false, trigger, modeContext, effectiveRules, sessionKey, previousPolicyState };
  }

  const result = compressHistory(trigger.messages, effectiveRules.preserveRecent, {
    modeContext,
    effectiveRules,
    historyInfo: context.historyInfo || null,
    hookPhase: context.hookPhase || "unknown",
    triggerReason: trigger.reason,
    sessionKey,
    previousPolicyState,
  });
  if (!result?.success || !result?.compressed) {
    return { ok: false, trigger, modeContext, effectiveRules, sessionKey, previousPolicyState };
  }

  return {
    ok: true,
    trigger,
    compressed: result.compressed,
    modeContext,
    effectiveRules,
    sessionKey,
    previousPolicyState,
  };
}

function logCompression(result, source) {
  if (!CONFIG.verbose || !result?.ok) {
    return;
  }

  const { trigger, compressed } = result;
  const saved = compressed.tokens_saved || 0;
  const ratio = compressed.compression_ratio || 0;

  console.log(
    `📦 Context Optimizer (${source}): mode=${trigger.mode || MODE.GENERAL} phase=${trigger.phase} reason=${trigger.reason} history=${trigger.historyLength} estTokens=${trigger.tokenEstimate}`
  );
  const keptMessages = Array.isArray(compressed.recent) ? compressed.recent.length : 0;
  const keptRounds = Math.floor(keptMessages / 2);
  console.log(`✅ 保留最近 ${keptRounds} 轮 (${keptMessages} 条, ${estimateTokens(compressed.recent || [])} tokens)`);
  if (compressed.type === PHASE.COMPRESSED) {
    console.log(`📝 压缩 ${compressed.original_count} 条 → 摘要 (${saved} tokens, ${(ratio * 100).toFixed(0)}%节省)`);
  }
}

function writeCompactionMetric(event, hookPhase, result, historyInfo = null) {
  const policy = result?.compressed?.policy_v2 || null;
  const payload = {
    hook_phase: hookPhase,
    reason: result?.trigger?.reason,
    mode: result?.trigger?.mode || MODE.GENERAL,
    mode_score: Number(result?.trigger?.modeScore || 0),
    mode_signals: result?.trigger?.modeSignals || [],
    history_length: result?.trigger?.historyLength,
    token_estimate: result?.trigger?.tokenEstimate,
    tokens_saved: result?.compressed?.tokens_saved || 0,
    effective_preserve_recent: Number(result?.effectiveRules?.preserveRecent || result?.trigger?.effectiveRules?.preserveRecent || 0),
    effective_summary_rounds: Number(result?.effectiveRules?.summaryRounds || result?.trigger?.effectiveRules?.summaryRounds || 0),
    effective_compress_after_rounds: Number(
      result?.effectiveRules?.compressAfterRounds || result?.trigger?.effectiveRules?.compressAfterRounds || 0
    ),
    effective_token_trigger_estimate: Number(
      result?.effectiveRules?.tokenTriggerEstimate || result?.trigger?.effectiveRules?.tokenTriggerEstimate || 0
    ),
    effective_trigger_soft_ratio: Number(
      result?.effectiveRules?.triggerSoftRatio || result?.trigger?.effectiveRules?.triggerSoftRatio || 0
    ),
    effective_trigger_hard_ratio: Number(
      result?.effectiveRules?.triggerHardRatio || result?.trigger?.effectiveRules?.triggerHardRatio || 0
    ),
    policy_v2_refreshed: Boolean(policy?.refreshed),
    policy_v2_events: Array.isArray(policy?.events) ? policy.events : [],
    policy_v2_l2_score: Number(policy?.l2_score || 0),
    policy_v2_l2_written: Boolean(policy?.l2_record),
    policy_v2_replay: typeof policy?.replay === "string" ? policy.replay : "",
  };
  const sessionKey = extractSessionKey(event);
  if (sessionKey) {
    payload.session_key = sessionKey;
  }
  if (historyInfo && typeof historyInfo === "object") {
    payload.history_source = historyInfo.source || "event";
    payload.fallback_used = Boolean(historyInfo.fallbackUsed);
    payload.history_direct = Number(historyInfo.directCount || 0);
    payload.history_resolved = Number(historyInfo.resolvedCount || 0);
  }
  writeMetric("hook_compaction", payload);
}

function handleBootstrap(event) {
  if (CONFIG.verbose) {
    console.log("🔄 Context Optimizer Hook ready");
  }

  return {
    ...event,
    data: {
      ...event.data,
      _contextOptimizer: {
        initialized: true,
        status: "ready",
        config: {
          preserveRecent: CONFIG.preserveRecent,
          preserveRecentMessages: getPreserveRecentMessageCount(),
          compressionThreshold: CONFIG.compressionThreshold,
          compressAfterRounds: CONFIG.compressAfterRounds,
          tokenTriggerEstimate: CONFIG.tokenTriggerEstimate,
          triggerSoftRatio: CONFIG.triggerSoftRatio,
          triggerHardRatio: CONFIG.triggerHardRatio,
          mode: CONFIG.mode,
        },
      },
    },
  };
}

async function handleBeforeAgentStart(event) {
  const historyInfo = getHistoryForCompression(event, "before_agent_start");
  const result = runCompression(event, historyInfo.history, {
    historyInfo,
    hookPhase: "before_agent_start",
  });
  if (!result.ok) {
    return event;
  }

  const snapshot = buildSnapshot(result.compressed);
  if (!snapshot) {
    return event;
  }

  logCompression(result, "before_agent_start");
  writeCompactionMetric(event, "before_agent_start", result, historyInfo);
  return { prependContext: snapshot };
}

async function handleBeforePromptBuild(event) {
  const historyInfo = getHistoryForCompression(event, "before_prompt_build");
  const result = runCompression(event, historyInfo.history, {
    historyInfo,
    hookPhase: "before_prompt_build",
  });
  if (!result.ok) {
    return event;
  }

  const compressed = result.compressed || {};
  const recentMessages = toModelSafeMessages(compressed.recent || []);
  if (recentMessages.length === 0) {
    return event;
  }

  const summaryText = compressed.summary ? trimText(String(compressed.summary), 2000) : "";
  const messages = summaryText
    ? [{ role: "system", content: `历史摘要（压缩保留）:\n${summaryText}` }, ...recentMessages]
    : recentMessages;

  logCompression(result, "before_prompt_build");
  writeCompactionMetric(event, "before_prompt_build", result, historyInfo);
  writeSmartContextStatus(event, result, "before_prompt_build");
  return { messages };
}

async function handleInput(event) {
  const data = event?.data || {};
  const historyInfo = getHistoryForCompression(event, "agent:input");
  const result = runCompression(event, historyInfo.history, {
    historyInfo,
    hookPhase: "agent:input",
  });
  if (!result.ok) {
    return event;
  }

  const now = new Date().toISOString();
  const compressed = result.compressed;
  const policy = compressed.policy_v2 || null;

  logCompression(result, "agent:input");
  writeCompactionMetric(event, "agent:input", result, historyInfo);
  writeSmartContextStatus(event, result, "agent:input");

  return {
    ...event,
    data: {
      ...data,
      _contextOptimizer: {
        original_count: result.trigger.historyLength,
        tokens_estimate: result.trigger.tokenEstimate,
        trigger_reason: result.trigger.reason,
        mode: result.trigger.mode || MODE.GENERAL,
        mode_score: Number(result.trigger.modeScore || 0),
        mode_signals: result.trigger.modeSignals || [],
        effective_rules: result.effectiveRules || result.trigger.effectiveRules || null,
        policy_v2: policy,
        recent: compressed.recent,
        summary: compressed.summary,
        tokens_saved: compressed.tokens_saved || 0,
        compression_ratio: compressed.compression_ratio || 0,
        optimized_at: now,
      },
      sessionHistory: compressed.recent,
      sessionSummary: compressed.summary
        ? {
            content: compressed.summary,
            type: result.trigger.phase,
            mode: result.trigger.mode || MODE.GENERAL,
          }
        : null,
    },
  };
}

async function main(event) {
  if (!CONFIG.enabled) {
    return event;
  }

  const eventType = resolveEffectiveEventType(event);

  if (eventType === "before_agent_start") {
    return handleBeforeAgentStart(event);
  }

  switch (eventType) {
    case "before_prompt_build":
      return handleBeforePromptBuild(event);
    case "agent:input":
    case "input":
      return handleInput(event);
    case "agent:bootstrap":
    case "bootstrap":
      return handleBootstrap(event);
    default:
      return event;
  }
}

const handler = async (event) => main(event);
module.exports = handler;
module.exports.main = main;
module.exports.handleBeforeAgentStart = handleBeforeAgentStart;
module.exports.handleBeforePromptBuild = handleBeforePromptBuild;
module.exports.handleInput = handleInput;
module.exports.handleBootstrap = handleBootstrap;
module.exports.compressHistory = compressHistory;
module.exports.CONFIG = CONFIG;
module.exports.normalizeMessages = normalizeMessages;
module.exports.evaluateTrigger = evaluateTrigger;
module.exports.getHistoryFromEvent = getHistoryFromEvent;
module.exports.getHistoryForCompression = getHistoryForCompression;
module.exports.resolveSessionFileFromSessionKey = resolveSessionFileFromSessionKey;
module.exports.loadSessionHistoryFromFile = loadSessionHistoryFromFile;

if (require.main === module) {
  const testMessages = [
    { role: "user", content: "帮我创建一个新的项目" },
    { role: "assistant", content: "✅ 项目创建成功！\n📊 创建了 5 个文件" },
    { role: "user", content: "添加一些功能" },
    { role: "assistant", content: "✅ 已添加 3 个功能" },
    { role: "user", content: "继续添加更多功能" },
    { role: "assistant", content: "✅ 已添加 5 个功能\n📊 总共 8 个功能" },
    { role: "user", content: "完成项目" },
    { role: "assistant", content: "✅ 项目完成！\n🔧 共 8 个功能已实现" },
    { role: "user", content: "部署到生产环境" },
    { role: "assistant", content: "✅ 部署成功！\n🌐 运行在 https://example.com" },
    { role: "user", content: "检查运行状态" },
    { role: "assistant", content: "✅ 运行正常\n📈 99.9% uptime" },
  ];

  const result = runCompression({ type: "input" }, testMessages, { hookPhase: "self-test" });
  console.log(JSON.stringify({ ok: result.ok, trigger: result.trigger }, null, 2));
  if (result.ok) {
    console.log(buildSnapshot(result.compressed).slice(0, 500));
  }
}
