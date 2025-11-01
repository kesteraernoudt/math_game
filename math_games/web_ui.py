from flask import session
from .ui import GameUI
from .game_engine import GameState


class WebUI(GameUI):
    """Web-based user interface for the game."""
    
    def __init__(self):
        self._messages = []
        if 'history' not in session:
            session['history'] = []  # List of (number, answer, is_correct) tuples
    
    def display_welcome(self, rounds: int, factor: int) -> None:
        self._messages = [
            "Welcome to the Rounding Game!",
            f"You will be given {rounds} numbers to round.",
            "For each number, decide if it should be rounded up or down",
            f"to the nearest multiple of {factor}."
        ]
    
    def display_round(self, state: GameState) -> None:
        self._messages = [
            f"Round {state.current_round + 1}/{state.total_rounds}",
            f"Number: {state.current_number}",
            "Should this number be rounded up or down to the nearest",
            f"multiple of {state.factor}?",
            f"Factor {state.factor}: {state.lower_multiple} or {state.upper_multiple}"
        ]
    
    def get_answer(self) -> str:
        # This will be handled by the web form submission
        return session.get('last_answer', '')
    
    def display_result(self, is_correct: bool) -> None:
        self._messages.append("Correct!" if is_correct else "Incorrect!")
        # Add current round to history
        if 'current_number' in session and 'last_answer' in session:
            history_entry = {
                'number': session['current_number'],
                'answer': session['last_answer'],
                'is_correct': is_correct
            }
            session['history'] = session.get('history', []) + [history_entry]
    
    def display_game_over(self, state: GameState) -> None:
        self._messages = [
            "Game Over!",
            f"Final Score: {state.score}/{state.total_rounds}"
        ]
        # Do not clear history here; let it show at the end
    
    def get_messages(self) -> list[str]:
        """Get the current messages to display."""
        return self._messages.copy()
    
    def clear_messages(self) -> None:
        """Clear the current messages."""
        self._messages = []