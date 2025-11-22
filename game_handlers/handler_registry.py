"""Registry for game handlers."""
from typing import Dict, Type, Optional
from .base_handler import BaseGameHandler


class HandlerRegistry:
    """Registry for game handlers."""
    
    _handlers: Dict[str, Type[BaseGameHandler]] = {}
    
    @classmethod
    def register(cls, game_id: str, handler_class: Type[BaseGameHandler]) -> None:
        """Register a game handler class."""
        cls._handlers[game_id] = handler_class
    
    @classmethod
    def get_handler(cls, game_id: str, engine) -> Optional[BaseGameHandler]:
        """Get a handler instance for a game."""
        handler_class = cls._handlers.get(game_id)
        if handler_class is None:
            # Fallback to a generic handler if available
            return None
        return handler_class(game_id, engine)
    
    @classmethod
    def has_handler(cls, game_id: str) -> bool:
        """Check if a handler exists for a game."""
        return game_id in cls._handlers


