// --- Context Menu Setup ---
// Create context menu items for selected text and images when the extension is installed or reloaded
chrome.runtime.onInstalled.addListener(() => {
  // Remove all existing context menu items first to prevent duplicates
  chrome.contextMenus.removeAll(() => {
    // For selected text
    chrome.contextMenus.create({
      id: 'remember-text',
      title: 'Remember This',
      contexts: ['selection']
    });
    // For images
    chrome.contextMenus.create({
      id: 'remember-image',
      title: 'Remember This',
      contexts: ['image']
    });
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  // If user right-clicked selected text
  if (info.menuItemId === 'remember-text' && info.selectionText) {
    saveRememberedItem({
      type: 'text',
      content: info.selectionText,
      url: info.pageUrl,
      timestamp: new Date().toISOString()
    });
  } else if (info.menuItemId === 'remember-image' && info.srcUrl) {
    // If user right-clicked an image
    saveRememberedItem({
      type: 'image',
      content: info.srcUrl,
      url: info.pageUrl,
      timestamp: new Date().toISOString()
    });
  }
});

// Save remembered item to local storage
function saveRememberedItem(item) {
  // Add priority/highlight tag to user-flagged items
  const highlightedItem = {
    ...item,
    priority: true,
    type: 'highlight',
    originalType: item.type // Keep track of whether it was text or image
  };
  
  // Store highlighted items with regular visits data for unified storage
  chrome.storage.local.get({ visits: [] }, result => {
    const visits = result.visits;
    visits.push(highlightedItem);
    chrome.storage.local.set({ visits });
    console.log('Saved new highlighted item:', highlightedItem.originalType, highlightedItem.url);
    // Optionally, show a notification (requires notification permission)
    // chrome.notifications.create({
    //   type: 'basic',
    //   iconUrl: 'icon48.png',
    //   title: 'Saved',
    //   message: 'Content saved to Research Board.'
    // });
  });
}

// background.js
// Handles communication, PDF detection, browsing activity tracking, and storage

// --- Duplicate Content Prevention ---
// Track processed URLs for page data extraction to prevent duplicates during session
const processedPageData = new Set(); // Only track page data URLs to prevent re-extraction

// Check if page data for this URL has already been processed (for page data extraction only)
function isPageDataDuplicate(url) {
  if (processedPageData.has(url)) {
    return true;
  }
  processedPageData.add(url);
  return false;
}

// --- Browsing Activity Tracking ---
let activeTabId = null;
let tabStartTimes = {};

// Listen for tab activation
chrome.tabs.onActivated.addListener(activeInfo => {
  handleTabSwitch(activeInfo.tabId);
});

// Listen for tab updates (URL changes)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url) {
    handleTabSwitch(tabId);
    detectPDF(tabId, changeInfo.url);
  }
});

// Listen for tab removal (close)
chrome.tabs.onRemoved.addListener(tabId => {
  recordTimeSpent(tabId);
  delete tabStartTimes[tabId];
});

// Handle tab/window switch
function handleTabSwitch(tabId) {
  if (activeTabId !== null && tabStartTimes[activeTabId]) {
    recordTimeSpent(activeTabId);
  }
  activeTabId = tabId;
  tabStartTimes[tabId] = Date.now();
}

// Record time spent on a tab
function recordTimeSpent(tabId) {
  const start = tabStartTimes[tabId];
  if (!start) return;
  const timeSpent = Date.now() - start;
  chrome.tabs.get(tabId, tab => {
    if (chrome.runtime.lastError || !tab.url) return;
    const visit = {
      url: tab.url,
      timestamp: new Date(start).toISOString(),
      timeSpentMs: timeSpent
    };
    saveVisit(visit);
  });
}

