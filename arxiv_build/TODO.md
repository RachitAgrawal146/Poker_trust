# TODO.md — author action items (nothing here is for the bundler to write)

The bundle is built from your **final paraphrased manuscript** (the exact source
of `main5_updated_1.pdf`) and compiles cleanly offline. The items below are
prose / rights decisions only you can make. No wording was changed.

## 1. Figure 1 removed — one sentence still references it  *(required)*

Figure 1 (`00_game_of_trust.png`, a screenshot of Nicky Case's *Evolution of
Trust*) was removed — it is borrowed third-party content arXiv does not permit.
Its float and `\label{fig:pd}` are gone, and the remaining figures
auto-renumbered to 1–6.

But the body still points at it with `\ref{fig:pd}`, which now prints as
**"Figure&nbsp;??"**. The sentence to revise is at **`main.tex` line 420**
("Cooperation in repeated games" subsection):

> "When both prisoners select option (B), i.e., defect, neither receives any
> reward. **Figure~\ref{fig:pd} illustrates these four possible outcomes using
> the framing of Nicky Case's \textit{Evolution of Trust} interactive:** mutual
> cooperation provides a reward of $+2$ to both players; mutual defection
> provides a reward of $0$ to both players; and unilaterally defecting against a
> cooperator provides a reward of $+3$ to the defector and a loss of $-1$ to the
> cooperator."

**Decide / write (your words):** delete the `Figure~\ref{fig:pd} illustrates
these four possible outcomes using the framing of Nicky Case's \textit{Evolution
of Trust} interactive:` clause, or replace it with your own non-borrowed
framing. The payoff values ($+2$/$0$/$+3$/$-1$) stand on their own. Until then
the PDF shows "Figure&nbsp;??" here — a LaTeX *warning*, not an error, so arXiv
will still accept and build the submission.

## 2. Hardcoded figure/table numbers — none found  *(no action)*

Every figure/table reference uses `\ref{…}`, so numbering updates automatically.
No hardcoded "Figure 2"/"Table 3" strings in the prose.

## 3. shell-escape / biblatex / figure-format blockers — none  *(no action)*

No `minted`/`\write18` (builds with `-no-shell-escape`); bibliography is
BibTeX + natbib frozen to `main.bbl` (no biber); all figures are PNG (no EPS).

## 4. (Optional, not arXiv-blocking) references have no DOIs/URLs

`references.bib` has 17 entries and no DOI/URL fields. arXiv does not require
them; add them upstream and re-freeze the `.bbl` if you want clickable links.
