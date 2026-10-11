import pytest
from backend.app.storage.db import init_db
from backend.app.storage.repo import Repo
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.agent.controller import AgentController
from backend.app.agent.llm.fake import FakeLLM
from backend.app.agent.schemas import Decision, DecisionAction, Answer, EvidenceItem, ConflictItem, ConflictChosen

@pytest.fixture
def seeded_repo(tmp_path):
    db_file = tmp_path / "test_ctrl.db"
    init_db(db_file)
    repo = Repo(db_file)
    repo.save_document('doc1', 'Policy v3', 'policy.pdf', 'h1', 11, 'outline', 3, 'HR', '2025-01-01', [], '2025-01-01')
    repo.save_pages('doc1', [
        {'page_number': 1, 'text': 'Cover Helix Policy v3.2', 'norm': 'cover helix policy v3.2', 'norm_numeric': 'cover helix policy v3.2'},
        {'page_number': 4, 'text': 'Remote work is permitted up to 3 days per week.', 'norm': 'remote work is permitted up to 3 days per week.', 'norm_numeric': 'remote work is permitted up to 3 days per week.'},
        {'page_number': 9, 'text': 'Effective 2025-07-01, remote work increases to 4 days per week. Supersedes Section 2.', 'norm': 'effective 2025-07-01, remote work increases to 4 days per week. supersedes section 2.', 'norm_numeric': 'effective 2025-07-01, remote work increases to 4 days per week. supersedes section 2.'},
    ])
    repo.save_headings('doc1', [
        {'title': 'Cover', 'level': 1, 'page': 1},
        {'title': '2. Remote Work Eligibility', 'level': 1, 'page': 4},
        {'title': 'Appendix A — Amendment 1', 'level': 1, 'page': 9},
    ])
    return repo

def test_controller_scripted_happy_path(seeded_repo):
    backend = ToolBackend(seeded_repo)
    budget = Budget(max_calls=6)
    events = []
    gw = ToolGateway(backend, 'doc1', budget=budget, on_event=lambda e: events.append(e))

    # Canned decision 1: search keyword 'remote' and read page 4
    dec1 = Decision(
        standalone_question="How many days per week can employees work remotely?",
        question_type="lookup",
        reasoning_summary="Searching for remote and reading page 4",
        ready_to_answer=False,
        actions=[
            DecisionAction(tool="search_keyword", args={"keyword": "remote"}, purpose="find remote mentions"),
            DecisionAction(tool="get_page", args={"page_number": 4}, purpose="read section 2")
        ]
    )
    # Canned decision 2: read page 9 (supersession / amendment)
    dec2 = Decision(
        standalone_question="How many days per week can employees work remotely?",
        question_type="lookup",
        reasoning_summary="Reading amendment page 9",
        ready_to_answer=False,
        actions=[
            DecisionAction(tool="get_page", args={"page_number": 9}, purpose="read amendment 1")
        ]
    )
    # Canned decision 3: ready to answer
    dec3 = Decision(
        standalone_question="How many days per week can employees work remotely?",
        question_type="lookup",
        reasoning_summary="We have evidence from base text and amendment",
        ready_to_answer=True,
        actions=[]
    )
    # Canned final answer
    final_ans = Answer(
        status="answered",
        answer="Employees can work remotely up to 4 days per week under Amendment 1 (p. 9), which supersedes the earlier 3 days limit (p. 4).",
        evidence=[
            EvidenceItem(page=9, quote="remote work increases to 4 days per week", supports="current remote allowance")
        ],
        conflicts=[
            ConflictItem(
                topic="remote days",
                chosen=ConflictChosen(page=9, quote="remote work increases to 4 days per week"),
                superseded=[ConflictChosen(page=4, quote="Remote work is permitted up to 3 days per week")],
                resolution_rule="amendment_or_errata"
            )
        ]
    )

    fake_llm = FakeLLM(scripted_responses=[dec1, dec2, dec3, final_ans])
    ctrl = AgentController(
        gateway=gw,
        llm=fake_llm,
        session_id="sess_1",
        doc_id="doc1",
        num_pages=11
    )

    res = ctrl.run("How many days per week can employees work remotely?")
    assert res.answer_obj.status == "answered"
    # list_headings (1) + search_keyword (2) + get_page 4 (3) + get_page 9 (4) = 4 calls
    assert budget.used <= 6
    assert len(res.answer_obj.evidence) == 1
    assert res.verification["v1_quotes_valid"] == 1

def test_controller_adversarial_llm_cannot_break_budget(seeded_repo):
    backend = ToolBackend(seeded_repo)
    budget = Budget(max_calls=6)
    gw = ToolGateway(backend, 'doc1', budget=budget)
    
    # Adversarial LLM proposes 50 calls, bad tools, range exploits
    adversarial_llm = FakeLLM(adversarial_mode=True)
    ctrl = AgentController(
        gateway=gw,
        llm=adversarial_llm,
        session_id="sess_adv",
        doc_id="doc1",
        num_pages=11
    )

    # Controller should not crash, must respect budget <= 6, and strip injection
    res = ctrl.run("What is the policy?")
    assert budget.used <= 6
    # Injection echo stripped -> downgraded to insufficient
    assert res.answer_obj.status == "insufficient"