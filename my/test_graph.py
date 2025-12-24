import asyncio
import cognee
from cognee.api.v1.visualize.visualize import visualize_graph

async def main():
    await cognee.add([
        "Microsoft develops Azure.",
        "Microservices is a subfield of Cloud Architecture."
    ])

    await cognee.cognify()

    await visualize_graph("./test_graph.html")

asyncio.run(main())