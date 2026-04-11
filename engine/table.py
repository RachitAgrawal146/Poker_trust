"""
Table manager for 8-seat Limit Hold'em.

Owns the seat roster, the dealer button, the seeded RNG, and the rebuy
economics. ``play_hand`` is the only method the run loop needs to call: it
handles rebuys, deals a fresh deck, runs one ``Hand``, rotates the dealer
button, and returns the action log and any showdown data for logging.

The Table does NOT own trust model state or per-agent bookkeeping — that
lives on the agents themselves. This keeps the engine/agents boundary clean
for Stage 3.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from config import NUM_PLAYERS, SIMULATION
from engine.actions import ActionRecord
from engine.deck import Deck
from engine.game import Hand

__all__ = ["Table"]


_STARTING_STACK = SIMULATION["starting_stack"]


class Table:
    def __init__(
        self,
        agents: list,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
        logger: Optional[object] = None,
        run_id: Optional[int] = None,
    ) -> None:
        if len(agents) != NUM_PLAYERS:
            raise ValueError(
                f"Table requires exactly {NUM_PLAYERS} agents, got {len(agents)}"
            )
        self.seats = list(agents)
        # Assign seats and fresh stacks if agents came in unseated.
        for i, agent in enumerate(self.seats):
            agent.seat = i
            if not hasattr(agent, "stack") or agent.stack is None:
                agent.stack = _STARTING_STACK
            if not hasattr(agent, "rebuys"):
                agent.rebuys = 0
            # Every archetype agent expects a shared, seeded RNG. Injecting
            # here means the caller doesn't have to wire it up at
            # construction time, and it stays reproducible.
            if getattr(agent, "rng", None) is None:
                agent.rng = rng if rng is not None else None
        # Assign the table's RNG second so we always have one.
        self._rng: np.random.Generator = (
            rng if rng is not None else np.random.default_rng(seed)
        )
        # Any agent that still doesn't have an RNG picks up the table's.
        for agent in self.seats:
            if getattr(agent, "rng", None) is None:
                agent.rng = self._rng

        self.dealer_button: int = 0
        self.hand_number: int = 0
        #: Reference to the most recently played ``Hand`` instance. External
        #: tooling (e.g. the visualizer exporter) reads this to recover the
        #: full per-hand state without requiring Table to know about logging.
        self.last_hand: Optional[Hand] = None

        #: Stage 7 persistent logger hook. When set, ``play_hand`` forwards
        #: the just-played ``Hand`` to ``logger.log_hand(run_id, hand)`` after
        #: the dealer rotates. Both attributes are plain fields so callers
        #: can attach a logger lazily (e.g. after calling
        #: ``logger.start_run(...)`` to obtain the run_id).
        self.logger = logger
        self.run_id: Optional[int] = run_id

    # ------------------------------------------------------------------
    def play_hand(self) -> Tuple[List[ActionRecord], Optional[List[dict]]]:
        self.hand_number += 1
        self._handle_rebuys()

        # Lifecycle hook — agents reset per-hand scratch state, increment
        # hands_dealt, etc. Optional method: old scripted agents (DummyAgent)
        # don't care.
        for agent in self.seats:
            fn = getattr(agent, "on_hand_start", None)
            if callable(fn):
                fn(self.hand_number)

        deck = Deck(rng=self._rng)
        hand = Hand(self, deck, self._rng, self.hand_number)
        action_log, showdown_data = hand.play()
        self.last_hand = hand

        for agent in self.seats:
            fn = getattr(agent, "on_hand_end", None)
            if callable(fn):
                fn(self.hand_number)

        self._rotate_dealer()

        # Stage 7: forward the just-played hand to the persistent logger.
        if self.logger is not None and self.run_id is not None:
            self.logger.log_hand(self.run_id, hand)

        return action_log, showdown_data

    # ------------------------------------------------------------------
    def _handle_rebuys(self) -> None:
        for agent in self.seats:
            if agent.stack <= 0:
                agent.stack = _STARTING_STACK
                agent.rebuys = getattr(agent, "rebuys", 0) + 1

    def _rotate_dealer(self) -> None:
        self.dealer_button = (self.dealer_button + 1) % NUM_PLAYERS
