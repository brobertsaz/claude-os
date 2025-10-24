#!/usr/bin/env python3
"""
Migration script to convert from custom schema to PGVectorStore-compatible schema.

This script:
1. Backs up existing data
2. Creates new PGVectorStore-compatible tables
3. Migrates data from old schema to new schema
4. Verifies data integrity
5. Optionally drops old tables

Usage:
    python scripts/migrate_to_pgvector.py [--dry-run] [--keep-old]
"""

import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import json
from datetime import datetime
import uuid

# Connection parameters
import os
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'host.docker.internal'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'codeforge'),
    'user': os.getenv('POSTGRES_USER', 'iamanmp'),
    'password': os.getenv('POSTGRES_PASSWORD', '')
}

class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass

def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise MigrationError(f"Failed to connect to database: {e}")

def backup_data(conn):
    """Create backup of existing data"""
    print("\n" + "=" * 80)
    print("STEP 1: BACKING UP EXISTING DATA")
    print("=" * 80)

    backup_file = f"backup_codeforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count existing data
            cur.execute("SELECT COUNT(*) as count FROM knowledge_bases")
            kb_count = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM documents")
            doc_count = cur.fetchone()['count']

            print(f"\n✓ Found {kb_count} knowledge bases")
            print(f"✓ Found {doc_count} documents")

            # Export to SQL file
            import subprocess
            result = subprocess.run(
                ['pg_dump', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database'],
                 '-t', 'knowledge_bases', '-t', 'documents', '-f', backup_file],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"\n✓ Backup created: {backup_file}")
                return backup_file
            else:
                print(f"\n⚠ Warning: Could not create SQL backup: {result.stderr}")
                print("  Continuing with in-memory backup...")
                return None

    except Exception as e:
        print(f"\n⚠ Warning: Backup failed: {e}")
        print("  Continuing anyway...")
        return None

def get_existing_kbs(conn):
    """Get all existing knowledge bases"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, name, kb_type, description, metadata, created_at
            FROM knowledge_bases
            ORDER BY id
        """)
        return cur.fetchall()

def sanitize_table_name(kb_name):
    """Convert KB name to valid table name"""
    # Convert to lowercase, replace spaces/special chars with underscore
    table_name = kb_name.lower()
    table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
    # Remove consecutive underscores
    while '__' in table_name:
        table_name = table_name.replace('__', '_')
    # Remove leading/trailing underscores
    table_name = table_name.strip('_')
    # Add data_ prefix
    return f"data_{table_name}"

def normalize_kb_types(conn):
    """Normalize KB types to match new schema"""
    print("\n" + "=" * 80)
    print("STEP 2: NORMALIZING KB TYPES")
    print("=" * 80)

    type_mapping = {
        'documentation': 'DOCUMENTATION',
        'code': 'CODE',
        'generic': 'GENERIC',
        'agent-os': 'AGENT_OS',
        'agent_os': 'AGENT_OS'
    }

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, kb_type FROM knowledge_bases")
            kbs = cur.fetchall()

            for kb in kbs:
                old_type = kb['kb_type']
                new_type = type_mapping.get(old_type.lower(), 'GENERIC')

                if old_type != new_type:
                    cur.execute("UPDATE knowledge_bases SET kb_type = %s WHERE id = %s",
                               (new_type, kb['id']))
                    print(f"  {kb['name']}: {old_type} -> {new_type}")

            conn.commit()
            print("\n✓ KB types normalized")

    except Exception as e:
        conn.rollback()
        raise MigrationError(f"Failed to normalize KB types: {e}")

def create_new_schema(conn):
    """Create new PGVectorStore-compatible schema"""
    print("\n" + "=" * 80)
    print("STEP 3: CREATING NEW SCHEMA")
    print("=" * 80)

    try:
        with conn.cursor() as cur:
            # Read and execute schema file
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'core', 'schema_pgvector.sql')
            if not os.path.exists(schema_path):
                # Try current directory (for Docker execution)
                schema_path = 'schema_pgvector.sql'

            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            cur.execute(schema_sql)
            conn.commit()

            print("\n✓ New schema created successfully")

    except Exception as e:
        conn.rollback()
        raise MigrationError(f"Failed to create new schema: {e}")

def update_kb_metadata(conn, kb_id, table_name, embed_dim=768):
    """Update knowledge_bases table with new columns"""
    with conn.cursor() as cur:
        # Add columns if they don't exist
        cur.execute("""
            ALTER TABLE knowledge_bases
            ADD COLUMN IF NOT EXISTS table_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS embed_dim INTEGER DEFAULT 768,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)

        # Update the KB record
        cur.execute("""
            UPDATE knowledge_bases
            SET table_name = %s, embed_dim = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (table_name, embed_dim, kb_id))

        conn.commit()

