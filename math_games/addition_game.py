"""Example addition game to demonstrate how to add new games."""
import random
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
from .base_game import BaseGameEngine, GameState as BaseGameState


@dataclass
class AdditionGameState(BaseGameState):
    """Extended game state for addition game."""
    number1: int
    number2: int
    correct_answer: int


class AdditionGameEngine(BaseGameEngine):
    """A simple addition game where players solve addition problems."""
    
    def __init__(self, max_number=50, rounds=10, **kwargs):
        super().__init__(max_number=max_number, rounds=rounds, **kwargs)
        self.max_number = max_number
        self.rounds = rounds
        self.score = 0
        self.current_round = 0
        self._number1 = None
        self._number2 = None
        random.seed(datetime.now().timestamp())
    
    def _generate_problem(self) -> Tuple[int, int]:
        """Generate two random numbers for addition."""
        num1 = random.randint(1, self.max_number)
        num2 = random.randint(1, self.max_number)
        return num1, num2
    
    def _check_answer(self, num1: int, num2: int, answer: str) -> bool:
        """Check if the answer is correct."""
        try:
            user_answer = int(answer)
            correct_answer = num1 + num2
            return user_answer == correct_answer
        except ValueError:
            return False
    
    def get_game_state(self) -> AdditionGameState:
        """Get the current state of the game."""
        return AdditionGameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            number1=self._number1 or 0,
            number2=self._number2 or 0,
            correct_answer=(self._number1 or 0) + (self._number2 or 0)
        )
    
    def start_round(self) -> Optional[AdditionGameState]:
        """Start a new round and return the game state."""
        if self.current_round >= self.rounds:
            return None
        
        self._number1, self._number2 = self._generate_problem()
        return self.get_game_state()
    
    def submit_answer(self, answer: str) -> Tuple[bool, AdditionGameState]:
        """Submit an answer and get result."""
        if not self._number1 or not self._number2:
            raise ValueError("No active round in progress")
        
        is_correct = self._check_answer(self._number1, self._number2, answer)
        if is_correct:
            self.score += 1
        
        self.current_round += 1
        return is_correct, self.get_game_state()
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this game."""
        return {
            'max_number': 50,
            'rounds': 10
        }
    
    def get_game_name(self) -> str:
        """Get the display name of this game."""
        return "Addition Game"
    
    def get_game_description(self) -> str:
        """Get a description of this game."""
        return "Solve addition problems as fast as you can!"
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize game state to a dictionary for session storage."""
        state = self.get_game_state()
        return {
            'score': state.score,
            'current_round': state.current_round,
            'number1': state.number1,
            'number2': state.number2,
            'config': {
                'max_number': self.max_number,
                'rounds': self.rounds
            }
        }
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.score = data.get('score', 0)
        self.current_round = data.get('current_round', 0)
        self._number1 = data.get('number1')
        self._number2 = data.get('number2')
        config = data.get('config', {})
        self.max_number = config.get('max_number', 50)
        self.rounds = config.get('rounds', 10)
        self._config = config


