// src/frontend/data/tradingCheatsheet.ts
/**
 * TRADING CHEATSHEET ADAPTIVE DOMAIN KNOWLEDGE BASE
 * =================================================
 * Single canonical trading reference supporting 3 selectable presentation layers:
 *   - BEGINNER: Minimal jargon, plain English, friendly analogies, simple round examples.
 *   - INTERMEDIATE: Standard trader metrics, reference ranges, confirmations, invalidations.
 *   - ADVANCED: Institutional mechanics, volatility regimes, derivatives dynamics, confluence.
 * 
 * ABSOLUTE INVARIANTS:
 * - Zero dependency on live market feeds, broker states, or CanonicalWorkstationState.
 * - Semantic consistency: No mode may contradict another (e.g. VIX = volatility magnitude in all 3).
 * - All rule evaluations are deterministic and map to unified canonical scenario taxonomies.
 */

export type ExperienceLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";

export interface MetricInterpretationRange {
  label: string;
  range: string;
  interpretation: string;
  tone: "BULLISH" | "BEARISH" | "NEUTRAL" | "CAUTION";
}

export interface BeginnerConceptPresentation {
  shortLabel: string;
  friendlySubtitle: string;
  simpleDefinition: string;
  whyItMatters: string;
  simpleStates: Array<{
    label: string;
    rangeText?: string;
    description: string;
    tone?: "BULLISH" | "BEARISH" | "NEUTRAL" | "CAUTION";
  }>;
  simpleExample: string;
  rememberThis: string;
  simpleMistake: string;
  jargonBreakdown?: { term: string; fullName: string; simpleExplanation: string };
  nextConcept?: { id: string; label: string };
}

export interface IntermediateConceptPresentation {
  definition: string;
  whatItMeasures: string;
  ranges: MetricInterpretationRange[];
  traderTakeaway: string;
  commonMistake: string;
  confirmWith: string[];
  invalidationNotes: string[];
  relatedMetrics: string[];
  infoDetail: {
    whatIsThis: string;
    howTradersInterpretIt: string;
    commonRanges: string;
    confirmWith: string;
    commonMistake: string;
  };
}

export interface AdvancedConceptPresentation {
  mechanics: string;
  detailedRanges: Array<{
    label: string;
    range: string;
    regimeContext: string;
    optionOrMarketImpact: string;
  }>;
  regimeContext: string;
  confluenceRules: string[];
  failureConditions: string[];
  edgeCases: string[];
  relatedConcepts: string[];
  advancedHypotheticalExample: string;
  infoDetail: {
    definition: string;
    mechanics: string;
    regimeContext: string;
    confluence: string;
    failureConditions: string;
    edgeCases: string;
    relatedMetrics: string;
  };
}

export interface UnifiedTradingConcept {
  id: string;
  name: string;
  category: "VOLATILITY" | "BREADTH" | "OPTIONS" | "TECHNICAL" | "VOLUME" | "STRUCTURE";
  beginnerGroup: "FEELS" | "MOVING" | "OPTIONS" | "STRENGTH";
  canonicalDefinition: string;
  beginner: BeginnerConceptPresentation;
  intermediate: IntermediateConceptPresentation;
  advanced: AdvancedConceptPresentation;
}

export interface PriceOiMatrixRow {
  priceDirection: "PRICE ↑" | "PRICE ↓";
  oiDirection: "OI ↑" | "OI ↓";
  label: "LONG BUILDUP" | "SHORT BUILDUP" | "SHORT COVERING" | "LONG UNWINDING";
  beginnerLabel: string;
  beginnerExplanation: string;
  intermediateInterpretation: string;
  advancedMechanics: string;
  implication: string;
  warning: string;
  tone: "BULLISH" | "BEARISH" | "CAUTION";
}

export interface PriceActionConcept {
  id: string;
  title: string;
  beginnerTitle: string;
  beginnerDescription: string;
  whatItIs: string;
  whatItMeans: string;
  whatConfirms: string;
  whatInvalidates: string;
  advancedConfluence: string;
  tone: "BULLISH" | "BEARISH" | "NEUTRAL" | "CAUTION";
}

export interface SupportResistanceLevel {
  id: string;
  name: string;
  type: string;
  significance: "HIGH" | "VERY_HIGH" | "DYNAMIC" | "STRUCTURAL";
  beginnerExplanation: string;
  description: string;
  confluenceFactor: string;
  advancedAlgorithmNote: string;
}

export interface OptionOiConcept {
  id: string;
  name: string;
  beginnerExplanation: string;
  implication: string;
  dynamicsWithPrice: string;
  advancedDeltaGammaNote: string;
  warning: string;
  tone: "BULLISH" | "BEARISH" | "CAUTION" | "NEUTRAL";
}

export interface OpeningScenario {
  id: string;
  title: string;
  beginnerTitle: string;
  beginnerDescription: string;
  behavior: string;
  implication: string;
  confirmation: string;
  invalidation: string;
  advancedMarketProfileContext: string;
  tone: "BULLISH" | "BEARISH" | "NEUTRAL" | "CAUTION";
}

export interface UnifiedScenario {
  id: string;
  canonicalClassification: "BULLISH_CONTINUATION" | "BEARISH_CONTINUATION" | "RANGE_CHOP" | "FALSE_BREAKOUT_RISK" | "BEAR_TRAP_RISK" | "MIXED_CONFLICTING";
  title: {
    beginner: string;
    intermediate: string;
    advanced: string;
  };
  conditions: {
    beginner: string[];
    intermediate: string[];
    advanced: string[];
  };
  meaning: {
    beginner: string;
    intermediate: string;
    advanced: string;
  };
  invalidation: {
    beginner: string;
    intermediate: string;
    advanced: string;
  };
  tone: "BULLISH" | "BEARISH" | "RANGE" | "FALSE_BREAKOUT" | "BEAR_TRAP";
  confidenceBand: "STRONG MATCH" | "PARTIAL MATCH" | "HIGH CONFIDENCE";
}

export interface TrendVsRangeComparison {
  aspect: string;
  beginnerSummary: string;
  trendDay: string;
  rangeDay: string;
  advancedMechanics: string;
}

export interface IndicatorCombination {
  title: string;
  beginnerSummary: string;
  indicators: string[];
  outcome: string;
  rationale: string;
  advancedNuance: string;
  tone: "BULLISH" | "BEARISH" | "RANGE" | "CAUTION";
}

export interface GlobalRelationship {
  asset: string;
  beginnerExplanation: string;
  relationToNifty: string;
  mechanism: string;
  caveat: string;
  advancedMacroContext: string;
}

export interface RiskManagementRule {
  id: string;
  title: string;
  beginnerRule: string;
  intermediateRule: string;
  advancedRule: string;
  rationale: string;
  example: string;
}

