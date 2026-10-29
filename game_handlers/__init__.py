"""© Cigav Productions LLC
Game handlers for managing game-specific web logic."""
from .base_handler import BaseGameHandler
from .rounding_handler import RoundingGameHandler
from .addition_handler import AdditionGameHandler
from .money_handler import MoneyGameHandler
from .change_handler import ChangeGameHandler
from .money_compare_handler import MoneyCompareGameHandler
from .handler_registry import HandlerRegistry

# Register handlers
HandlerRegistry.register('rounding', RoundingGameHandler)
HandlerRegistry.register('addition', AdditionGameHandler)
HandlerRegistry.register('money', MoneyGameHandler)
HandlerRegistry.register('change', ChangeGameHandler)
HandlerRegistry.register('money_compare', MoneyCompareGameHandler)

__all__ = [
    'BaseGameHandler',
    'HandlerRegistry',
    'RoundingGameHandler',
    'AdditionGameHandler',
    'MoneyGameHandler',
    'ChangeGameHandler',
    'MoneyCompareGameHandler',
]


