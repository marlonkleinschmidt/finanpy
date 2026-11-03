const analysisContent = document.getElementById('analysis-content');

if (analysisContent) {
  const collapsedKey = 'finanpy-analysis-collapsed';

  // O armazenamento pode estar bloqueado; nesse caso, a análise só não lembra a escolha.
  try {
    if (localStorage.getItem(collapsedKey) === 'true') {
      analysisContent.open = false;
    }
    analysisContent.addEventListener('toggle', () => {
      try {
        localStorage.setItem(collapsedKey, String(!analysisContent.open));
      } catch {}
    });
  } catch {}
}

const analysisForm = document.getElementById('analysis-form');

if (analysisForm) {
  const analysisButton = analysisForm.querySelector('button[type="submit"]');
  const analysisStatus = document.getElementById('analysis-form-status');

  const setAnalysisLoading = (loading) => {
    analysisButton.disabled = loading;
    analysisStatus.textContent = loading ? analysisForm.dataset.loadingMessage : '';
  };

  analysisForm.addEventListener('submit', () => setAnalysisLoading(true));
  // Ao voltar pelo histórico, o navegador pode restaurar a página como ficou no envio.
  window.addEventListener('pageshow', () => setAnalysisLoading(false));
}
