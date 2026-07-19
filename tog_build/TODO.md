# TODO.md — author decisions before ToG upload

1. **Index Terms (required — blocks upload).** Replace the
   `[TODO-INDEX-TERMS: ...]` marker in `tog_submission/main.tex` with 4–6
   terms. Candidates drawn from your own text: trust, reputation, poker,
   Bayesian, agents, simulation, multi-agent.

2. **Confirm/adjust the relocation set (provisionally endorsed).** Moved:
   Box 1 → S1, Box 2 → S2, primer table → Table S1, TMA figure → Figure S1,
   plus the supplementary pointer list. The main text hit 10/10 pages with
   this set plus two table-width reflow fixes — no further moves needed.
   If you want any of the four back in the main text, the page gate will
   fail again (M0 with everything in main = 12 pages).

3. **Broader Impact Statement — AUTHOR-DECISION (measured).** Default
   applied: KEEP in main as `\section*` before References.
   - keep in main: 10 pages (current) — **costs nothing**
   - move to supplementary: still 10 pages (measured) — saves nothing, only adds slack
   - drop: still 10 pages (measured) — saves nothing
   Recommendation implicit in the numbers: keep.

4. **Abstract version.** Per the port spec, the abstract is byte-identical
   to the TMLR input — i.e., the **plain-language** abstract. Note that the
   arXiv build (`arxiv_build/finalpaper.pdf`) now carries your newer hedged
   technical abstract. Decide whether ToG should keep the plain-language
   version or receive the technical one; if the latter, say so and it will
   be swapped with the same verbatim+house-style mechanics as the arXiv pass
   (page impact will be re-measured — it is ~75% longer).

5. **"The author(s) declare" one-worder** from the TMLR pass is still
   AWAITING-AUTHOR-APPROVAL and applies verbatim here too
   (`tog_submission/main.tex`, Competing interests paragraph).

6. No `[TODO-SEAM]` markers exist (no approved cuts were supplied), and no
   TRIM_MAP decisions are pending (the page gate passed structurally).
