import random
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
from .base_game import BaseGameEngine, GameState as BaseGameState


@dataclass
class RoundingGameState(BaseGameState):
    """Extended game state for rounding game."""
    current_number: int
    factor: int
    lower_multiple: int
    upper_multiple: int


# Keep old GameState for backward compatibility
GameState = RoundingGameState


class RoundingGameEngine(BaseGameEngine):
    def __init__(self, max_number=100, rounds=10, factor=5, **kwargs):
        super().__init__(max_number=max_number, rounds=rounds, factor=factor, **kwargs)
        self.max_number = max_number
        self.rounds = rounds
        self.factor = factor
        self.score = 0
        self.current_round = 0
        self._current_number = None
        random.seed(datetime.now().timestamp()) 

    def _generate_number(self):
        return random.randint(1, self.max_number)

    def _get_closest_multiples(self, number) -> Tuple[int, int]:
        lower = (number // self.factor) * self.factor
        upper = lower + self.factor
        return lower, upper

    def _check_answer(self, number: int, answer: str) -> bool:
        lower, upper = self._get_closest_multiples(number)
        
        if abs(number - lower) < abs(number - upper):
            correct_answer = "down"
        elif abs(number - lower) > abs(number - upper):
            correct_answer = "up"
        else:  # Equal distance, round up by convention
            correct_answer = "up"
            
        return answer.lower() == correct_answer

    def get_game_state(self) -> RoundingGameState:
        """Get the current state of the game."""
        if self._current_number is not None:
            lower, upper = self._get_closest_multiples(self._current_number)
        else:
            lower, upper = 0, 0
        return RoundingGameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            current_number=self._current_number,
            factor=self.factor,
            lower_multiple=lower,
            upper_multiple=upper
        )

    def start_round(self) -> Optional[RoundingGameState]:
        """Start a new round and return the game state."""
        if self.current_round >= self.rounds:
            return None
            
        self._current_number = self._generate_number()
        return self.get_game_state()

    def submit_answer(self, answer: str) -> Tuple[bool, RoundingGameState]:
        """Submit an answer and get result.
        
        Returns:
            Tuple containing (is_correct, game_state).
        """
        if not self._current_number:
            raise ValueError("No active round in progress")
            
        is_correct = self._check_answer(self._current_number, answer)
        if is_correct:
            self.score += 1
            
        self.current_round += 1
        return is_correct, self.get_game_state()
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this game."""
        return {
            'max_number': 100,
            'rounds': 10,
            'factor': 10
        }
    
    def get_game_name(self) -> str:
        """Get the display name of this game."""
        return "Rounding Game"
    
    def get_game_description(self) -> str:
        """Get a description of this game."""
        return "Round numbers up or down to the nearest multiple"
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize game state to a dictionary for session storage."""
        state = self.get_game_state()
        return {
            'score': state.score,
            'current_round': state.current_round,
            'current_number': state.current_number,
            'config': {
                'max_number': self.max_number,
                'rounds': self.rounds,
                'factor': self.factor
            }
        }
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.score = data.get('score', 0)
        self.current_round = data.get('current_round', 0)
        self._current_number = data.get('current_number')
        config = data.get('config', {})
        self.max_number = config.get('max_number', 100)
        self.rounds = config.get('rounds', 10)
        self.factor = config.get('factor', 10)
        self._config = config
