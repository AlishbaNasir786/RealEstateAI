/**
 * competitor_sse.js
 * Connects to /api/run_competitor_engine via Server-Sent Events,
 * parses the engine's real progress-bar output, and drives the UI.
 *
 * The engine prints lines like:
 *   📊 [██████████░░░░░░░░░░] 45.0%  SALE Houses_Islamabad (9/20 segments)
 * We extract the percentage from those lines.
 */

document.addEventListener('DOMContentLoaded', () => {
  const runBtn      = document.getElementById('runScrapeBtn');
  const progressBox = document.getElementById('scrapeProgress');
  const progressText= document.getElementById('progressText');
  const progressFill= document.getElementById('progressFill');
  const logArea     = document.getElementById('logArea');
  const reportIframe= document.getElementById('reportIframe');

  if (!runBtn) return;

  runBtn.addEventListener('click', () => {
    // Disable button & show progress panel
    runBtn.disabled = true;
    progressBox.classList.add('visible');
    if (logArea) logArea.classList.add('visible');
    progressText.textContent = '0% — Connecting to scraper…';
    progressFill.style.width = '0%';
    if (logArea) logArea.textContent = '';

    let lastPct = 0;

    const evtSource = new EventSource('/api/run_competitor_engine');

    evtSource.onmessage = (event) => {
      const line = event.data;

      // ── Finished ────────────────────────────────────────────
      if (line.includes('[DONE]')) {
        progressText.textContent = '100% — Scrape complete! Refreshing report…';
        progressFill.style.width = '100%';
        evtSource.close();

        // Reload the iframe with a cache-buster so the new report shows
        setTimeout(() => {
          reportIframe.src =
            reportIframe.src.split('?')[0] + '?t=' + Date.now();
          // Keep progress visible briefly so user sees "100%"
          setTimeout(() => {
            progressBox.classList.remove('visible');
            if (logArea) logArea.classList.remove('visible');
            runBtn.disabled = false;
          }, 2000);
        }, 500);
        return;
      }

      // ── Error ───────────────────────────────────────────────
      if (line.includes('[ERROR]')) {
        progressText.textContent = 'Error during scraping. Check server logs.';
        progressFill.style.width = lastPct + '%';
        evtSource.close();
        runBtn.disabled = false;
        return;
      }

      // ── Try to extract a percentage from the engine's progress bar ──
      //    Pattern: "45.0%" somewhere in the line
      const pctMatch = line.match(/([\d.]+)%/);
      if (pctMatch) {
        const pct = Math.min(100, parseFloat(pctMatch[1]));
        if (pct > lastPct) lastPct = pct;
        progressText.textContent = `${lastPct.toFixed(1)}% — Scraping Zameen.com…`;
        progressFill.style.width = lastPct + '%';
      }

      // ── Append to live log (trimmed) ────────────────────────
      if (logArea && line.trim()) {
        logArea.textContent += line.trim() + '\n';
        logArea.scrollTop = logArea.scrollHeight;   // auto-scroll
      }
    };

    evtSource.onerror = () => {
      evtSource.close();
      if (lastPct >= 95) {
        // Likely finished just before the connection closed
        progressText.textContent = '100% — Completed!';
        progressFill.style.width = '100%';
        setTimeout(() => {
          reportIframe.src =
            reportIframe.src.split('?')[0] + '?t=' + Date.now();
          progressBox.classList.remove('visible');
          if (logArea) logArea.classList.remove('visible');
          runBtn.disabled = false;
        }, 1500);
      } else {
        progressText.textContent = 'Connection lost. Try again.';
        runBtn.disabled = false;
      }
    };
  });
});
