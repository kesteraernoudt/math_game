"""© Cigav Productions LLC
Money game where players build payments with $20, $5, and $1 bills."""
import random
import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .base_game import BaseGameEngine, GameState as BaseGameState
from .item_catalog import ItemCatalog


@dataclass
class MoneyGameState(BaseGameState):
    """Extended game state for the money game."""
    item_name: str
    item_price: int
    tax_amount: int
    total_due: int
    tax_rate: float
    show_tax: bool
    item_image: str
    awaiting_retry: bool
    available_counts: Dict[int, int]


class MoneyGameEngine(BaseGameEngine):
    """Game engine for building the best bill combination to match a price."""
    
    def __init__(
        self,
        max_price: int = 50,
        rounds: int = 10,
        tax_rate: float = 0.08,
        show_tax: bool = True,
        require_minimal_bills: bool = False,
        bill_limit_mode: str = "easy",
        allow_overpay: bool = False,
        **kwargs: Any,
    ):
        super().__init__(max_price=max_price, rounds=rounds, tax_rate=tax_rate, show_tax=show_tax, require_minimal_bills=require_minimal_bills, bill_limit_mode=bill_limit_mode, allow_overpay=allow_overpay, **kwargs)
        self.max_price = max_price
        self.rounds = rounds
        self.tax_rate = tax_rate
        self.show_tax = show_tax
        self.require_minimal_bills = require_minimal_bills
        self.bill_limit_mode = bill_limit_mode
        self.allow_overpay = allow_overpay
        self.score = 0
        self.current_round = 0
        self._item_name: Optional[str] = None
        self._item_price: int = 0
        self._tax_amount: int = 0
        self._total_due: int = 0
        self._item_image: str = ""
        self._awaiting_retry: bool = False
        self._last_result: Dict[str, Any] = {}
        self._available_counts: Dict[int, int] = {20: 999, 10: 999, 5: 999, 1: 999}
        self._items = ItemCatalog.items()
        random.seed(datetime.now().timestamp())

    def _build_item_image(self, label: str, color: str, emoji: str) -> str:
        """Create a small inline SVG data URI for the item."""
        return ItemCatalog.build_image(label, color, emoji)

    def _choose_price(self, item: Dict[str, Any]) -> int:
        """Choose a whole-dollar price for the given item honoring the max price cap."""
        return ItemCatalog.choose_price(item, self.max_price, random)

    def _generate_limits(self, pay_total: float) -> Dict[int, int]:
        """Generate available bill counts based on difficulty."""
        if self.bill_limit_mode == "easy":
            return {20: 999, 10: 999, 5: 999, 1: 999}
        if self.bill_limit_mode == "intermediate":
            return {20: 1, 10: 2, 5: 3, 1: 4}
        for _ in range(20):
            limits = {20: random.randint(0, 4), 10: random.randint(0, 4), 5: random.randint(0, 4), 1: random.randint(0, 4)}
            capacity = limits[20]*20 + limits[10]*10 + limits[5]*5 + limits[1]
            if capacity >= math.ceil(pay_total):
                return limits
        return {20: 2, 10: 2, 5: 3, 1: 5}

    def _choose_item(self) -> None:
        for _ in range(30):
            item = random.choice(self._items)
            self._item_name = item["name"]
            self._item_price = self._choose_price(item)
            if self.show_tax:
                raw_tax = self._item_price * self.tax_rate
                self._tax_amount = round(raw_tax, 2)
            else:
                self._tax_amount = 0.0
            self._total_due = round(self._item_price + self._tax_amount, 2)
            pay_total = math.ceil(self._total_due)
            limits = self._generate_limits(pay_total)
            capacity = limits[20]*20 + limits[10]*10 + limits[5]*5 + limits[1]
            if capacity >= pay_total:
                self._available_counts = limits
                break
        else:
            self._available_counts = {20: 2, 10: 2, 5: 3, 1: 5}
        self._item_image = self._build_item_image(item["name"], item["color"], item["emoji"])
        self._awaiting_retry = False

    def _best_combo(self, amount: float) -> Dict[int, int]:
        """Return the optimal bill breakdown for paying at least the amount (ceiled)."""
        remaining = math.ceil(amount)
        twenties = remaining // 20
        remaining = remaining % 20
        tens = remaining // 10
        remaining = remaining % 10
        fives = remaining // 5
        ones = remaining % 5
        return {20: twenties, 10: tens, 5: fives, 1: ones}

    def _best_combo_with_limits(self, amount: float, available: Dict[int, int]) -> Tuple[Dict[int, int], int]:
        """Return minimal payable total >= amount within availability; tie-break on fewest bills."""
        available = {int(k): v for k, v in available.items()}
        target = math.ceil(amount)
        best_combo: Dict[int, int] = {20: 0, 10: 0, 5: 0, 1: 0}
        best_total = None
        best_bills = None
        for c20 in range(available.get(20, 0) + 1):
            for c10 in range(available.get(10, 0) + 1):
                for c5 in range(available.get(5, 0) + 1):
                    for c1 in range(available.get(1, 0) + 1):
                        total = c20 * 20 + c10 * 10 + c5 * 5 + c1
                        if total < target:
                            continue
                        bills = c20 + c10 + c5 + c1
                        if best_total is None or total < best_total or (total == best_total and bills < best_bills):
                            best_total = total
                            best_bills = bills
                            best_combo = {20: c20, 10: c10, 5: c5, 1: c1}
        # If nothing found (should not happen because we guard capacity), fall back to zeros
        if best_total is None:
            return {20: 0, 10: 0, 5: 0, 1: 0}, 0
        return best_combo, best_total
    
    def get_best_combo(self) -> Dict[int, int]:
        """Public helper for the best combo of the current total."""
        if self.bill_limit_mode != "easy":
            avail = getattr(self, "_available_counts", {20:999,10:999,5:999,1:999})
            combo, _ = self._best_combo_with_limits(self._total_due, {int(k): v for k, v in avail.items()})
            return combo
        return self._best_combo(self._total_due)

    def _parse_answer(self, answer: str) -> Dict[int, int]:
        """Parse an answer string like '20:2,5:1,1:3' into counts."""
        counts = {20: 0, 10: 0, 5: 0, 1: 0}
        if not answer:
            return counts
        parts = [p.strip() for p in answer.split(",") if p.strip()]
        for part in parts:
            if ":" not in part:
                continue
            denom_str, count_str = part.split(":", 1)
            try:
                denom = int(denom_str)
                count = int(count_str)
            except ValueError:
                continue
            if denom in counts:
                counts[denom] = max(0, count)
        return counts

    def get_game_state(self) -> MoneyGameState:
        """Get the current state of the game."""
        return MoneyGameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            item_name=self._item_name or "",
            item_price=self._item_price,
            tax_amount=self._tax_amount,
            total_due=self._total_due,
            tax_rate=self.tax_rate,
            show_tax=self.show_tax,
            item_image=self._item_image,
            awaiting_retry=self._awaiting_retry,
            available_counts=self._available_counts if hasattr(self, "_available_counts") else {20:999,10:999,5:999,1:999}
        )

    def start_round(self) -> Optional[MoneyGameState]:
        """Start a new round or return the current state if retrying."""
        if self.current_round >= self.rounds:
            return None
        if self._awaiting_retry and self._item_name:
            return self.get_game_state()
        self._choose_item()
        return self.get_game_state()

    def submit_answer(self, answer: str) -> Tuple[bool, MoneyGameState]:
        """Submit an answer; do not advance the round on incorrect attempts."""
        if not self._item_name:
            raise ValueError("No active round in progress")
        counts = self._parse_answer(answer)
        user_total = (
            counts[20] * 20
            + counts[10] * 10
            + counts[5] * 5
            + counts[1] * 1
        )
        pay_target = math.ceil(self._total_due)
        available_raw = getattr(self, "_available_counts", {20: 999, 10: 999, 5: 999, 1: 999})
        available = {int(k): v for k, v in available_raw.items()}
        if self.bill_limit_mode != "easy":
            best_combo, best_total = self._best_combo_with_limits(self._total_due, available)
        else:
            best_combo = self._best_combo(self._total_due)
            best_total = pay_target
        # Pre-store the latest submission for debugging/inspection even if it fails validation
        self._last_result = {
            "counts": counts,
            "best_combo": best_combo,
            "user_total": user_total,
            "total_due": self._total_due,
            "pay_total": best_total,
            "is_correct": False,
            "show_tax": self.show_tax,
        }
        # Respect limits: if any submitted count exceeds availability, auto-fail
        for denom, cnt in counts.items():
            if cnt > available.get(denom, 0):
                self._awaiting_retry = True
                return False, self.get_game_state()
        exact_possible = (best_total == pay_target)

        if self.require_minimal_bills:
            if self.allow_overpay:
                is_correct = counts == best_combo and user_total == best_total
            else:
                if exact_possible:
                    is_correct = counts == best_combo and user_total == pay_target
                else:
                    is_correct = counts == best_combo and user_total == best_total
        else:
            if self.allow_overpay:
                is_correct = user_total >= pay_target
            else:
                if exact_possible:
                    is_correct = user_total == pay_target
                else:
                    is_correct = user_total == best_total
        # Defensive: if the submitted combo exactly matches the best and total, force correct
        if counts == best_combo and user_total == best_total:
            is_correct = True

        self._last_result = {
            "counts": counts,
            "best_combo": best_combo,
            "user_total": user_total,
            "total_due": self._total_due,
            "pay_total": best_total,
            "is_correct": is_correct,
            "show_tax": self.show_tax,
            "require_minimal": self.require_minimal_bills,
            "available": available,
            "comparisons": {
                "user_ge_target": user_total >= pay_target,
                "user_eq_target": user_total == pay_target,
                "user_eq_best_total": user_total == best_total,
                "counts_match_best": counts == best_combo,
                "exact_possible": exact_possible,
                "allow_overpay": getattr(self, "allow_overpay", False),
            },
        }

        if is_correct:
            self.score += 1
            self.current_round += 1
            self._awaiting_retry = False
        else:
            self._awaiting_retry = True

        return is_correct, self.get_game_state()

    def skip_round(self) -> Optional[MoneyGameState]:
        """Skip the current round and move to the next item without changing score."""
        if self.current_round >= self.rounds:
            return None
        self.current_round += 1
        self._awaiting_retry = False
        return self.start_round()

    def get_last_result(self) -> Dict[str, Any]:
        """Return metadata about the last submitted answer."""
        return self._last_result.copy()

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this game."""
        return {
            "max_price": 50,
            "rounds": 8,
            "tax_rate": 0.0938,
            "show_tax": False,
            "require_minimal_bills": False,
            "bill_limit_mode": "easy",
            "allow_overpay": False,
        }

    def get_game_name(self) -> str:
        """Get the display name of this game."""
        return "Money Match"

    def get_game_description(self) -> str:
        """Get a description of this game."""
        return "Choose the best $20, $5, and $1 bills to pay for items with or without sales tax."

    def serialize_state(self) -> Dict[str, Any]:
        """Serialize game state to a dictionary for session storage."""
        state = self.get_game_state()
        return {
            "score": state.score,
            "current_round": state.current_round,
            "item_name": state.item_name,
            "item_price": state.item_price,
            "tax_amount": state.tax_amount,
            "total_due": state.total_due,
            "tax_rate": state.tax_rate,
            "show_tax": state.show_tax,
            "item_image": state.item_image,
            "awaiting_retry": state.awaiting_retry,
            "available_counts": getattr(self, "_available_counts", {20: 999, 10: 999, 5: 999, 1: 999}),
            "config": {
                "max_price": self.max_price,
                "rounds": self.rounds,
                "tax_rate": self.tax_rate,
                "show_tax": self.show_tax,
                "require_minimal_bills": self.require_minimal_bills,
                "bill_limit_mode": self.bill_limit_mode,
                "allow_overpay": getattr(self, "allow_overpay", False),
            },
        }

    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.score = data.get("score", 0)
        self.current_round = data.get("current_round", 0)
        self._item_name = data.get("item_name")
        self._item_price = data.get("item_price", 0)
        self._tax_amount = data.get("tax_amount", 0)
        self._total_due = data.get("total_due", 0)
        self.tax_rate = data.get("tax_rate", self._config.get("tax_rate", 0.08))
        self.show_tax = data.get("show_tax", self._config.get("show_tax", True))
        avail = data.get("available_counts", {20: 999, 10: 999, 5: 999, 1: 999})
        self._available_counts = {int(k): v for k, v in avail.items()}
        self._item_image = data.get("item_image", "")
        self._awaiting_retry = data.get("awaiting_retry", False)
        config = data.get("config", {})
        self.max_price = config.get("max_price", self.max_price)
        self.rounds = config.get("rounds", self.rounds)
        self.tax_rate = config.get("tax_rate", self.tax_rate)
        self.show_tax = config.get("show_tax", self.show_tax)
        self.require_minimal_bills = config.get("require_minimal_bills", self.require_minimal_bills)
        self.bill_limit_mode = config.get("bill_limit_mode", self.bill_limit_mode)
        self.allow_overpay = config.get("allow_overpay", getattr(self, "allow_overpay", False))
        self._config = config
