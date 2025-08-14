// popup.js
// Fetches and displays saved websites from chrome.storage.local

document.addEventListener('DOMContentLoaded', function() {
  console.log('Popup loaded, initializing...');
  
  const message = document.getElementById('welcome-message');
  const websiteList = document.getElementById('website-list');
  const itemCount = document.getElementById('item-count');
  
  if (message) {
    message.textContent = 'Research Board';
  }
  
  // Fetch and display saved websites
  loadSavedWebsites();
  
  // Listen for storage changes to update the list in real-time
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.visits) {
      console.log('Storage changed, refreshing website list...');
      loadSavedWebsites();
    }
  });
});

// Fetch all saved data from chrome.storage.local and display websites
function loadSavedWebsites() {
  console.log('Loading saved websites from storage...');
  
  chrome.storage.local.get({ visits: [] }, function(result) {
    console.log('Raw storage data:', result);
    
    const visits = result.visits || [];
    console.log(`Found ${visits.length} total items in storage`);
    
    // Group and process the data
    const websiteData = processWebsiteData(visits);
    console.log('Processed website data:', websiteData);
    
    // Extract highlights data
    const highlightsData = extractHighlights(visits);
    console.log('Extracted highlights:', highlightsData);
    
    // Display the websites and highlights
    displayWebsites(websiteData);
    displayHighlights(highlightsData);
    
    // Update item count
    updateItemCount(visits.length, websiteData.length, highlightsData.length);
  });
}

// Process and group website data from storage
function processWebsiteData(visits) {
  const websiteMap = new Map();
  
  visits.forEach(item => {
    if (!item.url) return;
    
    try {
      const url = new URL(item.url);
      const domain = url.hostname;
      const key = domain;
      
      if (!websiteMap.has(key)) {
        websiteMap.set(key, {
          domain: domain,
          title: item.title || domain,
          url: item.url,
          visitCount: 0,
          totalTimeMs: 0,
          highlights: 0,
          lastVisit: null,
          types: new Set()
        });
      }
      
      const website = websiteMap.get(key);
      
      // Update based on item type
      if (item.type === 'visit') {
        website.visitCount += item.visitCount || 1;
        website.totalTimeMs += item.timeSpentMs || 0;
        website.lastVisit = item.lastVisit || item.timestamp;
      } else if (item.type === 'highlight' && item.priority) {
        website.highlights += 1;
      } else if (item.type === 'page_data' && item.title) {
        website.title = item.title; // Use page title if available
      }
      
      website.types.add(item.type || 'unknown');
      
    } catch (error) {
      console.error('Error processing URL:', item.url, error);
    }
  });
  
  // Convert map to array and sort by last visit
  return Array.from(websiteMap.values())
    .sort((a, b) => new Date(b.lastVisit || 0) - new Date(a.lastVisit || 0));
}

// Display websites in the popup
function displayWebsites(websites) {
  const websiteList = document.getElementById('website-list');
  
  if (!websites || websites.length === 0) {
    websiteList.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No websites saved yet</div>';
    return;
  }
  
  console.log(`Displaying ${websites.length} websites`);
  
  websiteList.innerHTML = websites.map(site => `
    <div class="website-item" data-url="${site.url}">
      <div class="website-title">${site.title}</div>
      <div class="website-url">${site.domain}</div>
      <div style="font-size: 11px; color: #999; margin-top: 2px;">
        ${site.visitCount > 0 ? `${site.visitCount} visits` : ''}
        ${site.highlights > 0 ? ` • ${site.highlights} highlights` : ''}
        ${site.totalTimeMs > 0 ? ` • ${formatTime(site.totalTimeMs)}` : ''}
      </div>
    </div>
  `).join('');
  
  // Add click listeners to website items
  websiteList.querySelectorAll('.website-item').forEach(item => {
    item.addEventListener('click', function() {
      const url = this.getAttribute('data-url');
      console.log('Clicked website:', url);
      // Open the website in a new tab
      chrome.tabs.create({ url: url });
    });
  });
}

// Update the item count display
function updateItemCount(totalItems, uniqueWebsites, highlightsCount) {
  const itemCount = document.getElementById('item-count');
  if (itemCount) {
    itemCount.textContent = `${uniqueWebsites} websites • ${highlightsCount} highlights • ${totalItems} total items`;
  }
}

// Extract and process highlights data
function extractHighlights(visits) {
  console.log('Extracting highlights from visits data...');
  
  const highlights = visits
    .filter(item => item.type === 'highlight' && item.priority === true)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)) // Sort by most recent
    .map(item => {
      try {
        const url = new URL(item.url);
        return {
          ...item,
          domain: url.hostname,
          displayContent: truncateText(item.content, 100)
        };
      } catch (error) {
        console.error('Error processing highlight URL:', item.url, error);
        return {
          ...item,
          domain: 'Unknown',
          displayContent: truncateText(item.content, 100)
        };
      }
    });
    
  console.log(`Found ${highlights.length} highlights`);
  return highlights;
}

// Display highlights in the scrollable section
function displayHighlights(highlights) {
  const highlightsContainer = document.getElementById('highlights-container');
  const highlightsTitle = document.getElementById('highlights-title');
  
  if (!highlights || highlights.length === 0) {
    highlightsContainer.innerHTML = '<div class="no-highlights">No highlights saved yet</div>';
    highlightsTitle.textContent = 'Recent Highlights (0)';
    return;
  }
  
  console.log(`Displaying ${highlights.length} highlights`);
  highlightsTitle.textContent = `Recent Highlights (${highlights.length})`;
  
  highlightsContainer.innerHTML = highlights.map(highlight => `
    <div class="highlight-item" data-url="${highlight.url}">
      <div class="highlight-content">${highlight.displayContent}</div>
      <div class="highlight-meta">
        <span class="highlight-type">${highlight.originalType || 'content'}</span>
        <span>${highlight.domain}</span> • 
        <span>${formatDate(highlight.timestamp)}</span>
      </div>
    </div>
  `).join('');
  
  // Add click listeners to highlight items
  highlightsContainer.querySelectorAll('.highlight-item').forEach(item => {
    item.addEventListener('click', function() {
      const url = this.getAttribute('data-url');
      console.log('Clicked highlight from:', url);
      // Open the website where this highlight came from
      chrome.tabs.create({ url: url });
    });
  });
}

// Utility function to truncate text
function truncateText(text, maxLength) {
  if (!text) return 'No content';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Format date for display
function formatDate(timestamp) {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  } catch (error) {
    return 'Unknown date';
  }
}

// Format time duration for display
function formatTime(milliseconds) {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m`;
  } else {
    return `${seconds}s`;
  }
}
