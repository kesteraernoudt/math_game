"""Game handlers for managing game-specific web logic."""
from .base_handler import BaseGameHandler
from .rounding_handler import RoundingGameHandler
from .addition_handler import AdditionGameHandler
from .money_handler import MoneyGameHandler
from .handler_registry import HandlerRegistry

# Register handlers
HandlerRegistry.register('rounding', RoundingGameHandler)
HandlerRegistry.register('addition', AdditionGameHandler)
HandlerRegistry.register('money', MoneyGameHandler)

__all__ = ['BaseGameHandler', 'HandlerRegistry', 'RoundingGameHandler', 'AdditionGameHandler', 'MoneyGameHandler']


