import random
from dataclasses import dataclass
from typing import Tuple, Optional
from datetime import datetime

@dataclass
class GameState:
    current_round: int
    total_rounds: int
    score: int
    current_number: int
    factor: int
    lower_multiple: int
    upper_multiple: int


class RoundingGameEngine:
    def __init__(self, max_number=100, rounds=10, factor=5):
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

    def get_game_state(self) -> GameState:
        """Get the current state of the game."""
        if self._current_number is not None:
            lower, upper = self._get_closest_multiples(self._current_number)
        else:
            lower, upper = 0, 0
        return GameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            current_number=self._current_number,
            factor=self.factor,
            lower_multiple=lower,
            upper_multiple=upper
        )

    def start_round(self) -> Optional[GameState]:
        """Start a new round and return the game state."""
        if self.current_round >= self.rounds:
            return None
            
        self._current_number = self._generate_number()
        return self.get_game_state()

    def submit_answer(self, answer: str) -> Tuple[bool, GameState]:
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
