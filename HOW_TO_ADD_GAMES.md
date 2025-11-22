# How to Add a New Game

This guide explains how to add a new game to the math games application.

## Step 1: Create Your Game Engine

Create a new file in the `math_games/` directory (e.g., `my_game.py`) and create a class that inherits from `BaseGameEngine`:

```python
from math_games.base_game import BaseGameEngine, GameState as BaseGameState
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any

@dataclass
class MyGameState(BaseGameState):
    """Extended game state for your game."""
    # Add any game-specific fields here
    current_problem: str
    # ... other fields

class MyGameEngine(BaseGameEngine):
    def __init__(self, rounds=10, difficulty='easy', **kwargs):
        super().__init__(rounds=rounds, difficulty=difficulty, **kwargs)
        self.rounds = rounds
        self.difficulty = difficulty
        self.score = 0
        self.current_round = 0
        # Initialize your game state
    
    def get_game_state(self) -> MyGameState:
        """Get the current state of the game."""
        return MyGameState(
            current_round=self.current_round,
            total_rounds=self.rounds,
            score=self.score,
            current_problem="...",  # Your game-specific data
        )
    
    def start_round(self) -> Optional[MyGameState]:
        """Start a new round and return the game state."""
        if self.current_round >= self.rounds:
            return None
        # Generate new problem/round
        return self.get_game_state()
    
    def submit_answer(self, answer: str) -> Tuple[bool, MyGameState]:
        """Submit an answer and get result."""
        # Check if answer is correct
        is_correct = self._check_answer(answer)
        if is_correct:
            self.score += 1
        self.current_round += 1
        return is_correct, self.get_game_state()
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this game."""
        return {
            'rounds': 10,
            'difficulty': 'easy'
        }
    
    def get_game_name(self) -> str:
        """Get the display name of this game."""
        return "My Game"
    
    def get_game_description(self) -> str:
        """Get a description of this game."""
        return "Description of what the game does"
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize game state for session storage."""
        state = self.get_game_state()
        return {
            'score': state.score,
            'current_round': state.current_round,
            'config': {
                'rounds': self.rounds,
                'difficulty': self.difficulty
            }
            # Add any other state you need to persist
        }
    
    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from session storage."""
        self.score = data.get('score', 0)
        self.current_round = data.get('current_round', 0)
        config = data.get('config', {})
        self.rounds = config.get('rounds', 10)
        self.difficulty = config.get('difficulty', 'easy')
        self._config = config
```

## Step 2: Register Your Game

In `math_games/__init__.py`, import and register your game:

```python
from .my_game import MyGameEngine

# Register all games
GameRegistry.register('my_game', MyGameEngine)
```

## Step 3: Create a Game-Specific Template

Each game should have its own template file named `game_<game_id>.html` in the `templates/` directory. The Flask app will automatically use your game-specific template if it exists, and fall back to the generic `game.html` if not.

### Template Naming Convention

- Template name: `game_<game_id>.html`
- Example: If your game ID is `my_game`, create `templates/game_my_game.html`

### Template Variables

Your template will have access to these variables:

- `messages`: List of messages to display (from WebUI)
- `game_active`: Boolean indicating if game is currently active
- `game_over`: Boolean indicating if game has ended
- `session`: Flask session object with game state
- `show_debug`: Boolean for debug mode
- `game_id`: The game ID string
- `game_info`: Dictionary with game name and description
- `game_config`: Current game configuration from session
- `default_config`: Default configuration for the game
- `engine`: The game engine instance (can access game state via `engine.get_game_state()`)

### Example Template Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ game_info.name }}</title>
    <style>
        /* Your game-specific styles */
    </style>
</head>
<body>
    <!-- Navigation -->
    <div>
        <a href="{{ url_for('index') }}">← Back to Games</a>
    </div>

    <div class="game-box">
        {% if game_active %}
            <!-- Active game UI -->
            <!-- Access game state via: session.games[game_id] or engine.get_game_state() -->
            <form method="POST">
                <!-- Your game-specific input fields -->
                <input type="text" name="answer" required>
                <button type="submit">Submit</button>
            </form>
            
            <!-- Score display -->
            <div>Score: {{ session.games[game_id].get('score', 0) }}</div>
            
            <!-- History -->
            {% if session.history %}
                {% for entry in session.history %}
                    <!-- Display history entries -->
                {% endfor %}
            {% endif %}
        {% else %}
            <!-- Configuration form -->
            <form method="POST">
                <!-- Configuration inputs based on default_config -->
                <input type="number" name="rounds" value="{{ game_config.get('rounds', default_config.get('rounds', 10)) }}">
                <button type="submit" name="action" value="start_game">Start Game</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
```

### Examples

- **Rounding Game**: Uses `templates/game.html` (the default/fallback template) with up/down buttons
- **Addition Game**: Uses `templates/game_addition.html` with a text input field for numeric answers

See `templates/game_addition.html` for a complete example of a game-specific template.

## Step 4: Test Your Game

1. Start the Flask app: `python web_app.py`
2. Navigate to `http://localhost:5000`
3. You should see your new game in the list
4. Click on it and test the gameplay

## Example Games

- **RoundingGameEngine** (`game_engine.py`): A game where players round numbers up or down
- **AdditionGameEngine** (`addition_game.py`): A simple addition game (example implementation)

## Key Points

- All games must inherit from `BaseGameEngine`
- Implement all abstract methods
- Use `serialize_state()` and `deserialize_state()` to persist game state in sessions
- Register your game in `__init__.py`
- The game will automatically appear on the game selection page

