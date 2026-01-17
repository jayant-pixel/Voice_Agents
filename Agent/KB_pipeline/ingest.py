#!/usr/bin/env python3
"""
KB Manager CLI Tool
===================
Command-line interface for knowledge base management.

Usage:
    python ingest.py                  # Ingest all documents (uses kb_parser)
    python ingest.py --force          # Force re-process all
    python ingest.py --stats          # Show KB statistics (uses kb_searcher)
    python ingest.py --query "text"   # Test retrieval (uses kb_searcher)
    python ingest.py --analyze file   # Analyze document content (uses kb_parser)
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent dir to path if running as script
# sys.path.insert(0, str(Path(__file__).parent.parent))

# Import both managers
from kb_parser import kb_parser
from kb_search import kb_searcher


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Base Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-process all documents"
    )
    
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show knowledge base statistics"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Test retrieval against the knowledge base"
    )
    
    parser.add_argument(
        "--analyze", "-a",
        type=str,
        help="Analyze content types in a specific document"
    )
    
    args = parser.parse_args()
    
    # Show stats (Lightweight)
    if args.stats:
        stats = kb_searcher.get_stats()
        print("\n📊 Knowledge Base Statistics")
        print("=" * 50)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show document details
        if kb_searcher.index.get("documents"):
            print("\n📁 Documents:")
            for doc_id, doc in kb_searcher.index["documents"].items():
                flags = []
                # Documents might be dicts or objects depending on implementation
                # kb_searcher loads them as dicts
                fname = doc.get('filename', 'Unknown')
                if doc.get("has_text"): flags.append("📝 text")
                if doc.get("has_tables"): flags.append("📊 tables")
                if doc.get("has_images"): flags.append("🖼️ images")
                if doc.get("has_charts"): flags.append("📈 charts")
                print(f"  • {fname}: {', '.join(flags)}")
        print()
        return
    
    # Analyze document (Heavy)
    if args.analyze:
        file_path = Path(args.analyze)
        if not file_path.exists():
            # Try in kb_data folder
            file_path = kb_parser.data_path / args.analyze
        
        if not file_path.exists():
            print(f"❌ File not found: {args.analyze}")
            return
        
        print(f"\n🔍 Analyzing: {file_path.name}")
        print("=" * 50)
        
        # Uses kb_parser.detector
        elements, summary = kb_parser.detector.detect_content(file_path)
        
        print(f"\n📋 Content Summary:")
        print(f"  Has text: {'✅' if summary['has_text'] else '❌'}")
        print(f"  Has tables: {'✅' if summary['has_tables'] else '❌'}")
        print(f"  Has images: {'✅' if summary['has_images'] else '❌'}")
        print(f"  Has charts: {'✅' if summary['has_charts'] else '❌'}")
        print(f"  Page count: {summary.get('page_count', 'N/A')}")
        
        print(f"\n📦 Element Counts:")
        for el_type, count in summary.get("element_counts", {}).items():
            print(f"  {el_type}: {count}")
        
        print(f"\n📝 First 5 Elements:")
        for i, el in enumerate(elements[:5]):
            preview = el.content[:100] + "..." if len(el.content) > 100 else el.content
            print(f"  [{el.element_type}] {preview}")
        print()
        return
    
    # Test retrieval (Lightweight)
    if args.query:
        print(f"\n🔍 Querying: \"{args.query}\"")
        print("-" * 50)
        result = asyncio.run(kb_searcher.query(args.query))
        print(f"\n📝 Answer (Raw Context):\n{result.text}")
        print(f"\n📚 Sources: {', '.join(result.sources)}")
        if result.images:
            print(f"🖼️ Images: {', '.join(result.images)}")
        print()
        return
    
    # Ingest documents (Heavy)
    print("\n📥 Knowledge Base Ingestion")
    print("=" * 50)
    print(f"  Data folder: {kb_parser.data_path}")
    print(f"  Force reprocess: {args.force}")
    print()
    
    count = kb_parser.ingest_all(force=args.force)
    
    print(f"\n✅ Ingestion complete!")
    # Get fresh stats from parser (as it has latest in memory)
    # Or reload searcher? Parser saves index.
    # We can just print count.
    
    print(f"   Processed {count} documents.")
    print()


if __name__ == "__main__":
    main()
