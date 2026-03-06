/**
 * Context Optimizer Hook
 *
 * 目标：在不改变既有行为预期的前提下，简化上下文压缩逻辑，
 * 将触发判断与压缩执行统一到单一路径。
 */

const { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } = require("fs");
const { join } = require("path");

const RUNTIME_DEFAULTS = {
  preserveRecent: 8,
  compressionThreshold: 20,
  tokenTriggerEstimate: 8000,
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

function toPositiveInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.floor(parsed);
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

  if (override && typeof override === "object") {
    return {
      preserveRecent: toPositiveInt(override.preserveRecent, RUNTIME_DEFAULTS.preserveRecent),
      compressionThreshold: toPositiveInt(override.compressionThreshold, RUNTIME_DEFAULTS.compressionThreshold),
      tokenTriggerEstimate: toPositiveInt(
        override.tokenTriggerEstimate,
        RUNTIME_DEFAULTS.tokenTriggerEstimate
      ),
      triggerSoftRatio: Number(override.triggerSoftRatio ?? 0.7) || 0.7,
      triggerHardRatio: Number(override.triggerHardRatio ?? 0.85) || 0.85,
      enabled: override.enabled !== false,
      verbose: Boolean(override.verbose),
      source: "single-source-override",
    };
  }

  const deepsea = readJson(deepseaPath);
  const smart = deepsea && typeof deepsea.smart_context === "object" ? deepsea.smart_context : null;

  if (smart) {
    return {
      preserveRecent: toPositiveInt(smart.full_rounds, RUNTIME_DEFAULTS.preserveRecent),
      compressionThreshold: toPositiveInt(smart.summary_rounds, RUNTIME_DEFAULTS.compressionThreshold),
      tokenTriggerEstimate: toPositiveInt(smart.full_tokens_max, RUNTIME_DEFAULTS.tokenTriggerEstimate),
      triggerSoftRatio: Number(smart.trigger_soft_ratio ?? 0.7) || 0.7,
      triggerHardRatio: Number(smart.trigger_hard_ratio ?? 0.85) || 0.85,
      enabled: true,
      verbose: false,
      source: "deepsea-config",
    };
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

// Smart Context tier rules (Deep-Sea Nexus):
// - Preserve full recent rounds (full_rounds)
// - After summary_rounds => force compressed
// - After compress_after_rounds => force compressed
// These should be applied before token-based fallback triggers.
const SMART_RULES = {
  fullRounds: CONFIG.preserveRecent,
  summaryRounds: CONFIG.compressionThreshold,
  compressAfterRounds: 35,
  triggerSoftRatio: 0.7,
  triggerHardRatio: 0.85,
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
        schema_version: "4.4.1",
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

    const dir = STATUS_STORE_PATH.replace(/\/[^/]+$/, "");
    if (dir && !existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    const store = readJson(STATUS_STORE_PATH) || {};
    store[sessionKey] = {
      sessionKey,
      hookPhase,
      phase: trigger.phase || PHASE.NONE,
      reason: trigger.reason || "unknown",
      historyMessages: Number(trigger.historyLength || 0),
      historyRounds: Math.max(1, Math.ceil(Number(trigger.historyLength || 0) / 2)),
      tokenEstimate: Number(trigger.tokenEstimate || 0),
      tokensSaved: Number(compressed.tokens_saved || 0),
      keepMessages: recentMessages,
      keepRounds,
      updatedAt: new Date().toISOString(),
      updatedAtMs: Date.now(),
    };

    writeFileSync(STATUS_STORE_PATH, JSON.stringify(store, null, 2), "utf-8");
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

function extractKeyPoints(messages) {
  const keyPoints = [];
  const rescuePoints = [];

  const rescuePatterns = [
    /(^|\s)(decision|决定|结论|方案)[:：]/i,
    /(^|\s)(next(\s+step|\s+action|_action)?|下一步|todo|待办|行动项)[:：]/i,
    /(^|\s)(blocked?|阻塞|卡住|风险|risk)[:：]/i,
  ];

  for (const msg of messages) {
    const role = msg.role || "unknown";
    const content = String(msg.content || "").trim();

    if (role === "user" && content.length > 50) {
      keyPoints.push(`用户询问: ${content.slice(0, 200)}...`);
    }

    if (role === "assistant") {
      const lines = content.split("\n");
      for (const line of lines) {
        if (line.includes("✅") || line.includes("❌") || line.includes("📊")) {
          keyPoints.push(line.trim().slice(0, 150));
        }
      }

      if (content.includes("## ")) {
        const titles = content.match(/## .+/g);
        if (titles) {
          keyPoints.push(...titles.slice(0, 3).map((x) => x.trim()));
        }
      }
    }

    const lines = content
      .split("\n")
      .map((x) => x.trim())
      .filter(Boolean);

    for (const line of lines) {
      if (line.length < 6 || line.length > 260) {
        continue;
      }
      if (rescuePatterns.some((pattern) => pattern.test(line))) {
        rescuePoints.push(line);
      }
    }
  }

  return [...keyPoints.slice(0, 14), ...rescuePoints.slice(0, 10)];
}

function buildSummary(totalCompressedRounds, keyPoints) {
  const lines = [
    "=== 会话摘要 ===",
    `📝 **会话摘要** (共 ${totalCompressedRounds} 轮对话)`,
    "",
    "**关键决策:**",
  ];

  for (let i = 0; i < Math.min(keyPoints.length, 15); i += 1) {
    lines.push(`${i + 1}. ${keyPoints[i]}`);
  }

  lines.push("");
  lines.push("=== 摘要结束 ===");

  return lines.join("\n");
}

function compressHistory(messages, preserveRecent = CONFIG.preserveRecent) {
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
  const keyPoints = extractKeyPoints(toCompress);
  const summary = buildSummary(Math.max(1, Math.ceil(toCompress.length / 2)), keyPoints);

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
      key_points_count: keyPoints.length,
      original_tokens: originalTokens,
      summary_tokens: summaryTokens,
      tokens_saved: tokensSaved,
      compression_ratio: originalTokens > 0 ? tokensSaved / originalTokens : 0,
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

function evaluateTrigger(event, messages) {
  const normalized = normalizeMessages(messages);
  const historyLength = normalized.length;
  const tokenEstimate = estimateTokens(normalized);
  const preserveRecentMessages = getPreserveRecentMessageCount();

  if (historyLength <= preserveRecentMessages) {
    return {
      shouldCompress: false,
      phase: PHASE.NONE,
      reason: "below-preserve-recent",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }

  // 0) Token-waterline fallback (70/85). Apply even before rounds rules.
  // Keep preserveRecent semantics: we compress older history, not the most recent turns.
  const usageRatio = readUsageRatio(event);
  if (usageRatio != null) {
    if (usageRatio >= Number(CONFIG.triggerHardRatio || SMART_RULES.triggerHardRatio || 0.85)) {
      return {
        shouldCompress: true,
        phase: PHASE.COMPRESSED,
        reason: "token:hard-ratio",
        historyLength,
        tokenEstimate,
        messages: normalized,
      };
    }
    if (usageRatio >= Number(CONFIG.triggerSoftRatio || SMART_RULES.triggerSoftRatio || 0.7)) {
      return {
        shouldCompress: true,
        phase: PHASE.SUMMARY,
        reason: "token:soft-ratio",
        historyLength,
        tokenEstimate,
        messages: normalized,
      };
    }
  }


  // 1) Smart Context tier rules first (8-20-35 by default).
  // NOTE: historyLength counts messages, not turns. We approximate turns as message pairs.
  //   - <= 8 rounds: keep raw recent context
  //   - 9~20 rounds: summary mode
  //   - 21~35 rounds: intelligent compression mode
  //   - >35 rounds: hard compression mode
  const estimatedRounds = Math.max(1, Math.ceil(historyLength / 2));
  if (SMART_RULES.compressAfterRounds > 0 && estimatedRounds > SMART_RULES.compressAfterRounds) {
    return {
      shouldCompress: true,
      phase: PHASE.COMPRESSED,
      reason: "smart:compress-after-rounds",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }
  if (SMART_RULES.summaryRounds > 0 && estimatedRounds > SMART_RULES.summaryRounds) {
    return {
      shouldCompress: true,
      phase: PHASE.COMPRESSED,
      reason: "smart:intelligent-compress-rounds",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }
  if (SMART_RULES.fullRounds > 0 && estimatedRounds > SMART_RULES.fullRounds) {
    return {
      shouldCompress: true,
      phase: PHASE.SUMMARY,
      reason: "smart:summary-window-rounds",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }

  // 2) Fallback triggers (token estimate thresholds).
  const byHistory = estimatedRounds > CONFIG.compressionThreshold;
  const byToken = tokenEstimate >= Number(CONFIG.tokenTriggerEstimate || 0);

  if (!byHistory && !byToken) {
    return {
      shouldCompress: false,
      phase: PHASE.NONE,
      reason: "below-threshold",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }

  return {
    shouldCompress: true,
    phase: byHistory ? PHASE.COMPRESSED : PHASE.SUMMARY,
    reason: byHistory ? "history-threshold" : "token-threshold",
    historyLength,
    tokenEstimate,
    messages: normalized,
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

function runCompression(event, messages) {
  const trigger = evaluateTrigger(event, messages);
  if (!trigger.shouldCompress) {
    return { ok: false, trigger };
  }

  const result = compressHistory(trigger.messages, CONFIG.preserveRecent);
  if (!result?.success || !result?.compressed) {
    return { ok: false, trigger };
  }

  return {
    ok: true,
    trigger,
    compressed: result.compressed,
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
    `📦 Context Optimizer (${source}): phase=${trigger.phase} reason=${trigger.reason} history=${trigger.historyLength} estTokens=${trigger.tokenEstimate}`
  );
  const keptMessages = Array.isArray(compressed.recent) ? compressed.recent.length : 0;
  const keptRounds = Math.floor(keptMessages / 2);
  console.log(`✅ 保留最近 ${keptRounds} 轮 (${keptMessages} 条, ${estimateTokens(compressed.recent || [])} tokens)`);
  if (compressed.type === PHASE.COMPRESSED) {
    console.log(`📝 压缩 ${compressed.original_count} 条 → 摘要 (${saved} tokens, ${(ratio * 100).toFixed(0)}%节省)`);
  }
}

function writeCompactionMetric(event, hookPhase, result, historyInfo = null) {
  const payload = {
    hook_phase: hookPhase,
    reason: result?.trigger?.reason,
    history_length: result?.trigger?.historyLength,
    token_estimate: result?.trigger?.tokenEstimate,
    tokens_saved: result?.compressed?.tokens_saved || 0,
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
          tokenTriggerEstimate: CONFIG.tokenTriggerEstimate,
        },
      },
    },
  };
}

async function handleBeforeAgentStart(event) {
  const historyInfo = getHistoryForCompression(event, "before_agent_start");
  const result = runCompression(event, historyInfo.history);
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
  const result = runCompression(event, historyInfo.history);
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
  const result = runCompression(event, historyInfo.history);
  if (!result.ok) {
    return event;
  }

  const now = new Date().toISOString();
  const compressed = result.compressed;

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

  const result = runCompression(testMessages);
  console.log(JSON.stringify({ ok: result.ok, trigger: result.trigger }, null, 2));
  if (result.ok) {
    console.log(buildSnapshot(result.compressed).slice(0, 500));
  }
}
