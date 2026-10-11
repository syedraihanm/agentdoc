from backend.app.agent.signals import find_amendment_headings, find_cross_references, partition_unread_hits

def test_find_amendment_headings():
    headings = [
        {"title": "1. Purpose and Scope", "level": 1, "page": 3},
        {"title": "Appendix A — Amendment 1", "level": 1, "page": 9},
        {"title": "Appendix B — Errata Notice", "level": 1, "page": 10},
    ]
    res = find_amendment_headings(headings)
    assert len(res) == 2
    assert res[0]["page"] == 9
    assert res[1]["page"] == 10

def test_partition_unread_hits():
    all_hits = {4, 6, 9, 10}
    read_pages = {4, 6}
    part = partition_unread_hits(all_hits, read_pages)
    assert part["before_last_read"] == []
    assert part["after_last_read"] == [9, 10]