"""© Cigav Productions LLC
Change game where players determine the correct change for a purchase."""
import math
import random
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import quote
from .base_game import BaseGameEngine, GameState
from .item_catalog import ItemCatalog


@dataclass
class ChangeGameState(GameState):
    """State object for the change game."""
    item_name: str
    item_price: float
    tax_amount: float
    total_due: float
    tax_rate: float
    show_tax: bool
    item_image: str
    pay_total: float
    pay_counts: Dict[int, int]
    change_due: float
    available_change: Dict[int, int]
    awaiting_retry: bool


class ChangeGameEngine(BaseGameEngine):
    """Engine for figuring out the change a customer should receive."""

    CHANGE_DENOMS = [1000, 500, 100, 25, 10, 5, 1]  # cents: $10, $5, $1, coins
    PAY_DENOMS = [2000, 1000, 500, 100]  # cents: $20, $10, $5, $1

    def __init__(
        self,
        max_price: int = 50,
        rounds: int = 8,
        tax_rate: float = 0.08,
        show_tax: bool = True,
        require_minimal_bills: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            max_price=max_price,
            rounds=rounds,
            tax_rate=tax_rate,
            show_tax=show_tax,
            require_minimal_bills=require_minimal_bills,
            **kwargs,
        )
        self.max_price = max_price
        self.rounds = rounds
        self.tax_rate = tax_rate
        self.show_tax = show_tax
        self.require_minimal_change = require_minimal_bills
        self.score = 0
        self.current_round = 0
        self._item_name: Optional[str] = None
        self._item_price: float = 0.0
        self._tax_amount: float = 0.0
        self._total_due: float = 0.0
        self._total_due_cents: int = 0
        self._pay_total_cents: int = 0
        self._pay_counts: Dict[int, int] = {den: 0 for den in self.PAY_DENOMS}
        self._change_due_cents: int = 0
        self._best_change_counts: Dict[int, int] = {den: 0 for den in self.CHANGE_DENOMS}
        self._last_result: Dict[str, Any] = {}
        self._available_change = {1000: 5, 500: 5, 100: 20, 25: 20, 10: 20, 5: 20, 1: 40}
        self._item_image: str = ""
        self._awaiting_retry: bool = False
        self._items = ItemCatalog.items()
        random.seed(datetime.now().timestamp())

    def _build_item_image(self, label: str, color: str, emoji: str) -> str:
        return ItemCatalog.build_image(label, color, emoji)

    def _choose_price(self, item: Dict[str, Any]) -> int:
        return ItemCatalog.choose_price(item, self.max_price, random)

    def _pick_payment_combo(self, total_due_cents: int) -> Tuple[Dict[int, int], int]:
        """Select a realistic payment combination of bills based on a random wallet."""
        for _ in range(40):
            wallet = {
                2000: random.randint(1, 3),  # kids often have $20s
                1000: random.randint(0, 2),
                500: random.randint(0, 2),
                100: random.randint(0, 3),
            }
            capacity = sum(den * cnt for den, cnt in wallet.items())
            if capacity < total_due_cents:
                continue
            best_total = None
            best_counts = None
            for c20 in range(wallet[2000] + 1):
                for c10 in range(wallet[1000] + 1):
                    for c5 in range(wallet[500] + 1):
                        for c1 in range(wallet[100] + 1):
                            total = c20 * 2000 + c10 * 1000 + c5 * 500 + c1 * 100
                            if total < total_due_cents:
                                continue
                            bills = c20 + c10 + c5 + c1
                            if (
                                best_total is None
                                or total < best_total
                                or (total == best_total and bills < sum(best_counts.values()))
                                or (
                                    total == best_total
                                    and bills == sum(best_counts.values())
                                    and c20 > best_counts.get(2000, 0)
                                )
                            ):
                                best_total = total
                                best_counts = {2000: c20, 1000: c10, 500: c5, 100: c1}
            if best_counts is not None:
                return best_counts, best_total
        pay_cents = int(math.ceil(total_due_cents / 100)) * 100
        best_counts = {den: 0 for den in self.PAY_DENOMS}
        remaining = pay_cents
        for denom in self.PAY_DENOMS:
            best_counts[denom] = remaining // denom
            remaining %= denom
        return best_counts, pay_cents

    def _best_change_combo(self, change_cents: int) -> Dict[int, int]:
        remaining = max(0, change_cents)
        best = {den: 0 for den in self.CHANGE_DENOMS}
        for denom in self.CHANGE_DENOMS:
            best[denom] = remaining // denom
            remaining %= denom
        return best

    def _choose_item(self) -> None:
        item = random.choice(self._items)
        price = self._choose_price(item)
        self._item_name = item["name"]
        self._item_price = float(price)
        price_cents = price * 100
        if self.show_tax:
            raw_tax = price_cents * self.tax_rate
            tax_cents = int(round(raw_tax))
        else:
            tax_cents = 0
        self._tax_amount = tax_cents / 100
        self._total_due_cents = price_cents + tax_cents
        self._total_due = self._total_due_cents / 100
        self._pay_counts, self._pay_total_cents = self._pick_payment_combo(self._total_due_cents)
        if self._pay_total_cents < self._total_due_cents:
            self._pay_total_cents = math.ceil(self._total_due_cents / 100) * 100
        self._change_due_cents = self._pay_total_cents - self._total_due_cents
        self._available_change = {1000: 5, 500: 5, 100: 20, 25: 20, 10: 20, 5: 20, 1: 40}
        self._best_change_counts = self._best_change_combo(self._change_due_cents)
        self._item_image = self._build_item_image(item["name"], item["color"], item["emoji"])

    def get_game_state(self) -> ChangeGameState:
        return ChangeGameState(
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
            pay_total=self._pay_total_cents / 100,
            pay_counts={den: self._pay_counts.get(den, 0) for den in self.PAY_DENOMS},
            change_due=self._change_due_cents / 100,
            available_change=self._available_change,
            awaiting_retry=self._awaiting_retry,
        )

    def start_round(self) -> Optional[ChangeGameState]:
        if self.current_round >= self.rounds:
            return None
        if getattr(self, "_awaiting_retry", False) and self._item_name:
            return self.get_game_state()
        self._choose_item()
        return self.get_game_state()

    def _parse_answer(self, answer: str) -> Dict[int, int]:
        counts = {den: 0 for den in self.CHANGE_DENOMS}
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

    def submit_answer(self, answer: str) -> Tuple[bool, ChangeGameState]:
        if self._item_name is None:
            raise ValueError("No active round in progress")
        counts = self._parse_answer(answer)
        user_total_cents = sum(den * cnt for den, cnt in counts.items())
        correct_total = self._change_due_cents
        best_counts = self._best_change_counts.copy()
        is_correct = user_total_cents == correct_total
        if self.require_minimal_change and is_correct:
            is_correct = counts == best_counts
        if is_correct:
            self.score += 1
            self.current_round += 1
            self._awaiting_retry = False
        else:
            self._awaiting_retry = True
        self._last_result = {
            "counts": counts,
            "best_combo": best_counts,
            "user_total": user_total_cents / 100,
            "change_due": correct_total / 100,
            "is_correct": is_correct,
            "pay_counts": self._pay_counts.copy(),
            "pay_total": self._pay_total_cents / 100,
            "total_due": self._total_due,
        }
        return is_correct, self.get_game_state()

    def skip_round(self) -> Optional[ChangeGameState]:
        if self.current_round >= self.rounds:
            return None
        self.current_round += 1
        return self.start_round()

    def get_last_result(self) -> Dict[str, Any]:
        return self._last_result.copy()

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        return {
            "max_price": 50,
            "rounds": 8,
            "tax_rate": 0.0938,
            "show_tax": True,
            "require_minimal_bills": False,
        }

    def get_game_name(self) -> str:
        return "Change Game"

    def get_game_description(self) -> str:
        return "Calculate the exact change a customer should get back after paying."

    def serialize_state(self) -> Dict[str, Any]:
        state = self.get_game_state()
        return {
            "score": state.score,
            "current_round": state.current_round,
            "config": self._config,
            "item_name": state.item_name,
            "item_price": state.item_price,
            "tax_amount": state.tax_amount,
            "total_due": state.total_due,
            "tax_rate": state.tax_rate,
            "show_tax": state.show_tax,
            "item_image": state.item_image,
            "pay_total": state.pay_total,
            "pay_counts": state.pay_counts,
            "change_due": state.change_due,
            "available_change": state.available_change,
        }

    def deserialize_state(self, data: Dict[str, Any]) -> None:
        super().deserialize_state(data)
        self._item_name = data.get("item_name")
        self._item_price = data.get("item_price", 0)
        self._tax_amount = data.get("tax_amount", 0)
        self._total_due = data.get("total_due", 0)
        self._total_due_cents = int(round(self._total_due * 100))
        self._pay_total_cents = int(round(data.get("pay_total", 0) * 100))
        self._pay_counts = {int(k): v for k, v in (data.get("pay_counts") or {}).items()}
        self._change_due_cents = int(round(data.get("change_due", 0) * 100))
        self._available_change = {int(k): v for k, v in (data.get("available_change") or {}).items()}
        self._best_change_counts = self._best_change_combo(self._change_due_cents)
        self._item_image = data.get("item_image", "")
        self._awaiting_retry = data.get("awaiting_retry", False)
