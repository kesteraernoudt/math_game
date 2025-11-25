"""© Cigav Productions LLC"""
from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from .game_engine import GameState


class GameUI(ABC):
    """Abstract base class for game user interfaces."""
    
    @abstractmethod
    def display_welcome(self, rounds: int, factor: int) -> None:
        """Display welcome message with game rules."""

    @abstractmethod
    def display_round(self, state: GameState) -> None:
        """Display the current round state."""

    @abstractmethod
    def get_answer(self) -> str:
        """Get the player's answer."""

    @abstractmethod
    def display_result(self, is_correct: bool) -> None:
        """Display whether the answer was correct or not."""

    @abstractmethod
    def display_game_over(self, state: GameState) -> None:
        """Display game over message with final score."""


class ConsoleUI(GameUI):
    """Console-based user interface for the game."""
    
    def display_welcome(self, rounds: int, factor: int) -> None:
        print("\nWelcome to the Rounding Game!")
        print(f"You will be given {rounds} numbers to round.")
        print("For each number, decide if it should be rounded up or down")
        print(f"to the nearest multiple of {factor}.")
    
    def display_round(self, state: GameState) -> None:
        print(f"\nRound {state.current_round + 1}/{state.total_rounds}")
        print(f"Number: {state.current_number}")
        print(f"Should this number be rounded up or down to the nearest "
              f"multiple of {state.factor}?")
        print("Possible answers: 'up' or 'down'")
        print(f"Factor {state.factor}: {state.lower_multiple} or "
              f"{state.upper_multiple}")
    
    def get_answer(self) -> str:
        while True:
            answer = input("Your answer (up/down): ").lower()
            if answer in ["up", "down"]:
                return answer
            print("Invalid input! Please enter 'up' or 'down'")
    
    def display_result(self, is_correct: bool) -> None:
        print("Correct!" if is_correct else "Incorrect!")
    
    def display_game_over(self, state: GameState) -> None:
        print("\nGame Over!")
        print(f"Final Score: {state.score}/{state.total_rounds}")
