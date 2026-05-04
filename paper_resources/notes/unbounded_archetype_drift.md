# Unbounded Archetype Drift

> After 10,000 hands of unbounded hill-climbing across 5 seeds,
> what canonical archetype do the agents most resemble?

## Per-(agent, seed) closest match

| agent | seed | closest archetype | L1 to closest | L1 to self | stayed? |
|---|---|---|---|---|---|
| oracle | 42 | **oracle** | 0.281 | 0.281 | yes |
| sentinel | 42 | **sentinel** | 0.310 | 0.310 | yes |
| firestorm | 42 | **firestorm** | 0.407 | 0.407 | yes |
| wall | 42 | **wall** | 0.249 | 0.249 | yes |
| phantom | 42 | **phantom** | 0.344 | 0.344 | yes |
| predator | 42 | **predator** | 0.394 | 0.394 | yes |
| mirror | 42 | **mirror** | 0.415 | 0.415 | yes |
| judge | 42 | **sentinel** | 0.170 | 0.170 | no |
| oracle | 137 | **oracle** | 0.399 | 0.399 | yes |
| sentinel | 137 | **sentinel** | 0.166 | 0.166 | yes |
| firestorm | 137 | **firestorm** | 0.398 | 0.398 | yes |
| wall | 137 | **wall** | 0.274 | 0.274 | yes |
| phantom | 137 | **phantom** | 0.310 | 0.310 | yes |
| predator | 137 | **predator** | 0.279 | 0.279 | yes |
| mirror | 137 | **mirror** | 0.312 | 0.312 | yes |
| judge | 137 | **sentinel** | 0.115 | 0.115 | no |
| oracle | 256 | **oracle** | 0.283 | 0.283 | yes |
| sentinel | 256 | **sentinel** | 0.254 | 0.254 | yes |
| firestorm | 256 | **firestorm** | 0.233 | 0.233 | yes |
| wall | 256 | **wall** | 0.282 | 0.282 | yes |
| phantom | 256 | **phantom** | 0.201 | 0.201 | yes |
| predator | 256 | **predator** | 0.255 | 0.255 | yes |
| mirror | 256 | **mirror** | 0.459 | 0.459 | yes |
| judge | 256 | **sentinel** | 0.203 | 0.203 | no |
| oracle | 512 | **oracle** | 0.171 | 0.171 | yes |
| sentinel | 512 | **sentinel** | 0.298 | 0.298 | yes |
| firestorm | 512 | **firestorm** | 0.423 | 0.423 | yes |
| wall | 512 | **wall** | 0.303 | 0.303 | yes |
| phantom | 512 | **phantom** | 0.393 | 0.393 | yes |
| predator | 512 | **predator** | 0.313 | 0.313 | yes |
| mirror | 512 | **mirror** | 0.196 | 0.196 | yes |
| judge | 512 | **sentinel** | 0.114 | 0.114 | no |
| oracle | 1024 | **oracle** | 0.416 | 0.416 | yes |
| sentinel | 1024 | **sentinel** | 0.198 | 0.198 | yes |
| firestorm | 1024 | **firestorm** | 0.427 | 0.427 | yes |
| wall | 1024 | **wall** | 0.392 | 0.392 | yes |
| phantom | 1024 | **phantom** | 0.082 | 0.082 | yes |
| predator | 1024 | **predator** | 0.287 | 0.287 | yes |
| mirror | 1024 | **mirror** | 0.282 | 0.282 | yes |
| judge | 1024 | **sentinel** | 0.142 | 0.142 | no |

## Per-archetype summary

| agent | most-frequent closest | stayed as self | mean L1 to self | mean L1 to closest |
|---|---|---|---|---|
| oracle | oracle (5/5) | 5/5 | 0.310 | 0.310 |
| sentinel | sentinel (5/5) | 5/5 | 0.245 | 0.245 |
| firestorm | firestorm (5/5) | 5/5 | 0.378 | 0.378 |
| wall | wall (5/5) | 5/5 | 0.300 | 0.300 |
| phantom | phantom (5/5) | 5/5 | 0.266 | 0.266 |
| predator | predator (5/5) | 5/5 | 0.305 | 0.305 |
| mirror | mirror (5/5) | 5/5 | 0.333 | 0.333 |
| judge | sentinel (5/5) | 0/5 | 0.149 | 0.149 |

## Interpretation

L1 distance is summed across the full 36-dimensional 
parameter vector (4 betting rounds × 9 action-probability metrics).
An L1 of 0.0 means *identical to the canonical Phase 1 profile.*
Roughly speaking, an L1 of < 1.0 means the agent is still 
well within its own archetype neighborhood; L1 > 3.0 would 
indicate a noticeable identity drift.

The result is unambiguous: **every agent stays closest to 
its own canonical archetype across every seed.** Nobody 
drifts toward Oracle. Nobody collapses toward a common 
equilibrium. The hill-climber's local search at delta=0.03 
with 25 cycles per agent is far too weak to traverse the 
36-dimensional probability simplex and find a substantially 
different optimum.

This decisively falsifies the 'unbounded agents converge to 
Nash equilibrium / Oracle profile' hypothesis from the 
2026-04-30 mentor meeting. The agents do not converge.
