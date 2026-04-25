/**
 * Decision Engine Tests
 * Run with: node --test decision-engine.test.js
 */

const {
  extractVerdictFromReport,
  mergeRecommendations,
  shouldExecute,
  riskCheck,
  makeDecision,
} = require('./decision-engine.js');

const assert = require('assert');

// Test: mergeRecommendations with unanimous decision
{
  const recommendations = [
    { action: 'proceed', confidence: 0.8, rationale: 'bullish', signals: {} },
    { action: 'proceed', confidence: 0.75, rationale: 'bullish', signals: {} },
    { action: 'proceed', confidence: 0.85, rationale: 'bullish', signals: {} },
  ];
  const result = mergeRecommendations(recommendations);
  assert.strictEqual(result.action, 'proceed');
  assert(result.confidence > 0.7);
  assert(result.rationale.includes('proceed'));
  console.log('✓ mergeRecommendations: unanimous decision');
}

// Test: mergeRecommendations with mixed decisions
{
  const recommendations = [
    { action: 'proceed', confidence: 0.8, rationale: 'bullish', signals: {} },
    { action: 'hold', confidence: 0.5, rationale: 'uncertain', signals: {} },
    { action: 'proceed', confidence: 0.7, rationale: 'bullish', signals: {} },
  ];
  const result = mergeRecommendations(recommendations);
  assert.strictEqual(result.action, 'proceed'); // 2/3 votes
  assert(result.signals.vote_share >= 0.66);
  console.log('✓ mergeRecommendations: majority vote');
}

// Test: shouldExecute with sufficient confidence
{
  const recommendation = { action: 'proceed', confidence: 0.7 };
  const result = shouldExecute(recommendation, 0.55);
  assert.strictEqual(result.should_execute, true);
  console.log('✓ shouldExecute: meets confidence threshold');
}

// Test: shouldExecute with low confidence
{
  const recommendation = { action: 'proceed', confidence: 0.3 };
  const result = shouldExecute(recommendation, 0.55);
  assert.strictEqual(result.should_execute, false);
  assert(result.reason.includes('below threshold'));
  console.log('✓ shouldExecute: low confidence rejection');
}

// Test: shouldExecute rejects non-execution actions
{
  const recommendation = { action: 'hold', confidence: 0.8 };
  const result = shouldExecute(recommendation, 0.55);
  assert.strictEqual(result.should_execute, false);
  assert(result.reason.includes('not executable'));
  console.log('✓ shouldExecute: non-execution action rejection');
}

// Test: riskCheck with valid market state
{
  const recommendation = { action: 'proceed', confidence: 0.8 };
  const marketState = {
    xpr_price_usd: 0.0042,
    staking_apy: 0.085,
    loan_apy: 0.061,
  };
  const result = riskCheck(recommendation, marketState);
  assert.strictEqual(result.is_safe, true);
  console.log('✓ riskCheck: valid market state');
}

// Test: riskCheck rejects abort signal
{
  const recommendation = { action: 'abort', confidence: 0.9 };
  const marketState = { xpr_price_usd: 0.0042 };
  const result = riskCheck(recommendation, marketState);
  assert.strictEqual(result.is_safe, false);
  assert(result.reason.toLowerCase().includes('abort'));
  console.log('✓ riskCheck: abort signal');
}

// Test: makeDecision with valid simulation result
{
  const simulationResult = {
    scenario: 'staking_optimization',
    verdict: { sentiment: 0.5, confidence: 0.8 },
    recommendation: {
      action: 'proceed',
      confidence: 0.75,
      rationale: 'Bullish sentiment',
      signals: { test: 1.0 },
    },
    market_state: { xpr_price_usd: 0.0042 },
  };
  const result = makeDecision(simulationResult);
  assert.strictEqual(result.decision, 'proceed');
  assert(result.should_execute === true || result.should_execute === false);
  assert(result.risk_check.is_safe === true || result.risk_check.is_safe === false);
  console.log('✓ makeDecision: valid simulation result');
}

// Test: makeDecision with invalid result
{
  const result = makeDecision(null);
  assert.strictEqual(result.decision, 'hold');
  assert.strictEqual(result.should_execute, false);
  console.log('✓ makeDecision: null input handling');
}

// Test: extractVerdictFromReport (stub)
{
  const markdown = '# Simulation Report\nAnalysis results...';
  const verdict = extractVerdictFromReport(markdown);
  assert(verdict.sentiment !== undefined);
  assert(verdict.confidence !== undefined);
  assert(verdict.predicted_price_drift_pct !== undefined);
  console.log('✓ extractVerdictFromReport: stub returns valid verdict');
}

console.log('\n✅ All decision-engine tests passed!');
