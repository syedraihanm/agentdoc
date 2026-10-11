import React, { useState } from 'react';
import { DocumentItem } from './lib/api';
import { UploadPage } from './pages/UploadPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvalPage } from './pages/EvalPage';

export function App() {
  const [currentDocs, setCurrentDocs] = useState<DocumentItem[]>([]);
  const [view, setView] = useState<'upload' | 'workspace' | 'eval'>('upload');

  const handleDocsSelected = (docs: DocumentItem[]) => {
    setCurrentDocs(docs);
    setView('workspace');
  };

  if (view === 'eval') {
    return (
      <EvalPage
        onBack={() => setView(currentDocs.length > 0 ? 'workspace' : 'upload')}
        activeDocId={currentDocs[0]?.doc_id}
      />
    );
  }

  if (currentDocs.length === 0 || view === 'upload') {
    return (
      <UploadPage
        onDocumentsSelected={handleDocsSelected}
        onNavigateToEval={() => setView('eval')}
      />
    );
  }

  return (
    <WorkspacePage
      docs={currentDocs}
      onReplaceDoc={() => setView('upload')}
      onNavigateToEval={() => setView('eval')}
    />
  );
}

export default App;