"""Base handler for game-specific web logic."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from flask import session


class BaseGameHandler(ABC):
    """Base class for game-specific web handlers."""
    
    def __init__(self, game_id: str, engine):
        """Initialize the handler with a game ID and engine."""
        self.game_id = game_id
        self.engine = engine
    
    @abstractmethod
    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        """Create a history entry for this game type."""
        pass
    
    @abstractmethod
    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        """Save game-specific state to the session."""
        pass
    
    @abstractmethod
    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get the initial state structure for this game type."""
        pass
    
    def save_pre_answer_state(self, game_state: Dict[str, Any]) -> None:
        """Save state needed before processing answer (for history)."""
        pass
    
    def setup_ui_display(self, ui, game_state: Dict[str, Any]) -> None:
        """Setup UI display for GET requests."""
        pass
    
    def setup_post_answer_ui(self, ui, new_state) -> None:
        """Setup UI display after processing answer."""
        pass
    
    def should_display_round(self) -> bool:
        """Return True if this game should display round info via UI."""
        return False


