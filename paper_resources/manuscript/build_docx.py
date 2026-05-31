#!/usr/bin/env python3
"""
build_docx.py -- generate an editable Word (.docx) version of the paper.

Converts main.tex -> main.docx via pandoc. Because the manuscript uses a
Science-style two-column title block, custom macros (\arch, \archentry,
\bbar, \rtp), tcolorbox story hands, and LaTeX \ref cross-references --
none of which survive a naive pandoc run -- this script first rewrites the
source into a pandoc-friendly form:

  * the \twocolumn[...] title block becomes \title/\author + abstract;
  * \input table files are inlined;
  * \arch{Name} is expanded to the archetype's brand hex color (bold);
  * \archentry / \bbar / tcolorbox are flattened to plain text + headings;
  * every figure/table/equation is numbered and its \ref{} is resolved to
    that number, with "Figure N." / "Table N." prefixed onto each caption;
  * citations are rendered numbered (IEEE) with a reference list.

Requires: pandoc (with citeproc). Run from anywhere:
    python3 build_docx.py
Output: main.docx (next to main.tex).
"""
import re, pathlib, subprocess, sys, tempfile

MAN = pathlib.Path(__file__).resolve().parent
src = (MAN / 'main.tex').read_text()

# ---------------------------------------------------------------- 1. inline \input
src = re.sub(r'\\input\{([^}]+)\}',
             lambda m: (MAN / m.group(1)).resolve().read_text(), src)

# ---------------------------------------------------------------- 2. title block
TITLE = ("Trust Dynamics in Multi-Agent Strategic Interaction: A Simulation "
         "Study of Bayesian Reputation Systems in 8-Player Limit Texas Hold'em")
AUTHOR = (r"Rachit Agrawal\\ \normalsize Independent research, 2025--2026.\\ "
          r"\normalsize Correspondence: rachit.agrawal@sahyadrischool.org")
ABSTRACT = (
 r"Reputation systems that infer trustworthiness from observed behavior are "
 r"widespread in online marketplaces, social networks, and financial platforms, "
 r"where prior empirical work \citep{resnick2002trust,bolton2004effective} "
 r"documents a \textit{transparency paradox}: agents with perfectly visible "
 r"cooperative records sometimes earn lower returns than agents with imperfect "
 r"records. We provide a controlled generative test of this dynamic in a "
 r"simulation of 8-player fixed-limit Texas Hold'em poker in which every agent "
 r"maintains a categorical posterior over the archetype of every other agent and "
 r"updates it after each observed action. We deploy four agent architectures "
 r"against the same game environment and posterior: frozen rule-based archetypes, "
 r"bounded online hill-climbing, large-language-model role-players, and language "
 r"models augmented with chain-of-thought, per-opponent memory, and self-updated "
 r"strategy notes. Across 5 random seeds per phase, the Pearson correlation "
 r"between trust and final stack falls along a four-tier ladder "
 r"($\rtp = -0.752 \pm 0.073$; $-0.637 \pm 0.125$; $-0.510 \pm 0.268$; "
 r"$-0.094 \pm 0.301$); the 95\% bootstrap interval for the final tier is "
 r"$[-0.32, +0.20]$, consistent with substantial but not necessarily complete "
 r"attenuation. A sub-experiment with unbounded hill-climbing at $11\times$ "
 r"greater parameter drift shifts the correlation by only $+0.028$, evidence "
 r"against the hypothesis that the trap is a bound-box artifact in this "
 r"simulation. We interpret the results as preliminary evidence that, in our "
 r"zero-sum testbed, observation-based reputation rewards exploitation under "
 r"simple agent policies and that reasoning scaffolds substantially attenuate "
 r"the effect; whether the attenuation reflects a structural property of "
 r"reasoning or a small-sample artifact of the Phase 3.1 run ($n=5$ seeds, "
 r"150 hands/seed) is left to a larger replication.")

_abs = '\\begin{abstract}\n' + ABSTRACT + '\n\\end{abstract}'
src = re.sub(r'\\twocolumn\[.*?\\thispagestyle\{firstpage\}',
             lambda m: _abs, src, count=1, flags=re.S)

preamble_inject = ('\\title{' + TITLE + '}\n\\author{' + AUTHOR + '}\n\\date{}\n'
                   '\\begin{document}')
src = src.replace('\\begin{document}', preamble_inject, 1)

# ---------------------------------------------------------------- 3. tcolorbox -> heading + text
src = re.sub(r'\\begin\{tcolorbox\}\[storyhand=\{(.*?)\}\]',
             r'\\par\\medskip\\noindent\\textbf{\1}\\par\\medskip', src, flags=re.S)
