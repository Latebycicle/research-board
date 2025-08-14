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
  // Check for duplicate page data before processing (skip on reload/revisit)
  if (isPageDataDuplicate(data.url)) {
    console.log('Skipping duplicate page data extraction for URL:', data.url);
    return;
  }
  
  // Add page data type for consistency
  data.type = 'page_data';
  
  // Store page data separately or with visits (depending on your preference)
  chrome.storage.local.get({ visits: [] }, result => {
    const visits = result.visits;
    visits.push(data);
    chrome.storage.local.set({ visits });
    console.log('Processing new page data:', data.url);
    console.log('Recived Page Data', data);
  });
}

// Process and store PDF data
function processPDFData(data) {
  // Check for duplicate PDF data before processing
  if (isPageDataDuplicate(data.url)) {
    console.log('Skipping duplicate PDF data extraction for URL:', data.url);
    return;
  }
  
  // Add PDF data type for consistency
  data.type = 'pdf_data';
  
  // Store PDF data with visits
  chrome.storage.local.get({ visits: [] }, result => {
    const visits = result.visits;
    visits.push(data);
    chrome.storage.local.set({ visits });
    console.log('Processing new PDF data:', data.url);
  });
}

// Send PDF URL to local backend for processing
function sendToBackend(url) {
  // TODO: Implement backend communication
  console.log('Send PDF URL to backend:', url);
}

