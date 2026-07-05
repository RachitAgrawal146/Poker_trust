#!/usr/bin/env python3
"""
build_prose_docx.py -- generate a prose-only Word (.docx) version of the paper.

Produces main_prose.docx: the running narrative (Abstract + Introduction
through Conclusion) with everything non-prose removed:
  * figures / charts and their captions
  * all tables (including the story-hand boxes)
  * display equations
  * footnotes
  * in-text citations and the reference list
  * back matter (Acknowledgments / References / Supplementary)

Kept: title, author, abstract, section headings, and all body prose.
Cross-references to floats are resolved to plain numbers ("Figure 2",
"Eq. 5", "Section 3.2") so the sentences still read normally; inline math
inside sentences (e.g. r_tp = -0.752) is preserved.

Run: python3 build_prose_docx.py   (requires pandoc)
Output: main_prose.docx (next to main.tex).
"""
import re, pathlib, subprocess, sys, tempfile

MAN = pathlib.Path(__file__).resolve().parent
src = (MAN / 'main.tex').read_text()

def strip_cmd(s, cmd):
    """Remove every occurrence of cmd{...} with balanced braces (e.g. \\footnote)."""
    out, i, n, L = [], 0, len(s), len(cmd)
    while i < n:
        if s.startswith(cmd, i) and i + L < n and s[i + L] == '{':
            depth, j = 0, i + L
            while j < n:
                if s[j] == '{': depth += 1
                elif s[j] == '}':
                    depth -= 1
                    if depth == 0: break
                j += 1
            i = j + 1
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

# 1. inline \input so float numbering is correct
src = re.sub(r'\\input\{([^}]+)\}',
             lambda m: (MAN / m.group(1)).resolve().read_text(), src)

# 2. title block -> title/author + abstract
TITLE = ("Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation "
         "Study of Bayesian Reputation Systems in 8-Player Limit Texas Hold'em")
AUTHOR = r"Rachit Agrawal\\ \normalsize Independent research, 2025--2026."
ABSTRACT = (
 r"Reputation systems that infer trustworthiness from observed behavior are "
 r"widespread in online marketplaces, social networks, and financial platforms, "
 r"where prior empirical work documents a \textit{transparency paradox}: agents "
 r"with perfectly visible cooperative records sometimes earn lower returns than "
 r"agents with imperfect records. We provide a controlled generative test of this "
 r"dynamic in a simulation of 8-player fixed-limit Texas Hold'em poker in which "
 r"every agent maintains a categorical posterior over the archetype of every "
 r"other agent and updates it after each observed action. We deploy four agent "
 r"architectures against the same game environment and posterior: frozen "
 r"rule-based archetypes, bounded online hill-climbing, large-language-model "
 r"role-players, and language models augmented with chain-of-thought, "
 r"per-opponent memory, and self-updated strategy notes. Across 5 random seeds "
 r"per phase, the Pearson correlation between trust and final stack falls along a "
 r"four-tier ladder ($\rtp = -0.752 \pm 0.073$; $-0.637 \pm 0.125$; "
 r"$-0.510 \pm 0.268$; $-0.094 \pm 0.301$); the 95\% bootstrap interval for the "
 r"final tier is $[-0.32, +0.20]$, consistent with substantial but not "
 r"necessarily complete attenuation. A sub-experiment with unbounded "
 r"hill-climbing at $11\times$ greater parameter drift shifts the correlation by "
 r"only $+0.028$, evidence against the hypothesis that the trap is a bound-box "
 r"artifact in this simulation. We interpret the results as preliminary evidence "
 r"that, in our zero-sum testbed, observation-based reputation rewards "
 r"exploitation under simple agent policies and that reasoning scaffolds "
 r"substantially attenuate the effect; whether the attenuation reflects a "
 r"structural property of reasoning or a small-sample artifact of the Phase 3.1 "
 r"run ($n=5$ seeds, 150 hands/seed) is left to a larger replication.")
src = re.sub(r'\\twocolumn\[.*?\\thispagestyle\{firstpage\}',
             lambda m: '\\begin{abstract}\n' + ABSTRACT + '\n\\end{abstract}',
             src, count=1, flags=re.S)

# 3. number map (document order) + section refs, then resolve \ref
labmap, fig, tab, eq, cur = {}, 0, 0, 0, None
for m in re.finditer(r'\\begin\{(figure\*?|table\*?|equation)\}|\\label\{([^}]+)\}', src):
    env, lab = m.group(1), m.group(2)
    if env:
        if env.startswith('figure'): fig += 1; cur = ('fig', fig)
        elif env.startswith('table'): tab += 1; cur = ('tab', tab)
        else: eq += 1; cur = ('eq', eq)
    elif lab and cur:
        labmap[lab] = cur; cur = None
labmap.update({'sec:results': ('sec', '4'), 'sec:archetypes': ('sec', '3.2'),
               'sec:posterior': ('sec', '3.3')})
src = re.sub(r'\\ref\{([^}]+)\}', lambda m: str(labmap.get(m.group(1), ('?', '?'))[1]), src)
src = re.sub(r'\\label\{[^}]+\}', '', src)

# 4. strip non-prose environments
src = re.sub(r'\\begin\{tcolorbox\}.*?\\end\{tcolorbox\}', '', src, flags=re.S)
src = re.sub(r'\\begin\{(figure\*?|table\*?)\}.*?\\end\{\1\}', '', src, flags=re.S)
src = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', src, flags=re.S)

# 5. strip footnotes (balanced) and citations (+ preceding space)
src = strip_cmd(src, r'\footnote')
src = re.sub(r'\s*\\citep\{[^}]*\}', '', src)
src = re.sub(r'\s*\\citet\{[^}]*\}', '', src)

# 6. strip back matter (Sources / References / Supplementary)
src = re.sub(r'\\section\*\{Sources and Acknowledgments\}.*?\\end\{document\}',
             r'\\end{document}', src, flags=re.S)

# 7. tidy stray layout commands
for cmd in (r'\FloatBarrier', r'\centering', r'\nopagebreak'):
    src = src.replace(cmd, '')
src = re.sub(r'\\captionsetup\{[^}]*\}', '', src)

# 8. flatten archetype macros to prose (drop the numeric bound line, #5)
inject = ('\\title{' + TITLE + '}\n\\author{' + AUTHOR + '}\n\\date{}\n'
          r'\renewcommand{\arch}[1]{\textbf{#1}}' + '\n'
          r'\renewcommand{\bbar}{ --- }' + '\n'
          r'\renewcommand{\archentry}[5]{\par\medskip\noindent\textbf{#1} --- '
          r'\textit{#2} (honesty #3). #4\par}' + '\n'
          '\\begin{document}')
src = src.replace('\\begin{document}', inject, 1)

# ---------------------------------------------------------------- write + pandoc
tmp = pathlib.Path(tempfile.mkdtemp()) / 'main_prose.tex'
tmp.write_text(src)
out = MAN / 'main_prose.docx'
cmd = ['pandoc', str(tmp), '-o', str(out), '--number-sections']
print('pandoc:', ' '.join(cmd))
r = subprocess.run(cmd)
if r.returncode == 0:
    print(f'wrote {out}')
sys.exit(r.returncode)