def migrate_kb_data(conn, kb, dry_run=False):
    """Migrate data for a single KB"""
    kb_id = kb['id']
    kb_name = kb['name']
    table_name = sanitize_table_name(kb_name)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating KB: {kb_name} -> {table_name}")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get document count
            cur.execute("SELECT COUNT(*) as count FROM documents WHERE kb_id = %s", (kb_id,))
            doc_count = cur.fetchone()['count']

            print(f"  Documents to migrate: {doc_count}")

            if dry_run:
                print(f"  [DRY RUN] Would create table: {table_name}")
                print(f"  [DRY RUN] Would migrate {doc_count} documents")
                return True

            # Create the new table
            cur.execute("SELECT create_kb_table(%s, %s, %s)", (kb_name, table_name, 768))

            # Update KB metadata
            update_kb_metadata(conn, kb_id, table_name, 768)

            # Migrate documents in batches
            batch_size = 100
            offset = 0
            migrated = 0

            while True:
                cur.execute("""
                    SELECT doc_id, content, metadata, embedding
                    FROM documents
                    WHERE kb_id = %s
                    ORDER BY id
                    LIMIT %s OFFSET %s
                """, (kb_id, batch_size, offset))

                batch = cur.fetchall()
                if not batch:
                    break

                # Insert into new table
                for doc in batch:
                    # Generate node_id if doc_id doesn't exist
                    node_id = doc['doc_id'] if doc['doc_id'] else str(uuid.uuid4())

                    # Embedding is already in correct format from PostgreSQL
                    # Just pass it directly
                    embedding = doc['embedding']

                    # Insert into new table
                    insert_query = sql.SQL("""
                        INSERT INTO {} (text, metadata_, node_id, embedding)
                        VALUES (%s, %s, %s, %s)
                    """).format(sql.Identifier(table_name))

                    cur.execute(insert_query, (
                        doc['content'],
                        json.dumps(doc['metadata']) if doc['metadata'] else None,
                        node_id,
                        embedding
                    ))

                    migrated += 1

                offset += batch_size
                print(f"  Migrated: {migrated}/{doc_count}", end='\r')

            conn.commit()
            print(f"  ✓ Migrated: {migrated}/{doc_count}")

            # Verify migration
            cur.execute(sql.SQL("SELECT COUNT(*) as count FROM {}").format(sql.Identifier(table_name)))
            new_count = cur.fetchone()['count']

            if new_count != doc_count:
                raise MigrationError(f"Verification failed: {new_count} != {doc_count}")

            print(f"  ✓ Verification passed: {new_count} documents")
            return True

    except Exception as e:
        conn.rollback()
        raise MigrationError(f"Failed to migrate KB {kb_name}: {e}")

def verify_migration(conn, kbs):
    """Verify all data was migrated correctly"""
    print("\n" + "=" * 80)
    print("STEP 5: VERIFYING MIGRATION")
    print("=" * 80)

    all_good = True

    for kb in kbs:
        kb_name = kb['name']
        table_name = sanitize_table_name(kb_name)

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Count old documents
                cur.execute("SELECT COUNT(*) as count FROM documents WHERE kb_id = %s", (kb['id'],))
                old_count = cur.fetchone()['count']

                # Count new documents
                cur.execute(sql.SQL("SELECT COUNT(*) as count FROM {}").format(sql.Identifier(table_name)))
                new_count = cur.fetchone()['count']

                if old_count == new_count:
                    print(f"✓ {kb_name}: {new_count} documents")
                else:
                    print(f"✗ {kb_name}: MISMATCH (old={old_count}, new={new_count})")
                    all_good = False

        except Exception as e:
            print(f"✗ {kb_name}: ERROR - {e}")
            all_good = False

    return all_good

def cleanup_old_schema(conn, dry_run=False):
    """Drop old tables"""
    print("\n" + "=" * 80)
    print(f"STEP 6: CLEANUP OLD SCHEMA {'[DRY RUN]' if dry_run else ''}")
    print("=" * 80)

    if dry_run:
        print("\n[DRY RUN] Would drop:")
        print("  - documents table")
        print("  - agent_os_content table (if exists)")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS documents CASCADE")
            print("✓ Dropped documents table")

            cur.execute("DROP TABLE IF EXISTS agent_os_content CASCADE")
            print("✓ Dropped agent_os_content table")

            conn.commit()

    except Exception as e:
        conn.rollback()
        raise MigrationError(f"Failed to cleanup old schema: {e}")

def main():
    parser = argparse.ArgumentParser(description='Migrate to PGVectorStore schema')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--keep-old', action='store_true', help='Keep old tables after migration')
    args = parser.parse_args()

    print("=" * 80)
    print("CODE-FORGE: MIGRATION TO PGVECTORSTORE SCHEMA")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠ DRY RUN MODE - No changes will be made\n")

    try:
        # Connect to database
        conn = get_connection()
        print("\n✓ Connected to database")

        # Backup existing data
        if not args.dry_run:
            backup_file = backup_data(conn)

        # Get existing KBs
        kbs = get_existing_kbs(conn)
        print(f"\n✓ Found {len(kbs)} knowledge bases to migrate")

        # Normalize KB types
        if not args.dry_run:
            normalize_kb_types(conn)

        # Create new schema
        if not args.dry_run:
            create_new_schema(conn)

        # Migrate each KB
        print("\n" + "=" * 80)
        print("STEP 4: MIGRATING DATA")
        print("=" * 80)

        for kb in kbs:
            migrate_kb_data(conn, kb, dry_run=args.dry_run)

        # Verify migration
        if not args.dry_run:
            if verify_migration(conn, kbs):
                print("\n✓ All data verified successfully!")
            else:
                raise MigrationError("Verification failed!")

        # Cleanup old schema
        if not args.keep_old:
            cleanup_old_schema(conn, dry_run=args.dry_run)

        conn.close()

        print("\n" + "=" * 80)
        print("✓ MIGRATION COMPLETE!")
        print("=" * 80)

        if not args.dry_run:
            print("\nNext steps:")
            print("1. Update RAGEngine to use PGVectorStore")
            print("2. Update ingestion to use PGVectorStore")
            print("3. Test queries on migrated data")

    except MigrationError as e:
        print(f"\n✗ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

