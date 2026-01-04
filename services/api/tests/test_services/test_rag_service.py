from unittest.mock import MagicMock, patch

import pytest
from api.models.rag import Collection, CollectionItem
from api.services.rag_service import RAGService


@pytest.mark.django_db
class TestRAGService:
    def test_init_with_collection(self, db):
        """Test RAGService initialization with collection."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGService, "_setup_client"):
            service = RAGService(collection)
            assert service.collection == collection

    def test_cosine_similarity(self, db):
        """Test cosine similarity calculation."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGService, "_setup_client"):
            service = RAGService(collection)

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]

        # Orthogonal vectors should have similarity 0
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.001

        # Identical vectors should have similarity 1
        similarity = service._cosine_similarity(vec1, vec3)
        assert abs(similarity - 1.0) < 0.001

    def test_chunk_text_no_chunking(self, db):
        """Test text chunking with NO_CHUNKING strategy."""
        collection = Collection.objects.create(
            name="Test Collection", chunking_strategy=Collection.ChunkingStrategy.NO_CHUNKING
        )

        with patch.object(RAGService, "_setup_client"):
            service = RAGService(collection)

        text = "This is a test sentence."
        chunks = service._chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_with_chunking(self, db):
        """Test text chunking functionality."""
        collection = Collection.objects.create(
            name="Test Collection",
            chunking_strategy=Collection.ChunkingStrategy.FIXED_LENGTH,
            chunk_length=50,
            chunk_overlap=10,
        )

        with patch.object(RAGService, "_setup_client"):
            service = RAGService(collection)

        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        chunks = service._chunk_text(text)

        assert len(chunks) > 1

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_add_document(self, mock_setup, db):
        """Test adding document to collection."""
        collection = Collection.objects.create(
            name="Test Collection", chunking_strategy=Collection.ChunkingStrategy.NO_CHUNKING
        )

        service = RAGService(collection)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        items = service.add_document(name="Test Doc", content="This is test content", metadata={"type": "test"})

        assert len(items) == 1
        assert items[0].name == "Test Doc"
        assert items[0].content == "This is test content"
        assert items[0].embedding is not None

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_add_document_chunking(self, mock_setup, db):
        """Test document chunking for large content."""
        collection = Collection.objects.create(
            name="Test Collection",
            chunking_strategy=Collection.ChunkingStrategy.FIXED_LENGTH,
            chunk_length=100,
            chunk_overlap=20,
        )

        service = RAGService(collection)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        # Create content longer than chunk_length
        long_content = "This is a test. " * 20  # ~320 characters

        items = service.add_document(name="Long Doc", content=long_content)

        # Should create multiple chunks
        assert len(items) > 1

        # Check naming convention for chunks
        assert "Part" in items[0].name

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_query_documents(self, mock_setup, db):
        """Test querying documents by similarity."""
        collection = Collection.objects.create(name="Test Collection")

        service = RAGService(collection)
        service._embedding_service = MagicMock()

        # Create test documents
        CollectionItem.objects.create(
            collection=collection, name="Doc 1", content="Python programming", embedding=[0.9, 0.1] + [0.0] * 766
        )
        CollectionItem.objects.create(
            collection=collection, name="Doc 2", content="JavaScript development", embedding=[0.1, 0.9] + [0.0] * 766
        )

        # Mock query embedding similar to Doc 1
        service._embedding_service.generate_embedding.return_value = [0.8, 0.2] + [0.0] * 766

        results = service.query("python code", top_k=1)

        assert len(results) == 1
        assert results[0]["name"] == "Doc 1"
        assert results[0]["similarity"] > 0.5

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_query_and_answer(self, mock_setup, db):
        """Test RAG query with AI answer generation."""
        collection = Collection.objects.create(name="Test Collection")

        service = RAGService(collection)
        service._embedding_service = MagicMock()
        service._completion_service = MagicMock()

        # Create test document
        CollectionItem.objects.create(
            collection=collection,
            name="Doc 1",
            content="Python is a programming language",
            embedding=[0.9, 0.1] + [0.0] * 766,
        )

        # Mock embedding
        service._embedding_service.generate_embedding.return_value = [0.8, 0.2] + [0.0] * 766

        # Mock AI completion
        service._completion_service.generate_with_context.return_value = "Python is indeed a programming language."

        result = service.query_and_answer("What is Python?", top_k=3)

        assert result["status"] == "success"
        assert result["answer"] == "Python is indeed a programming language."
        assert len(result["sources"]) >= 1

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_query_and_answer_no_results(self, mock_setup, db):
        """Test RAG query when no relevant documents found."""
        collection = Collection.objects.create(name="Test Collection")

        service = RAGService(collection)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        # No documents in collection
        result = service.query_and_answer("What is Python?")

        assert result["status"] == "error"
        assert "No relevant documents found" in result["message"]

    @patch("api.services.rag_service.RAGService._setup_client")
    def test_generate_embedding(self, mock_setup, db):
        """Test embedding generation."""
        collection = Collection.objects.create(name="Test Collection")

        service = RAGService(collection)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        embedding = service._generate_embedding("test text")

        assert len(embedding) == 768
        assert embedding[0] == 0.1
        service._embedding_service.generate_embedding.assert_called_once_with("test text")
