import httpx
import numpy as np

OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embeddings"
MODEL_NAME = "embeddinggemma:latest"

def get_embedding(text: str) -> np.ndarray:
    """Gets an embedding from Ollama and returns it as a numpy array."""
    try:
        response = httpx.post(OLLAMA_EMBED_URL, json={"model": MODEL_NAME, "prompt": text})
        response.raise_for_status()
        # The embedding is in the 'embedding' key of the JSON response
        return np.array(response.json()["embedding"])
    except httpx.RequestError as e:
        print(f"Error calling Ollama: {e}")
        return np.array([])

def cosine_similarity(v1, v2):
    """Calculates cosine similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

def run_test():
    print("--- Testing Embedding Integrity ---")


    # 1. Define sentences
    sentence1 = "A cat is resting on the warm rug."
    sentence2 = "The sleepy feline was lying on the mat."
    sentence3 = "NASA's big, shiny, new rocket launched towards the stars."

    # 2. Get embeddings
    print("Generating embeddings...")
    vec1 = get_embedding(sentence1)
    vec2 = get_embedding(sentence2)
    vec3 = get_embedding(sentence3)

    if vec1.size == 0 or vec2.size == 0 or vec3.size == 0:
        print("Failed to generate embeddings. Is Ollama running with 'embedding-gemma'?")
        return

    print("Embeddings generated successfully.")

    # 3. Calculate and print similarity scores
    similarity_1_2 = cosine_similarity(vec1, vec2)
    similarity_1_3 = cosine_similarity(vec1, vec3)

    print(f"\nSimilarity between 'cat' sentences: {similarity_1_2:.4f}")
    print(f"Similarity between 'cat' and 'rocket' sentences: {similarity_1_3:.4f}")

    # 4. Check results
    print("\n--- Verification ---")
    if similarity_1_2 > 0.7:
        print("✅ PASSED: Similar sentences have high similarity.")
    else:
        print("❌ FAILED: Similar sentences have low similarity.")

    if similarity_1_3 < 0.5:
        print("✅ PASSED: Dissimilar sentences have low similarity.")
    else:
        print("❌ FAILED: Dissimilar sentences have high similarity.")

if __name__ == "__main__":
    run_test()