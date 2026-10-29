"""© Cigav Productions LLC
Session support for the Money Compare game."""
from typing import Any, Dict
from flask import session
from .base_handler import BaseGameHandler


class MoneyCompareGameHandler(BaseGameHandler):
    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        result = self.engine.get_last_result()
        return {
            "selected_side": result.get("selected_side", answer),
            "correct_side": result.get("correct_side", ""),
            "comparison": result.get("comparison", "higher"),
            "left_total": result.get("left_total", 0),
            "right_total": result.get("right_total", 0),
            "is_correct": is_correct,
        }

    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        game_state["left_counts"] = new_state.left_counts
        game_state["right_counts"] = new_state.right_counts
        game_state["comparison"] = new_state.comparison
        game_state["correct_side"] = new_state.correct_side

    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "score": 0, "current_round": 0, "active": False, "over": False,
            "config": config, "left_counts": {}, "right_counts": {},
            "comparison": "higher", "correct_side": "left",
        }

    def handle_skip_round(self, game_state: Dict[str, Any]) -> None:
        session.setdefault("history", []).append({"is_correct": False, "skipped": True})
        new_state = self.engine.skip_round()
        game_state["score"] = self.engine.score
        game_state["current_round"] = self.engine.current_round
        if new_state is None:
            game_state["active"] = False
            game_state["over"] = True
        else:
            game_state["active"] = True
            self.save_state_to_session(game_state, new_state)
        session["games"][self.game_id] = game_state