// Save visit data to Chrome local storage
function saveVisit(visit) {
  chrome.storage.local.get({ visits: [] }, result => {
    const visits = result.visits;
    
    // Check if there's an existing visit for this URL
    const existingVisitIndex = visits.findIndex(v => v.url === visit.url && !v.priority);
    
    if (existingVisitIndex !== -1) {
      // Consolidate time spent and increment visit count
      visits[existingVisitIndex].timeSpentMs += visit.timeSpentMs;
      visits[existingVisitIndex].visitCount = (visits[existingVisitIndex].visitCount || 1) + 1;
      visits[existingVisitIndex].lastVisit = visit.timestamp;
      console.log('Updated existing visit:', visit.url, 'Total time:', visits[existingVisitIndex].timeSpentMs);
    } else {
      // New visit - add visit count
      visit.visitCount = 1;
      visit.type = 'visit';
      visits.push(visit);
      console.log('Saved new visit:', visit.url);
    }
    
    chrome.storage.local.set({ visits });
  });
}

// --- PDF Detection and Handling ---
function detectPDF(tabId, url) {
  if (url.match(/\.pdf($|\?)/i)) {
    chrome.tabs.sendMessage(tabId, { type: 'PROMPT_SAVE_PDF', url });
  }
}

// --- Research Board Backend Sync Logic ---
const STORAGE_KEY = 'researchBoardPages';
const SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

// Store minimal metadata in chrome.storage.local
function storePageLocally(meta) {
  chrome.storage.local.get([STORAGE_KEY], result => {
    const pages = result[STORAGE_KEY] || [];
    pages.push(meta);
    chrome.storage.local.set({ [STORAGE_KEY]: pages });
  });
}

// Remove synced or old items from local storage
function cleanupLocalStorage() {
  chrome.storage.local.get([STORAGE_KEY], result => {
    let pages = result[STORAGE_KEY] || [];
    const now = Date.now();
    pages = pages.filter(page => {
      // Remove if synced or older than MAX_AGE_MS
      return !page.synced && (now - new Date(page.accessedAt).getTime() < MAX_AGE_MS);
    });
    chrome.storage.local.set({ [STORAGE_KEY]: pages });
  });
}

// Try to sync pending items to backend
function syncPendingPages() {
  chrome.storage.local.get([STORAGE_KEY], result => {
    const pages = result[STORAGE_KEY] || [];
    pages.forEach(page => {
      if (!page.synced && page.pendingData) {
        sendDataToBackend(page.pendingData, (backendId) => {
          page.synced = true;
          page.backendId = backendId;
          delete page.pendingData;
          chrome.storage.local.set({ [STORAGE_KEY]: pages });
        });
      }
    });
  });
}

// Send data to backend API (with callback for backendId)
function sendDataToBackend(data, onSuccess) {
  console.log('[ResearchBoard] Sending to backend:', data);
  fetch('http://127.0.0.1:8000/api/v1/collect', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(result => {
    console.log('[ResearchBoard] Backend response:', result);
    if (result.success && result.page_id) {
      if (onSuccess) onSuccess(result.page_id);
    }
  })
  .catch(error => {
    console.error('[ResearchBoard] Error sending data to backend:', error);
    // If failed, queue for later upload
    queueForLater(data);
  });
}

// Queue data for later upload
function queueForLater(data) {
  const meta = {
    title: data.title,
    url: data.url,
    preview: (data.text || '').slice(0, 200),
    favicon: getFavicon(data),
    accessedAt: data.accessedAt,
    synced: false,
    pendingData: data // Only keep reference, not large blobs in local storage
  };
  storePageLocally(meta);
}

// Get favicon URL from page data
function getFavicon(data) {
  return data.favicon || '';
}

// Handle PAGE_DATA messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'PAGE_DATA' && message.data) {
    const data = message.data;
    // Prepare minimal metadata
    const meta = {
      title: data.title,
      url: data.url,
      preview: (data.text || '').slice(0, 200),
      favicon: getFavicon(data),
      accessedAt: data.accessedAt,
      synced: false
    };
    // Try backend sync
    sendDataToBackend(data, (backendId) => {
      meta.synced = true;
      meta.backendId = backendId;
      storePageLocally(meta);
    });
    // If backend unreachable, queue for later
    // (handled in sendDataToBackend's catch)
  }
});

// Periodic cleanup and sync
setInterval(() => {
  cleanupLocalStorage();
  syncPendingPages();
}, SYNC_INTERVAL);

