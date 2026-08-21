var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/frontend/viewmodels/session/MarketIntelligenceSessionResolver.ts
var MarketIntelligenceSessionResolver_exports = {};
__export(MarketIntelligenceSessionResolver_exports, {
  getCanonicalIstDate: () => getCanonicalIstDate,
  resolveMarketIntelligenceSession: () => resolveMarketIntelligenceSession
});
module.exports = __toCommonJS(MarketIntelligenceSessionResolver_exports);
function getCanonicalIstDate(customDate) {
  const now = customDate || /* @__PURE__ */ new Date();
  const istStr = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(now);
  const match = istStr.match(/(\d+)\/(\d+)\/(\d+),\s*(\d+):(\d+):(\d+)/);
  if (match) {
    const [, month, day, year, hour, minute, second] = match;
    return new Date(
      Date.UTC(
        parseInt(year, 10),
        parseInt(month, 10) - 1,
        parseInt(day, 10),
        parseInt(hour, 10),
        parseInt(minute, 10),
        parseInt(second, 10)
      )
    );
  }
  return new Date(now.getTime() + 5.5 * 60 * 60 * 1e3);
}
function resolveMarketIntelligenceSession(params) {
  const preview = params?.previewMode || "AUTO";
  const nowIst = getCanonicalIstDate(params?.customDate);
  const hour = nowIst.getUTCHours();
  const minute = nowIst.getUTCMinutes();
  const second = nowIst.getUTCSeconds();
  const hhmmss = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second).padStart(2, "0")}`;
  const timeStr = `${hhmmss} IST`;
  const mStatus = String(params?.marketSessionState?.status || "").toUpperCase();
  const isClosed = Boolean(
    params?.marketSessionState?.is_closed || ["CLOSED", "HOLIDAY", "WEEKEND", "POST_CLOSE"].includes(mStatus)
  );
  let lifecycleStage;
  let autoResolvedSubTab;
  if (isClosed && hhmmss < "09:00:00") {
    lifecycleStage = "TOMORROW_PLAN_ACTIVE";
    autoResolvedSubTab = "TOMORROW_PLAN";
  } else if (hhmmss < "09:10:00") {
    lifecycleStage = "PREPARING";
    autoResolvedSubTab = "MORNING_PLAN";
  } else if (hhmmss >= "09:10:00" && hhmmss <= "09:14:58") {
    lifecycleStage = "MORNING_PLAN_ACTIVE";
    autoResolvedSubTab = "MORNING_PLAN";
  } else if (hhmmss >= "09:14:59" && hhmmss < "15:25:00") {
    lifecycleStage = "LIVE_GUIDE_ACTIVE";
    autoResolvedSubTab = "LIVE_GUIDE";
  } else if (hhmmss >= "15:25:00" && hhmmss <= "15:29:59") {
    lifecycleStage = "LIVE_GUIDE_CLOSING_BUILD";
    autoResolvedSubTab = "LIVE_GUIDE";
  } else {
    lifecycleStage = "TOMORROW_PLAN_ACTIVE";
    autoResolvedSubTab = "TOMORROW_PLAN";
  }
  let effectiveSubTab = autoResolvedSubTab;
  if (preview === "MORNING_PLAN") effectiveSubTab = "MORNING_PLAN";
  else if (preview === "LIVE_GUIDE") effectiveSubTab = "LIVE_GUIDE";
  else if (preview === "TOMORROW_PLAN") effectiveSubTab = "TOMORROW_PLAN";
  let marketStatusText = "MARKET OPEN";
  if (isClosed) {
    marketStatusText = mStatus === "HOLIDAY" ? "MARKET HOLIDAY" : "MARKET CLOSED";
  } else if (hhmmss < "09:15:00") {
    marketStatusText = "PRE-OPEN";
  }
  return {
    currentIstTimeStr: timeStr,
    currentIstHHMMSS: hhmmss,
    lifecycleStage,
    effectiveSubTab,
    autoResolvedSubTab,
    previewMode: preview,
    isClosedSession: isClosed,
    marketStatusText
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  getCanonicalIstDate,
  resolveMarketIntelligenceSession
});
