from math_games.game_engine import RoundingGameEngine
from math_games.ui import ConsoleUI


def main():
    # Create the game engine and UI
    game = RoundingGameEngine()
    ui = ConsoleUI()
    
    # Display welcome message
    ui.display_welcome(game.rounds, game.factor)
    
    # Main game loop
    while True:
        # Start new round
        state = game.start_round()
        if state is None:  # Game is over
            break
            
        # Display round and get answer
        ui.display_round(state)
        answer = ui.get_answer()
        
        # Process answer and show result
        is_correct, state = game.submit_answer(answer)
        ui.display_result(is_correct)
    
    # Game over
    ui.display_game_over(game.get_game_state())


if __name__ == "__main__":
    main()
"""© Cigav Productions LLC"""
