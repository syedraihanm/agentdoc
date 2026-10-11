import re

# Optional harmless trailing words/punctuation, e.g. "hi there!", "thanks so much."
_TAIL = r'(\s+(there|all|team|pageturner|bot|so\s+much|a\s+lot|again))*\s*[!.?,]*\s*$'

SMALLTALK_PATTERNS = [
    (re.compile(r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))' + _TAIL, re.IGNORECASE),
     "Hello! I am PageTurner, an autonomous document assistant. I can answer questions about your uploaded PDF using metered tools under a strict 6-call budget. How can I help you today?"),
    (re.compile(r'^\s*(thanks|thank\s+you|thx|cheers|ok\s+thanks)' + _TAIL, re.IGNORECASE),
     "You're very welcome! Let me know if you have any other questions about the document."),
    (re.compile(r'^\s*(who\s+are\s+you|what\s+are\s+you|introduce\s+yourself)' + _TAIL, re.IGNORECASE),
     "I am PageTurner, a budgeted document-answering agent. I inspect documents using strict metered tools (list headings, search keywords, get page) without vector databases or embeddings."),
    (re.compile(r'^\s*(what\s+can\s+you\s+do|how\s+do\s+you\s+work|help)' + _TAIL, re.IGNORECASE),
     "You can ask me any question about your uploaded PDF. I will systematically plan searches, read relevant pages within a hard 6-call budget, verify verbatim evidence quotes, and provide transparent answers.")
]

def check_smalltalk(question: str) -> str | None:
    """Returns a canned reply ONLY if the whole message is smalltalk.
    'Hi, what is the refund window?' is NOT smalltalk and goes to the agent."""
    q = question.strip()
    for pattern, response in SMALLTALK_PATTERNS:
        if pattern.match(q):
            return response
    return None