import os
import pathlib
import asyncio
import cognee
from cognee.modules.search.types import SearchType


async def main():
    """
    Example script demonstrating how to use Cognee with SurrealDB

    This example:
    1. Configures Cognee to use SurrealDB as vector database
    2. Sets up data directories
    3. Adds sample data to Cognee
    4. Processes (cognifies) the data
    5. Performs different types of searches
    """
    # Configure SurrealDB as the vector database provider
    cognee.config.set_vector_db_config(
        {
            "vector_db_url": "http://localhost:8000",  # Default SurrealDB HTTP server URL
            "vector_db_key": "root:root",  # SurrealDB credentials format (username:password)
            "vector_db_provider": "surrealdb",  # Specify SurrealDB as provider
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
    dataset_name = "surrealdb_example"

    # Add sample text to the dataset
    sample_text = """SurrealDB is a multi-model database that combines graph, document, and vector capabilities into a single platform.
    It provides powerful querying with SurrealQL, a SQL-like query language designed for multi-model data operations.
    SurrealDB supports real-time subscriptions allowing applications to receive live updates as data changes in the database.
    The database offers built-in vector search capabilities, enabling semantic search and similarity matching for AI applications.
    It features strong schema-less and schema-full modes, giving developers flexibility in how they structure their data.
    SurrealDB provides inter-document relations and graph querying out of the box, making it ideal for complex, connected data.
    The system is designed for modern distributed applications with support for horizontal scaling and edge computing deployments."""

    # Add the sample text to the dataset
    await cognee.add([sample_text], dataset_name)

    # Process the added document to extract knowledge
    await cognee.cognify([dataset_name])

    # Now let's perform some searches
    # 1. Search for insights related to "SurrealDB"
    insights_results = await cognee.search(
        query_type=SearchType.GRAPH_COMPLETION, query_text="SurrealDB"
    )
    print("\nInsights about SurrealDB:")
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
