#!/usr/bin/env python3
"""
KB Test Script
==============
Simple script for testing knowledge base queries.
Now handles LLM synthesis locally to allow prompt iteration.

Usage:
    python test_kb.py "your question here"
    python test_kb.py  # Interactive mode
"""

import asyncio
import sys
import openai
from pathlib import Path

# Add parent dir to path if running as script
# sys.path.insert(0, str(Path(__file__).parent.parent))

from kb_search import kb_searcher as kb_manager


async def generate_answer(query: str, context: str, sources: list) -> str:
    """Synthesize answer using strict prompt."""
    try:
        client = openai.OpenAI()
        
        system_prompt = """You are a knowledgeable assistant that provides COMPLETE and ACCURATE answers based on provided context.

## CORE PRINCIPLES:
1. ACCURACY: Only answer based on context. Cite specific documents and PAGE NUMBERS (e.g., "See [Manual.pdf (p.12)]").
2. COMPLETENESS: Include values, ranges, tolerances, and conditions.
3. STRUCTURE: Use bullet points and clear sections.
4. CLARITY: Start with the direct answer.
"""
        user_prompt = f"""CONTEXT:\n{context[:15000]}\n\n---\n\nQUESTION: {query}\n\nProvide a structured answer based ONLY on the context."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating answer: {e}"


async def test_query(query: str) -> None:
    """Run a test query and print results."""
    print(f"\n{'='*60}")
    print(f"📝 QUERY: {query}")
    print(f"{'='*60}\n")
    
    # 1. Retrieve (Context Only)
    # Note: query() in kb_manager now behaves like retrieve() (returns raw chunks)
    result = await kb_manager.query(query)
    
    if "No relevant information" in result.text and not result.sources:
         print("❌ No relevant information found in KB.")
         return

    # 2. Synthesize (LLM Generation)
    print("🧠 Synthesizing Answer (using local test prompt)...")
    answer = await generate_answer(query, result.text, result.sources)
    
    print("\n📖 ANSWER:")
    print("-" * 40)
    print(answer)
    print("-" * 40)
    
    if result.sources:
        print(f"\n📚 Source Files: {', '.join(result.sources)}")
    
    print(f"\n📊 Confidence: {result.confidence:.2f}")
    if result.images:
        print(f"🖼️ Images: {result.images}")
    print()


async def interactive_mode():
    """Run in interactive mode."""
    print("\n" + "="*60)
    print("🔍 Knowledge Base Test - Interactive Mode")
    print("="*60)
    print("Type 'quit' or 'exit' to stop\n")
    
    # Show stats
    stats = kb_manager.get_stats()
    print(f"📊 KB Stats: {stats['documents']} docs, {stats['chunks']} chunks\n")
    
    while True:
        try:
            query = input("❓ Question: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not query:
                continue
            
            await test_query(query)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    # Check if query provided as argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        await test_query(query)
    else:
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