src = src.replace(r'\end{tcolorbox}', r'\par\medskip')

# ---------------------------------------------------------------- 4. number map (document order)
labmap, fig, tab, eq, cur = {}, 0, 0, 0, None
for m in re.finditer(r'\\begin\{(figure\*?|table\*?|equation)\}|\\label\{([^}]+)\}', src):
    env, lab = m.group(1), m.group(2)
    if env:
        if env.startswith('figure'): fig += 1; cur = ('fig', fig)
        elif env.startswith('table'): tab += 1; cur = ('tab', tab)
        else: eq += 1; cur = ('eq', eq)
    elif lab and cur:
        labmap[lab] = cur; cur = None
labmap['sec:results'] = ('sec', '4')      # pandoc --number-sections numbering
labmap['sec:archetypes'] = ('sec', '3.2')
labmap['sec:posterior'] = ('sec', '3.3')

# ---------------------------------------------------------------- 5. prefix captions
def _float_repl(m):
    whole, body = m.group(0), m.group(2)
    lm = re.search(r'\\label\{([^}]+)\}', body)
    if lm and lm.group(1) in labmap:
        typ, num = labmap[lm.group(1)]
        kind = 'Figure' if typ == 'fig' else 'Table'
        return re.sub(r'\\caption\{',
                      r'\\caption{\\textbf{' + f'{kind}~{num}.' + r'}~', whole, count=1)
    return whole
src = re.sub(r'\\begin\{(figure\*?|table\*?)\}(.*?)\\end\{\1\}', _float_repl, src, flags=re.S)

# ---------------------------------------------------------------- 6. equations: append (N)
def _eq_repl(m):
    body = m.group(1)
    lm = re.search(r'\\label\{([^}]+)\}', body)
    num = labmap.get(lm.group(1), ('eq', '?'))[1] if lm else '?'
    body = re.sub(r'\s*\\label\{[^}]+\}', '', body).rstrip()
    return r'\begin{equation}' + body + r'\qquad(' + str(num) + ')\n' + r'\end{equation}'
src = re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}', _eq_repl, src, flags=re.S)

# ---------------------------------------------------------------- 7. resolve \ref, drop \label
src = re.sub(r'\\ref\{([^}]+)\}', lambda m: str(labmap.get(m.group(1), ('?', '?'))[1]), src)
src = re.sub(r'\\label\{[^}]+\}', '', src)

# ---------------------------------------------------------------- 8. archetype brand colors
HEX = {'Oracle':'A8B5C3','Sentinel':'5C8159','Firestorm':'E75D3C','Wall':'A2A7A9',
       'Phantom':'836F91','Predator':'B93C41','Mirror':'CDD3D8','Judge':'3F4F7C'}
src = re.sub(r'\\arch\{(\w+)\}',
             lambda m: r'\textcolor[HTML]{' + HEX.get(m.group(1), '333333')
                       + r'}{\textbf{' + m.group(1) + r'}}', src)

# ---------------------------------------------------------------- 9. flatten custom macros
renews = (r'\renewcommand{\bbar}{ \textbar{} }' + '\n'
          r'\renewcommand{\archentry}[5]{\par\medskip\noindent\textbf{#1} \textbar{} '
          r'\textit{#2} \textbar{} honesty #3. #4\ (#5)\par}' + '\n')
src = src.replace(preamble_inject, renews + preamble_inject, 1)

# ---------------------------------------------------------------- 10. image widths fit a page
src = re.sub(r'width=\\linewidth', 'width=14cm', src)
src = re.sub(r'width=0\.9\d*\\textwidth', 'width=15cm', src)

# ---------------------------------------------------------------- write + pandoc
tmp = pathlib.Path(tempfile.mkdtemp()) / 'main_pandoc.tex'
tmp.write_text(src)
out = MAN / 'main.docx'
cmd = ['pandoc', str(tmp), '-o', str(out), '--citeproc',
       '--csl=' + str(MAN / 'ieee.csl'), '--bibliography=' + str(MAN / 'references.bib'),
       '--number-sections', '--resource-path=' + str(MAN) + ':' + str(MAN.parent / 'figures')]
print('pandoc:', ' '.join(cmd))
r = subprocess.run(cmd)
if r.returncode == 0:
    print(f'wrote {out}  ({fig} figures, {tab} tables, {eq} equations)')
sys.exit(r.returncode)
