# -*- coding: utf-8 -*-
"""
Phase 3 generated parameters package.

After running ``python phase3/generate_params.py`` (requires ANTHROPIC_API_KEY),
this package will contain the individual *_params.py files and
all_generated_params.py which exports:

    GENERATED_PARAMS  -- dict of 9 archetype param sets (correct key names)
    PREDATOR_EXPLOIT  -- per-opponent-type exploit table for Predator

Until generate_params.py has been run, importing GENERATED_PARAMS will
raise ImportError with instructions.
"""

try:
    from phase3.generated_params.all_generated_params import (
        GENERATED_PARAMS,
        PREDATOR_EXPLOIT,
    )
except ImportError:
    raise ImportError(
        "Generated parameters not found. Run:\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'\n"
        "  python phase3/generate_params.py\n"
        "to generate them via the Anthropic API."
    )

__all__ = ["GENERATED_PARAMS", "PREDATOR_EXPLOIT"]
