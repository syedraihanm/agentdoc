import ast
from pathlib import Path

FORBIDDEN_AGENT_IMPORTS = {
    'fitz', 'pymupdf', 'sqlite3', 'PIL', 'pytesseract', 'pdfplumber', 'pypdf',
    'backend.app.ingestion', 'backend.app.storage', 'backend.app.tools.backend'
}

def check_imports_in_file(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in FORBIDDEN_AGENT_IMPORTS:
                    assert not alias.name.startswith(forbidden), f'Forbidden import in {path.name}: {alias.name}'
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            for forbidden in FORBIDDEN_AGENT_IMPORTS:
                assert not mod.startswith(forbidden), f'Forbidden import in {path.name}: from {mod} import ...'

def test_agent_import_boundary():
    agent_dir = Path(__file__).resolve().parent.parent.parent / 'app' / 'agent'
    if not agent_dir.exists():
        return
    py_files = list(agent_dir.rglob('*.py'))
    for f in py_files:
        check_imports_in_file(f)