// --------------------------------------------------------------------------
// 1. UNIFIED CORE MARKET METRICS (15 METRICS WITH 3 EXPERIENCE LAYERS)
// --------------------------------------------------------------------------
export const UNIFIED_CORE_METRICS: UnifiedTradingConcept[] = [
  {
    id: "india_vix",
    name: "INDIA VIX",
    category: "VOLATILITY",
    beginnerGroup: "FEELS",
    canonicalDefinition: "National Volatility Index representing the market's expectation of near-term price fluctuations derived from out-of-the-money NIFTY option bid-ask quotes.",
    beginner: {
      shortLabel: "India VIX",
      friendlySubtitle: "How nervous is the market?",
      simpleDefinition: "India VIX tells you how much price movement and swing traders expect in NIFTY over the near term.",
      whyItMatters: "When the market is nervous or expects big news, VIX rises. When the market is calm and orderly, VIX stays lower.",
      simpleStates: [
        { label: "Calm Market", rangeText: "Below ~15", description: "Market is steady; daily price moves are generally smaller and more orderly.", tone: "NEUTRAL" },
        { label: "Nervous Market", rangeText: "Above ~20", description: "Traders expect larger, faster swings and wider price jumps.", tone: "CAUTION" }
      ],
      simpleExample: "EXAMPLE: If NIFTY is falling while VIX rises sharply, it suggests fear and volatility are increasing.",
      rememberThis: "VIX measures the SIZE of expected price swings, NOT whether prices will go up or down. A high VIX does NOT automatically mean the market must drop.",
      simpleMistake: "Assuming high VIX means sell and low VIX means buy.",
      jargonBreakdown: {
        term: "VIX",
        fullName: "Volatility Index",
        simpleExplanation: "A gauge measuring the expected speed and size of market price swings."
      },
      nextConcept: { id: "implied_volatility", label: "Implied Volatility (IV)" }
    },
    intermediate: {
      definition: "National Volatility Index annualized 30-day volatility expectation derived from NIFTY option bid-asks.",
      whatItMeasures: "Expected rate and magnitude of index fluctuations over the next 30 calendar days.",
      ranges: [
        { label: "Very Low", range: "< 12.0", interpretation: "Calm regime. Subdued premiums, narrow typical ranges, compressed intraday bars.", tone: "NEUTRAL" },
        { label: "Normal / Calm", range: "12.0 – 15.0", interpretation: "Standard operating regime. Orderly intraday trending or rotational flow.", tone: "NEUTRAL" },
        { label: "Elevated", range: "15.0 – 20.0", interpretation: "Increased uncertainty. Wider intraday swings, higher option premiums, expanded stops needed.", tone: "CAUTION" },
        { label: "High", range: "20.0 – 30.0", interpretation: "Stress or high-impact event environment. Fast accelerations, large gap risks.", tone: "BEARISH" },
        { label: "Extreme Stress", range: "> 30.0", interpretation: "Panic / Crisis regime. Liquidity thinning, severe slippage risk, directional whipsaws.", tone: "BEARISH" }
      ],
      traderTakeaway: "Adjust position sizing inversely to VIX magnitude: lower size when VIX expands; widen stop distances.",
      commonMistake: "Assuming high VIX means market must drop or low VIX means market must rally. VIX is a magnitude indicator, not a directional compass.",
      confirmWith: ["Market Breadth", "Option IV Rank", "ATR"],
      invalidationNotes: ["VIX spikes during pre-event uncertainty and often collapses sharply post-event (IV Crush)."],
      relatedMetrics: ["ATR", "Implied Volatility", "PCR"],
      infoDetail: {
        whatIsThis: "India VIX measures the market's expectation of near-term price fluctuations derived from out-of-the-money NIFTY option prices.",
        howTradersInterpretIt: "High VIX (>20) indicates expectation of larger price swings and costlier option premiums. Low VIX (<15) indicates smaller expected near-term swings.",
        commonRanges: "Normal range is 12.0 to 18.0; stress regimes trigger above 20.0.",
        confirmWith: "Combine with ATR and Constituent Breadth to calibrate stop distances and trade horizon.",
        commonMistake: "Trading with fixed stop points regardless of VIX regime; high VIX requires volatility-adjusted position sizing."
      }
    },
    advanced: {
      mechanics: "Calculated using the standard Black-Scholes variance swap formula, aggregating weighted bid-ask quotes of near-month and mid-month OTM NIFTY put and call options.",
      detailedRanges: [
        { label: "Compression", range: "< 12.0", regimeContext: "Mean-reversion / Pinning", optionOrMarketImpact: "Theta decay dominant, premium selling favored, watch for sudden volatility breakout." },
        { label: "Equilibrium", range: "12.0 – 16.0", regimeContext: "Balanced Auction", optionOrMarketImpact: "Orderly trend continuation or value rotation; standard risk-reward models hold." },
        { label: "Expansion", range: "16.0 – 22.0", regimeContext: "Risk-Off / Liquidity Repricing", optionOrMarketImpact: "Hedging demand surges, put skew steepens, intraday range expansion." },
        { label: "Turbulence", range: "> 22.0", regimeContext: "Event / Macro Shock", optionOrMarketImpact: "Gamma risk elevated for option writers, extreme slippage on stop triggers." }
      ],
      regimeContext: "Volatility exhibits strong mean-reverting characteristics: prolonged compression under 12.0 frequently resolves in explosive multi-day expansions.",
      confluenceRules: [
        "VIX Expansion + Price Breakdown + Deteriorating Breadth = High Bearish Momentum Confluence.",
        "VIX Compression + Price at Support + Improving Breadth = High Mean-Reversion / Floor Confluence."
      ],
      failureConditions: [
        "Bullish momentum can persist in high-VIX environments (e.g. short squeezes and aggressive momentum rallies).",
        "Low VIX does not prevent sharp, sudden flash breaks."
      ],
      edgeCases: [
        "Pre-Election / Pre-Budget IV Bid: VIX expands solely due to binary event date pricing; index price may remain completely stationary."
      ],
      relatedConcepts: ["IV Rank / Percentile", "Volatility Skew", "Realized vs Implied Volatility"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY consolidates between 24,000 and 24,100 while VIX compresses from 15.5 to 11.8 over 6 sessions. A subsequent 50-pt breakout on expanding volume triggers an immediate VIX jump to 14.2, signaling authentic volatility expansion.",
      infoDetail: {
        definition: "National Volatility Index capturing annualized 30-day variance expectation from NIFTY option surfaces.",
        mechanics: "Variance swap pricing methodology weighting strike prices inversely to strike distance squared.",
        regimeContext: "Guides Vega exposure, gamma risk management, and structural stop sizing.",
        confluence: "Cross-examine with index skew and realized 10-day ATR to detect underpriced or overpriced options.",
        failureConditions: "Event pricing distortion; decoupling during one-sided institutional cash accumulation.",
        edgeCases: "Expiry afternoon IV crush causing VIX drops despite heavy underlying index movement.",
        relatedMetrics: "Realized Volatility, Implied Volatility, ATR, Put-Call Ratio"
      }
    }
  },
  {
    id: "market_breadth",
    name: "MARKET BREADTH",
    category: "BREADTH",
    beginnerGroup: "FEELS",
    canonicalDefinition: "The net ratio of advancing versus declining constituent stocks across the NIFTY 50 index basket.",
    beginner: {
      shortLabel: "Market Breadth",
      friendlySubtitle: "How many NIFTY stocks are participating?",
      simpleDefinition: "Market Breadth tells you how many of the 50 major NIFTY stocks are rising versus how many are falling.",
      whyItMatters: "A healthy rally has many stocks moving up together. A fragile rally happens when only 1 or 2 giant stocks pull the index higher while the rest drop.",
      simpleStates: [
        { label: "Broad Buying", rangeText: "35+ stocks rising", description: "Most of the market is strong; rallies are healthier.", tone: "BULLISH" },
        { label: "Mixed Market", rangeText: "20–30 stocks rising", description: "Some stocks up, some down; market may chop sideways.", tone: "NEUTRAL" },
        { label: "Broad Selling", rangeText: "Under 15 stocks rising", description: "Most stocks are weak; market faces broad pressure.", tone: "BEARISH" }
      ],
      simpleExample: "EXAMPLE: If NIFTY is up +0.5%, but 35 stocks are falling and only 15 are rising, the move is driven by just a few heavyweights and may be fragile.",
      rememberThis: "NIFTY going up does NOT always mean the whole market is strong. Check whether other stocks are participating.",
      simpleMistake: "Buying breakouts when most stocks in the index are quietly falling.",
      nextConcept: { id: "vwap", label: "VWAP (Volume Weighted Average Price)" }
    },
    intermediate: {
      definition: "Advance/Decline ratio across the 50 constituent stocks of the NIFTY 50 index.",
      whatItMeasures: "Broad constituent participation supporting the headline index movement.",
      ranges: [
        { label: "Strong Positive", range: "> 35 ADV", interpretation: "Broad institutional buying across multiple sectors. High continuation probability for bullish moves.", tone: "BULLISH" },
        { label: "Healthy Positive", range: "30 – 35 ADV", interpretation: "Constructive participation. Index trends have solid internal footing.", tone: "BULLISH" },
        { label: "Balanced / Mixed", range: "22 – 28 ADV", interpretation: "Rotational / two-way market. Selective stock action, narrow index swings.", tone: "NEUTRAL" },
        { label: "Weak Breadth", range: "< 20 ADV", interpretation: "Deteriorating participation. Upside rallies are narrow or heavyweight-driven.", tone: "CAUTION" },
        { label: "Strong Negative", range: "< 15 ADV", interpretation: "Broad liquidation or selling pressure across the majority of constituents.", tone: "BEARISH" }
      ],
      traderTakeaway: "Always check whether index moves are accompanied by breadth alignment or merely 2–3 heavyweights.",
      commonMistake: "Buying index breakouts when breadth is declining (ADV < 20), which frequently produces false breakouts.",
      confirmWith: ["Bank NIFTY", "Sector Indices", "Volume"],
      invalidationNotes: ["Breadth divergence: Index makes new high while Advancers drop from 38 to 22."],
      relatedMetrics: ["Volume", "Bank NIFTY", "VWAP"],
      infoDetail: {
        whatIsThis: "Market Breadth measures the net ratio of advancing versus declining stocks within the index basket.",
        howTradersInterpretIt: "Strong breadth (>35 Advancers) proves institutional participation across sectors. Weak breadth (<15 Advancers) reveals broad distribution.",
        commonRanges: ">35 ADV indicates broad bull strength; <15 ADV indicates broad bear pressure; 22-28 is rotational.",
        confirmWith: "Confirm with banking sector alignment and volume expansion.",
        commonMistake: "Assuming an index rally is safe when fewer than 20 stocks are advancing."
      }
    },
    advanced: {
      mechanics: "Constituent-weighted and unweighted breadth metrics measuring market internal participation, cumulative advance-decline lines, and sector contribution dispersion.",
      detailedRanges: [
        { label: "Broad Expansion", range: "> 40 ADV", regimeContext: "Institutional Risk-On", optionOrMarketImpact: "Multi-sector capital allocation; high trend persistence; short fades get overrun." },
        { label: "Narrow Skew", range: "28 – 35 ADV", regimeContext: "Selective Rotation", optionOrMarketImpact: "Leadership concentrated in top 2 sectors (e.g. Financials + IT); index grinds higher." },
        { label: "Internal Divergence", range: "15 – 25 ADV with Index +", regimeContext: "Distribution Under Surface", optionOrMarketImpact: "Heavyweight propping while broad basket distributes; prime bull-trap precursor." },
        { label: "Broad Capitulation", range: "< 10 ADV", regimeContext: "Institutional Liquidation", optionOrMarketImpact: "Correlated panic selling across all sectors; high probability of cascading stop runs." }
      ],
      regimeContext: "Breadth divergences provide early warning signs: when headline NIFTY prints higher intraday highs while advance counts steadily deteriorate, an exhaustion break is imminent.",
      confluenceRules: [
        "Index Breakout + Breadth > 38 ADV + Bank Nifty Outperforming = High-Conviction Bullish Confluence.",
        "Index Breakdown + Breadth < 12 ADV + Heavyweight Selling = High-Conviction Bearish Confluence."
      ],
      failureConditions: [
        "Heavyweight stocks (Reliance, HDFC Bank, ICICI Bank, TCS, Infosys) command > 35% index weight; extreme moves in 2 heavyweights can temporarily overpower contrary breadth."
      ],
      edgeCases: [
        "Rebalancing Days: MSCI / FTSE rebalancing order flow can create sharp breadth distortion in the closing 30 minutes that does not reflect underlying trend."
      ],
      relatedConcepts: ["Advance-Decline Line", "Sector Dispersion", "Heavyweight Concentration Risk"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY surges +80 points to break 24,350 resistance, but NIFTY constituent breadth drops from 34 ADV to 18 ADV as HDFC Bank (+2.5%) carries the entire index. Two hours later, HDFC Bank stalls, and NIFTY drops 110 points.",
      infoDetail: {
        definition: "Internal health indicator measuring constituent participation percentage across the 50 index components.",
        mechanics: "Real-time tick aggregation tracking net positive vs negative delta across constituent equities.",
        regimeContext: "Differentiates true structural accumulation from deceptive heavyweight propping.",
        confluence: "Must be evaluated alongside Sector Relative Strength and Volume Breadth.",
        failureConditions: "Distorted during extreme single-stock corporate earnings announcements.",
        edgeCases: "Index constituent changes and index arbitrage basket rebalances.",
        relatedMetrics: "Advance-Decline Delta, Sector Momentum, Cumulative Volume"
      }
    }
  },
  {
    id: "pcr_oi",
    name: "PCR (OPEN INTEREST)",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "The numerical ratio of total Put Open Interest divided by total Call Open Interest across all active option strikes.",
    beginner: {
      shortLabel: "PCR (Put-Call Ratio)",
      friendlySubtitle: "Are traders positioned more in puts or calls?",
      simpleDefinition: "PCR compares how many Put option contracts are active versus how many Call option contracts are active.",
      whyItMatters: "Puts are often sold by large institutions to create a price floor (support). Calls are sold to create a price ceiling (resistance).",
      simpleStates: [
        { label: "More Puts (Supportive)", rangeText: "Put Heavy", description: "Sellers have built strong downside floor support.", tone: "BULLISH" },
        { label: "Balanced", rangeText: "Balanced", description: "Even positioning between buyers and sellers.", tone: "NEUTRAL" },
        { label: "More Calls (Overhead Resistance)", rangeText: "Call Heavy", description: "Heavy ceiling resistance overhead; upside may face selling pressure.", tone: "CAUTION" }
      ],
      simpleExample: "EXAMPLE: When PCR is high, option sellers have written many puts, creating support under the market as long as prices stay above support.",
      rememberThis: "A high PCR does NOT mean automatic BUY, and a low PCR does NOT mean automatic SELL. Always check if price is holding key support.",
      simpleMistake: "Assuming PCR > 1.0 means you should blindly buy call options.",
      jargonBreakdown: {
        term: "PCR",
        fullName: "Put-Call Ratio",
        simpleExplanation: "A ratio comparing active put contracts to call contracts to see where market support and resistance sit."
      },
      nextConcept: { id: "open_interest", label: "Open Interest (OI)" }
    },
    intermediate: {
      definition: "Total Put Open Interest divided by Total Call Open Interest across all active strikes.",
      whatItMeasures: "Cumulative positioning inventory of option market participants.",
      ranges: [
        { label: "Call-Heavy", range: "< 0.70", interpretation: "Aggressive call writing or put unwinding. Significant overhead resistance positioning.", tone: "BEARISH" },
        { label: "Mild Call Dominance", range: "0.70 – 0.90", interpretation: "Cautious tone. Resistance strikes well defended by call writers.", tone: "CAUTION" },
        { label: "Balanced", range: "0.90 – 1.10", interpretation: "Neutral positioning equilibrium. Market open to two-way auction.", tone: "NEUTRAL" },
        { label: "Put Strengthening", range: "1.10 – 1.30", interpretation: "Solid downside floor support building via put underwriting.", tone: "BULLISH" },
        { label: "Extreme Put Heavy", range: "> 1.30", interpretation: "Very heavy put writing. High support, but monitor for unwinding cascade if major support breaks.", tone: "BULLISH" }
      ],
      traderTakeaway: "Use PCR OI as a structural floor/ceiling confidence metric, but monitor intraday change in OI for shifts.",
      commonMistake: "Assuming PCR > 1.0 is unconditionally bullish without verifying if price is above key support.",
      confirmWith: ["Put Wall Strike", "Call Wall Strike", "Price vs VWAP"],
      invalidationNotes: ["If price breaks below the Put Wall, high PCR can trigger rapid put unwinding, accelerating a selloff."],
      relatedMetrics: ["PCR (Volume)", "Max Pain", "Open Interest"],
      infoDetail: {
        whatIsThis: "Put-Call Ratio (OI) is the ratio of total outstanding put contracts to total outstanding call contracts.",
        howTradersInterpretIt: "Values > 1.10 indicate put underwriting support; values < 0.80 indicate heavy call writing overhead.",
        commonRanges: "Standard range is 0.80 to 1.30; extremes occur outside this band.",
        confirmWith: "Cross-check with Put Wall support and Price position above VWAP.",
        commonMistake: "Treating PCR as an isolated buy/sell oscillator rather than a structural positioning backdrop."
      }
    },
    advanced: {
      mechanics: "Aggregated open interest volume ratio calculated as $\\Sigma(OI_{Puts}) / \\Sigma(OI_{Calls})$, sensitive to strike distribution and near-the-money vs far-OTM concentration.",
      detailedRanges: [
        { label: "Call Dominance / Cap", range: "< 0.65", regimeContext: "Overhead Resistance Grid", optionOrMarketImpact: "Call writers actively defend upper strikes; upward momentum requires aggressive short-covering fuel." },
        { label: "Neutral Band", range: "0.85 – 1.15", regimeContext: "Balanced Auction", optionOrMarketImpact: "Two-way gamma positioning; market responds primarily to spot price action and cash flows." },
        { label: "Put Cushion", range: "1.20 – 1.45", regimeContext: "Institutional Floor", optionOrMarketImpact: "Underwriters collect theta safely; dips toward key put strikes meet responsive buying." },
        { label: "Extreme Skew / Trap Hazard", range: "> 1.50", regimeContext: "Crowded Positioning", optionOrMarketImpact: "Vulnerable to gamma trap if spot breaks below major put strikes, forcing market makers to short futures." }
      ],
      regimeContext: "PCR OI represents positioning inventory (stock), while PCR Volume represents intraday transaction velocity (flow). A divergence between the two signals institutional rotation.",
      confluenceRules: [
        "PCR > 1.25 + Spot at Put Wall + Hammer Rejection Wick = High Support Bounce Confluence.",
        "PCR < 0.70 + Spot at Call Wall + Shooting Star Rejection = High Overhead Resistance Confluence."
      ],
      failureConditions: [
        "Support Cascade: High PCR becomes a severe bearish catalyst if key support breaks, as trapped put writers panic-cover by dumping index delta."
      ],
      edgeCases: [
        "Expiry Day Distortion: In the final 2 hours of weekly expiry, deep OTM worthless contracts distort the raw PCR ratio; focus strictly on ATM ± 2 strikes."
      ],
      relatedConcepts: ["Gamma Exposure (GEX)", "Dealer Positioning", "Max Pain Settlement"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY drops 150 points to test 24,000 where PCR is 1.35. If 24,000 holds, put writers collect full premium. However, if 24,000 breaks decisively with 5m close, 1.2 crore put contracts go ITM, triggering a 100-point liquidation cascade.",
      infoDetail: {
        definition: "Total Put open interest divided by Call open interest across all active strike series.",
        mechanics: "Reflects dealer hedging inventory and structural underwriting boundaries.",
        regimeContext: "Identifies whether the options market is configured as supportive cushion or overhead resistance.",
        confluence: "Must be combined with ATM Strike OI Change to observe real-time shift.",
        failureConditions: "Trapped put writer liquidations triggering rapid delta hedging downward.",
        edgeCases: "Deep OTM skew distortions on expiry day afternoons.",
        relatedMetrics: "ATM PCR, GEX Profile, Max Pain, Put Wall"
      }
    }
  },
  {
    id: "pcr_volume",
    name: "PCR (VOLUME)",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "Total intraday Put traded volume divided by Total Call traded volume.",
    beginner: {
      shortLabel: "PCR Volume",
      friendlySubtitle: "Which options are being traded most actively today?",
      simpleDefinition: "PCR Volume measures the speed of trades happening today in Put options compared to Call options.",
      whyItMatters: "While standard PCR looks at long-term positions, PCR Volume shows what traders are doing right now during today's session.",
      simpleStates: [
        { label: "More Calls Traded", rangeText: "Call Volume Heavy", description: "Traders are actively trading call options today.", tone: "CAUTION" },
        { label: "Balanced Activity", rangeText: "Balanced", description: "Equal trading activity between puts and calls.", tone: "NEUTRAL" },
        { label: "More Puts Traded", rangeText: "Put Volume Heavy", description: "Traders are actively trading put options today.", tone: "BULLISH" }
      ],
      simpleExample: "EXAMPLE: A sudden surge in put volume during a quiet morning suggests institutional hedging or active put writing.",
      rememberThis: "Trading volume shows activity, but does not tell you if traders held the positions overnight until you check Open Interest.",
      simpleMistake: "Confusing short-term volume spikes with permanent structural support.",
      nextConcept: { id: "call_wall", label: "Call Wall & Put Wall" }
    },
    intermediate: {
      definition: "Total intraday Put traded volume divided by Total Call traded volume.",
      whatItMeasures: "Current trading velocity and speculative/hedging activity flow during the active session.",
      ranges: [
        { label: "Call Activity Heavy", range: "< 0.80", interpretation: "Intraday traders actively buying/selling calls; indicates upward speculative focus or heavy call writing flow.", tone: "CAUTION" },
        { label: "Balanced Flow", range: "0.80 – 1.10", interpretation: "Even intraday volume turnover between calls and puts.", tone: "NEUTRAL" },
        { label: "Put Activity Heavy", range: "> 1.20", interpretation: "High put volume turnover; reflects active put hedging or strong put underwriting activity.", tone: "BULLISH" }
      ],
      traderTakeaway: "Differentiate PCR OI (accumulated stock) from PCR Volume (intraday flow velocity).",
      commonMistake: "Confusing short-term volume spikes with permanent structural shift in open interest.",
      confirmWith: ["PCR (OI)", "Volume", "Price vs VWAP"],
      invalidationNotes: ["Volume without OI buildup indicates day-trader scalping that disappears at market close."],
      relatedMetrics: ["PCR (OI)", "Volume", "Open Interest"],
      infoDetail: {
        whatIsThis: "PCR Volume measures the turnover ratio of puts versus calls traded during the current day.",
        howTradersInterpretIt: "High PCR volume shows elevated put transactions; low PCR volume shows call transaction dominance.",
        commonRanges: "0.80 to 1.20 represents balanced flow; extremes indicate one-sided intraday interest.",
        confirmWith: "Cross-check with PCR OI to see if volume creates permanent open interest.",
        commonMistake: "Assuming high put volume automatically equals bearish buying without checking if sellers wrote the puts."
      }
    },
    advanced: {
      mechanics: "Intraday flow ratio $\\Sigma(Vol_{Puts}) / \\Sigma(Vol_{Calls})$ tracking institutional transaction velocity and intraday delta adjustments.",
      detailedRanges: [
        { label: "Call Flow Dominant", range: "< 0.75", regimeContext: "Speculative Call Bid / Call Writing", optionOrMarketImpact: "High turnover on call strikes; check if bid-driven (buying) or ask-driven (writing)." },
        { label: "Equilibrium Flow", range: "0.85 – 1.15", regimeContext: "Standard Two-Way Turnover", optionOrMarketImpact: "Normal market maker turnover without directional institutional clustering." },
        { label: "Put Flow Dominant", range: "> 1.30", regimeContext: "Hedging / Put Underwriting", optionOrMarketImpact: "Heavy institutional turnover on put strikes; often leads to floor building if spot stabilizes." }
      ],
      regimeContext: "PCR Volume serves as a leading indicator for intraday turning points when it sharply diverges from the prevailing trend.",
      confluenceRules: [
        "Spot at support + Sudden PCR Volume spike > 1.40 + Delta Absorption = High Intraday Reversal Probability."
      ],
      failureConditions: ["High volume turnover can represent pure algorithmic market-maker churning with zero overnight retention."],
      edgeCases: ["Zero-DTE / Expiry Day scalping algorithms cycling high turnover around ATM strikes."],
      relatedConcepts: ["Order Flow Delta", "Bid-Ask Imbalance", "Trade Velocity"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY opens flat, but within 45 minutes PCR Volume surges to 1.65 while PCR OI stays 1.05. This signals heavy intraday put turnover (hedging or aggressive put selling) before it reflects in EOD open interest.",
      infoDetail: {
        definition: "Ratio of intraday traded put volume to call volume.",
        mechanics: "Measures intraday flow velocity and market participant activity distribution.",
        regimeContext: "Complements static OI by highlighting real-time speculative and hedging shifts.",
        confluence: "Combine with Cumulative Delta and VWAP interaction.",
        failureConditions: "Transient churn from algorithmic market makers.",
        edgeCases: "Expiry morning premium rollovers.",
        relatedMetrics: "PCR OI, Option Volume Turnover, Implied Volatility"
      }
    }
  },
  {
    id: "open_interest",
    name: "OPEN INTEREST (OI)",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "Total number of outstanding derivative contracts that have not been settled or closed.",
    beginner: {
      shortLabel: "Open Interest (OI)",
      friendlySubtitle: "Are new positions being added or removed?",
      simpleDefinition: "Open Interest counts how many total active contracts are currently open in the market.",
      whyItMatters: "Rising OI means new money and new positions are entering. Falling OI means traders are closing existing positions and exiting.",
      simpleStates: [
        { label: "OI Rising (+)", description: "More positions are being created; fresh money is entering the market.", tone: "NEUTRAL" },
        { label: "OI Falling (-)", description: "Traders are closing out their positions and taking profits or losses.", tone: "NEUTRAL" }
      ],
      simpleExample: "EXAMPLE: If price is going UP and OI is going UP, it suggests buyers are aggressively creating fresh long positions (Long Buildup).",
      rememberThis: "OI by itself does NOT tell you direction. You must always combine OI with PRICE DIRECTION.",
      simpleMistake: "Thinking high OI always means bullish.",
      jargonBreakdown: {
        term: "OI",
        fullName: "Open Interest",
        simpleExplanation: "The total count of active, unsettled contracts held by market participants."
      },
      nextConcept: { id: "price_oi_matrix", label: "Price + OI Matrix" }
    },
    intermediate: {
      definition: "Total number of outstanding derivative contracts that have not been settled or closed.",
      whatItMeasures: "Net financial capital committed to open derivative positions in the market.",
      ranges: [
        { label: "Expanding OI", range: "OI Rising (+)", interpretation: "Fresh capital entering the market. New positions being created.", tone: "NEUTRAL" },
        { label: "Contracting OI", range: "OI Falling (-)", interpretation: "Capital exiting. Existing positions being squared off / liquidated.", tone: "NEUTRAL" }
      ],
      traderTakeaway: "Always evaluate OI direction in tandem with price direction (Long Buildup, Short Buildup, Covering, Unwinding).",
      commonMistake: "Viewing high OI as bullish or bearish in isolation without direction of price movement.",
      confirmWith: ["Price Direction", "Volume", "Price vs OI Matrix"],
      invalidationNotes: ["OI changes near expiry often represent position rollover rather than directional conviction."],
      relatedMetrics: ["Volume", "PCR (OI)", "Price Action"],
      infoDetail: {
        whatIsThis: "Open Interest is the total count of active derivative contracts held by market participants at a specific strike or future.",
        howTradersInterpretIt: "Rising OI indicates new position commitments; falling OI indicates closing or liquidation of existing positions.",
        commonRanges: "Track net daily and intraday percentage change (+5% to +20% buildup).",
        confirmWith: "Always pair with price direction to categorize the buildup regime.",
        commonMistake: "Evaluating OI without checking whether price is rising or falling."
      }
    },
    advanced: {
      mechanics: "Contract tracking reflecting aggregate outstanding obligations across clearing corporation registers; adjusted in real-time as trades create, transfer, or extinguish contracts.",
      detailedRanges: [
        { label: "Aggressive Accumulation", range: "OI Change > +15%", regimeContext: "Institutional Commitment", optionOrMarketImpact: "High conviction capital commitment; establishes strong support or resistance." },
        { label: "Orderly Buildup", range: "OI Change +5% to +15%", regimeContext: "Standard Trend Development", optionOrMarketImpact: "Healthy institutional trend support without immediate crowding." },
        { label: "Liquidation / Covering", range: "OI Change < -10%", regimeContext: "Position Unwinding", optionOrMarketImpact: "Forced closing of losing positions; creates fast vertical price acceleration." }
      ],
      regimeContext: "OI dynamics reveal whether a move is powered by fresh institutional capital (buildup) or merely short-covering / long-unwinding fuel that will extinguish once stops are cleared.",
      confluenceRules: [
        "Price New High + Futures OI Expanding + Cash Volume Expanding = Authentic Institutional Markup."
      ],
      failureConditions: ["Rollover week distortions when near-month contracts shed OI while next-month contracts accumulate OI."],
      edgeCases: ["Intraday option writers selling strangles at ATM strikes, expanding OI on both calls and puts simultaneously."],
      relatedConcepts: ["Cumulative OI Delta", "Rollover Cost", "Futures Basis"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY rises 120 points while Futures OI drops by 14%. This is pure Short Covering, not fresh buying. Once short stops are cleared, the move is vulnerable to immediate exhaustion if fresh buyers do not step in.",
      infoDetail: {
        definition: "Total aggregate outstanding derivative contracts on exchange clearing records.",
        mechanics: "Incremented when buyer and seller both open new positions; decremented when both close.",
        regimeContext: "Differentiates sustainable multi-session trends from transient short squeezes.",
        confluence: "Evaluate alongside Futures Premium/Discount and Cash Delivery Volumes.",
        failureConditions: "Distorted during monthly expiry roll cycles.",
        edgeCases: "Delta-neutral institutional arbitrage spreads.",
        relatedMetrics: "Price vs OI Matrix, Basis Delta, Volume"
      }
    }
  },
  {
    id: "volume",
    name: "VOLUME",
    category: "VOLUME",
    beginnerGroup: "STRENGTH",
    canonicalDefinition: "The total quantity of shares or contracts transacted during a specified timeframe.",
    beginner: {
      shortLabel: "Volume",
      friendlySubtitle: "How much trading is actually happening?",
      simpleDefinition: "Volume measures how many shares or contracts are being bought and sold.",
      whyItMatters: "High volume means lots of participants and strong interest. Low volume means quiet trading where moves can be easily faked.",
      simpleStates: [
        { label: "High Volume", rangeText: "Busy trading", description: "Strong interest and conviction; moves are more reliable.", tone: "BULLISH" },
        { label: "Low Volume", rangeText: "Quiet trading", description: "Few participants; moves are more prone to sudden reversals and traps.", tone: "CAUTION" }
      ],
      simpleExample: "EXAMPLE: If price breaks above a key level on huge volume, it shows strong buyer conviction. If it breaks on tiny volume, it may quickly fail.",
      rememberThis: "Breakouts need healthy volume to succeed. Low-volume breakouts frequently fail.",
      simpleMistake: "Believing every price jump is real, even when volume is almost zero.",
      nextConcept: { id: "vwap", label: "VWAP (Volume Weighted Average Price)" }
    },
    intermediate: {
      definition: "Total number of shares or contracts transacted during a specified time interval.",
      whatItMeasures: "Market participation, conviction, and liquidity intensity behind a price move.",
      ranges: [
        { label: "High / Climactic", range: "> 1.5x Avg", interpretation: "High institutional conviction or potential climax/exhaustion at extreme levels.", tone: "NEUTRAL" },
        { label: "Normal", range: "0.8x – 1.2x Avg", interpretation: "Healthy regular order flow supporting ordinary price discovery.", tone: "NEUTRAL" },
        { label: "Low / Anemic", range: "< 0.6x Avg", interpretation: "Lack of institutional participation. High vulnerability to false breakouts and erratic chop.", tone: "CAUTION" }
      ],
      traderTakeaway: "Breakouts require volume expansion to be sustainable; low-volume breakouts carry high failure probabilities.",
      commonMistake: "Chasing price moves on declining volume, which often represents low-liquidity drift rather than true demand.",
      confirmWith: ["Breakout Levels", "Price vs VWAP", "Market Breadth"],
      invalidationNotes: ["Volume drying up at resistance indicates buyer exhaustion."],
      relatedMetrics: ["VWAP", "Open Interest", "ATR"],
      infoDetail: {
        whatIsThis: "Volume represents the total quantity of contracts or shares exchanged between buyers and sellers.",
        howTradersInterpretIt: "High volume confirms institutional interest and liquidity. Low volume suggests lack of broad participation.",
        commonRanges: ">1.5x average confirms breakouts; <0.6x average signals range chop.",
        confirmWith: "Confirm with price candle size and VWAP alignment.",
        commonMistake: "Assuming high volume is purely bullish; high volume at resistance can represent heavy institutional selling absorption."
      }
    },
    advanced: {
      mechanics: "Transaction count and turnover aggregation representing the auction liquidity consumed across the order book bid-ask matrix.",
      detailedRanges: [
        { label: "Climactic Volume", range: "> 2.5x 20-period Avg", regimeContext: "Exhaustion / Absorption", optionOrMarketImpact: "Often marks turning points or institutional liquidity transfer at major extremes." },
        { label: "Expansionary Volume", range: "1.3x – 2.0x Avg", regimeContext: "Trend Continuation", optionOrMarketImpact: "Healthy institutional sponsorship validating breakout legs." },
        { label: "Anemic Volume", range: "< 0.6x Avg", regimeContext: "Liquidity Vacuum", optionOrMarketImpact: "Vulnerable to algorithmic stop runs and false breakouts." }
      ],
      regimeContext: "Volume confirms the validity of price discovery: volume expansion on impulses with contraction on pullbacks is the hallmark of sustainable institutional trending.",
      confluenceRules: [
        "Resistance Breakout + Volume > 1.8x Avg + Breadth > 35 ADV = High Continuation Probability."
      ],
      failureConditions: ["Climactic volume at extreme highs often signals distribution (exhaustion bar) rather than continuation."],
      edgeCases: ["Pre-open matching and opening 1-minute prints containing accumulated overnight institutional block trades."],
      relatedConcepts: ["Volume Profile / Value Area", "Volume Delta", "VWAP Standard Deviation Bands"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY tests 24,500 resistance with the largest 5-minute volume bar of the day (+3.2x average), but the candle closes as a shooting star with a long upper wick. This reveals institutional supply absorbing all retail breakout buying.",
      infoDetail: {
        definition: "Total quantity of contracts or shares exchanged during an auction period.",
        mechanics: "Aggregates aggressive market orders hitting passive limit order books.",
        regimeContext: "Validates whether price levels represent accepted value or temporary exploration.",
        confluence: "Cross-reference with Volume Profile Point of Control (POC).",
        failureConditions: "High volume absorption stalling price progress at key levels.",
        edgeCases: "Expiry settlement auction index rebalance volume spikes.",
        relatedMetrics: "VWAP, Volume Profile, Open Interest"
      }
    }
  },
  {
    id: "vwap",
    name: "VWAP",
    category: "TECHNICAL",
    beginnerGroup: "MOVING",
    canonicalDefinition: "Volume Weighted Average Price calculated as the cumulative sum of (Price × Volume) divided by Total Volume for the intraday session.",
    beginner: {
      shortLabel: "VWAP",
      friendlySubtitle: "Where is the average traded price today?",
      simpleDefinition: "VWAP is the average price traders have paid today, giving more weight to prices where heavy volume was traded.",
      whyItMatters: "Institutions use VWAP as a fair-value benchmark. It helps you see which side (buyers or sellers) is currently winning today's auction.",
      simpleStates: [
        { label: "Price Above VWAP", description: "Buyers are generally in control; traders who bought today are mostly in profit.", tone: "BULLISH" },
        { label: "Price Near VWAP", description: "Market is balanced around fair value.", tone: "NEUTRAL" },
        { label: "Price Below VWAP", description: "Sellers are generally in control; buyers who bought today are mostly in loss.", tone: "BEARISH" }
      ],
      simpleExample: "EXAMPLE: When NIFTY stays above VWAP and bounces whenever it touches it, it shows buyers are defending the intraday average.",
      rememberThis: "VWAP is an intraday benchmark, NOT a magical guaranteed wall. If price crosses back and forth repeatedly, the market is choppy.",
      simpleMistake: "Shorting a strong upward trend just because price is high above VWAP.",
      jargonBreakdown: {
        term: "VWAP",
        fullName: "Volume Weighted Average Price",
        simpleExplanation: "The true volume-weighted average price paid by all traders today."
      },
      nextConcept: { id: "support_resistance", label: "Support & Resistance" }
    },
    intermediate: {
      definition: "Intraday benchmark calculated as total value traded divided by total volume traded.",
      whatItMeasures: "The true volume-weighted mean price paid by all intraday participants.",
      ranges: [
        { label: "Above VWAP", range: "Price > VWAP", interpretation: "Buyers maintain intraday control. Longs are generally in profit.", tone: "BULLISH" },
        { label: "At VWAP / Neutral", range: "Price ≈ VWAP", interpretation: "Fair value equilibrium. Balance between buyers and sellers.", tone: "NEUTRAL" },
        { label: "Below VWAP", range: "Price < VWAP", interpretation: "Sellers maintain intraday control. Shorts or sellers hold advantageous pricing.", tone: "BEARISH" }
      ],
      traderTakeaway: "Trade with the side of VWAP: favor longs above VWAP, favor shorts below VWAP; avoid directional entries during frequent VWAP whipsaws.",
      commonMistake: "Fading strong trends just because price is extended from VWAP without confirmation of exhaustion.",
      confirmWith: ["Market Breadth", "Opening Range", "Volume"],
      invalidationNotes: ["A close back through VWAP with expanding volume invalidates intraday directional bias."],
      relatedMetrics: ["Volume", "Price Action", "Floor Pivots"],
      infoDetail: {
        whatIsThis: "VWAP is the average price weighted by volume, resetting at market open each morning.",
        howTradersInterpretIt: "Price above VWAP indicates institutional buying dominance; price below indicates supply dominance.",
        commonRanges: "Acts as dynamic support in uptrends and dynamic resistance in downtrends.",
        confirmWith: "Combine with Market Breadth and Higher Low structure.",
        commonMistake: "Taking counter-trend fades when price is trending smoothly above VWAP all morning."
      }
    },
    advanced: {
      mechanics: "Calculated continuously from tick-level cash/futures trade streams as $\\frac{\\Sigma(P_i \\times V_i)}{\\Sigma V_i}$, resetting at 09:15 IST daily.",
      detailedRanges: [
        { label: "Trend Day Expansion", range: "Price > VWAP + 1.5 StdDev", regimeContext: "Institutional Markup", optionOrMarketImpact: "One-way momentum; VWAP slope is positive; pullbacks to VWAP hold cleanly." },
        { label: "Mean-Reverting Corridor", range: "Within ±0.5 StdDev of VWAP", regimeContext: "Rotational Equilibrium", optionOrMarketImpact: "Price repeatedly crosses VWAP; mean-reversion strategies dominate." },
        { label: "Trend Day Liquidation", range: "Price < VWAP - 1.5 StdDev", regimeContext: "Institutional Markdown", optionOrMarketImpact: "Persistent supply; bounces to VWAP are aggressively sold." }
      ],
      regimeContext: "VWAP is the primary execution benchmark for institutional order execution algorithms (TWAP/VWAP algorithms). Algorithmic participation clusters around VWAP tests.",
      confluenceRules: [
        "Price Pullback to VWAP + Confluence with Prior Day High + Breadth > 32 ADV = Prime Institutional Trend Long Setup."
      ],
      failureConditions: ["In choppy, non-trending regimes, price oscillates back and forth through VWAP, generating false breakout signals."],
      edgeCases: ["Opening 15 minutes: VWAP is unstable and highly volatile due to low cumulative volume base."],
      relatedConcepts: ["Anchored VWAP (AVWAP)", "VWAP Standard Deviation Bands", "Institutional Execution Algorithms"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY opens with a +60 pt gap, tests VWAP at 10:15 AM at 24,280, prints a bullish rejection hammer on rising volume, and resumes rallying to 24,400. Institutional algorithms actively defend the VWAP benchmark.",
      infoDetail: {
        definition: "Volume-weighted mean price representing intraday fair value.",
        mechanics: "Cumulative value divided by cumulative volume from market open.",
        regimeContext: "Serves as the intraday dividing line between buyer dominance and seller dominance.",
        confluence: "Pair with Standard Deviation Bands and Structural Pivot Levels.",
        failureConditions: "Frequent horizontal sine-wave whipsawing in range-bound markets.",
        edgeCases: "First 15 minutes of trading before volume stabilizes.",
        relatedMetrics: "Anchored VWAP, Moving Averages, Value Area"
      }
    }
  },
  {
    id: "adx",
    name: "ADX",
    category: "TECHNICAL",
    beginnerGroup: "STRENGTH",
    canonicalDefinition: "Average Directional Index measuring the non-directional strength and velocity of an underlying price trend.",
    beginner: {
      shortLabel: "ADX (Trend Strength)",
      friendlySubtitle: "How strong is the current trend?",
      simpleDefinition: "ADX is an indicator that tells you whether the market is strongly trending or moving sideways in a chop.",
      whyItMatters: "It helps you choose the right strategy: trend-following when ADX is high, or range trading when ADX is low.",
      simpleStates: [
        { label: "Weak / Sideways", rangeText: "Below 20", description: "No clear trend; price is moving sideways or chopping.", tone: "NEUTRAL" },
        { label: "Strong Trend", rangeText: "Above 25", description: "A powerful trend is active; moves have strong momentum.", tone: "BULLISH" }
      ],
      simpleExample: "EXAMPLE: When ADX is 35, the market is in a powerful trend. Trend-following strategies generally perform best.",
      rememberThis: "ADX does NOT tell you whether the market is going UP or DOWN. A rising ADX during a selloff means a strong DOWN trend.",
      simpleMistake: "Assuming a rising ADX always means price is rising.",
      jargonBreakdown: {
        term: "ADX",
        fullName: "Average Directional Index",
        simpleExplanation: "A gauge measuring how strong a trend is (without telling you the direction)."
      },
      nextConcept: { id: "rsi", label: "RSI (Relative Strength Index)" }
    },
    intermediate: {
      definition: "14-period indicator quantifying the strength of a price trend regardless of direction.",
      whatItMeasures: "Trend velocity and momentum presence versus non-trending chop.",
      ranges: [
        { label: "Absent / Chop", range: "< 15.0", interpretation: "No discernible trend. Strong mean-reversion and whipsaw environment.", tone: "NEUTRAL" },
        { label: "Weak / Developing", range: "15.0 – 20.0", interpretation: "Early trend development or transition phase.", tone: "NEUTRAL" },
        { label: "Established Trend", range: "20.0 – 25.0", interpretation: "Clear directional momentum underway. Breakout setups become more viable.", tone: "BULLISH" },
        { label: "Strong Trend", range: "25.0 – 40.0", interpretation: "Robust directional trending. Favor trend-following strategies; avoid counter-trend fades.", tone: "BULLISH" },
        { label: "Extreme / Climax", range: "> 40.0", interpretation: "Very powerful trend or mature momentum approaching exhaustion phase.", tone: "CAUTION" }
      ],
      traderTakeaway: "Use ADX to decide whether to employ trend-following or range-bound mean-reversion tactics.",
      commonMistake: "Assuming a rising ADX means price is rising. ADX rises during strong down trends too.",
      confirmWith: ["RSI", "Price Action (HH/HL or LH/LL)", "VWAP"],
      invalidationNotes: ["ADX dropping below 20 signals the trend is stalling and entering consolidation."],
      relatedMetrics: ["RSI", "ATR", "Trend vs Range"],
      infoDetail: {
        whatIsThis: "ADX measures how strongly a market is trending, without regard to whether the trend is up or down.",
        howTradersInterpretIt: "ADX > 25 indicates strong trend strength; ADX < 15 indicates sideways chop.",
        commonRanges: "<15 chop, 20-25 developing, 25-40 strong trend, >40 extreme.",
        confirmWith: "Pair with price direction (Higher Highs or Lower Lows) to determine trend vector.",
        commonMistake: "Fading breakouts when ADX is rising above 30."
      }
    },
    advanced: {
      mechanics: "Derived from Wilder's Directional Movement Index (+DI and -DI) over 14 periods, smoothed as an exponential moving average of DX.",
      detailedRanges: [
        { label: "Compression / Chop", range: "< 18.0", regimeContext: "Mean Reversion", optionOrMarketImpact: "Premium decay favored; breakout strategies face repeated whipsaws." },
        { label: "Trend Ignition", range: "20.0 – 28.0 (Rising)", regimeContext: "Breakout Expansion", optionOrMarketImpact: "Directional options buying viable; trailing stops on momentum legs." },
        { label: "Parabolic Trend", range: "35.0 – 50.0", regimeContext: "Mature Momentum", optionOrMarketImpact: "Counter-trend trades have very low edge; watch for blow-off exhaustion." }
      ],
      regimeContext: "ADX filters market regime: eliminates false trend signals during range days and prevents destructive counter-trend fading during trend days.",
      confluenceRules: [
        "ADX > 25 (Rising) + Price > VWAP + Breadth > 32 ADV = Prime Trend-Following Confluence."
      ],
      failureConditions: ["ADX is a lagging smoothed indicator; by the time ADX crosses 25, a significant portion of the initial impulse may have completed."],
      edgeCases: ["V-shaped sudden reversals: ADX stays high because it measures raw movement, but the underlying direction has flipped."],
      relatedConcepts: ["+DI / -DI Crossovers", "Trend Regime Filters", "ATR Volatility Ratio"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY breaks a 3-day consolidation range. ADX was 13.5 (extreme chop) and spikes to 22.4 on the breakout bar. Traders switch strategies from range-bound selling to breakout trend-following.",
      infoDetail: {
        definition: "Smoothed indicator quantifying non-directional trend strength.",
        mechanics: "Exponential average of directional movement differentials (+DI / -DI).",
        regimeContext: "Regime filter separating directional expansion from rotational chop.",
        confluence: "Cross-verify with +DI/-DI spread and Volume expansion.",
        failureConditions: "Lag in registering sharp V-reversals.",
        edgeCases: "Range expansion spikes that immediately compress.",
        relatedMetrics: "DMI (+DI / -DI), ATR, RSI"
      }
    }
  },
  {
    id: "rsi",
    name: "RSI",
    category: "TECHNICAL",
    beginnerGroup: "STRENGTH",
    canonicalDefinition: "Relative Strength Index momentum oscillator evaluating the speed and change of price movements on a 0 to 100 bounded scale.",
    beginner: {
      shortLabel: "RSI (Momentum)",
      friendlySubtitle: "Is price momentum stretched?",
      simpleDefinition: "RSI measures the speed and power of recent price gains compared to recent price drops.",
      whyItMatters: "It helps you see if buyers or sellers are pushing with strong speed, or if the move is running out of steam.",
      simpleStates: [
        { label: "Strong Upward Momentum", rangeText: "Above 60", description: "Buyers are pushing with strong speed and energy.", tone: "BULLISH" },
        { label: "Balanced", rangeText: "40 – 60", description: "Normal balanced price action.", tone: "NEUTRAL" },
        { label: "Strong Downward Momentum", rangeText: "Below 40", description: "Sellers are pushing with strong speed and energy.", tone: "BEARISH" }
      ],
      simpleExample: "EXAMPLE: During a strong bull trend, RSI can stay above 70 for hours while the market adds another 100 points.",
      rememberThis: "A high RSI (>70) does NOT mean sell immediately. It often means the upward trend has very strong momentum.",
      simpleMistake: "Blindly selling just because RSI crosses above 70.",
      jargonBreakdown: {
        term: "RSI",
        fullName: "Relative Strength Index",
        simpleExplanation: "A 0–100 scale measuring the speed and power of price momentum."
      },
      nextConcept: { id: "macd", label: "MACD" }
    },
    intermediate: {
      definition: "14-period momentum oscillator comparing magnitude of recent gains to recent losses.",
      whatItMeasures: "Speed and change of price momentum on a 0 to 100 bounded scale.",
      ranges: [
        { label: "Extreme Overbought", range: "> 80", interpretation: "Very strong upward momentum; watch for divergence or parabolic exhaustion.", tone: "CAUTION" },
        { label: "Overbought / Bullish Zone", range: "60 – 80", interpretation: "Strong bullish momentum characteristic of robust upward trends.", tone: "BULLISH" },
        { label: "Neutral / Equilibrium", range: "40 – 60", interpretation: "Balanced momentum. Typical of range-bound markets.", tone: "NEUTRAL" },
        { label: "Oversold / Bearish Zone", range: "20 – 40", interpretation: "Strong bearish momentum characteristic of sustained downtrends.", tone: "BEARISH" },
        { label: "Extreme Oversold", range: "< 20", interpretation: "Extended downward momentum; monitor for capitulation bounce or divergence.", tone: "CAUTION" }
      ],
      traderTakeaway: "In strong trends, RSI stays overbought (> 70) or oversold (< 30) for extended periods; use RSI for divergence and regime confirmation rather than blind fade triggers.",
      commonMistake: "Selling immediately when RSI crosses 70 in a strong trend day. Overbought often means strong momentum.",
      confirmWith: ["Price Structure (HH/HL)", "ADX", "Market Breadth"],
      invalidationNotes: ["Bearish divergence: Price makes higher high while RSI makes lower high."],
      relatedMetrics: ["MACD", "ADX", "VWAP"],
      infoDetail: {
        whatIsThis: "RSI measures price momentum by evaluating the ratio of average gains to average losses over 14 periods.",
        howTradersInterpretIt: "RSI > 70 reflects strong positive price momentum; RSI < 30 reflects strong negative price momentum.",
        commonRanges: "Bullish trend zone is 55–80; Bearish trend zone is 20–45; 40–60 is neutral.",
        confirmWith: "Combine with Higher Low price action and ADX trend strength.",
        commonMistake: "Treating overbought as an immediate sell trigger in powerful trend environments."
      }
    },
    advanced: {
      mechanics: "Calculated as $RSI = 100 - \\frac{100}{1 + RS}$, where $RS = \\frac{\\text{Smoothed Avg Gain}}{\\text{Smoothed Avg Loss}}$ over 14 periods.",
      detailedRanges: [
        { label: "Bullish Momentum Range", range: "55 – 80 (Support at 45)", regimeContext: "Bull Market Regime", optionOrMarketImpact: "RSI oscillates in upper range; dips to 45–50 act as momentum support." },
        { label: "Bearish Momentum Range", range: "20 – 45 (Resistance at 55)", regimeContext: "Bear Market Regime", optionOrMarketImpact: "RSI oscillates in lower range; rallies to 50–55 act as momentum resistance." },
        { label: "Structural Divergence", range: "Divergent Extremes", regimeContext: "Exhaustion Warning", optionOrMarketImpact: "Price prints higher high while RSI prints lower high with volume contraction." }
      ],
      regimeContext: "Andrew Cardwell's RSI Range Shift theory: during true bull regimes, RSI floor shifts up to 40–50; during bear regimes, RSI ceiling shifts down to 55–60.",
      confluenceRules: [
        "Bearish RSI Divergence + Price at Call Wall + Breadth Deteriorating = High-Probability Reversal Setup."
      ],
      failureConditions: ["In runaway institutional trend days, RSI can stay pinned at 75–85 all session while price rises hundreds of points."],
      edgeCases: ["Gaps: Large opening gaps distort the 14-period RSI calculation until enough intraday bars populate."],
      relatedConcepts: ["Cardwell Range Shift", "Hidden Divergence", "Multi-Timeframe Momentum Alignment"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY climbs from 24,200 to 24,350 with RSI at 78. Price pulls back to 24,300 where RSI resets to 52 (bullish support zone) while holding VWAP. Price then rallies to 24,450, demonstrating momentum range retention.",
      infoDetail: {
        definition: "Bounded 0–100 momentum oscillator tracking price change velocity.",
        mechanics: "Ratio of smoothed exponential average gains to average losses.",
        regimeContext: "Identifies momentum health, range shifts, and structural exhaustion divergences.",
        confluence: "Cross-verify with Volume Profile and Structural Resistance.",
        failureConditions: "Momentum embedding during runaway institutional trend days.",
        edgeCases: "Opening gap distortions in 14-period lookbacks.",
        relatedMetrics: "MACD, ADX, Stochastic Oscillator"
      }
    }
  },
  {
    id: "macd",
    name: "MACD",
    category: "TECHNICAL",
    beginnerGroup: "STRENGTH",
    canonicalDefinition: "Moving Average Convergence Divergence trend-following momentum indicator tracking the relationship between two exponential moving averages.",
    beginner: {
      shortLabel: "MACD",
      friendlySubtitle: "Is short-term momentum speeding up or slowing down?",
      simpleDefinition: "MACD compares a faster moving average to a slower moving average to see if price momentum is accelerating or losing steam.",
      whyItMatters: "It helps confirm whether a trend is speeding up in your favor or slowing down.",
      simpleStates: [
        { label: "Bullish Crossover", description: "Short-term momentum has crossed above the longer-term trend.", tone: "BULLISH" },
        { label: "Bearish Crossover", description: "Short-term momentum has crossed below the longer-term trend.", tone: "BEARISH" }
      ],
      simpleExample: "EXAMPLE: When MACD bars are growing taller and green, price momentum is accelerating upward.",
      rememberThis: "MACD is a lagging indicator. In sideways markets, it can give false signals as lines repeatedly cross back and forth.",
      simpleMistake: "Trading every tiny MACD crossover in a flat, choppy market.",
      jargonBreakdown: {
        term: "MACD",
        fullName: "Moving Average Convergence Divergence",
        simpleExplanation: "A tool that tracks how fast moving averages are separating (speeding up) or coming together (slowing down)."
      },
      nextConcept: { id: "atr", label: "ATR (Average True Range)" }
    },
    intermediate: {
      definition: "Moving Average Convergence Divergence trend-following momentum indicator (12, 26, 9).",
      whatItMeasures: "Relationship between two exponential moving averages and their rate of acceleration.",
      ranges: [
        { label: "Bullish Crossover", range: "MACD > Signal Line", interpretation: "Short-term momentum accelerating above longer-term trend.", tone: "BULLISH" },
        { label: "Histogram Expansion", range: "Bars Growing (+)", interpretation: "Momentum impulse strengthening in current direction.", tone: "BULLISH" },
        { label: "Histogram Contraction", range: "Bars Shrinking", interpretation: "Momentum decelerating. Potential consolidation or retracement approaching.", tone: "CAUTION" },
        { label: "Bearish Crossover", range: "MACD < Signal Line", interpretation: "Short-term momentum deteriorating below longer-term trend.", tone: "BEARISH" }
      ],
      traderTakeaway: "Use MACD zero-line positioning to identify overall trend regime and signal crossovers for timing.",
      commonMistake: "Trading every MACD crossover in sideways choppy markets, which leads to frequent whipsaws.",
      confirmWith: ["Zero Line Alignment", "RSI", "Price vs VWAP"],
      invalidationNotes: ["Histogram shrinking while price pushes into resistance indicates momentum deceleration."],
      relatedMetrics: ["RSI", "ADX", "VWAP"],
      infoDetail: {
        whatIsThis: "MACD tracks the difference between a 12-period EMA and a 26-period EMA, plotted against a 9-period Signal line.",
        howTradersInterpretIt: "Positive MACD above zero confirms upward momentum; negative MACD below zero confirms downward momentum.",
        commonRanges: "Above zero is bullish regime; below zero is bearish regime.",
        confirmWith: "Confirm with price action higher highs and volume expansion.",
        commonMistake: "Trading crossovers when price is oscillating inside a tight horizontal range."
      }
    },
    advanced: {
      mechanics: "Calculated as $MACD = EMA_{12}(P) - EMA_{26}(P)$, Signal Line $= EMA_9(MACD)$, Histogram $= MACD - Signal$.",
      detailedRanges: [
        { label: "Zero-Line Acceleration", range: "MACD > 0 and Rising", regimeContext: "Bullish Expansion", optionOrMarketImpact: "12 EMA separating from 26 EMA; institutional momentum dominant." },
        { label: "Deceleration / Re-test", range: "Histogram Ticking Inward", regimeContext: "Consolidation", optionOrMarketImpact: "Momentum slowing; potential pullback to short-term moving average." },
        { label: "Zero-Line Breakdown", range: "MACD < 0 and Falling", regimeContext: "Bearish Expansion", optionOrMarketImpact: "Persistent downward momentum; sellers control multi-period trend." }
      ],
      regimeContext: "Zero-line positioning defines structural regime: crossovers occurring ABOVE zero represent high-conviction bullish continuation, while crossovers BELOW zero represent weak counter-trend bounces.",
      confluenceRules: [
        "MACD Bullish Crossover Above Zero Line + Price Above VWAP + Breadth > 32 ADV = Strong Continuation Signal."
      ],
      failureConditions: ["Lag: In volatile whipsaw regimes, signal crossovers lag rapid price reversals."],
      edgeCases: ["Extended multi-week trends where histogram stays flat near zero while underlying index grinds higher."],
      relatedConcepts: ["Histogram Divergence", "Zero-Line Rejection", "Multi-Timeframe MACD Alignment"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY pulls back from 24,400 to 24,320. MACD remains well above the zero line and crosses back above the signal line as histogram turns positive. This zero-line confirmation triggers institutional continuation buying.",
      infoDetail: {
        definition: "Trend-following momentum oscillator tracking exponential moving average divergence.",
        mechanics: "Difference between fast 12 EMA and slow 26 EMA relative to 9 EMA signal line.",
        regimeContext: "Zero-line separation establishes overall trend regime and momentum impulse health.",
        confluence: "Cross-reference with RSI and VWAP slope.",
        failureConditions: "Repeated whipsaws in horizontal trading ranges.",
        edgeCases: "Slow grinding trends with flat histogram output.",
        relatedMetrics: "RSI, Exponential Moving Averages, ADX"
      }
    }
  },
  {
    id: "atr",
    name: "ATR",
    category: "TECHNICAL",
    beginnerGroup: "STRENGTH",
    canonicalDefinition: "Average True Range measuring the typical realized volatility and price range per period, accounting for gaps.",
    beginner: {
      shortLabel: "ATR (Expected Range)",
      friendlySubtitle: "How many points does NIFTY typically move in a day?",
      simpleDefinition: "ATR tells you the typical range (in points) that NIFTY moves in a day or timeframe.",
      whyItMatters: "It helps you set realistic profit targets and stop losses that fit the current market's actual movement.",
      simpleStates: [
        { label: "High ATR", rangeText: "Wide swings", description: "Daily moves are wider; need wider stops and bigger targets.", tone: "CAUTION" },
        { label: "Low ATR", rangeText: "Tight swings", description: "Daily moves are compressed and quiet.", tone: "NEUTRAL" }
      ],
      simpleExample: "EXAMPLE: If NIFTY's daily ATR is 180 points, a 15-point stop loss might be too tight and get hit by normal random market noise.",
      rememberThis: "ATR does NOT tell you which way price will go. It only tells you how wide the typical swings are.",
      simpleMistake: "Using the exact same 20-point stop loss every day, regardless of whether the market is calm or crazy.",
      jargonBreakdown: {
        term: "ATR",
        fullName: "Average True Range",
        simpleExplanation: "A measure of the typical point-range price moves over recent periods."
      },
      nextConcept: { id: "risk_rules", label: "Risk Management Rules" }
    },
    intermediate: {
      definition: "14-period indicator measuring market volatility through price range analysis.",
      whatItMeasures: "The typical realized trading range per period, accounting for gaps.",
      ranges: [
        { label: "High Volatility", range: "ATR Expanding (+)", interpretation: "Daily/intraday range widening. Larger price targets and wider stops required.", tone: "CAUTION" },
        { label: "Low Volatility", range: "ATR Compressing (-)", interpretation: "Narrow range consolidation. Range compression often precedes breakout expansion.", tone: "NEUTRAL" }
      ],
      traderTakeaway: "Base stop loss distances and profit target multiples on ATR rather than fixed arbitrary rupee amounts.",
      commonMistake: "Using fixed 20-point stop losses regardless of whether daily ATR is 80 points or 250 points.",
      confirmWith: ["India VIX", "Standard Deviation", "Stop Sizing Matrix"],
      invalidationNotes: ["Range compression (falling ATR) typically precedes sharp volatility expansion."],
      relatedMetrics: ["India VIX", "ADX", "Risk Management Rules"],
      infoDetail: {
        whatIsThis: "ATR measures the average true range of price movement over 14 periods, factoring in overnight gaps.",
        howTradersInterpretIt: "High ATR indicates wide price swings; low ATR indicates tight, compressed ranges.",
        commonRanges: "NIFTY daily ATR typically ranges between 100 and 250 points.",
        confirmWith: "Use ATR multiples (e.g. 1.5x ATR) to calibrate stop losses and target expectations.",
        commonMistake: "Trading fixed stop distances when market volatility doubles."
      }
    },
    advanced: {
      mechanics: "Calculated as the 14-period smoothed average of True Range, where $TR = \\max(H-L, |H-C_{prev}|, |L-C_{prev}|)$.",
      detailedRanges: [
        { label: "Range Compression", range: "ATR < 20-day 20th Percentile", regimeContext: "Volatility Squeeze", optionOrMarketImpact: "Option straddle prices cheap; high probability of imminent directional expansion." },
        { label: "Normal Realized Volatility", range: "Within 20th–80th Percentile", regimeContext: "Standard Realized Range", optionOrMarketImpact: "Standard intraday extensions; 1.0x ATR target projection holds." },
        { label: "Range Expansion", range: "ATR > 80th Percentile", regimeContext: "High-Volatility Regime", optionOrMarketImpact: "Wider slippage; reduce position size to maintain constant account risk." }
      ],
      regimeContext: "Essential for volatility-normalized risk budgeting ($Risk = Size \\times k \\times ATR$). Ensures position size automatically scales down when volatility expands.",
      confluenceRules: [
        "Intraday Move Reaches 1.5x Daily ATR + Major Structural Resistance Hit = High Mean-Reversion Exhaustion Zone."
      ],
      failureConditions: ["Non-directional: high ATR provides zero information on trend continuation vs reversal."],
      edgeCases: ["Single abnormal event gap bar artificially skewing the 14-period ATR reading for the next two weeks."],
      relatedConcepts: ["Chandelier Exits", "Keltner Channels", "Volatility-Adjusted Sizing"],
      advancedHypotheticalExample: "HYPOTHETICAL: NIFTY's 14-day ATR expands from 110 pts to 220 pts during earnings season. A disciplined trader cuts contract position sizing from 600 qty to 300 qty and widens stop distance from 25 pts to 50 pts, keeping total rupee risk exactly ₹15,000.",
      infoDetail: {
        definition: "True Range volatility measurement accounting for overnight price gaps.",
        mechanics: "Smoothed moving average of maximum true price excursions.",
        regimeContext: "Core engine for volatility-adjusted position sizing and realistic target modeling.",
        confluence: "Cross-reference with India VIX and Bollinger Band width.",
        failureConditions: "Zero directional predictive capacity.",
        edgeCases: "Single freak gap distorting rolling 14-period average.",
        relatedMetrics: "India VIX, Realized Volatility, Keltner Bands"
      }
    }
  },
  {
    id: "implied_volatility",
    name: "IMPLIED VOLATILITY (IV)",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "The market's forecast of underlying asset movement priced into option premiums.",
    beginner: {
      shortLabel: "Implied Volatility (IV)",
      friendlySubtitle: "Are option prices cheap or expensive right now?",
      simpleDefinition: "Implied Volatility (IV) tells you whether option premiums are currently priced expensive or cheap.",
      whyItMatters: "High IV makes option prices expensive. Low IV makes option prices relatively cheaper to buy.",
      simpleStates: [
        { label: "High IV", rangeText: "Expensive Options", description: "Options are costly; option sellers get high premium, buyers face high hurdles.", tone: "CAUTION" },
        { label: "Low IV", rangeText: "Cheap Options", description: "Option premiums are cheaper with lower cost to buy.", tone: "NEUTRAL" }
      ],
      simpleExample: "EXAMPLE: Before a major election or budget, IV spikes because traders are uncertain. Right after the event, IV collapses (called IV Crush).",
      rememberThis: "Buying options right before a big news event is risky because even if you guess the direction right, option prices can crash due to IV Crush.",
      simpleMistake: "Buying expensive options right before a big event without knowing about IV Crush.",
      jargonBreakdown: {
        term: "IV",
        fullName: "Implied Volatility",
        simpleExplanation: "A percentage showing how much volatility is baked into the current price of an option."
      },
      nextConcept: { id: "call_wall", label: "Call Wall & Put Wall" }
    },
    intermediate: {
      definition: "Market's forecast of underlying asset movement priced into option premiums.",
      whatItMeasures: "Option price richness and market expectation of future realized volatility.",
      ranges: [
        { label: "High IV", range: "IV Rank > 70%", interpretation: "Option premiums are expensive. Option sellers receive high premium; buyers face high hurdle.", tone: "CAUTION" },
        { label: "Normal IV", range: "IV Rank 30% – 70%", interpretation: "Balanced option pricing consistent with prevailing historical volatility.", tone: "NEUTRAL" },
        { label: "Low IV", range: "IV Rank < 30%", interpretation: "Option premiums are cheap. Lower theta risk for buyers; low premium cushion for sellers.", tone: "NEUTRAL" }
      ],
      traderTakeaway: "Be aware of IV Crush: buying options immediately before major binary events often loses value even if direction is correct.",
      commonMistake: "Buying OTM options during elevated IV spikes without considering post-event IV collapse.",
      confirmWith: ["India VIX", "IV Rank", "Historical Volatility"],
      invalidationNotes: ["Post-event IV crush rapidly reduces option premium values across all strikes."],
      relatedMetrics: ["India VIX", "PCR", "Open Interest"],
      infoDetail: {
        whatIsThis: "Implied Volatility is the volatility percentage implied by the market prices of options via pricing models.",
        howTradersInterpretIt: "High IV makes option contracts expensive; low IV makes option contracts relatively cheap.",
        commonRanges: "IV Rank > 70% is expensive; IV Rank < 30% is cheap.",
        confirmWith: "Compare IV with Realized Volatility to identify overpriced or underpriced options.",
        commonMistake: "Buying options before major binary events without planning for IV collapse."
      }
    },
    advanced: {
      mechanics: "Calculated by inverting Black-Scholes-Merton or binomial pricing algorithms to solve for standard deviation $(\\sigma)$ given observable market premium, strike, DTE, and risk-free rate.",
      detailedRanges: [
        { label: "IV Compression", range: "IV Rank < 20%", regimeContext: "Subdued Premiums", optionOrMarketImpact: "Vega risk low for buyers; long straddles/strangles have favorable risk-reward." },
        { label: "IV Expansion", range: "IV Rank 50% – 80%", regimeContext: "Demand Surge", optionOrMarketImpact: "Spreads preferred over naked options; premium selling provides high cushion." },
        { label: "IV Blowout / Climax", range: "IV Rank > 90%", regimeContext: "Panic / Crisis Bid", optionOrMarketImpact: "Extreme put skew; naked buying carries massive IV crush vulnerability." }
      ],
      regimeContext: "Volatility Skew: OTM put options typically trade at higher IV than corresponding OTM call options (the volatility smile/smirk) due to institutional downside tail-risk hedging.",
      confluenceRules: [
        "Elevated IV Rank (> 75%) + Spot at Strong Put Wall + Stable VIX = Prime Credit Spread / Covered Writing Environment."
      ],
      failureConditions: ["In explosive black-swan gaps, high IV continues expanding, causing catastrophic losses for naked option sellers despite high premium cushion."],
      edgeCases: ["Earnings IV crush: Overnight 50% IV collapse in individual stock options upon earnings release."],
      relatedConcepts: ["Volatility Skew & Smile", "IV Rank vs IV Percentile", "Vega Exposure"],
      advancedHypotheticalExample: "HYPOTHETICAL: Ahead of RBI Policy, 24,300 ATM Straddle trades at 340 pts (IV Rank 85%). RBI announces expected rate decision with no surprise. Within 15 minutes, ATM Straddle collapses to 210 pts purely due to IV Crush, even though NIFTY moved only 10 points.",
      infoDetail: {
        definition: "Forward-looking volatility percentage implied by market option pricing.",
        mechanics: "Inverse solution to option pricing PDE given traded market bid-asks.",
        regimeContext: "Determines option buyer hurdle rate, option seller edge, and strategy selection.",
        confluence: "Evaluate alongside Volatility Skew and Historical Realized Volatility.",
        failureConditions: "Runaway gaps blowing through credit spread short strikes.",
        edgeCases: "Binary event IV collapse immediately upon catalyst release.",
        relatedMetrics: "India VIX, Vega Delta, IV Skew"
      }
    }
  },
  {
    id: "max_pain",
    name: "MAX PAIN",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "The strike price where total option buyer payout (intrinsic value) would be minimized at expiry.",
    beginner: {
      shortLabel: "Max Pain",
      friendlySubtitle: "Where would option buyers lose the most money at expiry?",
      simpleDefinition: "Max Pain is the specific strike price where the highest number of option buyers would lose money if the market closed there on expiry day.",
      whyItMatters: "On expiry day afternoons, price sometimes drifts toward the Max Pain strike if there is no strong trend.",
      simpleStates: [
        { label: "Price Above Max Pain", description: "Call buyers are in the money; price may experience slight gravitational pull toward Max Pain near expiry if momentum slows.", tone: "NEUTRAL" },
        { label: "Price Near Max Pain", description: "Pinning zone; common on quiet expiry afternoons.", tone: "NEUTRAL" },
        { label: "Price Below Max Pain", description: "Put buyers are in the money; price may drift higher toward Max Pain if selling dries up.", tone: "NEUTRAL" }
      ],
      simpleExample: "EXAMPLE: On a quiet Thursday afternoon at 2:00 PM, NIFTY often settles close to the Max Pain strike as option writers defend their positions.",
      rememberThis: "Max Pain is NOT a guaranteed magnet. On strong trend days, the market will trend far away from Max Pain without looking back.",
      simpleMistake: "Treating Max Pain as a guaranteed price target on regular non-expiry days.",
      jargonBreakdown: {
        term: "Max Pain",
        fullName: "Maximum Pain Theory",
        simpleExplanation: "The strike price where the combined financial payout to option buyers is lowest at expiry."
      },
      nextConcept: { id: "call_wall", label: "Call Wall & Put Wall" }
    },
    intermediate: {
      definition: "Strike price where total option buyer payout (intrinsic value) would be minimized at expiry.",
      whatItMeasures: "The theoretical point of maximum financial loss for aggregate option buyers.",
      ranges: [
        { label: "Spot Above Max Pain", range: "Spot > Max Pain", interpretation: "Call buyers in the money; potential gravitational pull toward Max Pain near expiry if momentum slows.", tone: "NEUTRAL" },
        { label: "Spot At Max Pain", range: "Spot ≈ Max Pain", interpretation: "Pinning zone. Common settlement area during low-momentum expiry afternoons.", tone: "NEUTRAL" },
        { label: "Spot Below Max Pain", range: "Spot < Max Pain", interpretation: "Put buyers in the money; potential upward drift toward Max Pain if selling dries up.", tone: "NEUTRAL" }
      ],
      traderTakeaway: "Max Pain is most relevant in the final 2–3 hours of expiry day during range-bound conditions; it is easily overwhelmed by strong trend days.",
      commonMistake: "Treating Max Pain as a guaranteed directional target on non-expiry days or during strong trend days.",
      confirmWith: ["Call Wall Strike", "Put Wall Strike", "Expiry Day Timing (13:30+ IST)"],
      invalidationNotes: ["Strong institutional trend days ignore Max Pain completely."],
      relatedMetrics: ["Call Wall", "Put Wall", "PCR (OI)"],
      infoDetail: {
        whatIsThis: "Max Pain is the strike at which the aggregate monetary value of all active calls and puts expires with minimal payout.",
        howTradersInterpretIt: "Market makers and option writers profit most when price settles close to the Max Pain strike.",
        commonRanges: "Most actionable on expiry day between 13:30 and 15:15 IST.",
        confirmWith: "Cross-check with ATM Straddle pinning and quiet volume.",
        commonMistake: "Using Max Pain for directional forecasting early in the weekly expiry cycle."
      }
    },
    advanced: {
      mechanics: "Calculated iteratively as $\\text{argmin}_S \\left( \\Sigma [OI_{Call,K} \\times \\max(0, S-K)] + \\Sigma [OI_{Put,K} \\times \\max(0, K-S)] \\right)$ across all active strikes $K$.",
      detailedRanges: [
        { label: "Pinning Equilibrium", range: "Spot within ±25 pts of Max Pain", regimeContext: "Expiry Afternoon Gamma Pin", optionOrMarketImpact: "Dealers maintain delta neutrality without re-hedging; premium decays to zero smoothly." },
        { label: "Trend Dislocation", range: "Spot > 100 pts from Max Pain", regimeContext: "Breakout Trend Day", optionOrMarketImpact: "Institutional trend forces dealers into continuous directional re-hedging, abandoning Max Pain." }
      ],
      regimeContext: "Dealer Gamma Pinning: When market makers are net short options, they must buy when spot rises and sell when spot falls, creating an artificial gravitational dampener toward heavy open interest strikes.",
      confluenceRules: [
        "Expiry Day 14:00 IST + Low ATR + Spot between Call Wall & Put Wall + Max Pain Coinciding = High Expiry Pin Confluence."
      ],
      failureConditions: ["Strong external macro shocks or heavyweight institutional flows completely overpower dealer gamma pinning."],
      edgeCases: ["Shifting Max Pain: Heavy intraday option writing can cause the Max Pain strike to migrate dynamically during the session."],
      relatedConcepts: ["Gamma Pinning", "Dealer Delta Hedging", "Zero-DTE Mechanics"],
      advancedHypotheticalExample: "HYPOTHETICAL: On weekly expiry at 13:30 IST, NIFTY trades at 24,310 while Max Pain is 24,300. With VIX subdued at 12.2 and breadth balanced (24 ADV), NIFTY compresses into a tight 24,295–24,315 corridor and settles at 24,302.",
      infoDetail: {
        definition: "Theoretical settlement price minimizing total aggregate option buyer intrinsic value.",
        mechanics: "Optimization minimizing aggregate cash payout across call and put open interest grids.",
        regimeContext: "Relevant primarily in late expiry sessions with low directional momentum.",
        confluence: "Evaluate alongside ATM Straddle decay and dealer gamma profile.",
        failureConditions: "Overrun by multi-sector institutional trending.",
        edgeCases: "Intraday Max Pain strike migration.",
        relatedMetrics: "Call Wall, Put Wall, GEX Profile"
      }
    }
  },
  {
    id: "call_wall",
    name: "CALL WALL",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "The specific strike price possessing the single highest Call Open Interest across the active expiry series.",
    beginner: {
      shortLabel: "Call Wall",
      friendlySubtitle: "Where is the biggest option ceiling overhead?",
      simpleDefinition: "The Call Wall is the strike price where sellers have built the largest pile of Call option positions.",
      whyItMatters: "Option sellers defend this level to keep their options worthless, making it act like a strong ceiling (resistance).",
      simpleStates: [
        { label: "Above Spot", description: "Market has room to move higher before hitting major option seller resistance.", tone: "BULLISH" },
        { label: "Near Spot", description: "Immediate ceiling overhead; market faces heavy resistance unless strong buyers break through.", tone: "CAUTION" },
        { label: "Broken Above", description: "Call sellers are trapped; if they panic and cover, price can shoot up fast.", tone: "BULLISH" }
      ],
      simpleExample: "EXAMPLE: If 24,500 has the highest Call OI, sellers will try hard to keep NIFTY below 24,500 until expiry.",
      rememberThis: "The Call Wall is NOT unbreakable. If buyers push price above it with heavy volume, sellers are forced to cover, creating a fast rally.",
      simpleMistake: "Shorting blindly at the Call Wall when market breadth is overwhelmingly positive.",
      jargonBreakdown: {
        term: "Call Wall",
        fullName: "Highest Call Open Interest Strike",
        simpleExplanation: "The strike price with the most short call options, acting as major resistance."
      },
      nextConcept: { id: "put_wall", label: "Put Wall" }
    },
    intermediate: {
      definition: "The specific strike price possessing the single highest Call Open Interest.",
      whatItMeasures: "Maximum overhead resistance boundary where call sellers have deployed greatest capital.",
      ranges: [
        { label: "Well Above Spot", range: "Call Wall > Spot + 1.5%", interpretation: "Plenty of upside room before encountering heavy option seller resistance.", tone: "BULLISH" },
        { label: "Near Spot", range: "Call Wall ≈ Spot + 0.3%", interpretation: "Immediate ceiling. Heavy resistance expected unless major breakout triggers call covering.", tone: "CAUTION" },
        { label: "Breached", range: "Spot > Call Wall", interpretation: "Call writers trapped. Rapid short covering can trigger parabolic upward expansion.", tone: "BULLISH" }
      ],
      traderTakeaway: "Use the Call Wall as a prime resistance anchor, but prepare for explosive upside if price convincingly holds above it.",
      commonMistake: "Shorting blindly at the Call Wall when volume and breadth are overwhelmingly bullish.",
      confirmWith: ["Market Breadth", "Volume", "Price vs VWAP"],
      invalidationNotes: ["A 15-minute close above the Call Wall with expanding volume signals short-covering acceleration."],
      relatedMetrics: ["Put Wall", "PCR (OI)", "Max Pain"],
      infoDetail: {
        whatIsThis: "The Call Wall is the strike price with the largest concentration of Call Open Interest in the active expiry.",
        howTradersInterpretIt: "Represents significant resistance because call writers defend this level to keep premiums worthless.",
        commonRanges: "Typically 1% to 2% above current spot in normal volatility regimes.",
        confirmWith: "Cross-check with Prior Day High and Floor Pivot R1/R2.",
        commonMistake: "Assuming the Call Wall cannot be broken during powerful institutional buying days."
      }
    },
    advanced: {
      mechanics: "Strike index $K_{CW} = \\text{argmax}_K (OI_{Call,K})$, representing the largest short gamma liability boundary for option writers and dealers.",
      detailedRanges: [
        { label: "Resistance Defense", range: "Spot approaching Call Wall with Breadth < 25 ADV", regimeContext: "Supply Defense", optionOrMarketImpact: "Call writers sell futures to hedge delta, stalling the rally at the strike." },
        { label: "Gamma Squeeze Trigger", range: "Spot sustaining 15m close > Call Wall + Volume Expansion", regimeContext: "Short Squeeze", optionOrMarketImpact: "Trapped call writers buy back calls and buy underlying futures, triggering sharp upward acceleration." }
      ],
      regimeContext: "Market Structure Ceiling: The Call Wall defines the expected upper boundary for the weekly market profile. Migration of the Call Wall higher signals institutional range expansion.",
      confluenceRules: [
        "Call Wall Strike Coinciding with Multi-Day Resistance + RSI Divergence = High-Conviction Reversal Zone."
      ],
      failureConditions: ["In runaway short squeezes, call writers capitulate, turning resistance into explosive fuel."],
      edgeCases: ["Call Wall Roll-Up: When writers rapidly abandon 24,300 and re-establish at 24,500, opening an instant 200-point vacuum."],
      relatedConcepts: ["Short Gamma Squeeze", "Call Skew", "Strike Migration"],
      advancedHypotheticalExample: "HYPOTHETICAL: 24,400 holds 1.4 crore Call OI (Call Wall). NIFTY trades to 24,405 with Breadth at 42 ADV and Bank Nifty +1.8%. Rather than reversing, call writers panic and cover 45 lakh contracts in 30 minutes, rocketing NIFTY straight to 24,520.",
      infoDetail: {
        definition: "Strike possessing maximum Call Open Interest concentration.",
        mechanics: "Defines maximum dealer short gamma and underwriting capital commitment.",
        regimeContext: "Acts as primary macro resistance until broken by institutional volume.",
        confluence: "Pair with Floor Pivot R2 and Historical Multi-Day Peaks.",
        failureConditions: "Gamma squeeze triggering explosive upward momentum.",
        edgeCases: "Intraday roll-up to higher strikes.",
        relatedMetrics: "Put Wall, PCR OI, Max Pain"
      }
    }
  },
  {
    id: "put_wall",
    name: "PUT WALL",
    category: "OPTIONS",
    beginnerGroup: "OPTIONS",
    canonicalDefinition: "The specific strike price possessing the single highest Put Open Interest across the active expiry series.",
    beginner: {
      shortLabel: "Put Wall",
      friendlySubtitle: "Where is the biggest option floor below us?",
      simpleDefinition: "The Put Wall is the strike price where sellers have built the largest pile of Put option positions.",
      whyItMatters: "Option sellers defend this level to keep their puts worthless, making it act like a strong floor (support).",
      simpleStates: [
        { label: "Below Spot", description: "Market has a solid cushion below current price.", tone: "BULLISH" },
        { label: "Near Spot", description: "Immediate support floor being tested right now.", tone: "NEUTRAL" },
        { label: "Broken Below", description: "Put sellers are trapped; panic selling can accelerate the drop.", tone: "BEARISH" }
      ],
      simpleExample: "EXAMPLE: If 24,000 has the highest Put OI, sellers will try hard to keep NIFTY above 24,000.",
      rememberThis: "The Put Wall is NOT an unbreakable floor. If price breaks and stays below it, put sellers are forced to dump positions, causing a fast drop.",
      simpleMistake: "Buying the dip blindly at the Put Wall when the whole market is collapsing.",
      jargonBreakdown: {
        term: "Put Wall",
        fullName: "Highest Put Open Interest Strike",
        simpleExplanation: "The strike price with the most short put options, acting as major support."
      },
      nextConcept: { id: "price_oi_matrix", label: "Price + OI Matrix" }
    },
    intermediate: {
      definition: "The specific strike price possessing the single highest Put Open Interest.",
      whatItMeasures: "Maximum structural downside support boundary where put writers have deployed greatest capital.",
      ranges: [
        { label: "Well Below Spot", range: "Put Wall < Spot - 1.5%", interpretation: "Solid cushion below spot; market has breathing room above primary support floor.", tone: "BULLISH" },
        { label: "Near Spot", range: "Put Wall ≈ Spot - 0.3%", interpretation: "Immediate floor. Key support test underway.", tone: "NEUTRAL" },
        { label: "Breached", range: "Spot < Put Wall", interpretation: "Put writers trapped. Panic put unwinding can accelerate downside selloff.", tone: "BEARISH" }
      ],
      traderTakeaway: "Use the Put Wall as a key support floor, but exit longs promptly if price breaks and sustains below it.",
      commonMistake: "Buying the dip at Put Wall when market breadth is < 10 ADV and global cues are sharply negative.",
      confirmWith: ["Market Breadth", "Volume", "Price vs VWAP"],
      invalidationNotes: ["A 15-minute close below the Put Wall with expanding volume signals liquidation cascade."],
      relatedMetrics: ["Call Wall", "PCR (OI)", "Max Pain"],
      infoDetail: {
        whatIsThis: "The Put Wall is the strike price with the highest concentration of Put Open Interest in the active expiry.",
        howTradersInterpretIt: "Acts as strong support because put writers underwrite this floor to protect premium income.",
        commonRanges: "Typically 1% to 2% below current spot in normal volatility regimes.",
        confirmWith: "Cross-check with Prior Day Low and Floor Pivot S1/S2.",
        commonMistake: "Catching falling knives at the Put Wall when breadth is severely negative."
      }
    },
    advanced: {
      mechanics: "Strike index $K_{PW} = \\text{argmax}_K (OI_{Put,K})$, representing the largest short gamma downside boundary for option writers and dealers.",
      detailedRanges: [
        { label: "Floor Defense", range: "Spot testing Put Wall with Breadth > 25 ADV", regimeContext: "Support Absorption", optionOrMarketImpact: "Put writers absorb selling, encouraging responsive buying rebounds." },
        { label: "Liquidation Cascade", range: "Spot sustaining 15m close < Put Wall + VIX Expansion", regimeContext: "Gamma Breakdown", optionOrMarketImpact: "Trapped put writers buy back puts and sell underlying futures, accelerating downside momentum." }
      ],
      regimeContext: "Market Structure Floor: Defines the macro expected lower boundary for the weekly market auction. Downward migration of the Put Wall signals structural deterioration.",
      confluenceRules: [
        "Put Wall Strike Coinciding with Prior Day Low + Hammer Rejection + PCR > 1.20 = High-Probability Floor Bounce."
      ],
      failureConditions: ["In severe panic liquidation events, put writers unwind violently, turning the floor into an air pocket."],
      edgeCases: ["Put Wall Roll-Down: Writers abandoning 24,000 and fleeing to 23,800, creating an immediate 200-point vacuum."],
      relatedConcepts: ["Put Skew", "Dealer Delta Hedging", "Tail-Risk Cascades"],
      advancedHypotheticalExample: "HYPOTHETICAL: 24,100 holds 1.5 crore Put OI (Put Wall). NIFTY drops to 24,080 on weak breadth (< 12 ADV). Rather than bouncing, put writers dump hedges as VIX jumps from 14 to 18. NIFTY cascades 160 points straight to 23,920.",
      infoDetail: {
        definition: "Strike possessing maximum Put Open Interest concentration.",
        mechanics: "Defines maximum downside dealer short gamma and underwriting capital commitment.",
        regimeContext: "Acts as primary macro floor until broken by institutional liquidation.",
        confluence: "Pair with Floor Pivot S2 and Historical Multi-Day Lows.",
        failureConditions: "Unwinding cascade accelerating downward selloffs.",
        edgeCases: "Intraday roll-down to lower strikes during panic.",
        relatedMetrics: "Call Wall, PCR OI, Max Pain"
      }
    }
  }
];

// --------------------------------------------------------------------------
// 2. UNIFIED PRICE VS OPEN INTEREST MATRIX
// --------------------------------------------------------------------------
export const UNIFIED_PRICE_OI_MATRIX: PriceOiMatrixRow[] = [
  {
    priceDirection: "PRICE ↑",
    oiDirection: "OI ↑",
    label: "LONG BUILDUP",
    beginnerLabel: "NEW BUYING (Long Buildup)",
    beginnerExplanation: "Price is rising and new contracts are being created. Buyers are aggressively putting fresh money into the market.",
    intermediateInterpretation: "New long positions are actively being created as buyers aggressively bid price higher. High continuation probability when backed by volume and breadth.",
    advancedMechanics: "Institutional accumulation: aggressive bid-side delta creation with expanding open contract commitments; confirmed by positive futures basis and volume expansion.",
    implication: "Strongest bullish institutional signal. High continuation probability when supported by volume and breadth.",
    warning: "Verify volume and breadth confirmation; watch for exhaustion if approaching major Call Wall resistance.",
    tone: "BULLISH"
  },
  {
    priceDirection: "PRICE ↓",
    oiDirection: "OI ↑",
    label: "SHORT BUILDUP",
    beginnerLabel: "NEW SELLING (Short Buildup)",
    beginnerExplanation: "Price is falling and new contracts are being created. Sellers are aggressively putting fresh money on the short side.",
    intermediateInterpretation: "New short positions are aggressively entering the market, pushing prices downward. High probability of sustained downward drift or breakdown.",
    advancedMechanics: "Institutional distribution: aggressive offer-side delta creation with expanding derivative liabilities; confirmed by negative futures basis and VIX expansion.",
    implication: "Strongest bearish institutional signal. High probability of sustained downward drift or breakdown.",
    warning: "Check for potential bounce if price approaches major Put Wall support with oversold momentum.",
    tone: "BEARISH"
  },
  {
    priceDirection: "PRICE ↑",
    oiDirection: "OI ↓",
    label: "SHORT COVERING",
    beginnerLabel: "SHORTS EXITING (Short Covering)",
    beginnerExplanation: "Price is rising because trapped short sellers are rushing to buy back and close their losing positions.",
    intermediateInterpretation: "Existing short sellers are buying back contracts to close positions / cut losses, lifting price. Sharp, fast rally that may fade once short covering finishes.",
    advancedMechanics: "Mechanical short squeeze: forced buying from stop-loss liquidation of existing short inventory; sharp velocity with contracting open interest base.",
    implication: "Sharp, fast upward rally. Often rapid in velocity but can stall once short-covering fuel is exhausted.",
    warning: "Short covering alone does not equal fresh long investment; rally may fade unless fresh Long Buildup takes over.",
    tone: "CAUTION"
  },
  {
    priceDirection: "PRICE ↓",
    oiDirection: "OI ↓",
    label: "LONG UNWINDING",
    beginnerLabel: "LONGS EXITING (Long Unwinding)",
    beginnerExplanation: "Price is falling because traders who were in profit are closing their long trades and cashing out.",
    intermediateInterpretation: "Existing long position holders are exiting and taking profits or stopping out, depressing price. Orderly downward retracement.",
    advancedMechanics: "Long liquidation: voluntary profit realization or trailing stop triggers from existing long inventory without aggressive new short creation.",
    implication: "Orderly downward retracement or profit-taking drift. Often lacks aggressive new short selling conviction.",
    warning: "If long unwinding triggers critical support breaks, it can morph into aggressive fresh Short Buildup.",
    tone: "CAUTION"
  }
];

// --------------------------------------------------------------------------
// 3. UNIFIED PRICE ACTION CONCEPTS
// --------------------------------------------------------------------------
export const UNIFIED_PRICE_ACTION_CONCEPTS: PriceActionConcept[] = [
  {
    id: "higher_high_low",
    title: "Higher Highs & Higher Lows (HH / HL)",
    beginnerTitle: "Staircase Going Up (Higher Highs & Lows)",
    beginnerDescription: "Price keeps making higher peaks and higher dips, like climbing a staircase. It shows buyers are consistently in control.",
    whatItIs: "A sequence where each successive peak is higher than the previous peak and each trough is higher than the previous trough.",
    whatItMeans: "Buyers are consistently stepping in at higher prices, defining a healthy upward trend structure.",
    whatConfirms: "Sustained trading above VWAP with expanding volume and positive constituent breadth (> 30 ADV).",
    whatInvalidates: "Price breaking and closing below the previous Higher Low.",
    advancedConfluence: "Higher timeframe value acceptance above weekly developing Point of Control (POC) with progressive volume delta.",
    tone: "BULLISH"
  },
  {
    id: "lower_high_low",
    title: "Lower Highs & Lower Lows (LH / LL)",
    beginnerTitle: "Staircase Going Down (Lower Highs & Lows)",
    beginnerDescription: "Price keeps making lower peaks and lower dips, like going downstairs. It shows sellers are consistently in control.",
    whatItIs: "A sequence where each successive rally peak is lower and each decline reaches a new depth.",
    whatItMeans: "Sellers are aggressive and willing to accept lower prices, defining a clear downward trend structure.",
    whatConfirms: "Price staying below VWAP, expanding sell volume, negative constituent breadth (< 20 ADV).",
    whatInvalidates: "Price reclaiming and closing above the previous Lower High.",
    advancedConfluence: "Downward value migration with responsive rejection at descending VWAP bands.",
    tone: "BEARISH"
  },
  {
    id: "breakout",
    title: "Breakout",
    beginnerTitle: "Breaking the Ceiling (Breakout)",
    beginnerDescription: "Price moves above a strong ceiling level that previously stopped it from going higher. If buyers are strong, price can run.",
    whatItIs: "Price moving decisively beyond a well-defined resistance zone or multi-session consolidation range.",
    whatItMeans: "Supply at the resistance level has been absorbed, opening a new higher auction value area.",
    whatConfirms: "Heavy volume expansion, broad constituent breadth expansion, Call OI unwinding at the breakout strike.",
    whatInvalidates: "Price immediately falling back inside the range within 1–2 subsequent candles (False Breakout).",
    advancedConfluence: "Initial Balance expansion outside 3-day Value Area with aggressive ask-side market order delta.",
    tone: "BULLISH"
  },
  {
    id: "breakdown",
    title: "Breakdown",
    beginnerTitle: "Breaking the Floor (Breakdown)",
    beginnerDescription: "Price drops below a strong floor level that previously supported it. If sellers are strong, price can slide lower.",
    whatItIs: "Price moving decisively below a well-defined support floor or consolidation base.",
    whatItMeans: "Demand at the support floor has failed to absorb available selling supply.",
    whatConfirms: "Heavy sell volume, VIX expansion, deteriorating breadth (< 15 ADV), Put OI unwinding.",
    whatInvalidates: "Immediate sharp rejection and reclaim of the support level (Bear Trap).",
    advancedConfluence: "Break of composite high-volume node with cascading put writer stop liquidations.",
    tone: "BEARISH"
  },
  {
    id: "retest",
    title: "Retest / Pullback",
    beginnerTitle: "Checking the Broken Level (Retest)",
    beginnerDescription: "After breaking a ceiling, price comes back down to check if the old ceiling now acts as a new floor.",
    whatItIs: "Price returning to test a recently broken resistance (now potential support) or broken support (now resistance).",
    whatItMeans: "Market auction checking whether previous participants will defend the newly flipped structural level.",
    whatConfirms: "Decreasing volume on the pullback followed by strong rejection candle and volume resumption in breakout direction.",
    whatInvalidates: "Price closing deeply back through the retested level with heavy volume.",
    advancedConfluence: "Low-volume liquidity re-test of broken resistance node with order book absorption and VWAP convergence.",
    tone: "NEUTRAL"
  },
  {
    id: "rejection",
    title: "Rejection (Wick Action)",
    beginnerTitle: "Quick Pushback (Wick Rejection)",
    beginnerDescription: "Price tries to go too high or too low, but gets quickly rejected, leaving a long tail or wick on the candle.",
    whatItIs: "Price testing an extreme high or low and being swiftly pushed back, leaving a long upper or lower candle shadow.",
    whatItMeans: "Aggressive responsive buying (lower wick) or responsive selling (upper wick) overwhelming the auction at that level.",
    whatConfirms: "Follow-through candle closing in the direction of the rejection with increasing volume.",
    whatInvalidates: "Next candle slicing straight through the rejection wick extreme.",
    advancedConfluence: "Liquidity sweep of prior swing extreme with instantaneous absorption and high delta reversal.",
    tone: "CAUTION"
  }
];

// --------------------------------------------------------------------------
// 4. UNIFIED SCENARIO LIBRARY (3-LAYER PRESENTATIONS)
// --------------------------------------------------------------------------
export const UNIFIED_SCENARIO_LIBRARY: UnifiedScenario[] = [
  {
    id: "scen_bull_continuation",
    canonicalClassification: "BULLISH_CONTINUATION",
    title: {
      beginner: "Market keeps moving upward",
      intermediate: "Strong Bullish Continuation",
      advanced: "Expansionary Bullish Momentum & Trend Continuation"
    },
    conditions: {
      beginner: [
        "NIFTY is making higher highs and higher lows",
        "More stocks are rising than falling (35+ stocks)",
        "Banking stocks are strong and helping the move",
        "Price is trading comfortably above the intraday average (VWAP)"
      ],
      intermediate: [
        "Price trading comfortably above VWAP",
        "Sequence of Higher Highs and Higher Lows",
        "Constituent Breadth > 30–35 ADV",
        "Banking / Financials actively participating",
        "Overhead Call Wall resistance unwinding",
        "Volume expanding on upward impulse legs",
        "India VIX stable or compressing"
      ],
      advanced: [
        "Sustained value acceptance above session VWAP with positive slope",
        "Constituent advance breadth > 35 ADV with broad multi-sector contribution",
        "Banking sector outperforming headline index (+0.5% alpha)",
        "Call Wall delta unwinding with expanding Futures open interest (Long Buildup)",
        "Volume profile showing value area migration higher without divergence"
      ]
    },
    meaning: {
      beginner: "Buyers appear to be in control across most of the market. Dips toward support are generally being bought.",
      intermediate: "Probability of sustained upside continuation generally improves. Favor trend-following longs on pullbacks to VWAP/support.",
      advanced: "Multi-factor institutional markup regime. Asymmetric edge favors pullback execution to developing Value Area High (VAH) or VWAP with trailing structural stops."
    },
    invalidation: {
      beginner: "Price falls back below the opening level and more stocks start turning red.",
      intermediate: "Price loses VWAP and previous Higher Low, or constituent breadth drops below 20 ADV.",
      advanced: "Price acceptance below session VWAP, failure of previous Higher Low structure, and breadth deterioration < 20 ADV with banking breakdown."
    },
    tone: "BULLISH",
    confidenceBand: "STRONG MATCH"
  },
  {
    id: "scen_narrow_rally",
    canonicalClassification: "FALSE_BREAKOUT_RISK",
    title: {
      beginner: "Narrow rally (Only 1–2 big stocks pushing)",
      intermediate: "Weak Bullish / Narrow Heavyweight Rally",
      advanced: "Heavyweight-Distorted Narrow Rally / Distribution Risk"
    },
    conditions: {
      beginner: [
        "NIFTY headline number is green",
        "BUT more than half the stocks are actually falling",
        "Only 1 or 2 giant stocks are holding up the index",
        "Trading volume is quiet"
      ],
      intermediate: [
        "Headline Index rising (+0.5% to +1.0%)",
        "Constituent Breadth remains weak (< 20 ADV)",
        "Move driven by only 1–2 heavyweight stocks (e.g. Reliance / HDFC)",
        "Sector participation is negative across broader market",
        "Overall volume is mediocre",
        "India VIX remains unchanged or rises"
      ],
      advanced: [
        "Headline index printing higher highs while unweighted advance-decline drops < 18 ADV",
        "Top 2 constituents contributing > 80% of net index points",
        "Sector dispersion heavily negative across cyclical and mid-tier constituents",
        "Call writing persisting at near-OTM strikes despite headline index gains"
      ]
    },
    meaning: {
      beginner: "The rally is fragile and narrow. If the 1–2 big stocks take a breather, the whole index can drop quickly.",
      intermediate: "Rally structure is narrow and fragile. High vulnerability to swift reversals if the driving heavyweights encounter profit taking.",
      advanced: "Structural divergence indicating stealth distribution under index heavyweight cover. High vulnerability to rapid mean reversion."
    },
    invalidation: {
      beginner: "Other stocks start turning green and joining the move.",
      intermediate: "Breadth expands to > 30 ADV with multiple sectors joining the move.",
      advanced: "Constituent breadth expands decisively above 32 ADV with broad sector index confirmation."
    },
    tone: "FALSE_BREAKOUT",
    confidenceBand: "PARTIAL MATCH"
  },
  {
    id: "scen_false_breakout",
    canonicalClassification: "FALSE_BREAKOUT_RISK",
    title: {
      beginner: "Price breaks resistance but fails (Trap)",
      intermediate: "False Breakout / Bull Trap Risk",
      advanced: "Failed Breakout Auction / Liquidity Sweep & Reversal"
    },
    conditions: {
      beginner: [
        "Price briefly pushes above a ceiling level",
        "BUT very few stocks are participating",
        "Trading volume is weak",
        "Price quickly falls back below the ceiling"
      ],
      intermediate: [
        "Price briefly pushes above key multi-day resistance",
        "Volume fails to expand or is visibly anemic",
        "Constituent breadth does not confirm (< 22 ADV)",
        "Bank NIFTY fails to break its corresponding resistance",
        "Price quickly closes back below the breakout level",
        "India VIX begins ticking upward"
      ],
      advanced: [
        "Price exploration outside consolidation high rejected within 15 minutes",
        "Volume delta shows aggressive market buy orders absorbed by passive limit sell orders",
        "Breadth divergence with < 20 advancing constituents during breakout attempt",
        "Immediate reclaim of pre-breakout range value area with VIX expansion"
      ]
    },
    meaning: {
      beginner: "Buyers tried to push price higher, but sellers overpowered them. Trapped buyers may panic and sell, causing a fast drop.",
      intermediate: "Breakout failure probability increases significantly. Trapped breakout buyers frequently trigger rapid long liquidation downward.",
      advanced: "Failed auction mechanics: lack of responsive institutional buying at higher prices triggers liquidation cascade back to opposite value area boundary."
    },
    invalidation: {
      beginner: "Price shoots back above the ceiling with heavy volume and stays there.",
      intermediate: "Price re-breaks above resistance on heavy volume and sustains 15m close.",
      advanced: "Decisive 15-minute close above breakout extreme accompanied by > 1.8x volume and breadth expansion > 35 ADV."
    },
    tone: "FALSE_BREAKOUT",
    confidenceBand: "STRONG MATCH"
  },
  {
    id: "scen_bear_trend",
    canonicalClassification: "BEARISH_CONTINUATION",
    title: {
      beginner: "Market keeps moving downward",
      intermediate: "Strong Bearish Trend",
      advanced: "Sustained Bearish Liquidation & Trend Continuation"
    },
    conditions: {
      beginner: [
        "Price is making lower highs and lower lows",
        "Most stocks are falling (under 15 rising)",
        "Banking stocks are weak and dropping",
        "Price is staying below the intraday average (VWAP)"
      ],
      intermediate: [
        "Price trading consistently below VWAP",
        "Sequence of Lower Highs and Lower Lows",
        "Constituent Breadth severely negative (< 15 ADV)",
        "Banking and Heavyweights both showing aggressive supply",
        "Key support floors breaking with volume expansion",
        "India VIX expanding noticeably",
        "Put support strikes unwinding with aggressive Call writing"
      ],
      advanced: [
        "Sustained value acceptance below descending session VWAP",
        "Constituent breadth severely negative (< 12 ADV) with multi-sector liquidation",
        "Banking sector leading lower (-1.0% relative drag)",
        "Put Wall strikes unwinding with aggressive short buildup across futures and call writing",
        "India VIX expanding into elevated regime (> 18.0)"
      ]
    },
    meaning: {
      beginner: "Sellers are in control across most of the market. Avoid trying to guess the bottom until sellers calm down.",
      intermediate: "Probability of sustained downward drift and trend continuation is elevated. Avoid premature bottom-fishing.",
      advanced: "High-conviction institutional markdown regime. Asymmetric edge favors short execution on pullbacks to descending VWAP / value area."
    },
    invalidation: {
      beginner: "Price reclaims the intraday average and most stocks turn green.",
      intermediate: "Price decisively reclaims VWAP and previous Lower High with breadth recovery > 25 ADV.",
      advanced: "Price reclaim of session VWAP with expanding volume, breadth recovery > 28 ADV, and heavy responsive lower wicks at structural support."
    },
    tone: "BEARISH",
    confidenceBand: "STRONG MATCH"
  },
  {
    id: "scen_bear_trap",
    canonicalClassification: "BEAR_TRAP_RISK",
    title: {
      beginner: "Price dips below floor then springs back (Bear Trap)",
      intermediate: "Bear Trap / Spring Reversal",
      advanced: "Failed Breakdown Auction / Liquidity Grab & Short Squeeze"
    },
    conditions: {
      beginner: [
        "Price briefly drops below a floor level",
        "BUT immediately bounces right back up with a long tail",
        "Market breadth is actually positive or improving",
        "Banking stocks are holding strong"
      ],
      intermediate: [
        "Price briefly breaks below key support / Put Wall",
        "Swift rejection wick appears on heavy volume",
        "Price aggressively reclaims the broken level within 1–2 candles",
        "Constituent breadth begins improving (> 25 ADV)",
        "Short covering accelerates as trapped shorts scramble to cover"
      ],
      advanced: [
        "Support floor breached to trigger stop liquidity, followed by instant absorption wick",
        "Volume delta shows aggressive market sell orders absorbed by institutional limit buy orders",
        "Constituent breadth remains resilient (> 28 ADV) despite headline index dip",
        "Rapid reclaim of broken support strike with call buying and short covering"
      ]
    },
    meaning: {
      beginner: "Sellers tried to push price down, but strong buyers stepped in. Trapped sellers are forced to buy back, pushing price up.",
      intermediate: "Downside failure probability increases; high likelihood of sharp relief squeeze back toward VWAP and upper value area.",
      advanced: "Liquidity sweep followed by aggressive short squeeze. Trapped shorts fuel rapid rotational impulse toward opposite range extreme."
    },
    invalidation: {
      beginner: "Price drops back below the low tail on heavy volume.",
      intermediate: "Price loses the rejection low on fresh volume expansion.",
      advanced: "Price breaks below the rejection wick low with expanding volume and breadth deterioration < 15 ADV."
    },
    tone: "BEAR_TRAP",
    confidenceBand: "STRONG MATCH"
  },
  {
    id: "scen_range_chop",
    canonicalClassification: "RANGE_CHOP",
    title: {
      beginner: "Market has no clear direction (Choppy / Sideways)",
      intermediate: "Range-Bound / Choppy Whipsaw Market",
      advanced: "Rotational Auction / Low-Volatility Value Compression"
    },
    conditions: {
      beginner: [
        "Price is bouncing up and down crossing the average repeatedly",
        "About half the stocks are up and half are down",
        "Trend strength (ADX) is low",
        "Volatility (VIX) is quiet and calm"
      ],
      intermediate: [
        "Price oscillating back and forth across VWAP repeatedly",
        "ADX low (< 18.0) indicating absence of trend momentum",
        "Constituent Breadth balanced/mixed (22–28 ADV)",
        "India VIX low (< 13.0) and subdued",
        "Both Call Wall and Put Wall strikes contain the price action",
        "Lack of sector leadership or directional institutional flows"
      ],
      advanced: [
        "Price oscillating in Gaussian bell curve around session VWAP Point of Control",
        "ADX < 16.0 with +DI and -DI compressed together",
        "Constituent breadth hovering tightly between 22 and 28 ADV",
        "ATM straddle decay dominant; volume profile exhibits balanced two-way auction"
      ]
    },
    meaning: {
      beginner: "Neither buyers nor sellers are in charge. Breakout trades will often get trapped; patience is best.",
      intermediate: "Range-bound rotation is dominant. Trend breakout systems will face repeated whipsaws; favor mean-reversion at boundaries or stand aside.",
      advanced: "Balanced rotational regime. Edge favors premium harvesting and boundary mean-reversion with tight profit targets at VWAP."
    },
    invalidation: {
      beginner: "Price decisively breaks out of the range with strong volume and breadth.",
      intermediate: "Decisive range breakout with volume expansion and ADX ticking above 22.",
      advanced: "Decisive Initial Balance breakout supported by volume expansion > 1.5x, breadth > 35 ADV, and ADX crossing 22.0."
    },
    tone: "RANGE",
    confidenceBand: "STRONG MATCH"
  }
];

// --------------------------------------------------------------------------
// 5. UNIFIED RISK MANAGEMENT PRINCIPLES (3 LAYERS)
// --------------------------------------------------------------------------
export const UNIFIED_RISK_RULES: RiskManagementRule[] = [
  {
    id: "risk_invalidation",
    title: "Define Invalidation Point Before Entry",
    beginnerRule: "Always know where you will exit if you are wrong BEFORE you enter the trade.",
    intermediateRule: "Never enter a trade without a clearly defined structural stop loss based on technical invalidation.",
    advancedRule: "Model trade invalidation as a structural market hypothesis failure (e.g. loss of value area acceptance), not an arbitrary round rupee distance.",
    rationale: "If you don't know where your idea is wrong, you cannot calculate your true financial risk.",
    example: "EXAMPLE: Buying a breakout above 24,300 with invalidation set at 24,285 (15-point risk)."
  },
  {
    id: "risk_position_sizing",
    title: "Position Size Based on Stop Distance",
    beginnerRule: "Do not guess your trade size. If the stop loss is wider, trade fewer shares/contracts.",
    intermediateRule: "Position Size = (Account Capital × Max Risk %) / (Entry Price - Stop Loss Price).",
    advancedRule: "Normalize risk across varying volatility regimes: $Size = \\frac{\\text{Risk Budget}}{k \\times ATR}$, keeping total portfolio drawdowns strictly bounded.",
    rationale: "Ensures every single trade risks the exact same percentage of capital regardless of market volatility.",
    example: "EXAMPLE: On a ₹10 Lakh account risking 1% (₹10,000), a 20-pt stop allows 500 qty; a 40-pt stop allows only 250 qty."
  },
  {
    id: "risk_r_multiple",
    title: "Maintain Minimum 1:2 Risk-to-Reward Ratio",
    beginnerRule: "Only take trades where the realistic profit target is at least TWICE the size of your risk.",
    intermediateRule: "Target must be $\\ge 2 \\times \\text{Risk}$. Allows overall profitability even with a 40% win rate.",
    advancedRule: "Asymmetric expectancy modeling: ensure positive mathematical expectancy $E = (W \\times R_w) - (L \\times R_l) > 0$ after factoring slippage and transaction friction.",
    rationale: "Even if you win only 4 out of 10 trades, a 1:2 ratio leaves you net profitable.",
    example: "EXAMPLE: Risking 20 points requires a realistic structural target of at least 40 points."
  },
  {
    id: "risk_max_daily_loss",
    title: "Enforce Maximum Daily Loss Circuit Breaker",
    beginnerRule: "Stop trading for the day if you lose 2 trades in a row. Close the computer and walk away.",
    intermediateRule: "Set a hard daily loss limit (e.g. -2R). If triggered, trading terminates automatically for that session.",
    advancedRule: "Psychological and algorithmic kill-switch: mandatory trading cessation upon reaching daily risk budget to prevent revenge trading during adverse regimes.",
    rationale: "Protects your capital from bad market regimes and emotional revenge trading.",
    example: "EXAMPLE: If max daily loss is 2 stop hits, shut down the terminal after 2 consecutive losses."
  },
  {
    id: "risk_volatility_sizing",
    title: "Scale Down Size When Volatility (VIX) Expands",
    beginnerRule: "When the market is wild and nervous (high VIX), trade smaller size and give trades more breathing room.",
    intermediateRule: "When India VIX rises above 18–20, reduce position sizing by 30%–50% and widen stop distances.",
    advancedRule: "Dynamic volatility scaling: scale gross portfolio exposure inversely to rolling 10-day ATR and implied volatility rank.",
    rationale: "Higher volatility expands random price noise; wider stops protect against noise while reduced size caps rupee loss.",
    example: "EXAMPLE: In a VIX 24 environment, trade half standard size with 2x standard ATR stop."
  }
];

// --------------------------------------------------------------------------
// 6. ADAPTIVE SCENARIO RULE ENGINE ("IF X + Y + Z, THEN WHAT?")
// --------------------------------------------------------------------------

// 8 Canonical Inputs (Advanced / Full)
export interface CanonicalScenarioInputState {
  breadth: "STRONG_POSITIVE" | "POSITIVE" | "MIXED" | "NEGATIVE" | "STRONG_NEGATIVE";
  vix: "FALLING" | "STABLE_LOW" | "RISING" | "HIGH";
  price: "ABOVE_VWAP" | "BELOW_VWAP" | "CROSSING_VWAP" | "BREAKING_RESISTANCE" | "BREAKING_SUPPORT" | "INSIDE_RANGE";
  bankNifty: "STRONG" | "POSITIVE" | "NEUTRAL" | "WEAK";
  pcr: "CALL_HEAVY" | "BALANCED" | "SUPPORTIVE" | "EXTREME";
  oi: "LONG_BUILDUP" | "SHORT_BUILDUP" | "SHORT_COVERING" | "LONG_UNWINDING" | "MIXED";
  volume: "STRONG" | "NORMAL" | "WEAK";
  structure: "HIGHER_HIGHS" | "LOWER_LOWS" | "BREAKOUT" | "BREAKDOWN" | "RANGE";
}

// 4 Simplified Inputs (Beginner)
export interface BeginnerScenarioInputState {
  participation: "STRONG" | "MIXED" | "WEAK";
  volatility: "CALM" | "NORMAL" | "HIGH";
  priceDirection: "UP" | "SIDEWAYS" | "DOWN";
  banking: "STRONG" | "NEUTRAL" | "WEAK";
}

// 6 Moderate Inputs (Intermediate)
export interface IntermediateScenarioInputState {
  breadth: "STRONG_POSITIVE" | "POSITIVE" | "MIXED" | "NEGATIVE" | "STRONG_NEGATIVE";
  vix: "FALLING" | "STABLE_LOW" | "RISING" | "HIGH";
  price: "ABOVE_VWAP" | "BELOW_VWAP" | "CROSSING_VWAP" | "BREAKING_RESISTANCE" | "BREAKING_SUPPORT";
  bankNifty: "STRONG" | "POSITIVE" | "NEUTRAL" | "WEAK";
  pcr: "CALL_HEAVY" | "BALANCED" | "SUPPORTIVE" | "EXTREME";
  volume: "STRONG" | "NORMAL" | "WEAK";
}

// Output Result Interface Adapted to Experience Level
export interface AdaptiveScenarioResult {
  scenarioId: string;
  classification: "BULLISH_CONTINUATION" | "BEARISH_CONTINUATION" | "RANGE_CHOP" | "FALSE_BREAKOUT_RISK" | "BEAR_TRAP_RISK" | "MIXED_CONFLICTING";
  title: string;
  confidenceBand: "STRONG MATCH" | "PARTIAL MATCH" | "WEAK MATCH";
  supportingConditions: string[];
  opposingConditions: string[];
  interpretation: string;
  invalidation: string;
  educationalNote: string;
}

// Mapping Helpers between Beginner / Intermediate and Canonical
export function mapBeginnerToCanonical(b: BeginnerScenarioInputState): CanonicalScenarioInputState {
  return {
    breadth: b.participation === "STRONG" ? "STRONG_POSITIVE" : b.participation === "WEAK" ? "STRONG_NEGATIVE" : "MIXED",
    vix: b.volatility === "CALM" ? "FALLING" : b.volatility === "HIGH" ? "RISING" : "STABLE_LOW",
    price: b.priceDirection === "UP" ? "ABOVE_VWAP" : b.priceDirection === "DOWN" ? "BELOW_VWAP" : "CROSSING_VWAP",
    bankNifty: b.banking === "STRONG" ? "STRONG" : b.banking === "WEAK" ? "WEAK" : "NEUTRAL",
    pcr: b.priceDirection === "UP" ? "SUPPORTIVE" : b.priceDirection === "DOWN" ? "CALL_HEAVY" : "BALANCED",
    oi: b.priceDirection === "UP" ? "LONG_BUILDUP" : b.priceDirection === "DOWN" ? "SHORT_BUILDUP" : "MIXED",
    volume: b.participation === "STRONG" || b.volatility === "HIGH" ? "STRONG" : "NORMAL",
    structure: b.priceDirection === "UP" ? "HIGHER_HIGHS" : b.priceDirection === "DOWN" ? "LOWER_LOWS" : "RANGE"
  };
}

export function mapIntermediateToCanonical(i: IntermediateScenarioInputState): CanonicalScenarioInputState {
  return {
    breadth: i.breadth,
    vix: i.vix,
    price: i.price,
    bankNifty: i.bankNifty,
    pcr: i.pcr,
    oi: i.price === "BREAKING_RESISTANCE" || i.price === "ABOVE_VWAP" ? "LONG_BUILDUP" : i.price === "BREAKING_SUPPORT" || i.price === "BELOW_VWAP" ? "SHORT_BUILDUP" : "MIXED",
    volume: i.volume,
    structure: i.price === "BREAKING_RESISTANCE" ? "BREAKOUT" : i.price === "BREAKING_SUPPORT" ? "BREAKDOWN" : i.price === "ABOVE_VWAP" ? "HIGHER_HIGHS" : i.price === "BELOW_VWAP" ? "LOWER_LOWS" : "RANGE"
  };
}

// Master Deterministic Rule Engine with Multi-Layer Presentation
export function evaluateAdaptiveScenario(
  inputs: CanonicalScenarioInputState,
  level: ExperienceLevel
): AdaptiveScenarioResult {
  const supporting: string[] = [];
  const opposing: string[] = [];

  let bullScore = 0;
  let bearScore = 0;
  let chopScore = 0;

  // 1. Breadth Evaluation
  if (inputs.breadth === "STRONG_POSITIVE") {
    bullScore += 3;
    supporting.push(level === "BEGINNER" ? "Most stocks (35+) are rising, giving strong market support." : "Strong positive market breadth (> 35 ADV) provides broad constituent backing.");
  } else if (inputs.breadth === "POSITIVE") {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "More stocks are rising than falling (30+ stocks)." : "Positive market breadth (> 30 ADV) supports upward auction.");
  } else if (inputs.breadth === "STRONG_NEGATIVE") {
    bearScore += 3;
    supporting.push(level === "BEGINNER" ? "Most stocks are falling (under 15 rising), showing broad selling." : "Strong negative market breadth (< 15 ADV) indicates broad constituent selling.");
  } else if (inputs.breadth === "NEGATIVE") {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "More stocks are falling than rising." : "Negative market breadth (< 20 ADV) creates overhead drag.");
  } else {
    chopScore += 2;
    supporting.push(level === "BEGINNER" ? "About half the stocks are up and half are down (mixed participation)." : "Mixed market breadth (22–28 ADV) reflects balanced two-way market.");
  }

  // 2. VIX Evaluation
  if (inputs.vix === "FALLING") {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "Market nervousness (VIX) is falling, signaling calm and steady trading." : "Falling VIX indicates declining volatility risk and orderly price discovery.");
  } else if (inputs.vix === "STABLE_LOW") {
    bullScore += 1;
    chopScore += 1;
    supporting.push(level === "BEGINNER" ? "Volatility is low and quiet." : "Low/stable VIX reflects absence of market stress.");
  } else if (inputs.vix === "RISING" || inputs.vix === "HIGH") {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "Market nervousness (VIX) is rising, indicating wider price swings and stress." : "Rising/high VIX indicates expanding volatility and market uncertainty.");
  }

  // 3. Price & VWAP Evaluation
  if (inputs.price === "BREAKING_RESISTANCE" || inputs.price === "ABOVE_VWAP") {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "Price is trading above the intraday average, showing buyer control." : "Price positioned above VWAP / breaking resistance demonstrates buyer control.");
  } else if (inputs.price === "BREAKING_SUPPORT" || inputs.price === "BELOW_VWAP") {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "Price is trading below the intraday average, showing seller control." : "Price positioned below VWAP / breaking support demonstrates seller control.");
  } else if (inputs.price === "CROSSING_VWAP" || inputs.price === "INSIDE_RANGE") {
    chopScore += 3;
    supporting.push(level === "BEGINNER" ? "Price is moving back and forth across the average with no clear trend." : "Price repeatedly crossing VWAP / inside range confirms sideways rotational auction.");
  }

  // 4. Bank Nifty Evaluation
  if (inputs.bankNifty === "STRONG" || inputs.bankNifty === "POSITIVE") {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "Banking stocks are strong and helping push the market." : "Banking sector leadership confirms upward momentum.");
  } else if (inputs.bankNifty === "WEAK") {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "Banking stocks are weak, pulling down on the index." : "Banking sector weakness creates substantial drag on index continuation.");
  } else {
    chopScore += 1;
  }

  // 5. PCR & OI Evaluation
  if (inputs.pcr === "SUPPORTIVE" || inputs.pcr === "EXTREME") {
    bullScore += 1;
    supporting.push(level === "BEGINNER" ? "Option sellers have built a solid floor below price." : "Supportive PCR reflects robust put underwriting floor.");
  } else if (inputs.pcr === "CALL_HEAVY") {
    bearScore += 1;
    supporting.push(level === "BEGINNER" ? "Option sellers have built heavy ceiling resistance overhead." : "Call-heavy PCR indicates heavy overhead resistance positioning.");
  }

  if (inputs.oi === "LONG_BUILDUP" || inputs.oi === "SHORT_COVERING") {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "New buying or short covering is supporting the upward move." : `OI dynamic (${inputs.oi.replace("_", " ")}) confirms upward institutional flow.`);
  } else if (inputs.oi === "SHORT_BUILDUP" || inputs.oi === "LONG_UNWINDING") {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "New selling or long profit-taking is depressing prices." : `OI dynamic (${inputs.oi.replace("_", " ")}) confirms downward institutional flow.`);
  }

  // 6. Volume & Structure
  if (inputs.volume === "STRONG" && (inputs.structure === "BREAKOUT" || inputs.structure === "HIGHER_HIGHS")) {
    bullScore += 2;
    supporting.push(level === "BEGINNER" ? "Heavy trading volume confirms real buying power." : "Strong volume accompanied by breakout structure validates institutional participation.");
  } else if (inputs.volume === "STRONG" && (inputs.structure === "BREAKDOWN" || inputs.structure === "LOWER_LOWS")) {
    bearScore += 2;
    supporting.push(level === "BEGINNER" ? "Heavy trading volume confirms real selling pressure." : "Strong volume accompanied by breakdown structure validates institutional selling.");
  } else if (inputs.volume === "WEAK") {
    chopScore += 2;
    opposing.push(level === "BEGINNER" ? "Quiet/low trading volume makes moves harder to trust." : "Weak volume undermines trend breakout conviction.");
  }

  // Conflict & Trap Detection
  const isFalseBreakout =
    (inputs.price === "BREAKING_RESISTANCE" || inputs.structure === "BREAKOUT") &&
    (inputs.breadth === "NEGATIVE" || inputs.breadth === "STRONG_NEGATIVE" || inputs.bankNifty === "WEAK" || inputs.volume === "WEAK");

  const isBearTrap =
    (inputs.price === "BREAKING_SUPPORT" || inputs.structure === "BREAKDOWN") &&
    (inputs.breadth === "POSITIVE" || inputs.breadth === "STRONG_POSITIVE" || inputs.bankNifty === "STRONG" || inputs.pcr === "SUPPORTIVE");

  const isConflicting =
    !isFalseBreakout && !isBearTrap &&
    bullScore >= 4 && bearScore >= 4;

  if (isFalseBreakout) {
    opposing.push(level === "BEGINNER" ? "Most stocks and banks are NOT participating in the upward move." : "Negative constituent breadth and weak banking participation conflict with the breakout attempt.");
    return {
      scenarioId: "SCEN_FALSE_BREAKOUT_DETECTED",
      classification: "FALSE_BREAKOUT_RISK",
      title: level === "BEGINNER" ? "FALSE BREAKOUT (TRAP RISK)" : level === "INTERMEDIATE" ? "FALSE BREAKOUT / BULL TRAP RISK" : "FAILED BREAKOUT AUCTION / BULL TRAP RISK",
      confidenceBand: "STRONG MATCH",
      supportingConditions: supporting,
      opposingConditions: opposing,
      interpretation: level === "BEGINNER"
        ? "Price is trying to break above a ceiling, but most stocks and banks are weak. This move has a high chance of failing and dropping back down."
        : level === "INTERMEDIATE"
        ? "Price is attempting to break resistance, but constituent breadth, banking support, or volume are unsupportive. Breakout failure and mean-reversion probability is elevated."
        : "Price exploration outside structural resistance is unconfirmed by internal advance-decline breadth and banking delta; high probability of failed auction and mean reversion.",
      invalidation: level === "BEGINNER"
        ? "Other stocks turn green and volume surges, proving real buying interest."
        : "Breakout would be validated only if volume surges and constituent breadth expands above 30 Advancers.",
      educationalNote: level === "BEGINNER"
        ? "Never buy a breakout when most other stocks are quietly falling. True breakouts need broad market support."
        : "Never buy resistance breakouts without breadth and volume confirmation; narrow breakouts frequently fail and trap aggressive buyers."
    };
  }

  if (isBearTrap) {
    opposing.push(level === "BEGINNER" ? "Most stocks and banks remain strong despite the price dip." : "Positive breadth and resilient banking leadership conflict with the breakdown attempt.");
    return {
      scenarioId: "SCEN_BEAR_TRAP_DETECTED",
      classification: "BEAR_TRAP_RISK",
      title: level === "BEGINNER" ? "BEAR TRAP (REBOUND RISK)" : level === "INTERMEDIATE" ? "BEAR TRAP / REVERSAL RISK" : "FAILED BREAKDOWN / SHORT SQUEEZE RISK",
      confidenceBand: "STRONG MATCH",
      supportingConditions: supporting,
      opposingConditions: opposing,
      interpretation: level === "BEGINNER"
        ? "Price is dipping below support, but most stocks and banks are still strong. This drop may be a trap before price springs back upward."
        : level === "INTERMEDIATE"
        ? "Price is testing/breaking support, but underlying market breadth and sector resilience remain positive. Downside failure and sharp relief rebound probability is elevated."
        : "Downside exploration at support lacks broader market liquidation backing; asymmetric probability of liquidity sweep and rapid short squeeze.",
      invalidation: level === "BEGINNER"
        ? "Most stocks start falling and banks collapse, confirming real market-wide selling."
        : "Downside continuation would be validated only if market breadth collapses below 15 Advancers and banking breaks down.",
      educationalNote: level === "BEGINNER"
        ? "When price dips but most individual stocks stay green, buyers are often absorbing the dip."
        : "Support breakdowns in the face of strong constituent breadth often represent liquidity grabs before a sharp squeeze."
    };
  }

  if (isConflicting) {
    return {
      scenarioId: "SCEN_CONFLICTING_SIGNALS",
      classification: "MIXED_CONFLICTING",
      title: level === "BEGINNER" ? "MIXED / UNCLEAR SIGNALS" : level === "INTERMEDIATE" ? "MIXED / CONFLICTING SIGNALS" : "MIXED / CONFLICTING MARKET SIGNALS",
      confidenceBand: "PARTIAL MATCH",
      supportingConditions: supporting,
      opposingConditions: [
        level === "BEGINNER"
          ? "Bullish signals and Bearish signals are actively fighting each other."
          : "Bullish factors (e.g. breadth/price) are actively contradicted by Bearish factors (e.g. rising VIX, weak banks, or heavy call writing)."
      ],
      interpretation: level === "BEGINNER"
        ? "The market is sending mixed messages. Some signals say buy, while others say caution. It is usually best to wait for clarity rather than forcing a trade."
        : level === "INTERMEDIATE"
        ? "The selected market conditions contain strong opposing forces. Directional edge is severely degraded; high probability of two-way whipsaws."
        : "Opposing structural forces neutralize directional edge. Market exhibiting high entropy; risk-reward profile strongly favors capital preservation or reduced exposure.",
      invalidation: level === "BEGINNER"
        ? "Wait until most signals agree in one clear direction."
        : "Wait for one side of the conflict to resolve (e.g. breadth aligns with price and banks confirm).",
      educationalNote: level === "BEGINNER"
        ? "When market signals disagree, the smartest move is often to do nothing and protect your money."
        : "When market metrics point in opposite directions, the highest edge action is to stand aside or reduce size rather than forcing a directional bias."
    };
  }

  if (chopScore >= bullScore && chopScore >= bearScore) {
    return {
      scenarioId: "SCEN_RANGE_CHOP",
      classification: "RANGE_CHOP",
      title: level === "BEGINNER" ? "SIDEWAYS / CHOPPY MARKET" : level === "INTERMEDIATE" ? "RANGE-BOUND / CHOPPY ROTATION" : "ROTATIONAL RANGE / CHOP REGIME",
      confidenceBand: "STRONG MATCH",
      supportingConditions: supporting,
      opposingConditions: opposing,
      interpretation: level === "BEGINNER"
        ? "The market is moving sideways inside a channel. Price is likely to bounce between the top and bottom without a sustained breakout."
        : level === "INTERMEDIATE"
        ? "Conditions favor a range-bound, mean-reverting market. Price is likely to rotate between support and resistance boundaries without sustained trend continuation."
        : "Rotational equilibrium regime. Auction profile favors boundary mean reversion and premium harvesting; directional breakout systems face negative expectancy.",
      invalidation: level === "BEGINNER"
        ? "Price clearly breaks out above the ceiling or below the floor with heavy volume."
        : "A decisive breakout beyond the range accompanied by expanding volume and constituent breadth.",
      educationalNote: level === "BEGINNER"
        ? "In a sideways market, do not chase breakouts. Price will often reverse right back to the middle."
        : "In choppy regimes, trend-following breakout strategies struggle; favor fading extremes or observing until momentum develops."
    };
  }

  if (bullScore > bearScore) {
    const conf = bullScore >= 8 ? "STRONG MATCH" : "PARTIAL MATCH";
    return {
      scenarioId: "SCEN_BULLISH_CONTINUATION",
      classification: "BULLISH_CONTINUATION",
      title: level === "BEGINNER" ? "BULLISH TREND (BUYERS IN CONTROL)" : level === "INTERMEDIATE" ? "STRONG BULLISH CONTINUATION" : "EXPANSIONARY BULLISH CONTINUATION",
      confidenceBand: conf,
      supportingConditions: supporting,
      opposingConditions: opposing,
      interpretation: level === "BEGINNER"
        ? "Market conditions align favorably for prices to keep moving higher. Buyers are generally in control across most stocks."
        : level === "INTERMEDIATE"
        ? "Market conditions align favorably for sustained upward continuation. High-probability environment for trend-following long setups on pullbacks."
        : "Asymmetric bullish trend structure supported by broad constituent breadth, banking leadership, and constructive derivatives backdrop.",
      invalidation: level === "BEGINNER"
        ? "Price falls below the intraday average and most stocks turn red."
        : "Loss of intraday VWAP, deteriorating constituent breadth (< 20 ADV), or rejection from major Call Wall.",
      educationalNote: level === "BEGINNER"
        ? "When the trend is up, favor buying dips near support rather than trying to guess when the market will drop."
        : "Align trade entries with the prevailing trend: buy dips toward VWAP/support rather than chasing extended moves."
    };
  } else {
    const conf = bearScore >= 8 ? "STRONG MATCH" : "PARTIAL MATCH";
    return {
      scenarioId: "SCEN_BEARISH_CONTINUATION",
      classification: "BEARISH_CONTINUATION",
      title: level === "BEGINNER" ? "BEARISH TREND (SELLERS IN CONTROL)" : level === "INTERMEDIATE" ? "STRONG BEARISH CONTINUATION" : "EXPANSIONARY BEARISH LIQUIDATION",
      confidenceBand: conf,
      supportingConditions: supporting,
      opposingConditions: opposing,
      interpretation: level === "BEGINNER"
        ? "Market conditions align for prices to keep dropping. Sellers are in control across most stocks."
        : level === "INTERMEDIATE"
        ? "Market conditions align for sustained downward trend continuation. High-probability environment for trend-following short setups on pullbacks."
        : "Persistent institutional markdown regime backed by broad liquidation, banking weakness, and options call writing pressure.",
      invalidation: level === "BEGINNER"
        ? "Price reclaims the intraday average and most stocks turn green."
        : "Reclaim of intraday VWAP, breadth recovery above 25 ADV, or strong rejection wicks at Put Wall.",
      educationalNote: level === "BEGINNER"
        ? "In a strong downtrend, avoid trying to catch a falling knife until clear buying signs appear."
        : "In strong downward trends, avoid premature bottom fishing until clear structural higher lows and breadth recovery emerge."
    };
  }
}

