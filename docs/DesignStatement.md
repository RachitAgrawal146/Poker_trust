# Design Statement

> A north-star brief for design work in the Rachit Agrawal voice. This
> document is the **why**. The companion file `DesignCues` is the
> **how** (tokens, type scale, component CSS). Read this first when
> starting any new artifact — page, slide, diagram, paper figure,
> visualizer, or README. Read `DesignCues` when you are ready to
> commit values to pixels.
>
> Audited from two source artifacts:
> 1. `RachitAgrawal146/Rachitagrawal146.github.io-` — the personal
>    portfolio.
> 2. `RachitAgrawal146/game-algorithms-java` — the algorithms
>    laboratory.
>
> Both are the work of the same author. The voice is consistent across
> both. This statement is the distilled spine of that voice.

---

## 1. The one-line statement

**Quiet rigor, rendered in dark editorial.**

Every artifact should look like a page from a literary journal that
happens to be reporting on an experiment. Substance first, restraint
in the framing, one warm point of light against a deliberate dark
field. The reader should feel they have walked into a room where
someone is thinking carefully — not a room being marketed at them.

## 2. Five operating principles

These are the load-bearing ideas. Every design decision should be
traceable to one of them; if a decision violates one, it is the
decision that is wrong.

### 2.1 Laboratory, not showroom

The work is research. Frame it that way. Lead with the question, the
method, and the empirical finding — not with the product, the brand,
or the call to action. The portfolio's hero is a thought
("*I grew up learning to sit with things I didn't understand yet.*")
not a value proposition. The algorithms repo opens with "This isn't a
collection of tutorials. It's a laboratory." Match that register.

Implication: every page has a thesis. Every section has a finding.
Numbers and benchmarks are first-class content, not appendix material.

### 2.2 Restraint is the aesthetic

One accent colour (gold). Two type families doing real work (Cormorant
Garamond italic for display, DM Mono for labels), one sans for body
prose (Inter). No gradients except the gold sweep. No emoji. No
badges. No hero illustrations. No drop shadows except as light
sources. If you can remove a visual element and the meaning survives,
remove it.

The discipline mirrors the algorithms repo's "no external libraries,
all data structures from scratch" stance. In design as in code: you
earn the right to add a thing by demonstrating it does load-bearing
work.

### 2.3 Gold is light, never fill

The accent (`#c9a96e`) is treated as a light source — used for thin
borders, single-character emphasis inside a serif heading, hairline
underlines on hover, a glow behind a portrait, the cursor of a
typewriter animation, the leading `›` of a list item. Never as a
solid button background, never as a flood fill, never as a tint on
a large surface. The moment gold becomes mass, the page stops feeling
like a print object and starts feeling like a marketing page.

### 2.4 Slow time

Reveals run 0.7s. The hero typewriter takes a full second to settle.
The portrait halo breathes on a 6s cycle. Hover states fade in 300ms,
not 80. Nothing snaps, nothing bounces, nothing pops. The motion
language says: *this thing was made by a person who is willing to
wait, and who expects you to be too.* The same principle applies in
copy: long sentences are allowed, paragraphs may end on a quiet beat,
a section is permitted to contain only a single italicized line.

When in doubt, slow it down by 50%.

### 2.5 The page breathes from the left

Never centre-align body content by default. The text column is 760px
(780px on detail pages), set against a dark field, with section
numbers and mono labels hanging in the left margin like marginalia in
a book. Centring is reserved for the hero name and for ceremonial
moments. This is what gives every page the feeling of being read
rather than scanned.

## 3. The reader we are designing for

Not "users." Not "visitors." A **reader** — someone willing to spend
two minutes on a paragraph if the paragraph is worth two minutes.

Concretely: a reviewer skimming a research paper, a colleague opening
a project README, an admissions reader, a fellow practitioner. Not a
casual scroller, not a click-through funnel, not a marketing audience.

This audience model has consequences:
- Long-form prose is welcome. Don't compress every idea into bullet
  points.
- Technical density is a feature, not a wall. Show the benchmark,
  show the equation, name the algorithm.
- The CTA at the end of a page is allowed to be small. *"Let's talk."*
  is the entire contact section.
- Loading states, empty states, and error states should still feel
  like the same publication. Skeletons in dim grey, not spinners.

## 4. Voice & copy

