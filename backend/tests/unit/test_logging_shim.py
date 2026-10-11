from backend.app.tools.logging_shim import DefaultToolCallLogger

def test_logging_shim_records_call(tmp_path):
    log_file = tmp_path / "calls.jsonl"
    logger = DefaultToolCallLogger(log_file)
    
    def dummy_tool(page_number: int):
        return {"page": page_number, "text": "hello"}

    res = logger("get_page", {"page_number": 4}, dummy_tool)
    assert res == {"page": 4, "text": "hello"}
    assert logger.executed_calls_count == 1
    
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"tool": "get_page"' in lines[0]
    assert '"status": "success"' in lines[0]