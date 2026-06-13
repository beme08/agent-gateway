from app.rag.chunk import chunk_text


def test_short_text_returns_one_chunk():
    assert chunk_text("hello world", size=800) == ["hello world"]


def test_empty_returns_empty():
    assert chunk_text("", size=800) == []


def test_long_text_chunks_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, size=400, overlap=100)
    assert len(chunks) >= 3
    # Each chunk <= size
    assert all(len(c) <= 400 for c in chunks)
    # Overlap: chunk[1] starts 300 chars into chunk[0]
    assert chunks[1][:100] == chunks[0][300:400]


def test_chunk_count_proportional_to_length():
    text = "lorem ipsum " * 200  # ~2400 chars
    chunks = chunk_text(text, size=500, overlap=50)
    assert len(chunks) >= 4
