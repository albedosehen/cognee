import asyncio
from cognee.shared.logging_utils import get_logger
import aiohttp
from typing import List, Optional
import os
import litellm
import logging
import aiohttp.http_exceptions
from tenacity import (
    retry,
    stop_after_delay,
    wait_exponential_jitter,
    retry_if_not_exception_type,
    before_sleep_log,
)

from cognee.infrastructure.databases.vector.embeddings.EmbeddingEngine import EmbeddingEngine
from cognee.infrastructure.llm.tokenizer.HuggingFace import (
    HuggingFaceTokenizer,
)
from cognee.shared.rate_limiting import embedding_rate_limiter_context_manager
from cognee.shared.utils import create_secure_ssl_context

logger = get_logger("OllamaEmbeddingEngine")


class OllamaEmbeddingEngine(EmbeddingEngine):
    """
    Implements an embedding engine using the Ollama embedding model.

    Public methods:
    - embed_text
    - get_vector_size
    - get_tokenizer

    Instance variables:
    - model
    - dimensions
    - max_completion_tokens
    - endpoint
    - mock
    - huggingface_tokenizer_name
    - tokenizer
    """

    model: str
    dimensions: int
    max_completion_tokens: int
    endpoint: str
    mock: bool
    huggingface_tokenizer_name: str

    MAX_RETRIES = 5

    def __init__(
        self,
        model: Optional[str] = "avr/sfr-embedding-mistral:latest",
        dimensions: Optional[int] = 1024,
        max_completion_tokens: int = 512,
        endpoint: Optional[str] = "http://localhost:11434/api/embeddings",
        huggingface_tokenizer: str = "Salesforce/SFR-Embedding-Mistral",
        batch_size: int = 100,
    ):
        self.model = model
        self.dimensions = dimensions
        self.max_completion_tokens = max_completion_tokens
        self.endpoint = endpoint
        self.huggingface_tokenizer_name = huggingface_tokenizer
        self.batch_size = batch_size
        self.tokenizer = self.get_tokenizer()

        enable_mocking = os.getenv("MOCK_EMBEDDING", "false")
        if isinstance(enable_mocking, bool):
            enable_mocking = str(enable_mocking).lower()
        self.mock = enable_mocking in ("true", "1", "yes")

    async def embed_text(self, text: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a list of text prompts.

        If mocking is enabled, returns a list of zero vectors instead of actual embeddings.

        Parameters:
        -----------

            - text (List[str]): A list of text prompts for which to generate embeddings.

        Returns:
        --------

            - List[List[float]]: A list of embedding vectors corresponding to the text prompts.
        """
        if self.mock:
            return [[0.0] * self.dimensions for _ in text]

        embeddings = await asyncio.gather(*[self._get_embedding(prompt) for prompt in text])
        return embeddings

    @retry(
        stop=stop_after_delay(128),
        wait=wait_exponential_jitter(8, 128),
        retry=retry_if_not_exception_type(litellm.exceptions.NotFoundError),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    def _extract_embedding_from_response(self, data: dict, prompt_preview: str = "") -> List[float]:
        """
        Extract embedding vector from API response, handling multiple response formats.
        
        Supports:
        - Ollama format: {"embedding": [...]}
        - Alternative plural: {"embeddings": [[...], ...]}
        - OpenAI-like format: {"data": [{"embedding": [...]}]}
        
        Args:
            data: The JSON response from the embedding API
            prompt_preview: First 50 chars of prompt for logging (optional)
            
        Returns:
            List[float]: The embedding vector
            
        Raises:
            ValueError: If response format is not recognized or contains errors
        """
        # Check for error in response
        if "error" in data:
            error_msg = data.get("error", "Unknown error")
            logger.error(f"Ollama API error for prompt '{prompt_preview}': {error_msg}")
            raise ValueError(f"Ollama API returned error: {error_msg}")
        
        # Handle Ollama standard format: {"embedding": [...]}
        if "embedding" in data:
            embedding = data["embedding"]
            if isinstance(embedding, list) and len(embedding) > 0:
                logger.debug(f"Extracted embedding (Ollama format) with {len(embedding)} dimensions")
                return embedding
            else:
                raise ValueError("Ollama API returned empty or invalid 'embedding' field")
        
        # Handle alternative plural format: {"embeddings": [[...], ...]}
        elif "embeddings" in data:
            embeddings = data["embeddings"]
            if isinstance(embeddings, list) and len(embeddings) > 0:
                embedding = embeddings[0]
                if isinstance(embedding, list) and len(embedding) > 0:
                    logger.debug(f"Extracted embedding (plural format) with {len(embedding)} dimensions")
                    return embedding
            raise ValueError("Ollama API returned empty or invalid 'embeddings' field")
        
        # Handle OpenAI-like format: {"data": [{"embedding": [...]}]}
        elif "data" in data:
            data_items = data["data"]
            if isinstance(data_items, list) and len(data_items) > 0:
                first_item = data_items[0]
                if isinstance(first_item, dict) and "embedding" in first_item:
                    embedding = first_item["embedding"]
                    if isinstance(embedding, list) and len(embedding) > 0:
                        logger.debug(f"Extracted embedding (OpenAI format) with {len(embedding)} dimensions")
                        return embedding
            raise ValueError("Ollama API returned empty or invalid 'data' field")
        
        # No recognized format found
        available_keys = list(data.keys())
        logger.error(f"Unrecognized response format. Available keys: {available_keys}")
        raise ValueError(
            f"Unexpected response format from Ollama embedding API. "
            f"Expected 'embedding', 'embeddings', or 'data' fields, but got: {available_keys}. "
            f"Please verify the Ollama endpoint and model compatibility."
        )

    async def _get_embedding(self, prompt: str) -> List[float]:
        """
        Internal method to call the Ollama embeddings endpoint for a single prompt.
        
        Args:
            prompt: Text to generate embedding for
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            ValueError: If API response is invalid or contains errors
            aiohttp.ClientError: If network request fails
        """
        payload = {"model": self.model, "prompt": prompt, "input": prompt}
        prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt

        headers = {}
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        ssl_context = create_secure_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.endpoint, json=payload, headers=headers, timeout=60.0
                ) as response:
                    # Check HTTP status
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Ollama API request failed with status {response.status} "
                            f"for prompt '{prompt_preview}': {error_text}"
                        )
                        raise ValueError(
                            f"Ollama embedding API returned status {response.status}: {error_text}"
                        )
                    
                    # Parse JSON response
                    try:
                        data = await response.json()
                    except Exception as e:
                        response_text = await response.text()
                        logger.error(f"Failed to parse JSON response: {response_text[:200]}")
                        raise ValueError(f"Invalid JSON response from Ollama API: {str(e)}")
                    
                    # Extract and return embedding
                    return self._extract_embedding_from_response(data, prompt_preview)
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Ollama API at {self.endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting embedding for prompt '{prompt_preview}': {str(e)}")
            raise

    def get_vector_size(self) -> int:
        """
        Retrieve the size of the embedding vectors.

        Returns:
        --------

            - int: The dimension of the embedding vectors.
        """
        return self.dimensions

    def get_batch_size(self) -> int:
        """
        Return the desired batch size for embedding calls

        Returns:

        """
        return self.batch_size

    def get_tokenizer(self):
        """
        Load and return a HuggingFace tokenizer for the embedding engine.

        Returns:
        --------

            The instantiated HuggingFace tokenizer used by the embedding engine.
        """
        logger.debug("Loading HuggingfaceTokenizer for OllamaEmbeddingEngine...")
        tokenizer = HuggingFaceTokenizer(
            model=self.huggingface_tokenizer_name, max_completion_tokens=self.max_completion_tokens
        )
        logger.debug("Tokenizer loaded for OllamaEmbeddingEngine")
        return tokenizer
