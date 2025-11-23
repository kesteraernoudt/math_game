"""Handler for the money game web-specific logic."""
from typing import Dict, Any
from flask import session
from .base_handler import BaseGameHandler


class MoneyGameHandler(BaseGameHandler):
    """Handler for money game web interactions."""
    
    def create_history_entry(self, answer: str, state, is_correct: bool) -> Dict[str, Any]:
        """Create a history entry for the money game."""
        last_round = session.get("last_money_round", {})
        last_result = {}
        if hasattr(self.engine, "get_last_result"):
            last_result = self.engine.get_last_result()
        counts = last_result.get("counts", {})
        user_total = last_result.get("user_total")
        best_combo = last_result.get("best_combo") or {}
        total_due = last_result.get("total_due") or last_round.get("total_due")
        
        return {
            "item_name": last_round.get("item_name", ""),
            "item_price": last_round.get("item_price", 0),
            "tax_amount": last_round.get("tax_amount", 0),
            "total_due": total_due,
            "user_counts": counts,
            "best_counts": best_combo,
            "user_total": user_total,
            "is_correct": is_correct,
            "show_tax": last_round.get("show_tax", True),
            "skipped": False,
        }
    
    def save_state_to_session(self, game_state: Dict[str, Any], new_state) -> None:
        """Persist the current round data for the money game."""
        game_state["item_name"] = new_state.item_name
        game_state["item_price"] = new_state.item_price
        game_state["tax_amount"] = new_state.tax_amount
        game_state["total_due"] = new_state.total_due
        game_state["tax_rate"] = new_state.tax_rate
        game_state["show_tax"] = new_state.show_tax
        game_state["item_image"] = new_state.item_image
        game_state["awaiting_retry"] = new_state.awaiting_retry
    
    def get_initial_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initial state structure for the money game."""
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
            "tax_rate": config.get("tax_rate", 0.08),
            "show_tax": config.get("show_tax", True),
            "item_image": "",
            "awaiting_retry": False,
        }
    
    def save_pre_answer_state(self, game_state: Dict[str, Any]) -> None:
        """Save state before processing answer for history and feedback."""
        session["last_money_round"] = {
            "item_name": game_state.get("item_name", ""),
            "item_price": game_state.get("item_price", 0),
            "tax_amount": game_state.get("tax_amount", 0),
            "total_due": game_state.get("total_due", 0),
            "show_tax": game_state.get("show_tax", True),
        }
    
    def setup_post_answer_ui(self, ui, new_state) -> None:
        """Add detailed feedback after an answer is processed."""
        last_result = getattr(self.engine, "get_last_result", lambda: {})()
        if last_result:
            counts = last_result.get("counts", {})
            best_combo = last_result.get("best_combo", {})
            user_total = last_result.get("user_total")
            total_due = last_result.get("total_due")
            pay_total = last_result.get("pay_total", total_due)
            change = user_total - total_due
            is_correct = last_result.get("is_correct", False)
            show_tax = last_result.get("show_tax", False)

            if is_correct:
                if show_tax:
                    ui._messages[-1] = f"Correct! Total was ${total_due:.2f}; You paid ${user_total:.2f} and received change ${change:.2f}"
                else:
                    ui._messages[-1] = f"Correct! Total was ${total_due:.2f}; You paid ${user_total:.2f}"

            ui._messages.append(
                f"You used ${user_total} with {counts.get(20,0)}x$20, {counts.get(10,0)}x$10, {counts.get(5,0)}x$5, {counts.get(1,0)}x$1."
            )
            ui._messages.append(
                f"Best is ${pay_total} with {best_combo.get(20,0)}x$20, {best_combo.get(10,0)}x$10, {best_combo.get(5,0)}x$5, {best_combo.get(1,0)}x$1."
            )
            if is_correct and show_tax:
                ui._messages.append(f"Change back: ${change:.2f}")
    
    def handle_skip_round(self, game_state: Dict[str, Any]) -> None:
        """Skip the current round and update session state."""
        if "history" not in session:
            session["history"] = []
        # Clear retry state explicitly
        game_state["awaiting_retry"] = False
        if hasattr(self.engine, "_awaiting_retry"):
            self.engine._awaiting_retry = False
        session["last_answer"] = None
        # Clear any last result so we don't show stale messages
        if hasattr(self.engine, "_last_result"):
            self.engine._last_result = {}
        session["history"].append(
            {
                "item_name": game_state.get("item_name", ""),
                "item_price": game_state.get("item_price", 0),
                "tax_amount": game_state.get("tax_amount", 0),
                "total_due": game_state.get("total_due", 0),
                "user_counts": {},
                "best_counts": getattr(self.engine, "get_best_combo", lambda: {})(),
                "user_total": 0,
                "is_correct": False,
                "show_tax": game_state.get("show_tax", True),
                "skipped": True,
            }
        )
        game_state["awaiting_retry"] = False
        new_state = self.engine.skip_round()
        game_state["score"] = self.engine.score
        game_state["current_round"] = self.engine.current_round
        if new_state is None:
            game_state["active"] = False
            game_state["over"] = True
        else:
            game_state["active"] = True
            self.save_state_to_session(game_state, new_state)
            game_state["awaiting_retry"] = False
        session["games"][self.game_id] = game_state
