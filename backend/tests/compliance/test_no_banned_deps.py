from pathlib import Path

BANNED = [
    'langchain', 'langgraph', 'crewai', 'autogen', 'llama-index', 'llama_index',
    'haystack', 'semantic-kernel', 'semantic_kernel', 'dspy', 'faiss', 'chromadb',
    'pinecone', 'weaviate', 'qdrant', 'sentence-transformers', 'sentence_transformers',
    'rank-bm25', 'rank_bm25', 'scikit-learn', 'sklearn'
]

def test_no_banned_dependencies():
    pyproject_path = Path(__file__).resolve().parent.parent.parent.parent / 'pyproject.toml'
    assert pyproject_path.exists()
    content = pyproject_path.read_text(encoding='utf-8').lower()
    for banned in BANNED:
        assert banned not in content, f'Banned dependency found in pyproject.toml: {banned}'
