// content.js
// Extracts data from standard web pages and sends it to the background script

(function() {
  // Helper to get all meta tags as an object
  function getMetaTags() {
    const metas = document.getElementsByTagName('meta');
    const metaObj = {};
    for (let meta of metas) {
      if (meta.name || meta.getAttribute('property')) {
        metaObj[meta.name || meta.getAttribute('property')] = meta.content;
      }
    }
    return metaObj;
  }

  // Helper to get all images with alt text
  function getImages() {
    return Array.from(document.images).map(img => ({
      src: img.src,
      alt: img.alt || ''
    }));
  }

  // Extract visible text content
  function getVisibleText() {
    return document.body.innerText || '';
  }

  // Package all data
  function collectPageData() {
    return {
      html: document.documentElement.outerHTML,
      text: getVisibleText(),
      title: document.title,
      meta: getMetaTags(),
      images: getImages(),
      url: window.location.href,
      accessedAt: new Date().toISOString()
    };
  }

  // Send data to background script
  function sendData() {
    const data = collectPageData();
    chrome.runtime.sendMessage({ type: 'PAGE_DATA', data });
  }

  // Only run on standard web pages (not PDFs)
  if (!window.location.href.match(/\.pdf($|\?)/i) && !document.contentType?.includes('pdf')) {
    sendData();
  }
  
  // --- Detect Text Selection ---
  function handleSelection() {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      const selectedText = selection.toString();
      chrome.runtime.sendMessage({
        type: 'USER_SELECTION',
        data: {
          text: selectedText,
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      });
    }
  }
  
  // Listen for mouseup (end of selection) and keyup (Shift+Arrow selection)
  document.addEventListener('mouseup', handleSelection);
  document.addEventListener('keyup', event => {
    // Only fire on selection keys
    if ([16, 17, 18, 37, 38, 39, 40].includes(event.keyCode)) {
      handleSelection();
    }
  });
  
  // --- Detect Right-Click on Images ---
  document.addEventListener('contextmenu', function(event) {
    const target = event.target;
    if (target && target.tagName === 'IMG') {
      chrome.runtime.sendMessage({
        type: 'USER_IMAGE_RIGHTCLICK',
        data: {
          imageUrl: target.src,
          alt: target.alt || '',
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      });
    }
  });
  
  // --- (Optional) Programmatic Injection Example ---
  // This code is for reference if you want to inject this script from the extension programmatically.
  // chrome.scripting.executeScript({
  //   target: {tabId: <TAB_ID>},
  //   files: ['content.js']
  // });
  
  // --- Existing Extraction Logic (if needed) ---
  // (Retain or remove the following if you want to keep page extraction features)
  
})();
