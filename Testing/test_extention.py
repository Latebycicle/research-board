import sqlite3
import os
import numpy as np

DB_PATH = os.path.join("data", "app.db")
VECTOR_PATH = os.path.join(os.getcwd(), "vector0.dylib")
VSS_PATH = os.path.join(os.getcwd(), "vss0.dylib")

print("--- Independent SQLite Extension Test ---")

try:
    # 1. Connect to the database
    conn = sqlite3.connect(DB_PATH)
    print(f"✅ Connected to database: {DB_PATH}")

    # 2. Enable and load extensions
    conn.enable_load_extension(True)
    conn.load_extension(VECTOR_PATH)
    print(f"✅ Loaded extension: {VECTOR_PATH}")
    conn.load_extension(VSS_PATH)
    print(f"✅ Loaded extension: {VSS_PATH}")

    # 3. Create a dummy vector for the test query
    dummy_vector = np.random.rand(768).astype(np.float32).tobytes()
    
    # 4. Execute the vss_search function
    print("🚀 Attempting to run a vss_search query...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vss_search(?, 1)", (dummy_vector,))
    
    # If the above line runs without error, the test is a success
    print("\n🎉 SUCCESS! The vss_search function was found and executed correctly.")
    print("This proves your .dylib files are working. The issue is with the app's connection handling.")

except sqlite3.Error as e:
    print(f"\n❌ FAILED: An error occurred: {e}")
    print("If this failed, check that the .dylib files are in your project root and are not corrupted.")
finally:
    if 'conn' in locals():
        conn.close()