// --------------------------------------------------------------------------
// 7. PRESET SCENARIOS FOR ALL EXPERIENCE LEVELS
// --------------------------------------------------------------------------
export const ADAPTIVE_SCENARIO_PRESETS: Record<string, {
  name: { beginner: string; intermediate: string; advanced: string };
  description: { beginner: string; intermediate: string; advanced: string };
  canonicalState: CanonicalScenarioInputState;
  beginnerState: BeginnerScenarioInputState;
}> = {
  STRONG_BULLISH_TREND: {
    name: {
      beginner: "Healthy Bullish Move",
      intermediate: "Strong Bullish Trend",
      advanced: "Expansionary Bullish Trend"
    },
    description: {
      beginner: "Most stocks rising, price above average, banks strong.",
      intermediate: "Full bullish alignment across breadth, banks, VWAP, and volume.",
      advanced: "Confluent multi-factor markup with breadth > 35 ADV and positive derivatives delta."
    },
    canonicalState: {
      breadth: "STRONG_POSITIVE",
      vix: "FALLING",
      price: "BREAKING_RESISTANCE",
      bankNifty: "STRONG",
      pcr: "SUPPORTIVE",
      oi: "LONG_BUILDUP",
      volume: "STRONG",
      structure: "BREAKOUT"
    },
    beginnerState: {
      participation: "STRONG",
      volatility: "CALM",
      priceDirection: "UP",
      banking: "STRONG"
    }
  },
  STRONG_BEARISH_TREND: {
    name: {
      beginner: "Healthy Bearish Move",
      intermediate: "Strong Bearish Trend",
      advanced: "Institutional Markdown Regime"
    },
    description: {
      beginner: "Most stocks falling, price below average, banks weak.",
      intermediate: "Full bearish alignment across breadth, banks, breakdown, and short buildup.",
      advanced: "Liquidation cascade with breadth < 15 ADV, rising VIX, and short buildup."
    },
    canonicalState: {
      breadth: "STRONG_NEGATIVE",
      vix: "RISING",
      price: "BREAKING_SUPPORT",
      bankNifty: "WEAK",
      pcr: "CALL_HEAVY",
      oi: "SHORT_BUILDUP",
      volume: "STRONG",
      structure: "BREAKDOWN"
    },
    beginnerState: {
      participation: "WEAK",
      volatility: "HIGH",
      priceDirection: "DOWN",
      banking: "WEAK"
    }
  },
  RANGE_CHOP: {
    name: {
      beginner: "Sideways / Choppy Day",
      intermediate: "Range / Chop Market",
      advanced: "Rotational Equilibrium Corridor"
    },
    description: {
      beginner: "Stocks mixed, price crossing the average, low volatility.",
      intermediate: "Balanced breadth, low VIX, and price oscillating around VWAP.",
      advanced: "Balanced two-way auction within ±0.5 StdDev of VWAP; low ADX (<16)."
    },
    canonicalState: {
      breadth: "MIXED",
      vix: "STABLE_LOW",
      price: "CROSSING_VWAP",
      bankNifty: "NEUTRAL",
      pcr: "BALANCED",
      oi: "MIXED",
      volume: "WEAK",
      structure: "RANGE"
    },
    beginnerState: {
      participation: "MIXED",
      volatility: "NORMAL",
      priceDirection: "SIDEWAYS",
      banking: "NEUTRAL"
    }
  },
  FALSE_BREAKOUT: {
    name: {
      beginner: "False Breakout (Bull Trap)",
      intermediate: "False Breakout / Bull Trap",
      advanced: "Failed Breakout Auction"
    },
    description: {
      beginner: "Price broke a ceiling, but other stocks did not join.",
      intermediate: "Price breaks resistance but breadth is negative and volume is weak.",
      advanced: "Failed auction exploratory spike rejected back into value area with breadth divergence."
    },
    canonicalState: {
      breadth: "NEGATIVE",
      vix: "RISING",
      price: "BREAKING_RESISTANCE",
      bankNifty: "WEAK",
      pcr: "CALL_HEAVY",
      oi: "SHORT_BUILDUP",
      volume: "WEAK",
      structure: "RANGE"
    },
    beginnerState: {
      participation: "WEAK",
      volatility: "HIGH",
      priceDirection: "UP",
      banking: "WEAK"
    }
  },
  BEAR_TRAP: {
    name: {
      beginner: "Bear Trap (Quick Spring)",
      intermediate: "Bear Trap / Squeeze Reversal",
      advanced: "Liquidity Sweep & Squeeze"
    },
    description: {
      beginner: "Price dipped below a floor, but most stocks stayed green.",
      intermediate: "Price tests support but breadth is positive and banks are strong.",
      advanced: "Stop-sweep below structural support followed by aggressive short-squeeze absorption."
    },
    canonicalState: {
      breadth: "POSITIVE",
      vix: "FALLING",
      price: "BREAKING_SUPPORT",
      bankNifty: "STRONG",
      pcr: "SUPPORTIVE",
      oi: "SHORT_COVERING",
      volume: "STRONG",
      structure: "RANGE"
    },
    beginnerState: {
      participation: "STRONG",
      volatility: "CALM",
      priceDirection: "DOWN",
      banking: "STRONG"
    }
  }
};

