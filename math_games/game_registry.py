"""© Cigav Productions LLC
Game registry for managing and discovering available games."""
from typing import Dict, Type, Optional
from .base_game import BaseGameEngine


class GameRegistry:
    """Registry for game engines."""
    
    _games: Dict[str, Type[BaseGameEngine]] = {}
    
    @classmethod
    def register(cls, game_id: str, game_class: Type[BaseGameEngine]) -> None:
        """Register a game engine class."""
        cls._games[game_id] = game_class
    
    @classmethod
    def get_game(cls, game_id: str) -> Optional[Type[BaseGameEngine]]:
        """Get a game engine class by ID."""
        return cls._games.get(game_id)
    
    @classmethod
    def list_games(cls) -> Dict[str, Type[BaseGameEngine]]:
        """List all registered games."""
        return cls._games.copy()
    
    @classmethod
    def get_game_info(cls, game_id: str) -> Optional[Dict[str, str]]:
        """Get game information (name, description) by ID."""
        game_class = cls.get_game(game_id)
        if game_class is None:
            return None
        
        # Create a temporary instance to get game info
        # Use default config to avoid errors
        try:
            default_config = game_class.get_default_config()
            instance = game_class(**default_config)
            return {
                'id': game_id,
                'name': instance.get_game_name(),
                'description': instance.get_game_description()
            }
        except Exception:
            # Fallback if we can't instantiate
            return {
                'id': game_id,
                'name': game_id.replace('_', ' ').title(),
                'description': 'Math game'
            }
    
    @classmethod
    def list_game_info(cls) -> Dict[str, Dict[str, str]]:
        """List information for all registered games."""
        return {
            game_id: cls.get_game_info(game_id)
            for game_id in cls._games.keys()
        }
