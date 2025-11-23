"""Money game where players build payments with $20, $5, and $1 bills."""
import random
import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import quote
from .base_game import BaseGameEngine, GameState as BaseGameState


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


class MoneyGameEngine(BaseGameEngine):
    """Game engine for building the best bill combination to match a price."""
    
    def __init__(
        self,
        max_price: int = 50,
        rounds: int = 10,
        tax_rate: float = 0.08,
        show_tax: bool = True,
        require_minimal_bills: bool = False,
        **kwargs: Any,
    ):
        super().__init__(max_price=max_price, rounds=rounds, tax_rate=tax_rate, show_tax=show_tax, require_minimal_bills=require_minimal_bills, **kwargs)
        self.max_price = max_price
        self.rounds = rounds
        self.tax_rate = tax_rate
        self.show_tax = show_tax
        self.require_minimal_bills = require_minimal_bills
        self.score = 0
        self.current_round = 0
        self._item_name: Optional[str] = None
        self._item_price: int = 0
        self._tax_amount: int = 0
        self._total_due: int = 0
        self._item_image: str = ""
        self._awaiting_retry: bool = False
        self._last_result: Dict[str, Any] = {}
        self._items = [
            {"name": "Burger Meal", "min_price": 7, "max_price": 18, "color": "#f25f4c", "emoji": "🍔"},
            {"name": "Taco Trio", "min_price": 5, "max_price": 18, "color": "#ff8c42", "emoji": "🌮"},
            {"name": "Pizza Box", "min_price": 12, "max_price": 30, "color": "#d7263d", "emoji": "🍕"},
            {"name": "Chicken Basket", "min_price": 9, "max_price": 24, "color": "#f2b134", "emoji": "🍗"},
            {"name": "Grocery Apples", "min_price": 3, "max_price": 12, "color": "#5f0f40", "emoji": "🍎"},
            {"name": "Cereal Box", "min_price": 4, "max_price": 16, "color": "#2ec4b6", "emoji": "🥣"},
            {"name": "Orange Juice", "min_price": 3, "max_price": 12, "color": "#ff9f1c", "emoji": "🧃"},
            {"name": "Veggie Basket", "min_price": 6, "max_price": 18, "color": "#0ead69", "emoji": "🥕"},
            {"name": "Family Taco Pack", "min_price": 18, "max_price": 38, "color": "#f97316", "emoji": "🌯"},
            {"name": "Party Sub Tray", "min_price": 24, "max_price": 45, "color": "#f59e0b", "emoji": "🥪"},
            {"name": "Sushi Platter", "min_price": 22, "max_price": 48, "color": "#2563eb", "emoji": "🍣"},
            {"name": "Steak Dinner", "min_price": 25, "max_price": 60, "color": "#b91c1c", "emoji": "🥩"},
            {"name": "Seafood Bucket", "min_price": 20, "max_price": 55, "color": "#0ea5e9", "emoji": "🦐"},
            {"name": "BBQ Feast", "min_price": 28, "max_price": 65, "color": "#ea580c", "emoji": "🍖"},
            {"name": "Grocery Cart", "min_price": 25, "max_price": 70, "color": "#059669", "emoji": "🛒"},
            {"name": "Picnic Pack", "min_price": 15, "max_price": 40, "color": "#4f46e5", "emoji": "🧺"},
            {"name": "Veggie Burger", "min_price": 7, "max_price": 16, "color": "#3b8c5a", "emoji": "🥗"},
            {"name": "Falafel Wrap", "min_price": 6, "max_price": 15, "color": "#2f855a", "emoji": "🥙"},
            {"name": "Tofu Stir Fry", "min_price": 10, "max_price": 22, "color": "#14b8a6", "emoji": "🍲"},
            {"name": "Veggie Sushi Roll", "min_price": 8, "max_price": 18, "color": "#0ea5e9", "emoji": "🥒"},
            {"name": "Caprese Salad", "min_price": 6, "max_price": 14, "color": "#ef4444", "emoji": "🥬"},
            {"name": "Mediterranean Bowl", "min_price": 12, "max_price": 26, "color": "#f59e0b", "emoji": "🥗"},
        ]
        random.seed(datetime.now().timestamp())

    def _build_item_image(self, label: str, color: str, emoji: str) -> str:
        """Create a small inline SVG data URI for the item."""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="210" viewBox="0 0 240 210">'
            f'<rect width="240" height="210" rx="22" fill="{color}"/>'
            f'<text x="120" y="100" font-size="68" text-anchor="middle" dominant-baseline="middle">{emoji}</text>'
            f'<text x="120" y="178" font-size="24" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif">{label}</text>'
            f"</svg>"
        )
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    def _choose_price(self, item: Dict[str, Any]) -> int:
        """Choose a whole-dollar price for the given item honoring the max price cap."""
        low = min(item["min_price"], self.max_price)
        high = min(item["max_price"], self.max_price)
        if high < 1:
            return 1
        if low > high:
            low = max(1, high)
        return random.randint(low, high)

    def _choose_item(self) -> None:
        item = random.choice(self._items)
        self._item_name = item["name"]
        self._item_price = self._choose_price(item)
        self._tax_amount = round(self._item_price * self.tax_rate) if self.show_tax else 0
        if self.show_tax:
            raw_tax = self._item_price * self.tax_rate
            self._tax_amount = round(raw_tax, 2)
        else:
            self._tax_amount = 0.0
        self._total_due = round(self._item_price + self._tax_amount, 2)
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
    
    def get_best_combo(self) -> Dict[int, int]:
        """Public helper for the best combo of the current total."""
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
        pay_total = math.ceil(self._total_due)
        best_combo = self._best_combo(self._total_due)
        if self.require_minimal_bills:
            is_correct = user_total == pay_total and counts == best_combo
        else:
            # Accept any payment that meets or exceeds the needed total
            is_correct = user_total >= pay_total

        self._last_result = {
            "counts": counts,
            "best_combo": best_combo,
            "user_total": user_total,
            "total_due": self._total_due,
            "pay_total": pay_total,
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
            "tax_rate": 0.08,
            "show_tax": False,
            "require_minimal_bills": False,
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
            "config": {
                "max_price": self.max_price,
                "rounds": self.rounds,
                "tax_rate": self.tax_rate,
                "show_tax": self.show_tax,
                "require_minimal_bills": self.require_minimal_bills,
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
        self._item_image = data.get("item_image", "")
        self._awaiting_retry = data.get("awaiting_retry", False)
        config = data.get("config", {})
        self.max_price = config.get("max_price", self.max_price)
        self.rounds = config.get("rounds", self.rounds)
        self.tax_rate = config.get("tax_rate", self.tax_rate)
        self.show_tax = config.get("show_tax", self.show_tax)
        self.require_minimal_bills = config.get("require_minimal_bills", self.require_minimal_bills)
        self._config = config
