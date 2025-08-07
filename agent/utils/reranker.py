from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

class LocalReranker:
    def __init__(self, model_name: str, top_k: int = 10):
        self.model = CrossEncoder(model_name)
        self.top_k = top_k
    
    def rerank(self, documents, query):
        if not documents:
            return documents
        
        scores = []
        for doc in documents:
            text = doc.page_content[:512]
            score = self.model.predict([(query, text)])[0]
            scores.append((score, doc))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scores[:self.top_k]]

def get_reranker(top_k=10):
    return LocalReranker(MODEL_NAME, top_k)
