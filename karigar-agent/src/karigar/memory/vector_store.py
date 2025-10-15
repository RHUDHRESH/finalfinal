import chromadb
from chromadb.config import Settings

class VectorMemory:
    def __init__(self, persist_directory="./chroma_data"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.suppliers = self.client.get_or_create_collection("suppliers")
        self.products = self.client.get_or_create_collection("products")
    
    def store_supplier(self, supplier_id, name, materials, pricing, rating):
        doc = f"{name} supplies {materials} at {pricing}. Rating: {rating}"
        self.suppliers.add(
            documents=[doc],
            ids=[supplier_id],
            metadatas=[{"name": name, "rating": rating}]
        )
    
    def search_suppliers(self, query, n_results=5):
        results = self.suppliers.query(
            query_texts=[query],
            n_results=n_results
        )
        return results