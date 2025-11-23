// Flow State Facilitator - Background Worker
// Connects to the Native Messaging Host (Python) and blocks distracting tabs on trigger

let port = null;
let lastReportedTabId = null;

// Connect to the Native Messaging Host
function connectToNativeHost() {
  const hostName = "com.flow.engine"; // Must match the name in install_host.py
  console.log("Connecting to native host:", hostName);

  try {
    port = chrome.runtime.connectNative(hostName);

    port.onMessage.addListener((msg) => {
      console.log("Received from native host:", msg);
      try {
        // Handle "WAIT FOR BREAK" - close the distracting tab
        if (msg && msg.status === 'wait_for_break' && lastReportedTabId != null) {
          chrome.tabs.get(lastReportedTabId, (tab) => {
            if (chrome.runtime.lastError) {
              console.warn('tabs.get error:', chrome.runtime.lastError);
              return;
            }
            if (tab && tab.id) {
              chrome.tabs.remove(tab.id, () => {
                if (chrome.runtime.lastError) {
                  console.warn('tabs.remove error:', chrome.runtime.lastError);
                } else {
                  console.log('Closed tab on WAIT FOR BREAK:', tab.id);
                }
              });
            }
          });
        }
        // Handle intervention triggered (legacy)
        else if (msg && msg.status === 'intervention_triggered' && lastReportedTabId != null) {
          // Attempt to close the last reported (active) tab
          chrome.tabs.get(lastReportedTabId, (tab) => {
            if (chrome.runtime.lastError) {
              console.warn('tabs.get error:', chrome.runtime.lastError);
              return;
            }
            if (tab && tab.id) {
              chrome.tabs.remove(tab.id, () => {
                if (chrome.runtime.lastError) {
                  console.warn('tabs.remove error:', chrome.runtime.lastError);
                } else {
                  console.log('Blocked and closed tab', tab.id);
                }
              });
            }
          });
        }
      } catch (e) {
        console.error('Error handling native response:', e);
      }
    });

    port.onDisconnect.addListener(() => {
      console.log("Disconnected from native host");
      console.log("Error:", chrome.runtime.lastError);
      port = null;
      // Try to reconnect after a delay
      setTimeout(connectToNativeHost, 5000);
    });

  } catch (e) {
    console.error("Failed to connect:", e);
  }
}

// Send message to native host
function sendToNative(data) {
  if (!port) {
    connectToNativeHost();
  }

  if (port) {
    try {
      port.postMessage(data);
    } catch (e) {
      console.error("Failed to send message:", e);
    }
  }
}

// Monitor Tab Changes
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      reportActivity(tab);
    }
  } catch (e) {
    console.error("Error getting tab info:", e);
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && tab.active) {
    reportActivity(tab);
  }
});

function reportActivity(tab) {
  // Ignore chrome:// and internal pages
  if (!tab.url || tab.url.startsWith("chrome://") || tab.url.startsWith("edge://")) {
    return;
  }

  // Extract search query (Google, Bing, DuckDuckGo, YouTube search)
  try {
    const u = new URL(tab.url);
    const host = u.hostname.toLowerCase();
    let query = null;
    if (host.includes('google.') && u.pathname.startsWith('/search')) {
      query = u.searchParams.get('q');
    } else if (host.includes('bing.com') && u.pathname.startsWith('/search')) {
      query = u.searchParams.get('q');
    } else if (host.includes('duckduckgo.com')) {
      query = u.searchParams.get('q');
    } else if (host.includes('youtube.com') && (u.pathname.startsWith('/results'))) {
      query = u.searchParams.get('search_query');
    }
    if (query && query.trim().length > 0) {
      sendToNative({ type: 'search_query', query, engine: host, timestamp: Date.now() / 1000 });
    }
  } catch (e) {
    console.warn('query parse error:', e);
  }

  // Immediate local block for known distracting URLs (no backend round-trip required)
  try {
    const url = tab.url.toLowerCase();
    const distracting = [
      'youtube.com/shorts',
      'twitter.com',
      'x.com',
      'facebook.com',
      'instagram.com',
      'reddit.com',
      'tiktok.com',
      'netflix.com'
    ];
    if (distracting.some((d) => url.includes(d))) {
      chrome.tabs.remove(tab.id, () => {
        if (chrome.runtime.lastError) {
          console.warn('local block tabs.remove error:', chrome.runtime.lastError);
        } else {
          console.log('Locally blocked and closed tab', tab.id);
        }
      });
    }
  } catch (e) {
    console.warn('local block error:', e);
  }

  const activity = {
    type: "browser_activity",
    url: tab.url,
    title: tab.title || "Unknown",
    timestamp: Date.now() / 1000
  };

  console.log("Reporting activity:", activity);
  lastReportedTabId = tab.id || null;
  sendToNative(activity);
}

// Initial connection
connectToNativeHost();
