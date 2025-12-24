import asyncio
import cognee

async def main():

    # Create a clean slate for cognee -- reset data and system state
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    
    # Add sample content
    text = "Cognee turns documents into AI memory."
    await cognee.add(text)
    
    # Process with LLMs to build the knowledge graph
    await cognee.cognify()
    
    # Search the knowledge graph
    results = await cognee.search(
        query_text="What does Cognee do?"
    )
    
    # DEBUG: Print raw results object
    print(f"\n=== DEBUG INFO ===")
    print(f"Results type: {type(results)}")
    print(f"Results repr: {repr(results)}")
    print(f"Results value: {results}")
    
    # Check if it's a generator/iterator
    import inspect
    print(f"Is generator: {inspect.isgenerator(results)}")
    print(f"Is async generator: {inspect.isasyncgen(results)}")
    
    # If it's a list/tuple, print length
    if hasattr(results, '__len__'):
        print(f"Results length: {len(results)}")
    print(f"==================\n")
    
    # Print individual results
    print("Individual results:")
    for i, result in enumerate(results):
        print(f"  [{i}] {type(result).__name__}: {result}")
    
    if not results or (hasattr(results, '__len__') and len(results) == 0):
        print("⚠️ WARNING: No results returned!")

if __name__ == '__main__':
    asyncio.run(main())