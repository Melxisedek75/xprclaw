/**
 * Real XPR Network Wallet Integration
 *
 * Uses @proton/web-sdk via ESM CDN (no build step needed).
 * Falls back to mock mode if SDK fails to load (development).
 *
 * Production: replace ESM CDN with bundled version for performance.
 */

const XPR_TESTNET = {
  chainId: '21dcae42c0182200e93f954a074011f9048a7f6c33f6f6a63ad52aeea7caa024',
  rpcEndpoint: 'https://testnet.xprnetwork.org',
};

const XPR_MAINNET = {
  chainId: '384da888112027f0321850a169f737c33e53b388aad48b5adace4bab97f437e0',
  rpcEndpoint: 'https://proton.eosusa.io',
};

const APP_NAME = 'GCSC CLAW';
const APP_LOGO = 'https://melxisedek75.github.io/xprclaw/icon-512.png';

// Use testnet by default; change to MAINNET when ready
const NETWORK = XPR_TESTNET;

let session = null;
let link = null;
let ProtonWebSDK = null;
let useMockMode = false;

/**
 * Lazy-load @proton/web-sdk from ESM CDN.
 */
async function loadSDK() {
  if (ProtonWebSDK) return ProtonWebSDK;
  try {
    const mod = await import('https://esm.sh/@proton/web-sdk@4.2.13');
    ProtonWebSDK = mod.default || mod.ProtonWebSDK || mod;
    return ProtonWebSDK;
  } catch (err) {
    console.warn('[wallet] SDK load failed, falling back to mock mode:', err);
    useMockMode = true;
    return null;
  }
}

/**
 * Connect to XPR wallet (Anchor / WebAuth / Proton Wallet).
 * Returns session object with auth, chainId, accountName.
 */
async function connectWallet() {
  const sdk = await loadSDK();

  if (!sdk || useMockMode) {
    return mockConnect();
  }

  try {
    const result = await sdk({
      linkOptions: {
        endpoints: [NETWORK.rpcEndpoint],
        chainId: NETWORK.chainId,
        restoreSession: false,
      },
      transportOptions: {
        requestAccount: 'gcsctoken111',
        requestStatus: true,
      },
      selectorOptions: {
        appName: APP_NAME,
        appLogo: APP_LOGO,
        showSelector: true,
      },
    });

    link = result.link;
    const userSession = result.session;

    if (!userSession) {
      throw new Error('User cancelled wallet connection');
    }

    session = {
      auth: {
        actor: userSession.auth.actor.toString(),
        permission: userSession.auth.permission.toString(),
      },
      chainId: NETWORK.chainId,
      rpcEndpoint: NETWORK.rpcEndpoint,
      accountName: userSession.auth.actor.toString(),
      pubkey: userSession.publicKey ? userSession.publicKey.toString() : null,
      isConnected: true,
      _raw: userSession, // Keep raw session for transaction signing
    };

    console.log('[wallet] Connected:', session.accountName);
    return session;
  } catch (err) {
    console.error('[wallet] Connect failed:', err);
    throw err;
  }
}

/**
 * Mock connect for offline development / SDK load failure.
 */
async function mockConnect() {
  console.warn('[wallet] Using MOCK mode (no real wallet)');
  await new Promise(r => setTimeout(r, 800));
  const mockAddr = 'mock' + Math.random().toString(36).substr(2, 8);
  session = {
    auth: { actor: mockAddr, permission: 'active' },
    chainId: NETWORK.chainId,
    rpcEndpoint: NETWORK.rpcEndpoint,
    accountName: mockAddr,
    pubkey: 'PUB_K1_MOCK',
    isConnected: true,
    isMock: true,
  };
  return session;
}

/**
 * Disconnect wallet (removes session).
 */
async function disconnectWallet() {
  if (link && session && session._raw) {
    try {
      await link.removeSession(APP_NAME, session._raw.auth, session._raw.chainId);
    } catch (e) {
      console.warn('[wallet] Disconnect error:', e);
    }
  }
  session = null;
  link = null;
}

function getSession() { return session; }
function isConnected() { return !!(session && session.isConnected); }

/**
 * Sign and broadcast a transaction.
 * For mock mode: returns fake signature.
 */
async function signTransaction(actions) {
  if (!session) throw new Error('Wallet not connected');

  if (session.isMock) {
    console.log('[wallet] MOCK signing:', actions);
    return {
      signatures: ['SIG_K1_MOCK_' + Date.now()],
      serializedTransaction: new Uint8Array(32),
      transaction_id: 'mock_' + Math.random().toString(36).substr(2, 16),
    };
  }

  try {
    const result = await session._raw.transact({ actions }, { broadcast: true });
    console.log('[wallet] Transaction signed:', result.processed?.id);
    return result;
  } catch (err) {
    console.error('[wallet] Sign failed:', err);
    throw err;
  }
}

/**
 * Get account info & XPR/$XLAW balances via RPC.
 */
async function getBalance() {
  if (!session) throw new Error('Wallet not connected');

  if (session.isMock) {
    return { xpr: '1500.0000 XPR', xlaw: '50.0000 XLAW', isMock: true };
  }

  try {
    // Get XPR balance
    const xprRes = await fetch(`${NETWORK.rpcEndpoint}/v1/chain/get_currency_balance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: 'eosio.token',
        account: session.accountName,
        symbol: 'XPR',
      }),
    });
    const xprBalance = await xprRes.json();

    // Get $XLAW balance from gcsctoken111 contract
    const xlawRes = await fetch(`${NETWORK.rpcEndpoint}/v1/chain/get_currency_balance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: 'gcsctoken111',
        account: session.accountName,
        symbol: 'XLAW',
      }),
    });
    const xlawBalance = await xlawRes.json();

    return {
      xpr: xprBalance[0] || '0.0000 XPR',
      xlaw: xlawBalance[0] || '0.0000 XLAW',
      currency: 'XPR',
    };
  } catch (err) {
    console.error('[wallet] Balance fetch failed:', err);
    return { xpr: '?', xlaw: '?', error: err.message };
  }
}

// Exports
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    connectWallet, disconnectWallet, getSession, isConnected,
    signTransaction, getBalance,
  };
}
if (typeof window !== 'undefined') {
  window.WalletModule = {
    connectWallet, disconnectWallet, getSession, isConnected,
    signTransaction, getBalance,
  };
}
