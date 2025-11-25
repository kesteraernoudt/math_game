"""© Cigav Productions LLC
Handler for rounding game-specific web logic."""
from typing import Dict, Any
from flask import session
from .base_handler import BaseGameHandler


class RoundingGameHandler(BaseGameHandler):
    """Handler for rounding game web logic."""
    
    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        """Create a history entry for rounding game."""
        return {
            'number': session.get('current_number'),
            'answer': answer,
            'is_correct': is_correct
        }
    
    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        """Save rounding game state to session."""
        # Try to get current_number from state
        if hasattr(new_state, 'current_number'):
            game_state['current_number'] = new_state.current_number
            session['current_number'] = new_state.current_number
        # Fallback to engine attributes
        elif hasattr(self.engine, '_current_number'):
            game_state['current_number'] = self.engine._current_number
            session['current_number'] = self.engine._current_number
    
    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial state structure for rounding game."""
        return {
            'score': 0,
            'current_round': 0,
            'active': False,
            'over': False,
            'config': config,
            'current_number': None,
        }
    
    def save_pre_answer_state(self, game_state: Dict[str, Any]) -> None:
        """Save state before processing answer."""
        session['current_number'] = game_state.get('current_number')
    
    def setup_ui_display(self, ui, game_state: Dict[str, Any]) -> None:
        """Setup UI display for GET requests."""
        config = game_state.get('config', {})
        rounds = config.get('rounds', 10)
        factor = config.get('factor', 10)
        ui.display_welcome(rounds, factor)
        ui.display_round(self.engine.get_game_state())
    
    def setup_post_answer_ui(self, ui, new_state) -> None:
        """Setup UI display after processing answer."""
        ui.display_round(new_state)
    
    def should_display_round(self) -> bool:
        """Return True if this game should display round info via UI."""
        return True

