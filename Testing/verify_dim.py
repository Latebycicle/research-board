import sqlite3
import numpy as np
import os

DB_PATH = os.path.join("data", "app.db")

def verify_stored_dimension():
    """Connects to the DB and verifies the dimension of the first stored embedding."""
    print(f"--- Verifying Embedding Dimension in '{DB_PATH}' ---")

    if not os.path.exists(DB_PATH):
        print(f"❌ FAILED: Database file not found at '{DB_PATH}'.")
        return

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch the binary data of the first embedding
        cursor.execute("SELECT embedding FROM embeddings LIMIT 1;")
        result = cursor.fetchone()

        if result:
            embedding_blob = result[0]
            
            # Convert the binary blob back into a numpy array of float32
            float_array = np.frombuffer(embedding_blob, dtype=np.float32)
            dimension = len(float_array)
            
            print(f"\n✅ Success! The stored embedding has a dimension of: {dimension}")
            
            if dimension == 768:
                print("This matches the required dimension for your VSS index.")
            else:
                print(f"⚠️ WARNING: This does NOT match the expected 768 dimension.")

        else:
            print("Could not find any embeddings in the database to verify.")

    except Exception as e:
        print(f"❌ FAILED: An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    verify_stored_dimension()