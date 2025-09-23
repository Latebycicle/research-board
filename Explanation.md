# Research Board: Codebase Explanation

This document provides a detailed explanation of the Research Board project's codebase, architecture, and data flow.

## 1. Project Overview

Research Board is a multimodal desktop research assistant. It consists of two main components:

1.  **A FastAPI Backend (`app/`)**: A Python-based server that handles data collection, processing, storage, and retrieval. It exposes a REST API for the browser extension and future desktop application to interact with.
2.  **A Chrome Extension (`ChromeExtention/`)**: A browser extension responsible for capturing browsing activity, page content, and user interactions (like highlighting text or saving images).

The system is designed to be local-first, meaning all data is stored and processed on the user's machine, ensuring privacy.

## 2. Folder Structure

### 2.1. `app/`

This folder contains the core FastAPI backend application.

-   **Purpose**: To provide a robust API for collecting, storing, and querying research data. It handles content processing, database interactions, and business logic.
-   **Contents**: Python source code for the API server, including the main application entry point, API routes, database models, CRUD operations, and configuration.

### 2.2. `ChromeExtention/`

This folder contains the source code for the Google Chrome browser extension.

-   **Purpose**: To act as the primary data collection agent. It runs in the user's browser, tracking visited pages, capturing content, and allowing the user to save specific pieces of information.
-   **Contents**: JavaScript files for the background service worker, content scripts that run on web pages, and the HTML/JS for the popup interface. It also includes the `manifest.json` file, which defines the extension's properties and permissions.

### 2.3. `data/`

This folder is the designated location for the application's data.

-   **Purpose**: To store persistent data.
-   **Contents**: The SQLite database file (`app.db`) is stored here. This keeps the data separate from the application code.

## 3. File-by-File Explanation

### 3.1. `app/` - The FastAPI Backend

#### `app/main.py`

-   **Summary**: This is the main entry point for the FastAPI application. It initializes the FastAPI app, sets up CORS middleware to allow communication with the Chrome extension, includes the API routes defined in `api/routes.py`, and manages the application's lifecycle (startup and shutdown events).
-   **Key Logic**:
    -   `lifespan` function: An `asynccontextmanager` that ensures the database tables are created (`Base.metadata.create_all(bind=engine)`) when the application starts.
    -   **CORS Middleware**: Configured to allow requests from the Chrome extension (`chrome-extension://*`) and frontend development servers. This is crucial for security and functionality.
    -   **Router Inclusion**: It includes the `api_router` from `api/routes.py` under the `/api/v1` prefix, organizing all API endpoints.
    -   **Root and Health Endpoints**: Provides `/` and `/health` endpoints for basic API status checks.
    -   **Uvicorn Runner**: The `if __name__ == "__main__":` block allows running the server directly for development using `uvicorn`.

#### `app/api/routes.py`

-   **Summary**: This file defines all the API endpoints for the application. It handles the logic for creating, reading, and searching for pages, as well as collecting data from the Chrome extension.
-   **Key Files & Detailed Explanation**:
    -   **`POST /collect`**: This is one of the most critical endpoints.
        -   **Purpose**: To receive raw page data sent from the Chrome extension's `background.js`.
        -   **Data Flow**:
            1.  It receives a JSON payload containing the page's `html`, `url`, `title`, `meta` tags, `images`, and `text`.
            2.  It calls `ContentProcessor.process()` to clean the HTML, extract the main content, and generate a content hash.
            3.  It prepares a `PageCreate` schema object with the processed data.
            4.  It calls `crud.create_page()` to save the new page and its related data (like images) to the database.
            5.  It returns a success response with the newly created `page_id` and processed metadata.
        -   **Interaction**: This is the primary endpoint used by `background.js` to send captured web content to the backend.

    -   **`POST /pages`**: Creates a new page record. This is a more structured way to create pages compared to the `/collect` endpoint and is likely intended for use by the future desktop app or for testing.

    -   **`GET /pages/{page_id}`**: Retrieves a single page by its ID, including its images, PDF metadata, and time spent. It can optionally include the full embedding vectors.

    -   **`GET /pages`**: Lists all pages with pagination and filtering capabilities (by `page_type` or a search query `q`).