**Tone:** contemplative, precise, occasionally vulnerable. Italics
carry weight; do not waste them.

**Rules of thumb:**
- Em dashes (` &mdash; `) with spaces, never hyphens for emphasis.
- Curly quotes always. Straight quotes are a tell that nobody read
  the page.
- One italicized phrase per heading at most. Usually that phrase is
  in gold.
- Numbered sections (`01 — About`, `02 — Approach`). The number is
  part of the identity, not chrome.
- Findings are stated as findings, not as marketing claims.
  "94.2% pruning efficiency at depth 10" is good. "Blazing fast" is
  a violation.
- A section is allowed to consist of one sentence if that sentence
  carries the weight.

**Forbidden register:** startup-deck enthusiasm, "we believe" mission
statements, hype adjectives ("revolutionary," "powerful," "seamless"),
exclamation points in body copy, hand-wave verbs ("leverage,"
"unlock," "empower").

## 5. Structural patterns

These are the recurring shapes. New pages should compose from them
rather than invent new shapes.

| Shape | When to use |
|---|---|
| **Numbered section with mono label + serif italic title** | Default for every section that isn't the hero. |
| **Insight box** (gold hairline border, ghost gold wash, "Key Insight" mono label) | When a paragraph is the single most important thing in the section. One per section maximum. |
| **Currently / pinned card** (gold ring, corner accents, "pinned" label) | The single live status item on a page. Not a list. |
| **Dense data table** (mono header, hairline rows, hover-to-gold) | Empirical results. Comparison studies. Benchmark grids. |
| **Reveal-on-scroll list** (80ms staggered, 30px translate) | Project lists, timeline items, anything sequential. |
| **Hairline divider** (`border-top: 0.5px solid rgba(255,255,255,0.07)`) | Between major sections. Never a solid rule. |

## 6. Choices to default to (and choices to refuse)

**Default to:**
- Dark theme. There is no light mode and there should not be one.
- The 760px content column.
- A single accent. If a design needs a second accent, the design is
  doing too much.
- Noise texture overlay (`opacity: 0.035`) on every page. This is
  what makes the black feel like paper.
- Mono labels above serif headings.
- Anchor-style navigation (in-page) over multi-page funnels.

**Refuse:**
- Light backgrounds.
- Coloured fill on buttons or surfaces.
- Sans-serif headings (the serif italic is the signature; do not
  trade it away for "modern").
- Multi-column body layouts. The single column is intentional.
- Stock photography. Personal photography only, treated like plates
  in a monograph.
- Chart libraries used at default settings. If a chart is included,
  it is restyled to the palette.
- Cookie banners, popups, modals over content.

## 7. Cross-medium application

The voice is not a website skin. It applies wherever the work
appears.

- **Research papers / PDFs:** Cormorant Garamond for body if license
  permits, otherwise EB Garamond; section numbers in mono in the
  margin; figures in dark theme with gold series colour.
- **Slides / talks:** one idea per slide, italic display heading,
  body in Inter at large weight, no slide template chrome.
- **Diagrams (architecture, decision trees, agent graphs):** dark
  background, hairline edges, gold for the active path or the unit
  under discussion, mono labels for nodes, no rounded boxes with
  fills.
- **Visualizers / interactive demos** (e.g. the poker
  `visualizer/poker_table.html`): the same colour and type tokens
  apply; data is rendered in mono with hairline rules; transitions
  honour the slow-time principle.
- **READMEs:** open with the thesis, not the install command. Tables
  for empirical results. Em dashes. No emoji. No badges.
- **Commit messages and changelogs:** the same restraint and
  precision applies; one-line subject, blank line, prose body that
  states what changed and why.

## 8. The decision rule

When two design options both seem defensible, prefer the one that is:

1. **Quieter** &mdash; less motion, less colour, less ornament.
2. **More literal** &mdash; the label says what the thing is, not what
   it gestures toward.
3. **Slower** &mdash; longer fade, more whitespace, more breathing
   room around it.
4. **More empirical** &mdash; a number where a number can stand in
   for a claim.
5. **More personal** &mdash; written in the first person, signed,
   located ("from Ranchi," "Grade 12, Sahyadri").

If an option wins on all five, ship it. If it loses on three or
more, redesign it.

---

*This statement is intentionally short. The full token reference,
component CSS, animation specs, and breakpoint rules live in
`DesignCues`. Read both.*
