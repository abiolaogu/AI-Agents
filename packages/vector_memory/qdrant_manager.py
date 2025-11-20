"""
Qdrant Vector Database Manager
Handles agent memory, semantic search, and intelligent caching
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import hashlib
import json

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue,
        SearchRequest, ScrollRequest
    )
    from qdrant_client.http.exceptions import UnexpectedResponse
except ImportError:
    raise ImportError("Qdrant client not installed. Install with: pip install qdrant-client")

try:
    import openai
    from anthropic import Anthropic
except ImportError:
    print("Warning: OpenAI or Anthropic not installed for embeddings")

class QdrantMemoryManager:
    """Manages agent memory and semantic caching using Qdrant"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-small",
        embedding_dimension: int = 1536
    ):
        """
        Initialize Qdrant connection

        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: Optional API key for Qdrant Cloud
            embedding_provider: "openai" or "anthropic"
            embedding_model: Model name for embeddings
            embedding_dimension: Dimension of embedding vectors
        """
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

        # Initialize embedding client
        if embedding_provider == "openai":
            self.embedder = openai.Client()
        elif embedding_provider == "anthropic":
            self.embedder = Anthropic()
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")

    async def create_collection(self, collection_name: str, vector_size: Optional[int] = None):
        """Create a new collection in Qdrant"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size or self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Created collection: {collection_name}")
        except UnexpectedResponse as e:
            if "already exists" in str(e):
                print(f"Collection {collection_name} already exists")
            else:
                raise

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.embedding_provider == "openai":
            response = await asyncio.to_thread(
                self.embedder.embeddings.create,
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        else:
            # Anthropic doesn't have embeddings API yet, use OpenAI as fallback
            client = openai.Client()
            response = await asyncio.to_thread(
                client.embeddings.create,
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding

    async def store_agent_execution(
        self,
        collection_name: str,
        agent_id: str,
        task_description: str,
        result: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Store agent execution in vector database"""

        # Generate embedding for task + result
        combined_text = f"Task: {task_description}\nResult: {result}"
        embedding = await self.get_embedding(combined_text)

        # Create unique ID
        execution_id = hashlib.sha256(
            f"{agent_id}_{task_description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()

        # Create point
        point = PointStruct(
            id=execution_id,
            vector=embedding,
            payload={
                "agent_id": agent_id,
                "task_description": task_description,
                "result": result,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "type": "execution"
            }
        )

        # Upsert to collection
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=collection_name,
            points=[point]
        )

        return execution_id

    async def search_similar_executions(
        self,
        collection_name: str,
        task_description: str,
        agent_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """Search for similar past executions (semantic cache)"""

        # Generate embedding for query
        query_embedding = await self.get_embedding(task_description)

        # Build filter
        query_filter = None
        if agent_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="agent_id",
                        match=MatchValue(value=agent_id)
                    )
                ]
            )

        # Search
        results = await asyncio.to_thread(
            self.client.search,
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]

    async def get_agent_memory(
        self,
        collection_name: str,
        agent_id: str,
        limit: int = 100,
        time_range_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve agent's memory (past executions)"""

        # Build filter
        filter_conditions = [
            FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
            FieldCondition(key="type", match=MatchValue(value="execution"))
        ]

        # Add time filter if specified
        if time_range_hours:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            filter_conditions.append(
                FieldCondition(
                    key="timestamp",
                    range={
                        "gte": cutoff_time.isoformat()
                    }
                )
            )

        query_filter = Filter(must=filter_conditions)

        # Scroll through results
        results = await asyncio.to_thread(
            self.client.scroll,
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=limit,
            with_vectors=False
        )

        return [
            {
                "id": point.id,
                "payload": point.payload
            }
            for point in results[0]
        ]

    async def store_knowledge_base(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        category: str
    ) -> List[str]:
        """Store knowledge base documents"""

        points = []
        doc_ids = []

        for doc in documents:
            # Generate embedding
            text = doc.get("content", "")
            embedding = await self.get_embedding(text)

            # Create ID
            doc_id = doc.get("id") or hashlib.sha256(text.encode()).hexdigest()
            doc_ids.append(doc_id)

            # Create point
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "content": text,
                    "category": category,
                    "metadata": doc.get("metadata", {}),
                    "timestamp": datetime.now().isoformat(),
                    "type": "knowledge"
                }
            )
            points.append(point)

        # Batch upsert
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=collection_name,
            points=points
        )

        return doc_ids

    async def query_knowledge_base(
        self,
        collection_name: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query knowledge base using semantic search"""

        # Generate query embedding
        query_embedding = await self.get_embedding(query)

        # Build filter
        query_filter = Filter(
            must=[
                FieldCondition(key="type", match=MatchValue(value="knowledge"))
            ]
        )

        if category:
            query_filter.must.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )

        # Search
        results = await asyncio.to_thread(
            self.client.search,
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "content": hit.payload.get("content", ""),
                "metadata": hit.payload.get("metadata", {})
            }
            for hit in results
        ]

    async def semantic_cache_get(
        self,
        collection_name: str,
        query: str,
        similarity_threshold: float = 0.95,
        ttl_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """Get result from semantic cache if exists"""

        # Search for similar cached results
        results = await self.search_similar_executions(
            collection_name=collection_name,
            task_description=query,
            limit=1,
            score_threshold=similarity_threshold
        )

        if not results:
            return None

        # Check if cache is still valid (TTL)
        cached_result = results[0]
        cached_time = datetime.fromisoformat(cached_result["payload"]["timestamp"])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600

        if age_hours > ttl_hours:
            return None  # Cache expired

        return cached_result["payload"]

    async def semantic_cache_set(
        self,
        collection_name: str,
        query: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store result in semantic cache"""

        await self.store_agent_execution(
            collection_name=collection_name,
            agent_id="cache",
            task_description=query,
            result=json.dumps(result) if not isinstance(result, str) else result,
            metadata=metadata or {}
        )

    async def cleanup_old_memories(
        self,
        collection_name: str,
        retention_days: int = 90
    ):
        """Clean up old memories to save storage"""

        cutoff_time = datetime.now() - timedelta(days=retention_days)

        # Filter for old entries
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="timestamp",
                    range={
                        "lt": cutoff_time.isoformat()
                    }
                )
            ]
        )

        # Scroll and delete
        results = await asyncio.to_thread(
            self.client.scroll,
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=10000,
            with_vectors=False
        )

        point_ids = [point.id for point in results[0]]

        if point_ids:
            await asyncio.to_thread(
                self.client.delete,
                collection_name=collection_name,
                points_selector=point_ids
            )
            print(f"✓ Cleaned up {len(point_ids)} old memories from {collection_name}")

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection"""

        info = await asyncio.to_thread(
            self.client.get_collection,
            collection_name=collection_name
        )

        return {
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status
        }

class AgentMemoryContext:
    """Context manager for agent memory"""

    def __init__(self, memory_manager: QdrantMemoryManager, collection_name: str, agent_id: str):
        self.memory_manager = memory_manager
        self.collection_name = collection_name
        self.agent_id = agent_id
        self.current_task = None
        self.start_time = None

    async def __aenter__(self):
        self.start_time = datetime.now()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Auto-save execution on context exit
        if self.current_task and hasattr(self, 'result'):
            await self.memory_manager.store_agent_execution(
                collection_name=self.collection_name,
                agent_id=self.agent_id,
                task_description=self.current_task,
                result=self.result,
                metadata={
                    "execution_time_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "success": exc_type is None
                }
            )

    async def recall_similar_tasks(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recall similar past tasks"""
        self.current_task = task
        return await self.memory_manager.search_similar_executions(
            collection_name=self.collection_name,
            task_description=task,
            agent_id=self.agent_id,
            limit=limit
        )

    async def get_full_memory(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get agent's full memory for time window"""
        return await self.memory_manager.get_agent_memory(
            collection_name=self.collection_name,
            agent_id=self.agent_id,
            time_range_hours=hours
        )

    def set_result(self, result: str):
        """Set result to be saved"""
        self.result = result


# Global memory manager instance
memory_manager = QdrantMemoryManager()


async def init_collections():
    """Initialize standard collections"""
    collections = [
        "agent_executions",
        "knowledge_base",
        "semantic_cache",
        "business_ops",
        "sales_marketing",
        "customer_support",
        "finance_legal",
        "hr_people",
        "healthcare",
        "education",
        "product_tech",
        "data_science",
        "devops",
        "security"
    ]

    for collection in collections:
        await memory_manager.create_collection(collection)

    print(f"✓ Initialized {len(collections)} Qdrant collections")
