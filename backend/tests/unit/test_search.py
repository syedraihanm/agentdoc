import pytest
from backend.app.storage.db import init_db
from backend.app.storage.repo import Repo
from backend.app.tools.backend import ToolBackend

def test_search_substring_and_stem(tmp_path):
    init_db(tmp_path / "test.db")
    repo = Repo(tmp_path / "test.db")
    repo.save_document('doc1', 'Doc', 'f.pdf', 'hash1', 3, 'outline', 0, None, None, [], '2026-01-01')
    repo.save_pages('doc1', [
        {'page_number': 1, 'text': 'Termination conditions apply.', 'norm': 'termination conditions apply.', 'norm_numeric': 'termination conditions apply.'},
        {'page_number': 2, 'text': 'No rules here.', 'norm': 'no rules here.', 'norm_numeric': 'no rules here.'},
        {'page_number': 3, 'text': 'Employee was terminated early.', 'norm': 'employee was terminated early.', 'norm_numeric': 'employee was terminated early.'},
    ])
    
    backend = ToolBackend(repo)
    # Search stem "terminat" should hit page 1 and page 3
    hits = backend.search_keyword('doc1', 'terminat')
    assert hits == [1, 3]

    # Non-existent keyword returns empty list
    empty = backend.search_keyword('doc1', 'unobtainium')
    assert empty == []