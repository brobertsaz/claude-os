"""
Test what Ollama returns for embeddings.
Run with: docker exec code-forge-app python3 /workspace/app/test_ollama_embedding.py
"""

import os
from llama_index.embeddings.ollama import OllamaEmbedding

def main():
    print("=" * 60)
    print("Ollama Embedding Test")
    print("=" * 60)
    
    # Initialize Ollama embeddings
    embed_model = OllamaEmbedding(
        model_name="nomic-embed-text",
        base_url="http://ollama:11434"
    )
    
    # Generate embedding
    print("\n📊 Generating embedding for test query...")
    query = "how do the basic appointments work in pistn?"
    embedding = embed_model.get_text_embedding(query)
    
    print(f"\n✅ Embedding generated!")
    print(f"   Type: {type(embedding)}")
    print(f"   Length: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    print(f"   Data types of first 5: {[type(x) for x in embedding[:5]]}")
    
    # Test string conversion
    print("\n🧪 Testing string conversion...")
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    print(f"   String (first 100 chars): {embedding_str[:100]}")
    print(f"   String (last 50 chars): {embedding_str[-50:]}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

