/**
 * Decision Engine — processes simulation results and produces trading decisions
 * Coordinates multiple agent verdicts into a unified recommendation
 */

/**
 * Extract verdict from report markdown (stub)
 * In production, would use Claude to parse report text
 * @param {string} reportMarkdown - raw report markdown from MiroFish
 * @returns {Object} Verdict with sentiment, price_drift, social_volume, confidence
 */
function extractVerdictFromReport(reportMarkdown) {
  // Stub: return neutral verdict
  // Real implementation: parse report using Claude API
  return {
    sentiment: 0.0,
    predicted_price_drift_pct: 0.0,
    social_volume_delta_pct: 0.0,
    confidence: 0.5,
  };
}

/**
 * Merge multiple agent opinions into single recommendation
 * Uses consensus logic: majority vote on action, average confidence
 * @param {Array} recommendations - array of Recommendation objects
 * @returns {Object} merged Recommendation
 */
function mergeRecommendations(recommendations) {
  if (!recommendations || recommendations.length === 0) {
    return {
      action: 'hold',
      confidence: 0,
      rationale: 'No recommendations to merge',
      signals: {},
    };
  }

  // Count votes by action
  const actionVotes = {};
  let totalConfidence = 0;

  for (const rec of recommendations) {
    actionVotes[rec.action] = (actionVotes[rec.action] || 0) + 1;
    totalConfidence += rec.confidence;
  }

  // Majority vote
  const topAction = Object.entries(actionVotes).sort(([, a], [, b]) => b - a)[0][0];
  const voteShare = actionVotes[topAction] / recommendations.length;
  const avgConfidence = totalConfidence / recommendations.length;

  // Reduce confidence if not strong consensus
  const consensusMultiplier = voteShare >= 0.66 ? 1.0 : voteShare >= 0.5 ? 0.7 : 0.4;
  const finalConfidence = Math.max(0, Math.min(1, avgConfidence * consensusMultiplier));

  const rationale = `Merged ${recommendations.length} agent opinions: ${Object.entries(actionVotes)
    .map(([action, votes]) => `${votes}/${recommendations.length} ${action}`)
    .join(', ')}. Consensus: ${topAction} (${(voteShare * 100).toFixed(0)}% agreement).`;

  return {
    action: topAction,
    confidence: finalConfidence,
    rationale,
    signals: {
      vote_share: voteShare,
      agent_count: recommendations.length,
      consensus_multiplier: consensusMultiplier,
    },
  };
}

/**
 * Decision Policy: determine if recommendation meets execution threshold
 * @param {Object} recommendation - Recommendation with action, confidence
 * @param {number} [minConfidence=0.55] - minimum confidence to execute
 * @returns {Object} { should_execute: boolean, reason: string }
 */
function shouldExecute(recommendation, minConfidence = 0.55) {
  const executionActions = ['proceed'];
  const passConfidence = recommendation.confidence >= minConfidence;
  const isExecutionAction = executionActions.includes(recommendation.action);

  return {
    should_execute: isExecutionAction && passConfidence,
    reason: !isExecutionAction
      ? `Action '${recommendation.action}' not executable (needs 'proceed')`
      : !passConfidence
        ? `Confidence ${recommendation.confidence.toFixed(2)} below threshold ${minConfidence}`
        : `Action '${recommendation.action}' with ${recommendation.confidence.toFixed(2)} confidence (threshold: ${minConfidence})`,
  };
}

/**
 * Risk check: verify action doesn't exceed position limits
 * @param {Object} recommendation - trading recommendation
 * @param {Object} marketState - current market snapshot
 * @returns {Object} { is_safe: boolean, reason: string }
 */
function riskCheck(recommendation, marketState) {
  // Stub: basic checks only
  if (recommendation.action === 'abort') {
    return {
      is_safe: false,
      reason: 'Abort signal: market risk too high',
    };
  }

  // XPR price sanity check
  if (!marketState || !marketState.xpr_price_usd || marketState.xpr_price_usd <= 0) {
    return {
      is_safe: false,
      reason: 'Invalid market state: XPR price missing or invalid',
    };
  }

  return {
    is_safe: true,
    reason: 'Market state passed basic sanity checks',
  };
}

/**
 * Full decision pipeline
 * @param {Object} simulationResult - SimulationResult from adapter
 * @param {Object} options - { minConfidence: 0.55 }
 * @returns {Object} decision result with execution flag and rationale
 */
function makeDecision(simulationResult, options = {}) {
  const { minConfidence = 0.55 } = options;

  if (!simulationResult || !simulationResult.recommendation) {
    return {
      decision: 'hold',
      rationale: 'Invalid simulation result',
      confidence: 0,
      should_execute: false,
      execution_reason: 'No valid recommendation',
      risk_check: { is_safe: false, reason: 'No market state to verify' },
    };
  }

  const recommendation = simulationResult.recommendation;
  const executionCheck = shouldExecute(recommendation, minConfidence);
  const riskCheckResult = riskCheck(recommendation, simulationResult.market_state);

  return {
    decision: recommendation.action,
    rationale: recommendation.rationale,
    confidence: recommendation.confidence,
    should_execute: executionCheck.should_execute && riskCheckResult.is_safe,
    execution_reason: riskCheckResult.is_safe
      ? executionCheck.reason
      : riskCheckResult.reason,
    risk_check: riskCheckResult,
    signals: recommendation.signals,
    verdict: simulationResult.verdict,
  };
}

// Export for Node.js usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    extractVerdictFromReport,
    mergeRecommendations,
    shouldExecute,
    riskCheck,
    makeDecision,
  };
}
