// pdfContent.js
// Handles PDF detection, extraction, and user prompt in content script

(function() {
  // Listen for messages from background.js
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'PROMPT_SAVE_PDF' && message.url) {
      handlePDFPrompt(message.url);
    }
  });

  // Prompt user to save PDF
  function handlePDFPrompt(pdfUrl) {
    if (confirm('A PDF document was detected. Do you want to save it for research?')) {
      extractPDF(pdfUrl);
    }
  }

  // Try to fetch and extract PDF data
  async function extractPDF(pdfUrl) {
    try {
      const response = await fetch(pdfUrl);
      if (!response.ok) throw new Error('Failed to fetch PDF');
      const blob = await response.blob();
      // Use PDF.js or similar to extract text and metadata (not included here for brevity)
      // If not possible, fallback to sending URL to backend
      // For now, just send the URL for backend processing
      chrome.runtime.sendMessage({ type: 'PDF_URL_FOR_BACKEND', url: pdfUrl });
    } catch (err) {
      console.error('PDF extraction failed:', err);
      chrome.runtime.sendMessage({ type: 'PDF_URL_FOR_BACKEND', url: pdfUrl });
    }
  }
})();
