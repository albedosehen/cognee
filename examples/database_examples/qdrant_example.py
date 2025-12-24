import os
import pathlib
import asyncio
import cognee
from cognee.modules.search.types import SearchType


async def main():
    """
    Example script demonstrating how to use Cognee with Qdrant

    This example:
    1. Configures Cognee to use Qdrant as vector database
    2. Sets up data directories
    3. Adds sample data to Cognee
    4. Processes (cognifies) the data
    5. Performs different types of searches
    """
    # Configure Qdrant as the vector database provider
    cognee.config.set_vector_db_config(
        {
            "vector_db_url": "http://localhost:6333",  # Default Qdrant server URL
            "vector_db_key": "",  # Qdrant doesn't require an API key by default for local instances
            "vector_db_provider": "qdrant",  # Specify Qdrant as provider
        }
    )

    # Set up data directories for storing documents and system files
    # You should adjust these paths to your needs
    current_dir = pathlib.Path(__file__).parent
    data_directory_path = str(current_dir / "data_storage")
    cognee.config.data_root_directory(data_directory_path)

    cognee_directory_path = str(current_dir / "cognee_system")
    cognee.config.system_root_directory(cognee_directory_path)

    # Clean any existing data (optional)
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)

    # Create a dataset
    dataset_name = "qdrant_example"

    # Add sample text to the dataset
    sample_text = """Qdrant is an open-source vector similarity search engine written in Rust.
    It provides high-performance vector search capabilities with an extended filtering support.
    Qdrant can be deployed as a standalone service with a RESTful API and gRPC interface.
    The database is optimized for efficiency with features like quantization, on-disk payload storage, and configurable indexing.
    It supports HNSW (Hierarchical Navigable Small World) algorithm for fast and accurate approximate nearest neighbor search.
    Qdrant offers powerful filtering capabilities, allowing you to combine vector similarity search with attribute-based filtering.
    The system is designed for production use with features like snapshots, replication, and distributed deployment support."""

    # Add the sample text to the dataset
    await cognee.add([sample_text], dataset_name)

    # Process the added document to extract knowledge
    await cognee.cognify([dataset_name])

    # Now let's perform some searches
    # 1. Search for insights related to "Qdrant"
    insights_results = await cognee.search(
        query_type=SearchType.GRAPH_COMPLETION, query_text="Qdrant"
    )
    print("\nInsights about Qdrant:")
    for result in insights_results:
        print(f"- {result}")

    # 2. Search for text chunks related to "vector search"
    chunks_results = await cognee.search(
        query_type=SearchType.CHUNKS, query_text="vector search", datasets=[dataset_name]
    )
    print("\nChunks about vector search:")
    for result in chunks_results:
        print(f"- {result}")

    # 3. Get graph completion related to databases
    graph_completion_results = await cognee.search(
        query_type=SearchType.GRAPH_COMPLETION, query_text="database"
    )
    print("\nGraph completion for databases:")
    for result in graph_completion_results:
        print(f"- {result}")

    # Clean up (optional)
    # await cognee.prune.prune_data()
    # await cognee.prune.prune_system(metadata=True)


if __name__ == "__main__":
    asyncio.run(main())
