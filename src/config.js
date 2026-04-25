/**
 * Configuration for GCSC CLAW
 *
 * Update ADAPTER_URL when deploying backend to production.
 * Default: localhost (for local development)
 */

const CONFIG = {
  // Backend Adapter URL
  ADAPTER_URL: process.env.VITE_API_URL || 'http://localhost:8088',
  ADAPTER_HEALTH_ENDPOINT: '/healthz',

  // XPR Network Configuration
  XPR: {
    network: process.env.XPR_NETWORK || 'testnet',
    rpcUrl: process.env.XPR_RPC_URL || 'https://testnet.xprnetwork.org',
    chainId: '21dcae42c0182200e93f954a074011f9048a7f6c33f6f6a63ad52aeea7caa024',
  },

  // Timeouts
  ADAPTER_TIMEOUT_MS: 30000,
  WALLET_CONNECT_TIMEOUT_MS: 30000,

  // Feature Flags
  FEATURES: {
    PAPER_TRADING: true,
    REAL_TRADING: false,
    EXPERIMENTAL_FEATURES: false,
  },
};

/**
 * Get full adapter URL with endpoint
 */
function getAdapterUrl(endpoint = '') {
  const base = CONFIG.ADAPTER_URL;
  return endpoint ? `${base}${endpoint}` : base;
}

/**
 * Check if we're in development mode
 */
function isDevelopment() {
  return CONFIG.ADAPTER_URL.includes('localhost');
}

/**
 * Export
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CONFIG, getAdapterUrl, isDevelopment };
}

if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
  window.getAdapterUrl = getAdapterUrl;
  window.isDevelopment = isDevelopment;
}
