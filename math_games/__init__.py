"""© Cigav Productions LLC
Math games package."""
from .game_registry import GameRegistry
from .game_engine import RoundingGameEngine
from .addition_game import AdditionGameEngine
from .money_game import MoneyGameEngine
from .change_game import ChangeGameEngine

# Register all games
GameRegistry.register('rounding', RoundingGameEngine)
GameRegistry.register('addition', AdditionGameEngine)
GameRegistry.register('money', MoneyGameEngine)
GameRegistry.register('change', ChangeGameEngine)

__all__ = ['GameRegistry', 'RoundingGameEngine', 'AdditionGameEngine', 'MoneyGameEngine', 'ChangeGameEngine']
