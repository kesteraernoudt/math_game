"""© Cigav Productions LLC
Money comparison game with recognizable bills and coins."""
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .base_game import BaseGameEngine, GameState as BaseGameState


# Values are stored in cents so coin comparisons are always exact.
DENOMINATIONS = (2000, 1000, 500, 100, 25, 10, 5, 1)


@dataclass
class MoneyCompareGameState(BaseGameState):
    """The two money stacks shown in a comparison round."""
    left_counts: Dict[int, int]
    right_counts: Dict[int, int]
    left_total: int
    right_total: int
    comparison: str
    correct_side: str


class MoneyCompareGameEngine(BaseGameEngine):
    """Ask players to identify the higher or lower value of two money stacks."""

    def __init__(self, max_amount: int = 50, rounds: int = 8, **kwargs: Any):
        super().__init__(max_amount=max_amount, rounds=rounds, **kwargs)
        self.max_amount = max(1, int(max_amount))
        self.rounds = max(1, int(rounds))
        self.score = 0
        self.current_round = 0
        self._left_counts: Dict[int, int] = {}
        self._right_counts: Dict[int, int] = {}
        self._comparison = "higher"
        self._correct_side = "left"
        self._non_mixed_rounds = 0
        self._last_result: Dict[str, Any] = {}

    @staticmethod
    def _total(counts: Dict[int, int]) -> int:
        return sum(denomination * count for denomination, count in counts.items())

    @staticmethod
    def _counts(*pieces: Tuple[int, int]) -> Dict[int, int]:
        return {value: count for value, count in pieces if count > 0}

    def _make_stack_pair(self) -> Tuple[Dict[int, int], Dict[int, int], bool]:
        """Create a practical, visibly different non-tied pair within the cap.

        The patterns deliberately contrast number of pieces with their value. They
        are varied with a small offset, but never produce a pile of tiny coins.
        """
        cap = self.max_amount * 100
        patterns = (
            (self._counts((2000, 1)), self._counts((500, 3), (100, 2)), False),
            (self._counts((1000, 1)), self._counts((100, 3)), False),
            (self._counts((500, 1)), self._counts((100, 4)), False),
            (self._counts((25, 4), (10, 1)), self._counts((100, 1)), False),
            # These make bills and coins appear in the same stack on a regular basis.
            (self._counts((1000, 1), (25, 2)), self._counts((500, 2), (10, 2)), True),
            (self._counts((500, 1), (100, 4), (25, 3)), self._counts((1000, 1), (10, 2)), True),
            (self._counts((100, 1), (25, 3)), self._counts((25, 4), (10, 2)), True),
            (self._counts((25, 4)), self._counts((25, 3), (10, 2)), False),
        )
        allowed = [
            pattern for pattern in patterns
            if max(self._total(pattern[0]), self._total(pattern[1])) <= cap
            and self._total(pattern[0]) != self._total(pattern[1])
        ]
        mixed = [pattern for pattern in allowed if pattern[2]]
        choices = mixed if self._non_mixed_rounds >= 1 and mixed else allowed
        if choices:
            left, right, is_mixed = random.choice(choices)
            self._non_mixed_rounds = 0 if is_mixed else self._non_mixed_rounds + 1
            if random.choice((True, False)):
                return left, right, is_mixed
            return right, left, is_mixed
        # Safe fallback that also honors the lowest allowed cap of $1.
        return self._counts((25, 4)), self._counts((25, 3), (10, 2)), False

    def _new_round(self) -> None:
        self._left_counts, self._right_counts, _ = self._make_stack_pair()
        self._comparison = random.choice(("higher", "lower"))
        left_total = self._total(self._left_counts)
        right_total = self._total(self._right_counts)
        if self._comparison == "higher":
            self._correct_side = "left" if left_total > right_total else "right"
        else:
            self._correct_side = "left" if left_total < right_total else "right"

    def get_game_state(self) -> MoneyCompareGameState:
        return MoneyCompareGameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            left_counts=self._left_counts.copy(),
            right_counts=self._right_counts.copy(),
            left_total=self._total(self._left_counts),
            right_total=self._total(self._right_counts),
            comparison=self._comparison,
            correct_side=self._correct_side,
        )

    def start_round(self) -> Optional[MoneyCompareGameState]:
        if self.current_round >= self.rounds:
            return None
        if not self._left_counts and not self._right_counts:
            self._new_round()
        return self.get_game_state()

    def submit_answer(self, answer: str) -> Tuple[bool, MoneyCompareGameState]:
        selected = str(answer).strip().lower()
        is_correct = selected == self._correct_side
        if is_correct:
            self.score += 1
        self._last_result = {
            "selected_side": selected,
            "correct_side": self._correct_side,
            "comparison": self._comparison,
            "left_total": self._total(self._left_counts),
            "right_total": self._total(self._right_counts),
            "is_correct": is_correct,
        }
        self.current_round += 1
        self._left_counts = {}
        self._right_counts = {}
        return is_correct, self.get_game_state()

    def skip_round(self) -> Optional[MoneyCompareGameState]:
        if self.current_round >= self.rounds:
            return None
        self.current_round += 1
        self._left_counts = {}
        self._right_counts = {}
        return self.start_round()

    def get_last_result(self) -> Dict[str, Any]:
        return self._last_result.copy()

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        return {"max_amount": 50, "rounds": 8}

    def get_game_name(self) -> str:
        return "Money Compare"

    def get_game_description(self) -> str:
        return "Look at two stacks of bills and coins. Choose the stack worth more or less."

    def serialize_state(self) -> Dict[str, Any]:
        state = self.get_game_state()
        return {
            "score": state.score,
            "current_round": state.current_round,
            "left_counts": state.left_counts,
            "right_counts": state.right_counts,
            "comparison": state.comparison,
            "correct_side": state.correct_side,
            "non_mixed_rounds": self._non_mixed_rounds,
            "config": {"max_amount": self.max_amount, "rounds": self.rounds},
        }

    def deserialize_state(self, data: Dict[str, Any]) -> None:
        self.score = int(data.get("score", 0))
        self.current_round = int(data.get("current_round", 0))
        self._left_counts = {int(key): int(value) for key, value in data.get("left_counts", {}).items()}
        self._right_counts = {int(key): int(value) for key, value in data.get("right_counts", {}).items()}
        config = data.get("config", {})
        self.max_amount = max(1, int(config.get("max_amount", self.max_amount)))
        self.rounds = max(1, int(config.get("rounds", self.rounds)))
        self._comparison = data.get("comparison", "higher")
        self._correct_side = data.get("correct_side", "left")
        self._non_mixed_rounds = int(data.get("non_mixed_rounds", 0))
        self._config = config
