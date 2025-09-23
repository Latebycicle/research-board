import faiss
import numpy as np
from typing import List, Tuple, Dict, Optional

class FaissIndex:
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(dimension)
        self.id_map: Dict[int, int] = {}  # faiss_id -> page_id
        self.next_faiss_id = 0

    def build_from_db(self, db_session):
        """Build the FAISS index from all embeddings in the database."""
        from app.models.models import Embedding
        embeddings = db_session.query(Embedding.id, Embedding.page_id, Embedding.embedding).all()
        if not embeddings:
            return
        vectors = []
        for emb_id, page_id, emb_blob in embeddings:
            vec = np.frombuffer(emb_blob, dtype=np.float32)
            if vec.shape[0] != self.dimension:
                continue
            vectors.append(vec)
            self.id_map[self.next_faiss_id] = page_id
            self.next_faiss_id += 1
        if vectors:
            arr = np.stack(vectors).astype(np.float32)
            self.index.add(arr)

    def add(self, page_id: int, vector: List[float]):
        """Add a new vector to the index."""
        vec = np.array(vector, dtype=np.float32).reshape(1, -1)
        self.index.add(vec)
        self.id_map[self.next_faiss_id] = page_id
        self.next_faiss_id += 1

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        """Search for the top_k most similar vectors. Returns (page_id, score) tuples."""
        q = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        D, I = self.index.search(q, top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            if idx == -1:
                continue
            page_id = self.id_map.get(idx)
            if page_id is not None:
                results.append((page_id, float(dist)))
        return results

    def save_index(self):
        """Persist the FAISS index to disk."""
        faiss.write_index(self.index, self.index_path)

    def load_index(self):
        """Load the FAISS index from disk."""
        self.index = faiss.read_index(self.index_path)

# Global shared FAISS index instance
faiss_index = FaissIndex(dimension=768, index_path='data/faiss_index.bin')
