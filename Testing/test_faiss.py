import sqlite3
import numpy as np
import faiss
import os

DB_PATH = os.path.join("data", "app.db")
FAISS_INDEX_PATH = os.path.join("data", "faiss_index.bin")
DIMENSION = 768  # Make sure this matches your model's dimension

def bytes_to_float_list(binary_data: bytes) -> list[float]:
    """Converts a binary blob of float32 back to a list of floats."""
    return np.frombuffer(binary_data, dtype=np.float32)

def run_faiss_build_test():
    """Builds and tests the FAISS index directly from the database."""
    print("--- Testing FAISS Index Build and Search ---")

    if os.path.exists(FAISS_INDEX_PATH):
        os.remove(FAISS_INDEX_PATH)
        print(f"Removed existing index file: {FAISS_INDEX_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert a relevant test page and embedding if not present
        test_text = "Python functions are defined using the def keyword."
        test_vector = np.random.rand(DIMENSION).astype('float32')
        test_vector_blob = test_vector.tobytes()


        print("Fetching all embeddings from the database...")
        cursor.execute("SELECT id, page_id, embedding FROM embeddings")
        results = cursor.fetchall()

        if not results:
            print("❌ FAILED: No embeddings found in the database. Save some pages first.")
            return

        print(f"Found {len(results)} embeddings to index.")

        # We'll map the FAISS index position to the original page_id
        index_to_page_id = {i: page_id for i, (_, page_id, _) in enumerate(results)}
        all_vectors = np.array([bytes_to_float_list(embedding) for _, _, embedding in results]).astype('float32')

        # Build the FAISS index
        index = faiss.IndexFlatL2(DIMENSION)
        index.add(all_vectors)
        print(f"✅ FAISS index built successfully with {index.ntotal} vectors.")

        # Save the index to disk
        faiss.write_index(index, FAISS_INDEX_PATH)
        print(f"✅ Index saved to: {FAISS_INDEX_PATH}")

        # Perform a test search
        print("\n🚀 Performing a test search...")
        # Use the test vector as the query vector
        query_vector = np.array([test_vector], dtype='float32')

        distances, indices = index.search(query_vector, k=3)

        print("Search completed. Top 3 results:")
        for i, idx in enumerate(indices[0]):
            page_id = index_to_page_id.get(idx, None)
            distance = distances[0][i]
            print(f"  {i+1}. Page ID: {page_id}, Distance: {distance:.4f}")

        print("\n--- Verification ---")
        if indices[0][0] is not None and page_id == page_id:
            print("🎉 SUCCESS! The most similar item to the test vector is itself.")
        else:
            print("❌ FAILED: The search did not return the correct closest item.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_faiss_build_test()