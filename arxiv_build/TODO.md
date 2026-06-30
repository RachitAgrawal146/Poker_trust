# TODO.md — author action items

The bundle is built from your final paraphrased manuscript and compiles cleanly
offline with **zero errors and zero undefined-reference warnings**. The one
required fix is done; what remains are optional consistency calls only you can
make.

## ✅ 1. "Figure ??" dangling reference — FIXED

Done in this revision (on your instruction). The broken clause
`Figure~\ref{fig:pd} illustrates these four possible outcomes using the framing
of Nicky Case's \textit{Evolution of Trust} interactive:` was deleted and the
next word capitalized. The sentence now reads:

> "…When both prisoners select option (B), i.e., defect, neither receives any
> reward. **Mutual cooperation provides a reward of +2** to both players; mutual
> defection provides a reward of 0…"

No "Figure ??" remains; the compile has no undefined references. This also
removed the last textual tie to the borrowed figure.

## 2. (Optional, not a blocker) Affiliation consistency

The title page says "Independent research, 2025–2026" while you're submitting
from your school email / put your school on the arXiv form. arXiv accepts
"Independent research" fine — this is purely a consistency call. Pick one
identity and make the paper and the form agree. (Keeping "Independent research"
is defensible if the school didn't supervise the Polygence work.) **Not changed
— your call; left exactly as written.**

## 3. (Optional, not a blocker) Abstract register

The abstract is more colloquial than a typical cs.GT abstract ("petri-dish,"
"swapped the minds of the agents"). arXiv has no style rules, so this is a
voice/first-impression decision, not a compliance issue. **Not changed — left
exactly as written; revise only if you want to.**

## Non-issues (verified, no action)

- **Hardcoded figure/table numbers:** none — every reference uses `\ref{…}`.
- **shell-escape / biblatex / EPS:** none — builds `-no-shell-escape`, BibTeX +
  natbib frozen to `main.bbl`, all figures PNG.
- **Reference DOIs/URLs:** none in the source; arXiv doesn't require them (add
  upstream and re-freeze the `.bbl` if you want clickable links).

After uploading: form → primary class **cs.GT** → endorsement → finalize. (Noted
from your message: sole-authored, so the endorser route differs from a co-author
submission — confirm the under-18 consent path is sorted before starting.)
