#!/usr/bin/env python3
"""
Script to inspect PGVectorStore's table schema.
Creates a test table and inspects its structure.
"""

from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine, inspect, text
import sys

def main():
    # Connection string (use host.docker.internal when running in Docker)
    connection_string = "postgresql://iamanmp@host.docker.internal:5432/codeforge"

    print("=" * 80)
    print("CREATING TEST PGVECTORSTORE TABLE")
    print("=" * 80)

    try:
        # Create a test PGVectorStore
        vector_store = PGVectorStore.from_params(
            connection_string=connection_string,
            table_name="test_schema_inspection",
            embed_dim=768,  # nomic-embed-text dimension
            perform_setup=True,  # This will create the table
            hybrid_search=False,  # Start simple
            hnsw_kwargs=None  # No HNSW for now
        )

        print("\n✓ PGVectorStore created successfully")

        # Inspect the created table
        engine = create_engine(connection_string)
        inspector = inspect(engine)

        print("\n" + "=" * 80)
        print("TABLE SCHEMA: test_schema_inspection")
        print("=" * 80)

        # Get columns
        columns = inspector.get_columns("test_schema_inspection", schema="public")
        print("\nCOLUMNS:")
        for col in columns:
            col_type = str(col['type'])
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col.get('default', 'N/A')}" if col.get('default') else ""
            print(f"  - {col['name']:<20} {col_type:<30} {nullable}{default}")

        # Get indexes
        indexes = inspector.get_indexes("test_schema_inspection", schema="public")
        print("\nINDEXES:")
        if indexes:
            for idx in indexes:
                unique = "UNIQUE" if idx['unique'] else "NON-UNIQUE"
                print(f"  - {idx['name']:<40} {unique:<12} columns={idx['column_names']}")
        else:
            print("  (No indexes found)")

        # Get primary key
        pk = inspector.get_pk_constraint("test_schema_inspection", schema="public")
        print("\nPRIMARY KEY:")
        if pk and pk.get('constrained_columns'):
            print(f"  - {pk['name']}: {pk['constrained_columns']}")
        else:
            print("  (No primary key)")

        # Get foreign keys
        fks = inspector.get_foreign_keys("test_schema_inspection", schema="public")
        print("\nFOREIGN KEYS:")
        if fks:
            for fk in fks:
                print(f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        else:
            print("  (No foreign keys)")

        # Show sample CREATE TABLE statement
        print("\n" + "=" * 80)
        print("EQUIVALENT CREATE TABLE STATEMENT")
        print("=" * 80)
        print("\nCREATE TABLE test_schema_inspection (")
        for i, col in enumerate(columns):
            col_type = str(col['type'])
            nullable = "" if col['nullable'] else " NOT NULL"
            default = f" DEFAULT {col.get('default')}" if col.get('default') else ""
            comma = "," if i < len(columns) - 1 else ""
            print(f"    {col['name']} {col_type}{nullable}{default}{comma}")
        print(");")

        print("\n" + "=" * 80)
        print("MULTI-TENANCY STRATEGY")
        print("=" * 80)
        print("""
PGVectorStore supports multi-tenancy through:

Option 1: Separate tables per KB
  - table_name = f"data_{kb_name}"
  - Pros: Clean isolation, easy to delete entire KB
  - Cons: Many tables, harder to query across KBs

Option 2: Single table with metadata filtering
  - Store kb_id in metadata JSONB column
  - Filter queries with: metadata_->>'kb_id' = '1'
  - Pros: Single table, easier cross-KB queries
  - Cons: Requires careful filtering, harder to delete KB

Option 3: Hybrid - One table per KB type
  - data_generic, data_code, data_documentation, data_agent_os
  - Use metadata for kb_id within each type
  - Pros: Balance of isolation and manageability
  - Cons: More complex logic

RECOMMENDATION: Option 1 (separate tables) for simplicity and clean isolation.
""")

        # Clean up test table
        print("\n" + "=" * 80)
        print("CLEANUP")
        print("=" * 80)

        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_schema_inspection CASCADE"))
            conn.commit()

        print("\n✓ Test table dropped")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

