from unittest.mock import MagicMock, patch

import pytest
from api.models.rag import Collection, CollectionItem
from api.services.rag import RAGServiceV1, RAGServiceV2, RAGVersion, get_rag_service


@pytest.mark.django_db
class TestRAGService:
    """Tests for RAG service module (V1 and V2 implementations)."""

    def test_init_with_collection(self, db):
        """Test RAG service initialization with collection."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV1, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V1)
            assert service.collection == collection
            assert service.version == RAGVersion.V1

    def test_get_rag_service_v2(self, db):
        """Test getting V2 RAG service."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV2, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V2)
            assert service.collection == collection
            assert service.version == RAGVersion.V2

    def test_get_rag_service_latest(self, db):
        """Test getting latest RAG service (defaults to V2)."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV2, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.LATEST)
            assert service.version == RAGVersion.V2

    def test_cosine_similarity(self, db):
        """Test cosine similarity calculation."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV1, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V1)

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]

        # Orthogonal vectors should have similarity 0
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.001

        # Identical vectors should have similarity 1
        similarity = service._cosine_similarity(vec1, vec3)
        assert abs(similarity - 1.0) < 0.001

    def test_chunk_text_no_chunking_v1(self, db):
        """Test V1 text chunking with NO_CHUNKING strategy."""
        collection = Collection.objects.create(
            name="Test Collection", chunking_strategy=Collection.ChunkingStrategy.NO_CHUNKING
        )

        with patch.object(RAGServiceV1, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V1)

        text = "This is a test sentence."
        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0]["content"] == text

    def test_chunk_text_with_chunking_v1(self, db):
        """Test V1 text chunking functionality."""
        collection = Collection.objects.create(
            name="Test Collection",
            chunking_strategy=Collection.ChunkingStrategy.FIXED_LENGTH,
            chunk_length=50,
            chunk_overlap=10,
        )

        with patch.object(RAGServiceV1, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V1)

        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        chunks = service.chunk_text(text)

        assert len(chunks) > 1

    def test_chunk_text_v2_sentence_based(self, db):
        """Test V2 sentence-based chunking."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV2, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V2)

        # Long text that should be chunked by sentences
        text = "This is the first sentence. " * 50  # ~1400 chars
        chunks = service.chunk_text(text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert "chunk_type" in chunk
            assert chunk["chunk_type"] in ["sentences", "paragraphs", "full", "single"]

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_add_document(self, mock_setup, db):
        """Test adding document to collection."""
        collection = Collection.objects.create(
            name="Test Collection", chunking_strategy=Collection.ChunkingStrategy.NO_CHUNKING
        )

        service = get_rag_service(collection, version=RAGVersion.V1)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        items = service.add_document(name="Test Doc", content="This is test content", metadata={"type": "test"})

        assert len(items) == 1
        assert items[0].name == "Test Doc"
        assert items[0].content == "This is test content"
        assert items[0].embedding is not None

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_add_document_chunking(self, mock_setup, db):
        """Test document chunking for large content."""
        collection = Collection.objects.create(
            name="Test Collection",
            chunking_strategy=Collection.ChunkingStrategy.FIXED_LENGTH,
            chunk_length=100,
            chunk_overlap=20,
        )

        service = get_rag_service(collection, version=RAGVersion.V1)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        # Create content longer than chunk_length
        long_content = "This is a test. " * 20  # ~320 characters

        items = service.add_document(name="Long Doc", content=long_content)

        # Should create multiple chunks
        assert len(items) > 1

        # Check naming convention for chunks
        assert "Part" in items[0].name

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_query_documents_v1(self, mock_setup, db):
        """Test V1 querying documents by similarity (no filtering)."""
        collection = Collection.objects.create(name="Test Collection")

        service = get_rag_service(collection, version=RAGVersion.V1)
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

    @patch("api.services.rag.v2.RAGServiceV2._setup_client")
    def test_query_documents_v2_with_filtering(self, mock_setup, db):
        """Test V2 querying with minimum similarity filtering."""
        collection = Collection.objects.create(name="Test Collection")

        # V2 with high min_similarity threshold
        service = get_rag_service(collection, version=RAGVersion.V2, min_similarity=0.5)
        service._embedding_service = MagicMock()

        # Create test documents - one relevant, one not
        CollectionItem.objects.create(
            collection=collection, name="Doc 1", content="Python programming", embedding=[0.9, 0.1] + [0.0] * 766
        )
        CollectionItem.objects.create(
            collection=collection, name="Doc 2", content="Unrelated content", embedding=[0.1, 0.1] + [0.0] * 766
        )

        # Mock query embedding similar to Doc 1
        service._embedding_service.generate_embedding.return_value = [0.8, 0.2] + [0.0] * 766

        results = service.query("python code", top_k=5)

        # Should only return Doc 1 (above threshold), not Doc 2
        assert len(results) == 1
        assert results[0]["name"] == "Doc 1"

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_query_and_answer(self, mock_setup, db):
        """Test RAG query with AI answer generation."""
        collection = Collection.objects.create(name="Test Collection")

        service = get_rag_service(collection, version=RAGVersion.V1)
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

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_query_and_answer_no_results(self, mock_setup, db):
        """Test RAG query when no relevant documents found."""
        collection = Collection.objects.create(name="Test Collection")

        service = get_rag_service(collection, version=RAGVersion.V1)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        # No documents in collection
        result = service.query_and_answer("What is Python?")

        assert result["status"] == "error"
        assert "No relevant documents found" in result["message"]

    @patch("api.services.rag.v1.RAGServiceV1._setup_client")
    def test_generate_embedding(self, mock_setup, db):
        """Test embedding generation."""
        collection = Collection.objects.create(name="Test Collection")

        service = get_rag_service(collection, version=RAGVersion.V1)
        service._embedding_service = MagicMock()
        service._embedding_service.generate_embedding.return_value = [0.1] * 768

        embedding = service._generate_embedding("test text")

        assert len(embedding) == 768
        assert embedding[0] == 0.1
        service._embedding_service.generate_embedding.assert_called_once_with("test text")


@pytest.mark.django_db
class TestRAGServiceV2Specific:
    """Tests specific to V2 RAG service features."""

    @patch("api.services.rag.v2.RAGServiceV2._setup_client")
    def test_hybrid_search(self, mock_setup, db):
        """Test V2 hybrid search (embedding + keyword)."""
        collection = Collection.objects.create(name="Test Collection")

        service = get_rag_service(collection, version=RAGVersion.V2, min_similarity=0.1)
        service._embedding_service = MagicMock()

        # Create test documents
        CollectionItem.objects.create(
            collection=collection,
            name="Doc 1",
            content="Python programming language tutorial",
            embedding=[0.8, 0.2] + [0.0] * 766,
        )
        CollectionItem.objects.create(
            collection=collection,
            name="Doc 2",
            content="JavaScript web development guide",
            embedding=[0.7, 0.3] + [0.0] * 766,
        )

        # Mock query embedding
        service._embedding_service.generate_embedding.return_value = [0.75, 0.25] + [0.0] * 766

        results = service.query_hybrid("Python programming", top_k=2)

        assert len(results) >= 1
        # Results should have combined_score
        for result in results:
            assert "combined_score" in result
            assert "keyword_score" in result

    def test_sentence_splitting(self, db):
        """Test V2 sentence splitting with abbreviation handling."""
        collection = Collection.objects.create(name="Test Collection")

        with patch.object(RAGServiceV2, "_setup_client"):
            service = get_rag_service(collection, version=RAGVersion.V2)

        text = "Dr. Smith said hello. Mr. Jones replied. This is sentence three."
        sentences = service._split_into_sentences(text)

        # Should handle abbreviations correctly
        assert len(sentences) == 3
        assert "Dr." in sentences[0] or "Dr" in sentences[0]
