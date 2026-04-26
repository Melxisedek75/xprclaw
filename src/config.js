/**
 * Configuration for GCSC CLAW - Browser Safe
 * No process.env references - works in pure browser
 */

window.CONFIG = {
  ADAPTER_URL: 'https://xprclaw-production.up.railway.app',
  ADAPTER_HEALTH_ENDPOINT: '/health',
  XPR: {
    network: 'testnet',
    rpcUrl: 'https://testnet.xprnetwork.org',
    chainId: '21dcae42c0182200e93f954a074011f9048a7f6c33f6f6a63ad52aeea7caa024',
  },
  ADAPTER_TIMEOUT_MS: 30000,
  WALLET_CONNECT_TIMEOUT_MS: 30000,
  FEATURES: {
    PAPER_TRADING: true,
    REAL_TRADING: false,
    EXPERIMENTAL_FEATURES: false,
  },
};

window.getAdapterUrl = function(endpoint) {
  endpoint = endpoint || '';
  return window.CONFIG.ADAPTER_URL + endpoint;
};

window.isDevelopment = function() {
  return window.CONFIG.ADAPTER_URL.includes('localhost');
};
