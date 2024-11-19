// Known configurations - but we'll also capture everything for unknown domains
// Update the known configurations to use normalized domains
const CAPTURE_CONFIG = {
  "linkedin.com": {
    cookies: ["li_at", "JSESSIONID", "bcookie"],
    headers: ["csrf-token", "user-agent"],
  },
  "x.com": {
    cookies: ["auth_token", "ct0", "twid", "guest_id"],
    headers: [
      "x-csrf-token",
      "x-twitter-client-language",
      "authorization",
      "user-agent",
    ],
  },
};

// State management
let state = {
  isCapturing: false,
  domains: new Set(),
  sessions: {}, // Indexed by host
};

function normalizeDomain(domain) {
  try {
    domain = domain.trim().toLowerCase();
    domain = domain.replace(/^(https?:\/\/)?/, "");
    domain = domain.replace(/^www\./, "");
    domain = domain.split("/")[0];
    return domain;
  } catch (error) {
    console.error("Domain normalization error:", error);
    return null;
  }
}

function getHostFromUrl(url) {
  try {
    const urlObj = new URL(url);
    // Remove www. prefix to match normalized domains
    return urlObj.hostname.replace(/^www\./, "");
  } catch (error) {
    console.error("URL parsing error:", error);
    return null;
  }
}

// Initialize session data structure for a host
function initSession(host) {
  const normalizedHost = normalizeDomain(host);
  if (!state.sessions[normalizedHost]) {
    state.sessions[normalizedHost] = {
      cookies: {},
      headers: {},
      timestamp: new Date().toISOString(),
      host: host,
    };
  }
}

// Storage management
async function saveState() {
  try {
    await chrome.storage.local.set({
      isCapturing: state.isCapturing,
      domains: Array.from(state.domains),
      sessions: state.sessions,
    });
  } catch (error) {
    console.error("State save error:", error);
  }
}

async function loadState() {
  try {
    const data = await chrome.storage.local.get([
      "isCapturing",
      "domains",
      "sessions",
    ]);
    state.isCapturing = data.isCapturing || false;
    state.domains = new Set(data.domains || []);
    state.sessions = data.sessions || {};
  } catch (error) {
    console.error("State load error:", error);
    state.isCapturing = false;
    state.domains = new Set();
    state.sessions = {};
  }
}

// Capture handlers
function shouldCaptureForDomain(host) {
  const normalizedHost = normalizeDomain(host);
  return state.domains.has(normalizedHost);
}

function shouldCaptureItem(host, name, type) {
  const normalizedHost = normalizeDomain(host);
  const config = CAPTURE_CONFIG[normalizedHost];

  if (config) {
    return config[type].includes(name.toLowerCase());
  }
  return true; // Capture everything if no specific config
}

async function captureRequest(details) {
  if (!state.isCapturing) return;

  const host = getHostFromUrl(details.url);
  if (!host || !shouldCaptureForDomain(host)) return;

  try {
    const normalizedHost = normalizeDomain(host);
    initSession(normalizedHost);

    // Capture headers
    if (details.requestHeaders) {
      details.requestHeaders.forEach((header) => {
        const name = header.name.toLowerCase();
        if (shouldCaptureItem(normalizedHost, name, "headers")) {
          state.sessions[normalizedHost].headers[name] = header.value;
        }
      });
    }

    await saveState();
  } catch (error) {
    console.error("Request capture error:", error);
  }
}

async function captureCookies(domain) {
  const normalizedDomain = normalizeDomain(domain);
  try {
    const cookies = await chrome.cookies.getAll({ domain: normalizedDomain });

    initSession(normalizedDomain);

    cookies.forEach((cookie) => {
      const name = cookie.name.toLowerCase();
      if (shouldCaptureItem(normalizedDomain, name, "cookies")) {
        state.sessions[normalizedDomain].cookies[name] = cookie.value;
      }
    });

    await saveState();
  } catch (error) {
    console.error("Cookie capture error:", error);
  }
}

// Message handlers
function handleMessage(message, sender, sendResponse) {
  const respond = (response) => {
    try {
      sendResponse(response);
    } catch (error) {
      console.error("Response send error:", error);
    }
  };

  (async () => {
    try {
      switch (message.action) {
        case "startCapture":
          state.isCapturing = true;
          await saveState();
          respond({ success: true });
          break;

        case "stopCapture":
          state.isCapturing = false;
          await saveState();
          respond({ success: true });
          break;

        case "addDomain":
          const domain = normalizeDomain(message.domain);
          if (domain) {
            state.domains.add(domain);
            await saveState();
            respond({ success: true, domain });
          } else {
            respond({ success: false, error: "Invalid domain" });
          }
          break;

        case "removeDomain":
          state.domains.delete(message.domain);
          delete state.sessions[message.domain];
          await saveState();
          respond({ success: true });
          break;

        case "getState":
          respond({
            isCapturing: state.isCapturing,
            domains: Array.from(state.domains),
          });
          break;

        case "exportData":
          respond({
            success: true,
            data: state.sessions, // Already in the correct format
          });
          break;

        case "clearData":
          state.sessions = {};
          await saveState();
          respond({ success: true });
          break;

        default:
          respond({ success: false, error: "Unknown action" });
      }
    } catch (error) {
      console.error("Message handling error:", error);
      respond({ success: false, error: error.message });
    }
  })();

  return true;
}

// Initialize
async function initialize() {
  try {
    await loadState();

    // Set up listeners for header capture
    chrome.webRequest.onSendHeaders.addListener(
      captureRequest,
      { urls: ["<all_urls>"] },
      ["requestHeaders", "extraHeaders"]
    );

    chrome.runtime.onMessage.addListener(handleMessage);

    // Periodically capture cookies for monitored domains
    setInterval(async () => {
      if (state.isCapturing) {
        for (const domain of state.domains) {
          await captureCookies(domain);
        }
      }
    }, 5000);
  } catch (error) {
    console.error("Initialization error:", error);
  }
}

initialize();
