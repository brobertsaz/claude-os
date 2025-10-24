"""
Quick test script to debug vector query issue.
Run with: docker exec code-forge-app python3 /app/test_vector_query.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    print("=" * 60)
    print("PostgreSQL Vector Query Test")
    print("=" * 60)
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "host.docker.internal"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "codeforge"),
        user=os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get a sample embedding from the database
            print("\n📊 Getting sample embedding from database...")
            cur.execute("SELECT embedding FROM documents WHERE kb_id = 2 LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("❌ No documents found in kb_id=2")
                return
            
            sample_embedding = result['embedding']
            print(f"✅ Got sample embedding")
            print(f"   Type: {type(sample_embedding)}")
            print(f"   Length: {len(sample_embedding) if hasattr(sample_embedding, '__len__') else 'N/A'}")
            
            # Test 1: Query using the sample embedding directly (as returned from DB)
            print("\n🧪 Test 1: Query using embedding AS-IS from database")
            try:
                cur.execute(
                    """
                    SELECT content, 1 - (embedding <=> %s) as similarity
                    FROM documents
                    WHERE kb_id = 2
                    ORDER BY embedding <=> %s
                    LIMIT 5
                    """,
                    (sample_embedding, sample_embedding)
                )
                results = cur.fetchall()
                print(f"   ✅ Results: {len(results)}")
                if results:
                    print(f"   Top similarity: {results[0]['similarity']:.4f}")
                    print(f"   Content preview: {results[0]['content'][:80]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 2: Convert to list and back to string
            print("\n🧪 Test 2: Query using string-formatted embedding with ::vector cast")
            try:
                embedding_list = list(sample_embedding)
                embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"
                print(f"   Embedding string (first 100 chars): {embedding_str[:100]}...")
                
                cur.execute(
                    """
                    SELECT content, 1 - (embedding <=> %s::vector) as similarity
                    FROM documents
                    WHERE kb_id = 2
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5
                    """,
                    (embedding_str, embedding_str)
                )
                results = cur.fetchall()
                print(f"   Results: {len(results)}")
                if results:
                    print(f"   ✅ Top similarity: {results[0]['similarity']:.4f}")
                else:
                    print("   ❌ NO RESULTS - This is the problem!")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 3: Try without ::vector cast but with string
            print("\n🧪 Test 3: Query using string WITHOUT ::vector cast")
            try:
                cur.execute(
                    """
                    SELECT content, 1 - (embedding <=> %s) as similarity
                    FROM documents
                    WHERE kb_id = 2
                    ORDER BY embedding <=> %s
                    LIMIT 5
                    """,
                    (embedding_str, embedding_str)
                )
                results = cur.fetchall()
                print(f"   Results: {len(results)}")
                if results:
                    print(f"   ✅ Top similarity: {results[0]['similarity']:.4f}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
    finally:
        conn.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

