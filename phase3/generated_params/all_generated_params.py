# -*- coding: utf-8 -*-
"""
Combined LLM-generated parameters for all 8 archetypes.

Imports the individual param files and maps them to the canonical key names
expected by llm_agent.py and run_phase3.py:

    oracle, sentinel, firestorm, wall, phantom,
    predator_baseline, mirror_default,
    judge_cooperative, judge_retaliatory

Usage::

    from phase3.generated_params.all_generated_params import GENERATED_PARAMS
    from phase3.generated_params.all_generated_params import PREDATOR_EXPLOIT
"""

from phase3.generated_params.oracle_params import ORACLE_PARAMS
from phase3.generated_params.sentinel_params import SENTINEL_PARAMS
from phase3.generated_params.firestorm_params import FIRESTORM_PARAMS
from phase3.generated_params.wall_params import WALL_PARAMS
from phase3.generated_params.phantom_params import PHANTOM_PARAMS
from phase3.generated_params.predator_params import (
    PREDATOR_BASELINE_PARAMS,
    PREDATOR_EXPLOIT,
)
from phase3.generated_params.mirror_params import MIRROR_DEFAULT_PARAMS
from phase3.generated_params.judge_params import (
    JUDGE_PRE_TRIGGER,
    JUDGE_POST_TRIGGER,
)

# ---------------------------------------------------------------------------
# GENERATED_PARAMS: canonical combined dict
# ---------------------------------------------------------------------------
# Keys match what llm_agent.py expects via _ARCHETYPE_TO_PARAM_KEY:
#   "oracle", "sentinel", "firestorm", "wall", "phantom"
#   "predator_baseline" (not "predator")
#   "mirror_default" (not "mirror")
#   "judge_cooperative" (not "judge_pre_trigger")
#   "judge_retaliatory" (not "judge_post_trigger")
# ---------------------------------------------------------------------------

GENERATED_PARAMS = {
    "oracle": ORACLE_PARAMS,
    "sentinel": SENTINEL_PARAMS,
    "firestorm": FIRESTORM_PARAMS,
    "wall": WALL_PARAMS,
    "phantom": PHANTOM_PARAMS,
    "predator_baseline": PREDATOR_BASELINE_PARAMS,
    "mirror_default": MIRROR_DEFAULT_PARAMS,
    "judge_cooperative": JUDGE_PRE_TRIGGER,
    "judge_retaliatory": JUDGE_POST_TRIGGER,
}