// --------------------------------------------------------------------------
// 8. ADDITIONAL REFERENCE COLLECTIONS
// --------------------------------------------------------------------------
export const UNIFIED_TREND_VS_RANGE: TrendVsRangeComparison[] = [
  {
    aspect: "Opening Behavior",
    beginnerSummary: "Trend days start with strong direction; Range days open and wander back and forth.",
    trendDay: "Opens with directional conviction, often outside prior range; holds initial balance boundary.",
    rangeDay: "Opens inside prior day range; rotational auction back and forth through open price.",
    advancedMechanics: "Open-Drive or Open-Test-Drive profile vs Open-Auction in Range."
  },
  {
    aspect: "VWAP Interaction",
    beginnerSummary: "Trend days stay on one side of average; Range days cross the average repeatedly.",
    trendDay: "Price stays strictly on one side of VWAP (above in bull, below in bear); pullbacks to VWAP hold firmly.",
    rangeDay: "Price repeatedly crosses VWAP multiple times throughout the session like a horizontal sine wave.",
    advancedMechanics: "Persistent 1.5+ StdDev skew with positive/negative slope vs oscillating Point of Control."
  },
  {
    aspect: "Market Participation",
    beginnerSummary: "Trend days have one-sided market breadth (35+ stocks); Range days have 50/50 mix.",
    trendDay: "Decisive one-sided breadth (> 35 ADV in bull trend, < 15 ADV in bear trend) sustained all day.",
    rangeDay: "Mixed breadth hovering between 20 and 30 Advancers with no clear constituent momentum.",
    advancedMechanics: "Unweighted constituent advance-decline momentum confirms volume delta flow."
  },
  {
    aspect: "Best Strategy",
    beginnerSummary: "Trend days: trade with the move. Range days: buy the floor and sell the ceiling.",
    trendDay: "Trend following: buy pullbacks to VWAP/EMAs; trail stops; avoid fading the move.",
    rangeDay: "Mean reversion: buy support, sell resistance; take quick profits at VWAP; avoid breakout chasing.",
    advancedMechanics: "Directional delta momentum with trailing stops vs delta-neutral short strangle / iron condor harvesting."
  }
];

