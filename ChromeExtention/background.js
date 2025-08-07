// --- Context Menu Setup ---
// Create context menu items for selected text and images when the extension is installed or reloaded
chrome.runtime.onInstalled.addListener(() => {
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
  chrome.storage.local.get({ remembered: [] }, result => {
    const remembered = result.remembered;
    remembered.push(item);
    chrome.storage.local.set({ remembered });
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
    visits.push(visit);
    chrome.storage.local.set({ visits });
  });
}

// --- PDF Detection and Handling ---
function detectPDF(tabId, url) {
  if (url.match(/\.pdf($|\?)/i)) {
    chrome.tabs.sendMessage(tabId, { type: 'PROMPT_SAVE_PDF', url });
  }
}

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'PAGE_DATA') {
    // Handle standard web page data
    processPageData(message.data);
  } else if (message.type === 'PDF_DATA') {
    // Handle PDF data
    processPDFData(message.data);
  } else if (message.type === 'PDF_URL_FOR_BACKEND') {
    // Forward PDF URL to backend for processing
    sendToBackend(message.url);
  }
});

// Process and store page data
function processPageData(data) {
  // TODO: Store in SQLite via backend or extension DB
  console.log('Received page data:', data);
}

// Process and store PDF data
function processPDFData(data) {
  // TODO: Store in SQLite via backend or extension DB
  console.log('Received PDF data:', data);
}

// Send PDF URL to local backend for processing
function sendToBackend(url) {
  // TODO: Implement backend communication
  console.log('Send PDF URL to backend:', url);
}

