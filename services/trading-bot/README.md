# XPRClaw Trading Bot

Autonomous trading decision system that coordinates with the MiroFish multi-agent simulator.

## Architecture

- **client.js**: HTTP client to call MiroFish adapter's `POST /v1/simulate` endpoint
- **decision-engine.js**: Decision logic that processes simulation results
  - Merges multiple agent opinions
  - Applies execution thresholds
  - Performs risk checks
  - Returns final trading decision

## Usage

### Basic Flow

```javascript
const SimulatorClient = require('./client');
const { makeDecision } = require('./decision-engine');

const client = new SimulatorClient('http://localhost:8088');

const request = {
  scenario: 'staking_optimization',
  market_state: {
    xpr_price_usd: 0.0042,
    staking_apy: 0.085,
    loan_apy: 0.061,
    metalx_xpr_usd_spread_bps: 23,
    treasury_xpr: 1250000,
    open_loan_xpr: 300000,
    timestamp: new Date().toISOString(),
  },
  horizon_hours: 24,
  max_rounds: 30,
};

try {
  const result = await client.simulate(request);
  const decision = makeDecision(result, { minConfidence: 0.55 });
  
  console.log('Decision:', decision.decision);
  console.log('Should Execute:', decision.should_execute);
  console.log('Confidence:', decision.confidence);
  console.log('Reason:', decision.execution_reason);
} catch (error) {
  console.error('Simulation failed:', error);
}
```

## Decision Rules

### Recommendation Merging

Combines N agent verdicts via majority vote:
- `proceed`: Execute the planned action
- `reduce`: Scale down position
- `hold`: Maintain current position
- `abort`: Stop and de-risk

### Execution Threshold

By default requires `confidence >= 0.55` and `action == 'proceed'`.

### Risk Checks

- Validates market state (XPR price > 0)
- Rejects abort signals
- Rejects invalid inputs

## Testing

```bash
node decision-engine.test.js
```

All 10 tests pass:
- Unanimous merging
- Majority voting with mixed decisions
- Confidence thresholds
- Risk validation
- Edge cases (null input, invalid state)

## Integration

Connect with Node.js bot/trading engine:

```javascript
const bot = {
  async updateMarketState(state) {
    this.marketState = state;
  },
  
  async runDecisionCycle() {
    const request = {
      scenario: 'staking_optimization',
      market_state: this.marketState,
      horizon_hours: 24,
      max_rounds: 30,
    };
    
    const result = await this.client.simulate(request);
    return makeDecision(result);
  }
};
```

## Configuration

- MiroFish adapter URL: `http://localhost:8088` (default)
- Request timeout: `300000ms` (5 minutes, default)
- Min confidence threshold: `0.55` (configurable per decision)
- Cache: Results cached server-side (1 hour default)

## Next Steps

1. **LLM Integration**: Replace `extractVerdictFromReport` stub with Claude API
2. **Live Market Data**: Connect to XPR Network price feeds
3. **Paper Trading**: Simulate trades without real execution
4. **Execution**: Add actual transaction signing (Proton Toolkit)
5. **Monitoring**: Add observability (Sentry, Prometheus)
