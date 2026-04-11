"""
Single-hand game engine for 8-player Limit Texas Hold'em.

A ``Hand`` plays exactly one hand: post blinds, deal hole cards, run four
betting rounds (preflop, flop, turn, river) with bet-cap enforcement, then
either a showdown or a walkover when everyone else folds. The engine is
agnostic about who the agents are — it only requires the minimal
"AgentProtocol":

- ``seat`` (int), ``stack`` (int), ``name``, ``archetype``
- ``decide_action(game_state) -> ActionType``
- ``receive_hole_cards(cards: list[int])``
- ``observe_action(record: ActionRecord)`` (may be a no-op in early stages)
- ``observe_showdown(showdown_data: list[dict])`` (may be a no-op)

Limit Hold'em rules implemented:

- SB=1, BB=2 posted by the two seats immediately left of the dealer.
- Preflop action begins UTG (dealer + 3) and ends with the big blind
  exercising the "BB option" (check or raise).
- Post-flop action begins with the first non-folded seat left of the dealer.
- Bet size is 2 (small bet) on preflop and flop, 4 (big bet) on turn and
  river.
- Bet cap is 4 per round (1 bet + 3 raises). At the cap, a RAISE is
  silently converted to CALL.
- A round ends when every still-active player has acted at least once AND
  all non-folded contributions match the current bet.
- A RAISE re-opens action for everyone else: they must act again even if
  they already acted this round.
- Showdown happens iff 2+ players reach the end of river betting.
- Ties split the pot as evenly as possible; any chip remainder goes to the
  earliest seat in showdown order (deterministic, reproducible).

Short-stack / all-in handling: if an agent cannot fully cover the required
call, they put in what they have and continue as effectively all-in. Side
pots are NOT implemented yet (they'll come when rebuy logic stabilizes in
Stage 3+); for now the whole pot is awarded to the best hand at showdown,
with a short stack contributing what it has. This is adequate for the
200-chip starting stacks and 48-chip-per-hand ceiling imposed by the bet
cap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from treys import Card, Evaluator

from config import NUM_PLAYERS, SIMULATION
from engine.actions import ActionRecord, ActionType

__all__ = ["GameState", "Hand"]


_EVAL = Evaluator()

_SB = SIMULATION["small_blind"]
_BB = SIMULATION["big_blind"]
_SMALL_BET = SIMULATION["small_bet"]
_BIG_BET = SIMULATION["big_bet"]
_BET_CAP = SIMULATION["bet_cap"]


@dataclass
class GameState:
    """Everything an agent sees when deciding an action."""

    hand_id: int
    betting_round: str            # "preflop" | "flop" | "turn" | "river"
    community_cards: List[int]
    pot_size: int
    current_bet: int              # max per-player round contribution so far
    cost_to_call: int             # what *this* player still owes to match
    bet_count: int                # number of bets+raises this round (cap=4)
    bet_cap: int
    bet_size: int                 # chips a BET or RAISE adds
    num_active_players: int       # non-folded players still in the hand
    active_opponent_seats: List[int]
    player_seat: int
    player_stack: int
    player_position: int          # (seat - dealer) mod NUM_PLAYERS
    dealer_seat: int
    actions_this_round: List[ActionRecord] = field(default_factory=list)

    def pot_contribution(self, seat: int) -> int:  # pragma: no cover
        """Stub used by the Mirror agent in Stage 6. Returns 0 here; Stage 6
        will wire up real contribution tracking."""
        return 0


def _bet_size_for_round(round_name: str) -> int:
    return _SMALL_BET if round_name in ("preflop", "flop") else _BIG_BET


class Hand:
    """Plays a single hand to completion and returns the action log and any
    showdown data."""

    def __init__(self, table, deck, rng: np.random.Generator, hand_id: int):
        self.table = table
        self.deck = deck
        self.rng = rng
        self.hand_id = hand_id

        # Seats the table considers "seated" this hand. We copy so that
        # later rebuy bookkeeping doesn't mutate state mid-hand.
        self._all_seats: List[int] = [a.seat for a in self.table.seats]

        # Active = still holding cards (hasn't folded, hasn't been pre-eliminated).
        self.active: set = set(self._all_seats)
        self.folded: set = set()

        # Snapshots taken now so the table's dealer_button can rotate after
        # play() without corrupting anything downstream (e.g. the visualizer
        # exporter).
        self.dealer_seat: int = table.dealer_button
        self.sb_seat: int = (table.dealer_button + 1) % NUM_PLAYERS
        self.bb_seat: int = (table.dealer_button + 2) % NUM_PLAYERS

        # Per-hand bookkeeping.
        self.hole_cards: Dict[int, List[int]] = {}
        self.community_cards: List[int] = []
        # Per-street community, for the replay visualizer.
        self.flop_cards: List[int] = []
        self.turn_card: List[int] = []
        self.river_card: List[int] = []
        self.pot: int = 0
        self.final_pot: int = 0    # pot before award (for display)
        # Total contribution this hand, per seat, used for showdown accounting.
        self.hand_contribution: Dict[int, int] = {s: 0 for s in self._all_seats}
        # Contribution within the current betting round (reset each round).
        self.round_contribution: Dict[int, int] = {s: 0 for s in self._all_seats}
        # Stacks at the start of the hand (for ActionRecord.stack_before).
        self.stack_before_hand: Dict[int, int] = {
            a.seat: a.stack for a in self.table.seats
        }
        # Filled in at end of play().
        self.stack_after_hand: Dict[int, int] = {}

        self.action_log: List[ActionRecord] = []
        self.showdown_data: Optional[List[dict]] = None
        self._seq: int = 0  # monotonic sequence counter within this hand

    # ------------------------------------------------------------------
    # Top-level play loop
    # ------------------------------------------------------------------
    def play(self) -> Tuple[List[ActionRecord], Optional[List[dict]]]:
        self._post_blinds()
        self._deal_hole_cards()

        if self._betting_round("preflop"):
            self._deal_community(3)            # Flop
            if self._betting_round("flop"):
                self._deal_community(1)        # Turn
                if self._betting_round("turn"):
                    self._deal_community(1)    # River
                    self._betting_round("river")

        if self._count_active() >= 2:
            self._showdown()
        else:
            self._award_pot_to_last_standing()

        # Snapshot for downstream visualizers / loggers.
        self.stack_after_hand = {a.seat: a.stack for a in self.table.seats}
        return self.action_log, self.showdown_data

    # ------------------------------------------------------------------
    # Setup: blinds and hole cards
    # ------------------------------------------------------------------
    def _post_blinds(self) -> None:
        sb_seat = (self.table.dealer_button + 1) % NUM_PLAYERS
        bb_seat = (self.table.dealer_button + 2) % NUM_PLAYERS
        self._move_chips(sb_seat, _SB)
        self._move_chips(bb_seat, _BB)
        # Blinds count as round contribution during preflop.
        self.round_contribution[sb_seat] = _SB
        self.round_contribution[bb_seat] = _BB

    def _deal_hole_cards(self) -> None:
        # Deal in action order starting left of dealer, one card at a time
        # twice, to match real-world dealing (doesn't affect math but keeps
        # the deck ordering consistent with a physical deal).
        order = [(self.table.dealer_button + 1 + i) % NUM_PLAYERS
                 for i in range(NUM_PLAYERS)]
        cards_by_seat: Dict[int, List[int]] = {s: [] for s in order}
        for _ in range(2):
            for seat in order:
                cards_by_seat[seat].append(self.deck.deal(1)[0])
        for seat, cards in cards_by_seat.items():
            self.hole_cards[seat] = cards
            self.table.seats[seat].receive_hole_cards(cards)

    # ------------------------------------------------------------------
    # Betting round
    # ------------------------------------------------------------------
    def _betting_round(self, round_name: str) -> bool:
        """Run one betting round. Returns True if the hand continues."""
        bet_size = _bet_size_for_round(round_name)

        if round_name == "preflop":
            # Blinds already posted and recorded in round_contribution.
            current_bet = _BB
            bet_count = 1
            start_seat = (self.table.dealer_button + 3) % NUM_PLAYERS  # UTG
        else:
            # Reset round-local contributions for the new street.
            self.round_contribution = {s: 0 for s in self._all_seats}
            current_bet = 0
            bet_count = 0
            start_seat = (self.table.dealer_button + 1) % NUM_PLAYERS  # left of dealer

        to_act: List[int] = self._order_from(start_seat)
        acted: set = set()
        round_actions: List[ActionRecord] = []

        while to_act:
            if self._count_active() < 2:
                break
            seat = to_act.pop(0)
            if seat in self.folded or seat not in self.active:
                continue

            agent = self.table.seats[seat]
            # Short-stacked players still get asked — decide_action can
            # return CALL for "all-in call" and the engine will contribute
            # min(stack, to_call).
            if agent.stack <= 0:
                # Can't act; treat as check if no bet, otherwise auto-fold.
                if current_bet > self.round_contribution[seat]:
                    self._apply_fold(seat, round_name, bet_size,
                                     current_bet, bet_count, round_actions)
                    continue
                # No cost to call; just record a check.
                self._record(seat, round_name, ActionType.CHECK, 0,
                             current_bet, bet_count, round_actions)
                acted.add(seat)
                continue

            game_state = self._build_game_state(
                seat, round_name, current_bet, bet_count, bet_size,
                round_actions,
            )
            action = agent.decide_action(game_state)

            if action == ActionType.FOLD:
                self._apply_fold(seat, round_name, bet_size,
                                 current_bet, bet_count, round_actions)
                acted.add(seat)
                continue

            if action == ActionType.CHECK:
                if self.round_contribution[seat] != current_bet:
                    raise ValueError(
                        f"Seat {seat} ({agent.archetype}) checked with "
                        f"cost_to_call={current_bet - self.round_contribution[seat]}"
                    )
                self._record(seat, round_name, ActionType.CHECK, 0,
                             current_bet, bet_count, round_actions)
                acted.add(seat)
                continue

            if action == ActionType.CALL:
                to_call = current_bet - self.round_contribution[seat]
                if to_call <= 0:
                    # Nothing to call — treat as check.
                    self._record(seat, round_name, ActionType.CHECK, 0,
                                 current_bet, bet_count, round_actions)
                    acted.add(seat)
                    continue
                paid = min(to_call, agent.stack)
                self._move_chips(seat, paid)
                self.round_contribution[seat] += paid
                self._record(seat, round_name, ActionType.CALL, paid,
                             current_bet, bet_count, round_actions)
                acted.add(seat)
                continue

            if action == ActionType.BET and current_bet != 0:
                # Agent returned BET but there's already a bet on the street
                # (typically the preflop BB option: cost_to_call=0 so the
                # agent's "no bet pending" branch fires and returns BET,
                # but current_bet is already 2 from the BB posting). Upgrade
                # it to a RAISE and fall through to the RAISE handler.
                action = ActionType.RAISE

            if action == ActionType.BET:
                paid = min(bet_size, agent.stack)
                self._move_chips(seat, paid)
                self.round_contribution[seat] += paid
                current_bet = paid
                bet_count = 1
                self._record(seat, round_name, ActionType.BET, paid,
                             current_bet, bet_count, round_actions)
                acted = {seat}  # Everyone else must act again.
                to_act = self._order_from_excluding(
                    (seat + 1) % NUM_PLAYERS, exclude={seat},
                )
                continue

            if action == ActionType.RAISE:
                if current_bet == 0:
                    # Treat "raise" with no bet as an opening bet.
                    paid = min(bet_size, agent.stack)
                    self._move_chips(seat, paid)
                    self.round_contribution[seat] += paid
                    current_bet = paid
                    bet_count = 1
                    self._record(seat, round_name, ActionType.BET, paid,
                                 current_bet, bet_count, round_actions)
                    acted = {seat}
                    to_act = self._order_from_excluding(
                        (seat + 1) % NUM_PLAYERS, exclude={seat},
                    )
                    continue
                if bet_count >= _BET_CAP:
                    # Cap reached — downgrade to call.
                    to_call = current_bet - self.round_contribution[seat]
                    paid = min(to_call, agent.stack)
                    self._move_chips(seat, paid)
                    self.round_contribution[seat] += paid
                    self._record(seat, round_name, ActionType.CALL, paid,
                                 current_bet, bet_count, round_actions)
                    acted.add(seat)
                    continue
                # Standard raise: bump current_bet by one bet_size.
                new_bet = current_bet + bet_size
                delta = new_bet - self.round_contribution[seat]
                paid = min(delta, agent.stack)
                self._move_chips(seat, paid)
                self.round_contribution[seat] += paid
                current_bet = new_bet
                bet_count += 1
                self._record(seat, round_name, ActionType.RAISE, paid,
                             current_bet, bet_count, round_actions)
                acted = {seat}
                to_act = self._order_from_excluding(
                    (seat + 1) % NUM_PLAYERS, exclude={seat},
                )
                continue

            raise ValueError(f"Unknown action: {action!r}")

        self.action_log.extend(round_actions)
        return self._count_active() >= 2

    # ------------------------------------------------------------------
    # Action helpers
    # ------------------------------------------------------------------
    def _apply_fold(
        self,
        seat: int,
        round_name: str,
        bet_size: int,
        current_bet: int,
        bet_count: int,
        round_actions: List[ActionRecord],
    ) -> None:
        self.folded.add(seat)
        self._record(seat, round_name, ActionType.FOLD, 0,
                     current_bet, bet_count, round_actions)

    def _build_game_state(
        self,
        seat: int,
        round_name: str,
        current_bet: int,
        bet_count: int,
        bet_size: int,
        round_actions: List[ActionRecord],
    ) -> GameState:
        agent = self.table.seats[seat]
        cost = max(0, current_bet - self.round_contribution[seat])
        opponents = [s for s in self.active
                     if s != seat and s not in self.folded]
        return GameState(
            hand_id=self.hand_id,
            betting_round=round_name,
            community_cards=list(self.community_cards),
            pot_size=self.pot,
            current_bet=current_bet,
            cost_to_call=cost,
            bet_count=bet_count,
            bet_cap=_BET_CAP,
            bet_size=bet_size,
            num_active_players=self._count_active(),
            active_opponent_seats=opponents,
            player_seat=seat,
            player_stack=agent.stack,
            player_position=(seat - self.table.dealer_button) % NUM_PLAYERS,
            dealer_seat=self.table.dealer_button,
            actions_this_round=list(round_actions),
        )

    def _record(
        self,
        seat: int,
        round_name: str,
        action_type: ActionType,
        amount: int,
        current_bet: int,
        bet_count: int,
        round_actions: List[ActionRecord],
    ) -> None:
        agent = self.table.seats[seat]
        self._seq += 1
        moves_chips = action_type in (
            ActionType.CALL, ActionType.BET, ActionType.RAISE,
        )
        record = ActionRecord(
            hand_id=self.hand_id,
            seat=seat,
            archetype=agent.archetype,
            betting_round=round_name,
            action_type=action_type,
            amount=amount,
            pot_before=self.pot - amount if moves_chips else self.pot,
            pot_after=self.pot,
            stack_before=agent.stack + amount if moves_chips else agent.stack,
            stack_after=agent.stack,
            sequence_num=self._seq,
            num_opponents_remaining=self._count_active() - 1,
            position_relative_to_dealer=(
                (seat - self.table.dealer_button) % NUM_PLAYERS
            ),
            bet_count=bet_count,
            current_bet=current_bet,
            hand_strength_bucket=None,
        )
        round_actions.append(record)
        # Broadcast to all seats so later stages can update trust beliefs.
        for a in self.table.seats:
            a.observe_action(record)

    def _move_chips(self, seat: int, amount: int) -> None:
        """Transfer chips from a seat's stack into the pot."""
        if amount <= 0:
            return
        agent = self.table.seats[seat]
        amount = min(amount, agent.stack)
        agent.stack -= amount
        self.pot += amount
        self.hand_contribution[seat] += amount

    # ------------------------------------------------------------------
    # Ordering and counting
    # ------------------------------------------------------------------
    def _order_from(self, start_seat: int) -> List[int]:
        """Seats in clockwise order starting with ``start_seat``, filtered to
        those still non-folded and active."""
        out: List[int] = []
        for i in range(NUM_PLAYERS):
            s = (start_seat + i) % NUM_PLAYERS
            if s in self.active and s not in self.folded:
                out.append(s)
        return out

    def _order_from_excluding(self, start_seat: int, exclude: set) -> List[int]:
        return [s for s in self._order_from(start_seat) if s not in exclude]

    def _count_active(self) -> int:
        return sum(1 for s in self.active if s not in self.folded)

    # ------------------------------------------------------------------
    # Community cards
    # ------------------------------------------------------------------
    def _deal_community(self, n: int) -> None:
        cards = self.deck.deal(n)
        self.community_cards.extend(cards)
        # Tag by street for the visualizer.
        if len(self.community_cards) == 3:
            self.flop_cards = list(cards)
        elif len(self.community_cards) == 4:
            self.turn_card = list(cards)
        elif len(self.community_cards) == 5:
            self.river_card = list(cards)

    # ------------------------------------------------------------------
    # Showdown / pot award
    # ------------------------------------------------------------------
    def _showdown(self) -> None:
        self.final_pot = self.pot
        contenders: List[int] = [s for s in self.active if s not in self.folded]
        # treys: lower rank = better hand.
        ranked: List[Tuple[int, int]] = []
        for seat in contenders:
            rank = _EVAL.evaluate(self.community_cards, self.hole_cards[seat])
            ranked.append((seat, rank))
        ranked.sort(key=lambda x: x[1])
        best_rank = ranked[0][1]
        winners = [seat for seat, rank in ranked if rank == best_rank]

        # Split pot, remainder to earliest (leftmost of dealer) winner.
        per_winner = self.pot // len(winners)
        remainder = self.pot - per_winner * len(winners)
        order = self._order_from((self.table.dealer_button + 1) % NUM_PLAYERS)
        winners_ordered = [s for s in order if s in winners]
        winnings: Dict[int, int] = {s: per_winner for s in winners}
        if remainder > 0 and winners_ordered:
            winnings[winners_ordered[0]] += remainder

        for seat, amt in winnings.items():
            self.table.seats[seat].stack += amt

        self.showdown_data = []
        for seat, rank in ranked:
            won_amt = winnings.get(seat, 0)
            entry = {
                "hand_id": self.hand_id,
                "seat": seat,
                "archetype": self.table.seats[seat].archetype,
                "hole_cards": list(self.hole_cards[seat]),
                "hand_rank": rank,
                "won": seat in winners,
                "pot_won": won_amt,
            }
            self.showdown_data.append(entry)

        self.pot = 0
        for a in self.table.seats:
            a.observe_showdown(self.showdown_data)

    def _award_pot_to_last_standing(self) -> None:
        self.final_pot = self.pot
        survivors = [s for s in self.active if s not in self.folded]
        assert len(survivors) == 1, f"Expected 1 survivor, got {len(survivors)}"
        winner = survivors[0]
        self.table.seats[winner].stack += self.pot
        self.showdown_data = None  # No showdown on a walkover
        self._walkover_winner: int = winner
        self.pot = 0