## 3.x. Semantic Search: FAISS-Powered Vector Search (2025+)

### Why the Switch to FAISS?

Earlier versions of Research Board used the `sqlite-vss` extension for vector search. However, this approach introduced complex dependency and versioning issues, especially on Apple Silicon and with Python 3.12. To resolve these problems and provide a more robust, production-ready solution, the project now uses [FAISS](https://github.com/facebookresearch/faiss) for all vector search operations.

### The New FAISS Workflow

- **Centralized Index Management:**
    - All logic for building, searching, and persisting the vector index is now in `app/vector_store.py`, which defines the `FaissIndex` class.
    - A single, global instance (`faiss_index`) is created and shared across the backend.

- **Index Storage:**
    - The FAISS index is stored on disk at `data/faiss_index.bin`.
    - This file is loaded into memory at application startup, or built from scratch if it does not exist.

- **Automated Index Initialization:**
    - In `app/main.py`, the `lifespan` function loads the FAISS index from disk if present, or calls a helper in `app/crud.py` to fetch all embeddings and build the index if not.
    - This ensures the index is always available and up-to-date when the API starts.

- **Live Index Updates:**
    - In `app/crud.py`, the `create_page` function adds new vectors to the FAISS index immediately after saving them to the database, and persists the updated index to disk.
    - This guarantees that new content is instantly searchable.

- **Semantic Search API:**
    - The `semantic_search` function in `app/crud.py` now calls `faiss_index.search()` directly, rather than running SQL queries. This makes search fast, reliable, and decoupled from the database engine.

### Benefits

- **Stability:** No more dependency hell or native extension issues.
- **Performance:** FAISS is highly optimized for large-scale vector search.
- **Simplicity:** All vector search logic is in Python, with a single, well-documented code path.
- **Portability:** The system works on any platform supported by FAISS and Python, including Apple Silicon.

**In summary:**
> The Research Board backend now uses a robust, production-grade FAISS index for all semantic search operations. The index is managed in `app/vector_store.py`, loaded or built at startup in `main.py`, kept live and up-to-date by `crud.py`, and stored on disk for persistence. This architecture is fast, reliable, and easy to maintain.

#### `app/content_processor.py`

-   **Summary**: A static class responsible for cleaning and extracting meaningful content from raw HTML.
-   **Key Files & Detailed Explanation**:
    -   **`process(html, url)` method**:
        -   **Purpose**: To take raw, messy HTML and distill it into clean, useful data for storage and analysis.
        -   **Logic & Data Flow**:
            1.  **Readability**: It first uses the `readability-lxml` library (`Document(html)`) to identify and extract the main article content from the page, stripping away ads, navigation bars, and other boilerplate. `doc.summary()` returns the cleaned HTML of the main content.
            2.  **Sanitization**: It then uses `BeautifulSoup` to further sanitize this cleaned HTML. It removes `<script>`, `<style>`, and `<iframe>` tags, and strips all `on*` event handler attributes (e.g., `onclick`) to prevent potential script injection issues when this content is rendered later.
            3.  **Text Extraction**: `soup.get_text()` is used to get a clean, plain-text representation of the main content.
            4.  **Metadata Extraction**: It parses the original HTML again with `BeautifulSoup` to find metadata like `author` and `publish_date` from `<meta>` tags.
            5.  **Hashing**: It computes a SHA256 hash of the clean text (`content_hash`). This is a smart way to enable deduplication of content, even if the URL changes slightly (e.g., with different query parameters).
        -   **Interaction**: This processor is called exclusively by the `/collect` endpoint in `api/routes.py`. It's a crucial step that ensures the data stored in the database is clean and relevant.

#### `app/crud.py`

-   **Summary**: Stands for **C**reate, **R**ead, **U**pdate, **D**elete. This file contains all the functions that directly interact with the database. It abstracts away the SQLAlchemy query logic from the API routes.
-   **Key Logic**:
    -   **`create_page`**: A transactional function that creates a `Page` record, along with its associated `Image`, `PDF`, and `PageTimeSpent` records. It also logs the creation event in the `History` table.
    -   **`semantic_search`**: Implements the vector search logic using `sqlite-vss`.
        -   **Input**: A 768-dimensional embedding vector (generated from the query text).
        -   **Process**: Executes a SQL query against the `vss_embeddings` virtual table to efficiently find the most similar embeddings using vector search.
        -   **Output**: Returns a list of (page_id, distance) tuples, which are then mapped to page info for the API response.
    -   **Vector Conversion**: The `float_list_to_bytes` and `bytes_to_float_list` functions are helpers for converting embedding vectors (lists of floats) to and from the `BLOB` format required for storage in the SQLite database.

#### `app/db/database.py`

-   **Summary**: This file handles the database connection.
-   **Key Logic**:
    -   It creates the SQLAlchemy `engine` using the `DATABASE_URL` from the configuration.
    -   It sets up a `SessionLocal` factory for creating new database sessions.
    -   The `get_db` function is a FastAPI dependency that provides a database session to the API route handlers and ensures the session is closed after the request is finished.
    -   It includes an event listener (`set_sqlite_pragma`) to enable foreign key support (`PRAGMA foreign_keys=ON`) for SQLite, which is important for data integrity but not on by default.

#### `app/models/models.py`

-   **Summary**: Defines the database schema using SQLAlchemy's ORM. Each class represents a table in the database.
-   **Key Models**:
    -   `Page`: The central table, storing information about each captured web page or PDF.
    -   `Embedding`: Stores vector embeddings associated with a page. The `embedding` column is of type `LargeBinary` to store the vector as a blob.
    -   `History`: Tracks user interactions with pages (e.g., 'opened', 'highlighted').
    -   `PageTimeSpent`: Tracks the total time a user has spent on a page.

#### `app/schemas.py`

-   **Summary**: Contains Pydantic models that define the shape of the data for API requests and responses.
-   **Purpose**: These schemas are used by FastAPI for data validation, serialization, and documentation. For example, when a request comes into the `POST /pages` endpoint, FastAPI uses the `PageCreate` schema to validate that the incoming JSON is correctly formatted.

#### `app/config.py`

-   **Summary**: Manages all application settings. It uses `pydantic-settings` to load configuration from environment variables or a `.env` file, providing a single, type-safe source of truth for configuration.

### 3.2. `ChromeExtention/` - The Browser Extension

#### `ChromeExtention/background.js`

-   **Summary**: This is the service worker for the Chrome extension. It runs in the background, independently of any web page, and manages the extension's core logic.
-   **Key Files & Detailed Explanation**:
    -   **Context Menu**: It sets up the "Remember This" right-click context menu for selected text and images. When a user clicks this, it captures the selected content (`info.selectionText` or `info.srcUrl`) and saves it to `chrome.storage.local` with a `priority: true` flag.
    -   **Browsing Activity Tracking**:
        -   **Purpose**: To track how much time a user spends on each tab.
        -   **Logic**: It uses a combination of `chrome.tabs` listeners (`onActivated`, `onUpdated`, `onRemoved`) to manage a `tabStartTimes` object. When a user switches away from a tab or closes it, `recordTimeSpent` is called to calculate the duration and save it to local storage.
    -   **Backend Communication (`sendDataToBackend`)**:
        -   **Purpose**: To send captured page data to the FastAPI backend.
        -   **Data Flow**:
            1.  It receives `PAGE_DATA` messages from `content.js`.
            2.  It makes a `fetch` request to the `http://127.0.0.1:8000/api/v1/collect` endpoint, sending the page data as a JSON payload.
            3.  If the request is successful, it receives the `page_id` from the backend and stores a minimal metadata object in `chrome.storage.local` with `synced: true`.
            4.  If the request fails (e.g., the backend server is not running), the `catch` block calls `queueForLater`, which stores the data with `synced: false` so it can be retried later.
    -   **Periodic Sync**: `setInterval` is used to periodically call `syncPendingPages`, which attempts to send any unsynced data to the backend. This ensures that data captured while the backend was offline is not lost.

#### `ChromeExtention/content.js`

-   **Summary**: This script is injected into every web page the user visits (as defined in `manifest.json`). Its primary job is to extract information from the page and send it to `background.js`.
-   **Logic**:
    -   On page load (`document_idle`), it calls `collectPageData` to gather the page's full HTML, visible text, title, meta tags, and images.
    -   It then sends this data to `background.js` using `chrome.runtime.sendMessage({ type: 'PAGE_DATA', data })`.
    -   It also listens for `mouseup` and `keyup` events to detect when a user selects text and sends this selection to the background script.

#### `ChromeExtention/popup.js` and `popup.html`

-   **Summary**: These files create the UI that appears when the user clicks the extension's icon in the Chrome toolbar.
-   **Logic**:
    -   `popup.js` fetches all the data stored in `chrome.storage.local` (`visits`).
    -   It processes this data to group visits by website, calculate total time spent, and count highlights.
    -   It then dynamically generates HTML to display a list of visited websites and recent highlights.
    -   It adds click listeners to these items, allowing the user to open the corresponding website in a new tab.

#### `ChromeExtention/manifest.json`

-   **Summary**: The manifest file is the entry point of the extension. It defines the extension's name, version, permissions, and what scripts to run.
-   **Key Permissions**:
    -   `tabs`: To get information about open tabs (URL, title).
    -   `storage`: To use `chrome.storage.local` for storing captured data.
    -   `activeTab`: To interact with the currently active tab.
    -   `contextMenus`: To create the right-click menu items.
-   **Content Scripts**: It specifies that `content.js` should be injected into all URLs (`<all_urls>`).

## 4. Overall Project Logic and Workflow

Here is the end-to-end data flow for the primary use case of capturing a web page:

1.  **User Visits a Page**: The user navigates to a new web page.
2.  **Content Script Executes**: `content.js` is automatically injected into the page. It scrapes the page's HTML, text, and metadata.
3.  **Data Sent to Background**: `content.js` sends the scraped data to `background.js` via a `PAGE_DATA` message.
4.  **Backend Sync Attempt**: `background.js` receives the data and immediately attempts to send it to the FastAPI backend's `/api/v1/collect` endpoint.
5.  **Backend Processing**:
    -   The `/collect` endpoint in `api/routes.py` receives the raw data.
    -   It passes the HTML to `ContentProcessor.process()`.
    -   The processor cleans the HTML, extracts the main content, and generates a hash.
6.  **Database Storage**:
    -   The route handler calls `crud.create_page()`.
    -   The `crud` function creates a new `Page` record in the `app.db` SQLite database, along with any associated `Image` records.
7.  **Response to Extension**: The backend responds to `background.js` with a success message and the new `page_id`.
8.  **Local Storage Update**: `background.js` updates its record in `chrome.storage.local` to mark the page as `synced: true`.
9.  **Time Tracking**: As the user stays on the page, `background.js` tracks the time. When they switch tabs or close the page, the time spent is recorded and saved to `chrome.storage.local`. This data is also periodically synced to the backend.

## 5. LLM and Embedding Model Recommendations

For your goals of local, efficient semantic search on Apple Silicon, here are my recommendations:

**Best All-in-One Embedding Model:**

-   **Model**: `all-MiniLM-L6-v2` from the `sentence-transformers` library.
-   **Why**:
    -   **Performance**: It is extremely fast and lightweight, making it perfect for running on consumer hardware.
    -   **Quality**: It offers a great balance between speed and accuracy for semantic search tasks. It's a very popular and well-regarded model for RAG.
    -   **Size**: It's small (around 90MB), so it won't consume a lot of RAM or disk space.
    -   **Compatibility**: It works excellently with `sentence-transformers`, which is easy to integrate into your Python backend.

**Implementation Strategy:**

1.  **Add `sentence-transformers` to `requirements.txt`**:
    ```
    sentence-transformers
    torch
    ```
2.  **Modify `content_processor.py` or create a new `embedding_service.py`**:
    -   When a new page is processed, after extracting the `clean_text`, pass this text to the `all-MiniLM-L6-v2` model to generate a vector embedding.
    -   The `sentence-transformers` library makes this simple:
        ```python
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')

        text_to_embed = result["text"]
        embedding_vector = model.encode(text_to_embed).tolist()
        ```
3.  **Store the Embedding**:
    -   When calling `crud.create_page`, include the generated `embedding_vector` in the `PageCreate` schema.
    -   The `crud.py` logic will then store this vector as a `BLOB` in the `embeddings` table.

**For Vector Search Performance (`sqlite-vss`):**

-   You are correct to identify `sqlite-vss` as the ideal next step. The brute-force cosine similarity in `crud.py` will become very slow as your database grows.
-   **`sqlite-vss`** is a SQLite extension that provides high-performance vector similarity search (using the FAISS library under the hood). It is perfect for your local-first architecture.
-   **Action**: Once you have a few hundred embeddings, prioritize integrating `sqlite-vss`. This will involve:
    1.  Compiling/installing the `sqlite-vss` extension.
    2.  Creating a virtual table for your embeddings (e.g., `vss_embeddings`).
    3.  Changing your `semantic_search` function to query this virtual table instead of performing manual calculations. The query now looks like:
        ```sql
        SELECT e.page_id, r.distance
        FROM vss_embeddings r
        JOIN embeddings e ON e.id = r.rowid
        WHERE vss_search(r.embedding, :query_embedding)
        LIMIT :top_k
        ```

This combination of `all-MiniLM-L6-v2` for embedding generation and `sqlite-vss` for search will give you a powerful, fast, and entirely local semantic search capability on your Mac.


---
---
---

# Research Board App: Full Detailed Report

## 1. Project Overview

The Research Board app is a next-generation research augmentation platform designed to help users (students, academics, knowledge workers) capture, organize, and retrieve web-based information, PDFs, and their own highlights as part of a RAG (Retrieval-Augmented Generation) pipeline. The tool tightly integrates a Chrome extension for data capture with a robust FastAPI backend and a normalized SQLite database, providing a foundation for advanced semantic search, time-based analytics, and personal knowledge management.

The core vision is to help users not only save and revisit online content, but also to actively engage with it (through highlights and “Remember this” actions), track their time and engagement, and later leverage AI models to retrieve, surface, and summarize what matters most from their reading history.

---

## 2. Requirements and Design Goals

### 2.1 Functional Requirements

- **Web & PDF Capture:** Scrape the content (title, author, publish date, cleaned HTML/text, images, etc.) from web pages and PDFs visited by the user, via a Chrome extension.
- **Highlights / “Remember this”:** Allow the user to select and save important snippets from any page (“Remember this”), storing these as distinct, high-signal page entries.
- **Time Tracking:** Record time spent on each unique page, accumulating across sessions and revisits.
- **History and Engagement:** Log all significant actions (opened, revisited, remember_created, time spend flush) for analytics and session reconstruction.
- **Semantic Search & Retrieval:** Prepare for embedding generation and vector search to enable “find anything I’ve read or highlighted” via AI-powered retrieval.
- **Revisit Handling:** Ensure that revisiting the same page (by canonical URL) rolls into the same base entry, accumulating time and refreshing metadata as needed, rather than creating duplicates.
- **Structured Data Model:** Support one-to-many relations (page→images, page→embeddings, page→history), and allow “remember” entries to link back to their base page.
- **Robust Error Handling:** Ensure resilience to network failures and allow for eventual consistency via local retry queues.
- **Browser Integration:** Seamless Chrome extension experience with background and content scripts, robust message passing, and context menu actions.
- **Analytics & RAG-Readiness:** Store all data necessary for future retrieval, ranking, and summarization (including highlights, engagement, and content).

### 2.2 Technical & UX Requirements

- **Cross-Platform & Efficient:** Leverage SQLite (file-based, lightweight), optimized for Apple Silicon (M1 Max, 32GB RAM).
- **Minimal Latency:** Fast, local queries and updates for smooth user experience.
- **Extensible:** Ready for vector search (sqlite-vss, FTS5), tagging, multi-user support, and importance weighting.
- **Clear Separation:** Base pages (web/pdf) vs. “remember” highlights—each a distinct document in retrieval workflows.
- **Canonicalization:** Store and query by canonical URL (normalize, strip tracking params, etc.) to avoid duplication.
- **Embeddings:** Accept and store computed embeddings (from server or extension), and prepare for future integration with Open Source LLMs.
- **Open Architecture:** Clean, well-documented codebase; all logic explained for future maintainers and collaborators.

---

## 3. Implementation Plan and Decisions

### 3.1 Data Model & Backend

Based on iterative design (see prior chat), the SQLite schema includes:

- **page**: Stores web/pdf/remember entries, with key metadata and content, a canonical URL, and a page_type field. For "remember" pages, a base_page_id links back to the main document.
- **image**: One-to-many relationship with page; stores image URLs and alt text.
- **pdf**: Metadata for PDFs (file path, size, num_pages), linked 1:1 with page.
- **embedding**: Stores vector embeddings for semantic search, linked to page.
- **page_time_spent**: Tracks accumulated seconds per page.
- **history**: Logs actions (opened, revisit, remember_created, etc.) with timestamp and session ID.
- **user**: (For future multi-user support.)

Key features:
- **Canonicalization**: A utility canonicalizes URLs (lowercase, strips fragments, drops tracking params, sorts queries) to ensure all revisits/updates are associated with the same page.
- **Upsert on Base Pages**: POST /pages for a base page (web/pdf) first canonicalizes the URL, checks for an existing entry, updates metadata and accumulates time if found, or inserts anew if not.
- **"Remember this" Pages**: Each selection is saved as a new row (page_type=remember), always referencing the base page. These are never merged or overwritten.
- **Embeddings**: Accept list[float], store as float32 BLOB; ready for future Open Source vector search integration.
- **API Endpoints**: Endpoints for creating pages, updating highlights, tracking access/time, logging history, and retrieving by canonical URL (with/without remember pages).

### 3.2 Chrome Extension

- **Content Script**: Extracts all relevant metadata, cleaned HTML (using Readability or fallback), images, and (for PDFs) basic file info. Handles selection extraction for “Remember this.”
- **Background Script**:
  - Handles tab/session state: tracks active tab, start time, accumulated time.
  - On page scrape, canonicalizes URL and syncs with backend (fetches/creates base page as needed).
  - On tab revisit, reuses existing pageId and logs revisit.
  - Handles context menu for “Remember this”: on selection, builds payload and posts to backend as a new remember page.
  - Robust retry mechanism: failed network requests are queued and retried.
  - Minimal, actionable logging for debugging.

### 3.3 Workflow & Data Flow

1. **User visits a page** → Content script scrapes metadata/content/images → Sends to background script.
2. **Background script** canonicalizes URL, checks backend for existing base page:
    - If found: updates metadata/access/time, logs revisit.
    - If not found: creates new base page, logs opened.
3. **User selects text and triggers "Remember this"** (via context menu):
    - Selection is captured, payload built (highlight, full content, url, etc.), and a new remember page is created, referencing base page.
    - History logs remember_created.
4. **Time Spent**: Tracked per page across sessions, accumulated, and flushed to backend.
5. **History**: All meaningful actions logged for analytics/retrieval.
6. **Retrieval**: (Planned) RAG pipeline can access both base and remember pages, with semantic search over embeddings.

---

## 4. Key Features and Future Extensions

- **Semantic & Hybrid Search**: Database and API are ready for integration with vector search (sqlite-vss), FTS5, or hybrid approaches.
- **Importance Ranking**: “Remember this” pages will be weighted higher in retrieval/AI generation.
- **Tagging, Multi-user, and Sharing**: DB schema supports future expansion for collaborative research.
- **Open-Source Compatibility**: Designed for local models (MiniLM, BGE, E5, etc.) on Apple Silicon.

---

## 5. Summary

The Research Board app is a full-stack, extensible platform for capturing, enriching, and retrieving personal research data from the browser. Through careful schema design, canonicalization, robust Chrome extension integration, and a RAG-ready backend, it lays the foundation for a knowledge workflow that is AI-first, user-centric, and future-proof.
