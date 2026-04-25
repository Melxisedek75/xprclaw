/**
 * API Client for GCSC CLAW FastAPI Adapter
 *
 * Handles all communication with backend:
 * - Health checks
 * - Simulation requests
 * - Bot status queries
 */

/**
 * Make API request with timeout and error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = window.getAdapterUrl(endpoint);
  const timeout = options.timeout || window.CONFIG.ADAPTER_TIMEOUT_MS;
  const method = options.method || 'GET';
  const body = options.body ? JSON.stringify(options.body) : null;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout (${timeout}ms)`);
    }
    throw error;
  }
}

/**
 * Health Check
 */
async function getHealth() {
  try {
    return await apiRequest('/healthz');
  } catch (error) {
    console.error('Health check failed:', error);
    return {
      status: 'offline',
      error: error.message,
    };
  }
}

/**
 * Run Simulation (core operation)
 */
async function simulate(request) {
  return await apiRequest('/v1/simulate', {
    method: 'POST',
    body: request,
  });
}

/**
 * Get Bot Status (stub for future implementation)
 */
async function getBotStatus() {
  try {
    // TODO: Implement /bot/status endpoint in adapter
    return {
      mode: 'paper',
      pnl: 0,
      positions: [],
      lastUpdate: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Bot status fetch failed:', error);
    return { error: error.message };
  }
}

/**
 * Convenience: Run full decision flow
 *
 * 1. Check health
 * 2. Request simulation
 * 3. Return decision + verdict
 */
async function runFullFlow(marketState, scenario = 'staking_optimization') {
  try {
    // Health check first
    const health = await getHealth();
    if (health.error) {
      return { error: `Backend offline: ${health.error}` };
    }

    // Run simulation
    const simRequest = {
      scenario,
      market_state: marketState,
      horizon_hours: 24,
      max_rounds: 30,
    };

    const result = await simulate(simRequest);

    return {
      success: true,
      decision: result.recommendation?.action || 'hold',
      confidence: result.recommendation?.confidence || 0,
      rationale: result.recommendation?.rationale || '',
      verdict: result.verdict,
      result,
    };
  } catch (error) {
    console.error('Full flow failed:', error);
    return {
      success: false,
      error: error.message,
      decision: 'hold',
      confidence: 0,
    };
  }
}

/**
 * Export for use in HTML
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    apiRequest,
    getHealth,
    simulate,
    getBotStatus,
    runFullFlow,
  };
}

if (typeof window !== 'undefined') {
  window.ApiClient = {
    getHealth,
    simulate,
    getBotStatus,
    runFullFlow,
  };
}
