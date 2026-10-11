import pymupdf

def extract_tables_as_markdown(page: pymupdf.Page) -> str | None:
    try:
        tabs = page.find_tables()
        if not tabs or len(tabs.tables) == 0:
            return None
        
        md_tables = []
        for tab in tabs.tables:
            df = tab.extract()
            if not df or len(df) < 2:
                continue
            # Header
            header = [str(c or '').replace('\n', ' ').strip() for c in df[0]]
            md = ['| ' + ' | '.join(header) + ' |']
            md.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
            # Rows
            for row in df[1:]:
                cells = [str(c or '').replace('\n', ' ').strip() for c in row]
                md.append('| ' + ' | '.join(cells) + ' |')
            md_tables.append('\n'.join(md))
        
        if md_tables:
            return '\n\n' + '\n\n'.join(md_tables)
        return None
    except Exception:
        return None
