"""© Cigav Productions LLC"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any


@dataclass
class GameState:
    """Base game state that all games should use or extend."""
    current_round: int
    total_rounds: int
    score: int
    # Additional game-specific fields can be added by subclasses


class BaseGameEngine(ABC):
    """Abstract base class for all game engines."""
    
    def __init__(self, **kwargs):
        """Initialize the game engine with configuration."""
        self.score = 0
        self.current_round = 0
        self._config = kwargs
    
    @abstractmethod
    def get_game_state(self) -> GameState:
        """Get the current state of the game."""
        pass
    
    @abstractmethod
    def start_round(self) -> Optional[GameState]:
        """Start a new round and return the game state."""
        pass
    
    @abstractmethod
    def submit_answer(self, answer: str) -> Tuple[bool, GameState]:
        """Submit an answer and get result.
        
        Returns:
            Tuple containing (is_correct, game_state).
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this game."""
        pass
    
    @abstractmethod
    def get_game_name(self) -> str:
        """Get the display name of this game."""
        pass
    
    @abstractmethod
    def get_game_description(self) -> str:
        """Get a description of this game."""
        pass
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize game state to a dictionary for session storage."""
        state = self.get_game_state()
        return {
            'score': state.score,
            'current_round': state.current_round,
            'config': self._config
        }
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.score = data.get('score', 0)
        self.current_round = data.get('current_round', 0)
        self._config = data.get('config', {})
