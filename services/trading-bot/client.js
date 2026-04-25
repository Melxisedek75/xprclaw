/**
 * XPRSimulator HTTP Client — communicates with MiroFish adapter backend
 * Usage: const client = new SimulatorClient('http://localhost:8088');
 *        const result = await client.simulate(request);
 */

class SimulatorClient {
  constructor(baseUrl = 'http://localhost:8088', timeout = 300000) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeout = timeout;
  }

  /**
   * POST /v1/simulate — run market simulation
   * @param {Object} request - SimulationRequest
   * @param {string} request.scenario - one of: staking_optimization, loan_management, arbitrage_window, treasury_rebalance, news_reaction
   * @param {Object} request.market_state - current market snapshot
   * @param {number} request.horizon_hours - simulation horizon (1-168)
   * @param {number} request.max_rounds - max simulation rounds (5-200)
   * @param {number} request.min_confidence - min confidence threshold (0-1)
   * @param {number} [request.cache_ttl_override_seconds] - override cache TTL
   * @returns {Promise<Object>} SimulationResult with verdict and recommendation
   */
  async simulate(request) {
    const url = `${this.baseUrl}/v1/simulate`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * GET /healthz — health check
   * @returns {Promise<Object>} health status
   */
  async healthz() {
    const url = `${this.baseUrl}/healthz`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * GET / — service info
   * @returns {Promise<Object>} service metadata
   */
  async info() {
    const url = this.baseUrl;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }
}

// Export for Node.js/ESM usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SimulatorClient;
}
