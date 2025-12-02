"""© Cigav Productions LLC
Shared catalog and helpers for grocery/food items used across games."""

import random
from typing import Any, Dict, List
from urllib.parse import quote


class ItemCatalog:
    """Central item catalog shared by money and change games."""

    ITEMS: List[Dict[str, Any]] = [
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
        {"name": "Steak Dinner", "min_price": 25, "max_price": 50, "color": "#b91c1c", "emoji": "🥩"},
        {"name": "Seafood Bucket", "min_price": 20, "max_price": 50, "color": "#0ea5e9", "emoji": "🦐"},
        {"name": "BBQ Feast", "min_price": 28, "max_price": 50, "color": "#ea580c", "emoji": "🍖"},
        {"name": "Grocery Cart", "min_price": 25, "max_price": 50, "color": "#059669", "emoji": "🛒"},
        {"name": "Picnic Pack", "min_price": 15, "max_price": 40, "color": "#4f46e5", "emoji": "🧺"},
        {"name": "Veggie Burger", "min_price": 7, "max_price": 16, "color": "#3b8c5a", "emoji": "🥗"},
        {"name": "Falafel Wrap", "min_price": 6, "max_price": 15, "color": "#2f855a", "emoji": "🥙"},
        {"name": "Tofu Stir Fry", "min_price": 10, "max_price": 22, "color": "#14b8a6", "emoji": "🍲"},
        {"name": "Veggie Sushi Roll", "min_price": 8, "max_price": 18, "color": "#0ea5e9", "emoji": "🥒"},
        {"name": "Caprese Salad", "min_price": 6, "max_price": 14, "color": "#ef4444", "emoji": "🥬"},
        {"name": "Mediterranean Bowl", "min_price": 12, "max_price": 26, "color": "#f59e0b", "emoji": "🥗"},
        {"name": "Soda", "min_price": 2, "max_price": 6, "color": "#2563eb", "emoji": "🥤"},
        {"name": "Diet Soda", "min_price": 2, "max_price": 6, "color": "#0ea5e9", "emoji": "🥤"},
        {"name": "Popcorn Bucket", "min_price": 4, "max_price": 12, "color": "#f59e0b", "emoji": "🍿"},
        {"name": "Kettle Corn", "min_price": 5, "max_price": 14, "color": "#fbbf24", "emoji": "🍿"},
        {"name": "Chocolate Candy", "min_price": 3, "max_price": 10, "color": "#7c3aed", "emoji": "🍫"},
        {"name": "Gummy Candy", "min_price": 3, "max_price": 10, "color": "#10b981", "emoji": "🍬"},
        {"name": "Sugar-Free Candy", "min_price": 3, "max_price": 10, "color": "#a855f7", "emoji": "🍭"},
        {"name": "Cupcake", "min_price": 4, "max_price": 12, "color": "#f472b6", "emoji": "🧁"},
        {"name": "Slice of Cake", "min_price": 5, "max_price": 14, "color": "#fb7185", "emoji": "🍰"},
        {"name": "Diet Chocolate Bar", "min_price": 3, "max_price": 10, "color": "#8b5cf6", "emoji": "🍫"},
    ]

    @classmethod
    def items(cls) -> List[Dict[str, Any]]:
        """Return the shared item catalog."""
        return cls.ITEMS

    @staticmethod
    def build_image(label: str, color: str, emoji: str) -> str:
        """Create an inline SVG data URI for the item card."""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="210" viewBox="0 0 240 210">'
            f'<rect width="240" height="210" rx="22" fill="{color}"/>'
            f'<text x="120" y="100" font-size="68" text-anchor="middle" dominant-baseline="middle">{emoji}</text>'
            f'<text x="120" y="178" font-size="24" text-anchor="middle" fill="#fff" font-family="Arial,sans-serif">{label}</text>'
            f"</svg>"
        )
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    @staticmethod
    def choose_price(item: Dict[str, Any], max_price: int, rng: Any = None) -> int:
        """Choose a whole-dollar price within the item range and max cap."""
        r = rng or random
        low = min(item["min_price"], max_price)
        high = min(item["max_price"], max_price)
        if high < 1:
            return 1
        if low > high:
            low = max(1, high)
        return r.randint(low, high)
