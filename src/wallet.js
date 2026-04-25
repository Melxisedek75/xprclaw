/**
 * Wallet Integration for XPR Network
 *
 * TODO: Install @proton/web-sdk for production
 * For MVP: simple fetch-based implementation
 *
 * Production setup:
 * 1. npm install @proton/web-sdk
 * 2. Replace this file with real SDK integration
 * 3. Update app.html to import from build output
 */

/**
 * Wallet session object (when connected)
 */
let session = null;

/**
 * Request wallet connection
 * MVP: mock implementation
 * Production: await ProtonWebSDK.connect()
 */
async function connectWallet() {
  try {
    // Simulated connection delay
    await new Promise(resolve => setTimeout(resolve, 1200));

    // Generate mock address for MVP testing
    const mockAddr = 'xprtest' + Math.random().toString(36).substr(2, 9) + '111112222';

    session = {
      auth: {
        actor: mockAddr.split('test')[0] || 'xprtest',
        permission: 'active',
      },
      chainId: '21dcae42c0182200e93f954a074011f9048a7f6c33f6f6a63ad52aeea7caa024', // XPR Testnet
      rpcEndpoint: 'https://testnet.xprnetwork.org',
      accountName: mockAddr,
      pubkey: 'PUB_K1_K1LoqCgJ7F8K5w' + Math.random().toString(36).substr(2, 20), // Mock pubkey
      isConnected: true,
    };

    return session;
  } catch (error) {
    console.error('Wallet connection failed:', error);
    throw error;
  }
}

/**
 * Disconnect wallet
 */
function disconnectWallet() {
  session = null;
}

/**
 * Get current session
 */
function getSession() {
  return session;
}

/**
 * Check if wallet is connected
 */
function isConnected() {
  return session && session.isConnected;
}

/**
 * Sign a transaction (stub for MVP)
 * Production: session.signTransaction(...)
 */
async function signTransaction(actions) {
  if (!session) throw new Error('Wallet not connected');

  console.log('Transaction to sign:', actions);

  // Mock signing for MVP
  return {
    signatures: ['SIG_K1_' + Math.random().toString(36).substr(2, 20)],
    serializedTransaction: new Uint8Array(32),
  };
}

/**
 * Get account balance (stub)
 * Production: RPC call to XPR node
 */
async function getBalance() {
  if (!session) throw new Error('Wallet not connected');

  try {
    // TODO: Real RPC call
    // const response = await fetch(session.rpcEndpoint, {
    //   method: 'POST',
    //   body: JSON.stringify({
    //     jsonrpc: '2.0',
    //     id: 1,
    //     method: 'eth_getBalance',
    //     params: [session.accountName, 'latest'],
    //   }),
    // });

    // Mock response for MVP
    return {
      xpr: '1500.0000',
      xlaw: '50.0000',
      currency: 'XPR',
    };
  } catch (error) {
    console.error('Failed to get balance:', error);
    throw error;
  }
}

/**
 * Export for use in HTML/JS
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    connectWallet,
    disconnectWallet,
    getSession,
    isConnected,
    signTransaction,
    getBalance,
  };
}

// Also export to window for direct HTML use
if (typeof window !== 'undefined') {
  window.WalletModule = {
    connectWallet,
    disconnectWallet,
    getSession,
    isConnected,
    signTransaction,
    getBalance,
  };
}