export const UNIFIED_INDICATOR_COMBINATIONS: IndicatorCombination[] = [
  {
    title: "High Momentum Bullish Trend Alignment",
    beginnerSummary: "When price is above average, momentum is strong, and most stocks are green, the upward move has high credibility.",
    indicators: ["RSI > 65 (Bullish Zone)", "ADX > 25 (Rising)", "Price > VWAP", "Breadth > 32 ADV"],
    outcome: "Strong Trend Continuation Credibility",
    rationale: "Overbought RSI supported by high ADX, VWAP support, and broad constituent breadth confirms authentic institutional trend buying rather than exhaustion.",
    advancedNuance: "RSI range shift into 55–80 zone backed by positive cumulative volume delta and expanding Initial Balance.",
    tone: "BULLISH"
  },
  {
    title: "Overbought Exhaustion / Reversal Warning",
    beginnerSummary: "When price shoots high into a ceiling but other stocks are dropping, the move is running out of steam.",
    indicators: ["RSI > 75 (Extended)", "Breadth < 20 ADV (Weakening)", "Major Resistance Hit", "VIX Ticking Up"],
    outcome: "High Reversal / Pullback Risk",
    rationale: "Overbought reading occurring into structural resistance while market breadth is deteriorating indicates momentum is running on fumes.",
    advancedNuance: "Bearish divergence at multi-day Value Area High accompanied by rising put skew.",
    tone: "CAUTION"
  },
  {
    title: "Quiet Consolidation / False Breakout Trap",
    beginnerSummary: "When market is quiet and trend strength is low, breakout attempts will often fail.",
    indicators: ["Low VIX (< 12.0)", "ADX < 15 (No Trend)", "Mixed Breadth (24 ADV)", "Price Crossing VWAP"],
    outcome: "High Chop / Breakout Failure Risk",
    rationale: "Low volatility and absent trend strength indicate range compression; directional breakout attempts are prone to immediate failure.",
    advancedNuance: "Compressed Bollinger Width (< 20th percentile) causing repeated mean-reversion whipsaws.",
    tone: "RANGE"
  },
  {
    title: "Robust Support Confluence",
    beginnerSummary: "When option floor (Put Wall) matches chart support and market breadth is positive, price is likely to bounce.",
    indicators: ["PCR > 1.15 (Put Supportive)", "Put Wall Strike Coinciding", "Price Testing Floor Pivot S1", "Breadth Improving"],
    outcome: "High Support Floor Credibility",
    rationale: "Derivatives positioning (Put Wall) aligning with mathematical pivots and improving breadth creates high-probability structural demand floor.",
    advancedNuance: "Coinciding High Volume Node (HVN) and Put Wall strike providing dealer long-gamma stabilization.",
    tone: "BULLISH"
  }
];

