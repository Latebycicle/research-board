import httpx
import pprint

API_SEARCH_URL = "http://127.0.0.1:8000/api/v1/search/semantic"

def run_search_test():
    """Tests the refactored FAISS-powered semantic search endpoint."""
    print("\n--- Testing Live FAISS-Powered Semantic Search API ---")
    
    # Define a search query related to one of your saved pages.
    search_query = "How do you define a function in Python?"
    
    payload = {
        "query": search_query,
        "top_k": 3
    }
    
    try:
        print(f"Sending query to backend: '{search_query}'")
        
        response = httpx.post(API_SEARCH_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        results = response.json()
        
        print("\n--- ✅ Search Results Received ---")
        pprint.pprint(results)
        
        print("\n--- Verification ---")
        if results:
            print("Test PASSED: The API returned results from the FAISS index.")
            print("Manually verify if the page titles above are relevant to the query.")
        else:
            print("Test WARNING: The search returned no results. Did your server build the index at startup?")
            
    except httpx.HTTPStatusError as e:
        print(f"❌ FAILED: API returned an error: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ FAILED: Error calling the search API: {e}")
        print("--- Is your FastAPI server running? ---")

if __name__ == "__main__":
    run_search_test()