# TODO.md — author action items (nothing here is for the bundler to write)

The source bundle compiles cleanly offline and is arXiv-ready as-is (it will
build with a single "Figure&nbsp;??" placeholder). The items below are prose /
rights decisions that only you, the author, can make. I did **not** change any
wording — by policy and by your instruction.

## 1. Figure 1 removed — one sentence now references a figure that no longer exists  *(required)*

Figure 1 (`00_game_of_trust.png`, a screenshot of Nicky Case's *Evolution of
Trust*) was removed because it is borrowed third-party content arXiv does not
permit. Its `\begin{figure}…\end{figure}` float and `\label{fig:pd}` are gone.

The remaining figures **auto-renumbered 2–7 → 1–6** correctly. But the body
prose still points at the deleted figure with `\ref{fig:pd}`, which now prints
as **"Figure&nbsp;??"**. The exact sentence to revise is at **`main.tex` line
420** (in the "Cooperation in repeated games" subsection):

> "When both prisoners select option (B), i.e., defect, neither receives any
> reward. **Figure~\ref{fig:pd} illustrates these four possible outcomes using
> the framing of Nicky Case's \textit{Evolution of Trust} interactive:** mutual
> cooperation provides a reward of $+2$ to both players; mutual defection
> provides a reward of $0$ to both players; and unilaterally defecting against a
> cooperator provides a reward of $+3$ to the defector and a loss of $-1$ to the
> cooperator."

**What you need to decide / write (your words):**
- Remove the `Figure~\ref{fig:pd} illustrates these four possible outcomes using
  the framing of Nicky Case's \textit{Evolution of Trust} interactive:` clause,
  **or** replace it with your own non-borrowed framing. The payoff values that
  follow ($+2$/$0$/$+3$/$-1$) stand on their own and need no figure.
- Because the figure depicted **borrowed** content, also consider whether the
  two earlier mentions of the *Evolution of Trust* framing still read correctly
  without the image; they remain in the prose and were not altered.

Until this is edited, the PDF shows "Figure&nbsp;??" here (a LaTeX *warning*,
not an error — arXiv will still accept and build the submission).

## 2. Hardcoded figure/table numbers — none found  *(no action)*

Every figure and table reference in the manuscript uses `\ref{…}`, so LaTeX
renumbered them automatically. There are **no** hardcoded "Figure 2"/"Table 3"
strings in the prose to fix. (Verified against `main.tex` and the compiled
`.aux`.)

## 3. shell-escape / biblatex / figure-format blockers — none  *(no action)*

- No `minted`, `\write18`, or other shell-escape package — the document builds
  with `-no-shell-escape`.
- Bibliography is **BibTeX + natbib** (not biblatex/biber), frozen to
  `main.bbl`, which is the robust path for arXiv. No biber fragility.
- All figures are PNG (pdflatex-native); no EPS conversion was needed.

## 4. (Optional, not arXiv-blocking) references have no DOIs/URLs

`references.bib` has 17 entries and no DOI/URL fields, so the frozen
bibliography contains none. arXiv does not require them, but if you want
clickable links in the published version, add DOI/`https://` fields to the
`.bib` upstream and re-freeze the `.bbl`. *This is a content/metadata choice,
not a compile blocker.*