export const UNIFIED_GLOBAL_RELATIONSHIPS: GlobalRelationship[] = [
  {
    asset: "NASDAQ / US Tech → Indian IT Sector",
    beginnerExplanation: "When US technology stocks do well overnight, Indian IT stocks (TCS, Infosys, Wipro) usually start the morning strong.",
    relationToNifty: "High positive correlation for IT constituents (TCS, Infosys, HCLTech, Wipro, TechM).",
    mechanism: "Global institutional capital re-rates tech sector valuations and enterprise spending sentiment in tandem.",
    caveat: "Currency movements (USD/INR depreciation) can partially offset US tech declines for Indian IT earnings.",
    advancedMacroContext: "Monitored via SOX semiconductor index, US 10Y yield sensitivity, and cloud capex guidance cycles."
  },
  {
    asset: "Brent Crude Oil ($/bbl)",
    beginnerExplanation: "India imports most of its oil. When crude oil spikes high, it increases costs for Indian companies, which can hurt the stock market.",
    relationToNifty: "Inverse correlation for oil-importing economies like India.",
    mechanism: "Elevated crude (> $90/bbl) increases import bill, CAD pressure, and input costs for paints, tires, airlines, and chemicals.",
    caveat: "Benefits upstream exploration companies (ONGC, Oil India), partially cushioning the total headline index impact.",
    advancedMacroContext: "Direct inflationary transmission mechanism affecting RBI repo rate trajectory and INR currency pressure."
  },
  {
    asset: "US 10-Year Treasury Yield",
    beginnerExplanation: "When US bond yields rise, foreign investors can earn good returns safely in the US, so they may pull money out of emerging markets like India.",
    relationToNifty: "Inverse correlation with Emerging Market risk assets.",
    mechanism: "Rising US risk-free yields make US assets more attractive, leading to FII capital outflows from Emerging Markets.",
    caveat: "Strong domestic institutional (DII) inflows in India have historically absorbed external FII selling pressure.",
    advancedMacroContext: "Global equity risk premium compression driving cross-border portfolio allocation rebalancing."
  }
];
