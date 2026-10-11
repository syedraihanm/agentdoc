from backend.app.storage.db import init_db
from backend.app.storage.repo import Repo
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.tools.logging_shim import DefaultToolCallLogger

def test_no_cross_question_cache(tmp_path):
    init_db(tmp_path / "test.db")
    repo = Repo(tmp_path / "test.db")
    repo.save_document('doc1', 'Doc', 'f.pdf', 'h', 3, 'outline', 0, None, None, [], '2026-01-01')
    repo.save_pages('doc1', [
        {'page_number': 1, 'text': 'Page 1', 'norm': 'page 1', 'norm_numeric': 'page 1'},
        {'page_number': 2, 'text': 'Page 2', 'norm': 'page 2', 'norm_numeric': 'page 2'},
    ])

    backend = ToolBackend(repo)
    logger = DefaultToolCallLogger(tmp_path / "calls.jsonl")

    # Run 1
    gw1 = ToolGateway(backend, 'doc1', budget=Budget(max_calls=6), logger=logger)
    ok1, res1, st1 = gw1.execute('get_page', {'page_number': 1})
    assert ok1 is True
    assert st1 == 'ok'
    assert logger.executed_calls_count == 1

    # Run 2 (Distinct question / gateway instance)
    gw2 = ToolGateway(backend, 'doc1', budget=Budget(max_calls=6), logger=logger)
    # Even though page 1 was read in Run 1, in Run 2 it MUST execute again through logger (not cached across questions)
    ok2, res2, st2 = gw2.execute('get_page', {'page_number': 1})
    assert ok2 is True
    assert st2 == 'ok' # NOT deduped across runs!
    assert logger.executed_calls_count == 2