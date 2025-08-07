# GitHub Copilot Instructions

## Project Overview

**Repository Name:** research-board

**Description:**  
A multimodal desktop research assistant designed to help users collect, organize, and analyze browsing activity using AI-powered summarization, semantic search, and explainable recommendations. Built for students and researchers, research-board integrates browser data, local storage, and advanced LLMs to provide insightful, transparent, and cognitively-aware research support—all running locally on macOS.

---

## Context

- **Developer:** 4th year Computer Science student at Christ University, Bangalore
- **Specialization:** AI/ML (major), Psychology (minor)
- **Primary OS:** macOS (Apple Silicon, M1 Max, 32GB RAM)
- **Preferred IDE:** VSCode Insiders

---

## Coding & Design Guidelines

1. **Platform:**  
   - All core features must run locally on macOS.  
   - Use cross-platform technologies (Electron, Tauri, or similar) for the desktop app, but optimize and test on Apple Silicon.

2. **Tech Stack:**  
   - **Frontend:** Vue.js (preferably with Vuetify or Quasar for Material Design)
   - **Desktop:** Electron or Tauri
   - **Backend:** Node.js/Express or Python/Flask (choose based on best local LLM support and developer ergonomics)
   - **Database:** SQLite (local, file-based)
   - **Browser Extension:** Chrome (MV3), but ensure the data pipeline is modular for future Firefox/Safari support.
   - **AI/ML:** Use open-source LLMs (Llama.cpp, Mistral, or Hugging Face Transformers) for summarization, QA, and semantic search.  
   - **Image/Multimodal:** Integrate BLIP-2 or CLIP for image understanding if possible.

3. **Features:**
   - **Data Collection:** Capture URLs, time spent, selected content (text/images), and save to local database.
   - **Summarization & Search:** Provide concise summaries, semantic search, and chat over collected data.
   - **Explainable AI:** Outputs must include references to sources (citations) and, where possible, chain-of-thought explanations.
   - **Cognitive Tools:** Where relevant, include features inspired by cognitive science and psychology (reflection prompts, metacognition aids).

4. **Best Practices:**
   - Write clear, well-documented, modular code.
   - Use meaningful commit messages.
   - Prioritize privacy: all user data should remain local unless explicitly exported.
   - Make UX accessible and visually clean (Material 3 preferred).
   - Write tests for all core modules.

---

## Copilot Usage

- **Code Suggestions:**  
  - Prefer idiomatic, modern JavaScript/TypeScript (or Python for backend if chosen).
  - Generate code that works on Apple Silicon/Mac hardware.
  - Suggest clear function/variable names and thorough docstrings/comments.
  - When generating prompts for LLMs, ensure outputs include citations and explanatory steps if possible.

- **Documentation:**  
  - When writing or updating documentation, explain AI/ML features in simple terms.
  - Include setup steps for Mac users (Apple Silicon specifics if needed).
  - Provide clear instructions for building, running, and testing the app locally.

- **Issue/PR Templates:**  
  - Use clear, concise language in issue and PR templates.
  - Encourage users to specify platform (macOS, Apple Silicon) when reporting bugs.

---

## References

- [Chrome Extension Docs](https://developer.chrome.com/docs/extensions/mv3/)
- [Vue.js](https://vuejs.org/)
- [Vuetify](https://vuetifyjs.com/)
- [Quasar](https://quasar.dev/)
- [Electron](https://www.electronjs.org/)
- [Tauri](https://tauri.app/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [Llama.cpp](https://github.com/ggerganov/llama.cpp)
- [BLIP-2](https://huggingface.co/docs/transformers/model_doc/blip-2)
- [Material 3 Guidelines](https://m3.material.io/)

---

## Additional Notes

- If unsure, prefer solutions that maximize local privacy, explainability, and cognitive support.
- Always ensure compatibility with macOS and Apple Silicon.
- Prioritize features that help users understand and reflect on their research process.

---