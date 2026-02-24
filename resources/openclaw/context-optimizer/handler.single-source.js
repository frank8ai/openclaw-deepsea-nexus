/**
 * Context Optimizer Hook
 *
 * 目标：在不改变既有行为预期的前提下，简化上下文压缩逻辑，
 * 将触发判断与压缩执行统一到单一路径。
 */

const { appendFileSync, existsSync, readFileSync } = require("fs");
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
      enabled: true,
      verbose: false,
      source: "deepsea-config",
    };
  }

  return { ...RUNTIME_DEFAULTS, source: "runtime-default" };
}

const CONFIG = loadRuntimeConfig();

const METRICS_LOG =
  process.env.OPENCLAW_SMART_CONTEXT_METRICS_LOG ||
  join(process.env.HOME || "", ".openclaw", "workspace", "logs", "smart_context_metrics.log");

const PHASE = {
  NONE: "none",
  SUMMARY: "summary",
  COMPRESSED: "compressed",
};

function getEventType(event) {
  return String(event?.type || event?.event?.type || "unknown").toLowerCase();
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

  if (totalMessages <= preserveRecent) {
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

  const recent = normalized.slice(-preserveRecent);
  const toCompress = normalized.slice(0, -preserveRecent);
  const keyPoints = extractKeyPoints(toCompress);
  const summary = buildSummary(toCompress.length, keyPoints);

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

function evaluateTrigger(messages) {
  const normalized = normalizeMessages(messages);
  const historyLength = normalized.length;
  const tokenEstimate = estimateTokens(normalized);

  if (historyLength <= CONFIG.preserveRecent) {
    return {
      shouldCompress: false,
      phase: PHASE.NONE,
      reason: "below-preserve-recent",
      historyLength,
      tokenEstimate,
      messages: normalized,
    };
  }

  const byHistory = historyLength > CONFIG.compressionThreshold;
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

function runCompression(messages) {
  const trigger = evaluateTrigger(messages);
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
  console.log(
    `✅ 保留最近 ${Array.isArray(compressed.recent) ? compressed.recent.length : 0} 条 (${estimateTokens(compressed.recent || [])} tokens)`
  );
  if (compressed.type === PHASE.COMPRESSED) {
    console.log(`📝 压缩 ${compressed.original_count} 条 → 摘要 (${saved} tokens, ${(ratio * 100).toFixed(0)}%节省)`);
  }
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
          compressionThreshold: CONFIG.compressionThreshold,
          tokenTriggerEstimate: CONFIG.tokenTriggerEstimate,
        },
      },
    },
  };
}

async function handleBeforeAgentStart(event) {
  const history = getHistoryFromEvent(event);
  const result = runCompression(history);
  if (!result.ok) {
    return event;
  }

  const snapshot = buildSnapshot(result.compressed);
  if (!snapshot) {
    return event;
  }

  logCompression(result, "before_agent_start");
  writeMetric("hook_compaction", {
    hook_phase: "before_agent_start",
    reason: result.trigger.reason,
    history_length: result.trigger.historyLength,
    token_estimate: result.trigger.tokenEstimate,
    tokens_saved: result.compressed.tokens_saved || 0,
  });
  return { prependContext: snapshot };
}

async function handleBeforePromptBuild(event) {
  const history = getHistoryFromEvent(event);
  const result = runCompression(history);
  if (!result.ok) {
    return event;
  }

  const snapshot = buildSnapshot(result.compressed);
  if (!snapshot) {
    return event;
  }

  logCompression(result, "before_prompt_build");
  writeMetric("hook_compaction", {
    hook_phase: "before_prompt_build",
    reason: result.trigger.reason,
    history_length: result.trigger.historyLength,
    token_estimate: result.trigger.tokenEstimate,
    tokens_saved: result.compressed.tokens_saved || 0,
  });
  return { prependContext: snapshot };
}

async function handleInput(event) {
  const data = event?.data || {};
  const history = getHistoryFromEvent(event);
  const result = runCompression(history);
  if (!result.ok) {
    return event;
  }

  const now = new Date().toISOString();
  const compressed = result.compressed;

  logCompression(result, "agent:input");
  writeMetric("hook_compaction", {
    hook_phase: "agent:input",
    reason: result.trigger.reason,
    history_length: result.trigger.historyLength,
    token_estimate: result.trigger.tokenEstimate,
    tokens_saved: compressed.tokens_saved || 0,
  });

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

  const eventType = getEventType(event);

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
