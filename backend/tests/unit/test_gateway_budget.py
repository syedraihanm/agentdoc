import pytest
from backend.app.storage.repo import Repo
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.tools.schemas import ToolError

@pytest.fixture
def test_repo(tmp_path):
    from backend.app.storage.db import init_db
    db_file = tmp_path / 'test.db'
    init_db(db_file)
    repo = Repo(db_file)
    
    # Seed sample document
    repo.save_document(
        doc_id='doc123',
        title='Sample Handbook',
        filename='handbook.pdf',
        sha256='abc123sha',
        num_pages=3,
        headings_source='outline',
        headings_count=2,
        author='HR',
        created='2025-01-01',
        warnings=[],
        uploaded_at='2025-01-01T00:00:00Z'
    )
    repo.save_pages('doc123', [
        {'page_number': 1, 'text': 'Page 1 text about remote work.', 'norm': 'page 1 text about remote work.', 'norm_numeric': 'page 1 text about remote work.'},
        {'page_number': 2, 'text': 'Page 2 cost is ,500.', 'norm': 'page 2 cost is ,500.', 'norm_numeric': 'page 2 cost is 1500.'},
        {'page_number': 3, 'text': 'Page 3 Appendix remote rules.', 'norm': 'page 3 appendix remote rules.', 'norm_numeric': 'page 3 appendix remote rules.'},
    ])
    repo.save_headings('doc123', [
        {'title': '1. Remote Work', 'level': 1, 'page': 1},
        {'title': 'Appendix: Overrides', 'level': 1, 'page': 3}
    ])
    return repo

def test_tool_backend_shapes(test_repo):
    backend = ToolBackend(test_repo)
    
    # 1. list_documents
    docs = backend.list_documents()
    assert isinstance(docs, list)
    assert len(docs) == 1
    assert docs[0]['doc_id'] == 'doc123'
    assert 'metadata' in docs[0]
    assert docs[0]['metadata']['num_pages'] == 3

    # 2. list_headings
    headings = backend.list_headings('doc123')
    assert isinstance(headings, list)
    assert len(headings) == 2
    assert headings[0] == {'title': '1. Remote Work', 'level': 1, 'page': 1}

    # 3. get_page
    p1 = backend.get_page('doc123', 1)
    assert p1 == {'page_number': 1, 'text': 'Page 1 text about remote work.'}
    
    # Rejects invalid page types
    with pytest.raises(ToolError):
        backend.get_page('doc123', '1') # string
    with pytest.raises(ToolError):
        backend.get_page('doc123', 99) # out of range

    # 4. search_keyword
    hits = backend.search_keyword('doc123', 'remote')
    assert hits == [1, 3] # returns sorted list[int]
    
    # Numeric search matches ,500 via "1500"
    num_hits = backend.search_keyword('doc123', '1500')
    assert num_hits == [2]

def test_gateway_budget_and_allowlist(test_repo):
    backend = ToolBackend(test_repo)
    budget = Budget(max_calls=6)
    events = []
    gw = ToolGateway(backend, doc_id='doc123', budget=budget, on_event=lambda e: events.append(e))

    # Unknown tool refused
    ok, res, status = gw.execute('hack_tool', {})
    assert ok is False
    assert status == 'refused'
    assert budget.used == 0

    # Invalid args refused without spending budget
    ok, res, status = gw.execute('get_page', {'page_number': '1-3'})
    assert ok is False
    assert status == 'refused'
    assert budget.used == 0

    # 1. list_headings (spends 1)
    ok, res, status = gw.execute('list_headings')
    assert ok is True
    assert status == 'ok'
    assert budget.used == 1

    # Dedupe does not spend budget
    ok, res, status = gw.execute('list_headings')
    assert ok is True
    assert status == 'deduped'
    assert budget.used == 1

    # Calls 2, 3, 4, 5, 6
    for i in range(1, 4):
        ok, res, status = gw.execute('get_page', {'page_number': i})
        assert ok is True
    # Spent: 1 + 3 = 4
    ok, res, status = gw.execute('search_keyword', {'keyword': 'remote'})
    assert ok is True
    # Spent: 5
    ok, res, status = gw.execute('search_keyword', {'keyword': '1500'})
    assert ok is True
    # Spent: 6
    assert budget.used == 6
    assert budget.remaining == 0

    # 7th call MUST BE REFUSED
    ok, res, status = gw.execute('get_page', {'page_number': 1}) # already cached, so deduped
    assert status == 'deduped'
    assert budget.used == 6

    # 7th NEW call MUST BE REFUSED by budget check
    ok, res, status = gw.execute('search_keyword', {'keyword': 'fresh'})
    assert ok is False
    assert status == 'refused'
    assert budget.used == 6
