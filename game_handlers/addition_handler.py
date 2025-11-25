"""© Cigav Productions LLC
Handler for addition game-specific web logic."""
from typing import Dict, Any
from flask import session
from .base_handler import BaseGameHandler


class AdditionGameHandler(BaseGameHandler):
    """Handler for addition game web logic."""
    
    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        """Create a history entry for addition game."""
        return {
            'number1': session.get('last_number1'),
            'number2': session.get('last_number2'),
            'user_answer': answer,
            'correct_answer': getattr(state, 'correct_answer', None) or (
                session.get('last_number1', 0) + session.get('last_number2', 0)
            ),
            'is_correct': is_correct
        }
    
    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        """Save addition game state to session."""
        # Try to get number1/number2 from state
        if hasattr(new_state, 'number1'):
            game_state['number1'] = new_state.number1
        if hasattr(new_state, 'number2'):
            game_state['number2'] = new_state.number2
        # Fallback to engine attributes
        if hasattr(self.engine, '_number1'):
            game_state['number1'] = self.engine._number1
        if hasattr(self.engine, '_number2'):
            game_state['number2'] = self.engine._number2
    
    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial state structure for addition game."""
        return {
            'score': 0,
            'current_round': 0,
            'active': False,
            'over': False,
            'config': config,
            'number1': None,
            'number2': None,
        }
    
    def save_pre_answer_state(self, game_state: Dict[str, Any]) -> None:
        """Save state before processing answer."""
        session['last_number1'] = game_state.get('number1')
        session['last_number2'] = game_state.get('number2')
    
    def setup_ui_display(self, ui, game_state: Dict[str, Any]) -> None:
        """Setup UI display for GET requests."""
        # Addition game template handles display directly
        pass
    
    def setup_post_answer_ui(self, ui, new_state) -> None:
        """Setup UI display after processing answer."""
        # Addition game template handles display directly
        pass



