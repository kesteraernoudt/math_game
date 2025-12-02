"""© Cigav Productions LLC
Handler for the change game web logic."""
from typing import Dict, Any
from flask import session
from .base_handler import BaseGameHandler


class ChangeGameHandler(BaseGameHandler):
    """Handles state persistence and history for Change Game."""

    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        last_round = session.get("last_change_round", {})
        last_result = getattr(self.engine, "get_last_result", lambda: {})() or {}
        return {
            "item_name": last_round.get("item_name", ""),
            "item_price": last_round.get("item_price", 0),
            "tax_amount": last_round.get("tax_amount", 0),
            "total_due": last_round.get("total_due", 0),
            "pay_total": last_round.get("pay_total", 0),
            "pay_breakdown": last_round.get("pay_breakdown", {}),
            "user_counts": last_result.get("counts", {}),
            "best_counts": last_result.get("best_combo", {}),
            "user_total": last_result.get("user_total", 0),
            "change_due": last_result.get("change_due", 0),
            "is_correct": is_correct,
            "show_tax": last_round.get("show_tax", True),
            "skipped": False,
            "raw_answer": answer,
            "debug_payload": session.get("debug_payload"),
        }

    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        game_state["item_name"] = new_state.item_name
        game_state["item_price"] = new_state.item_price
        game_state["tax_amount"] = new_state.tax_amount
        game_state["total_due"] = new_state.total_due
        game_state["tax_rate"] = new_state.tax_rate
        game_state["show_tax"] = new_state.show_tax
        game_state["item_image"] = new_state.item_image
        game_state["pay_total"] = new_state.pay_total
        game_state["pay_counts"] = new_state.pay_counts
        game_state["change_due"] = new_state.change_due
        game_state["available_counts"] = new_state.available_change
        game_state["awaiting_retry"] = new_state.awaiting_retry

    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "score": 0,
            "current_round": 0,
            "active": False,
            "over": False,
            "config": config,
            "item_name": "",
            "item_price": 0,
            "tax_amount": 0,
            "total_due": 0,
            "item_image": "",
            "pay_total": 0,
            "pay_counts": {},
            "change_due": 0,
            "available_counts": {1000: 5, 500: 5, 100: 20, 25: 20, 10: 20, 5: 20, 1: 40},
            "awaiting_retry": False,
        }

    def save_pre_answer_state(self, game_state: Dict[str, Any]) -> None:
        session["last_change_round"] = {
            "item_name": game_state.get("item_name", ""),
            "item_price": game_state.get("item_price", 0),
            "tax_amount": game_state.get("tax_amount", 0),
            "total_due": game_state.get("total_due", 0),
            "pay_total": game_state.get("pay_total", 0),
            "pay_breakdown": game_state.get("pay_counts", {}),
            "show_tax": game_state.get("show_tax", True),
            "change_due": game_state.get("change_due", 0),
        }

    def handle_skip_round(self, game_state: Dict[str, Any]) -> None:
        if "history" not in session:
            session["history"] = []
        session["history"].append({
            "item_name": game_state.get("item_name", ""),
            "item_price": game_state.get("item_price", 0),
            "tax_amount": game_state.get("tax_amount", 0),
            "total_due": game_state.get("total_due", 0),
            "pay_total": game_state.get("pay_total", 0),
            "pay_breakdown": game_state.get("pay_counts", {}),
            "user_counts": {},
            "best_counts": {},
            "user_total": 0,
            "change_due": game_state.get("change_due", 0),
            "is_correct": False,
            "show_tax": game_state.get("show_tax", True),
            "skipped": True,
        })
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
