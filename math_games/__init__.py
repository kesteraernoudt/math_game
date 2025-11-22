"""Math games package."""
from .game_registry import GameRegistry
from .game_engine import RoundingGameEngine
from .addition_game import AdditionGameEngine
from .money_game import MoneyGameEngine

# Register all games
GameRegistry.register('rounding', RoundingGameEngine)
GameRegistry.register('addition', AdditionGameEngine)
GameRegistry.register('money', MoneyGameEngine)

__all__ = ['GameRegistry', 'RoundingGameEngine', 'AdditionGameEngine', 'MoneyGameEngine']
