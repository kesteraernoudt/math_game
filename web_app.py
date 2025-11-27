"""© Cigav Productions LLC"""
"""© Cigav Productions LLC"""
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from math_games import GameRegistry
from math_games.web_ui import WebUI
from game_handlers import HandlerRegistry
from jinja2.exceptions import TemplateNotFound

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management


def get_or_create_game_state(game_id: str):
    """Get or create serializable game state data for a specific game."""
    if 'games' not in session:
        session['games'] = {}
    
    if game_id not in session['games']:
        # Get default config for the game
        game_class = GameRegistry.get_game(game_id)
        if game_class is None:
            return None
        
        default_config = game_class.get_default_config() if hasattr(game_class, 'get_default_config') else {}
        
        # Get handler to create proper initial state
        engine = game_class(**default_config) if default_config else game_class()
        handler = HandlerRegistry.get_handler(game_id, engine)
        
        if handler:
            initial_state = handler.get_initial_state(default_config)
        else:
            # Fallback generic state
            initial_state = {
                'score': 0,
                'current_round': 0,
                'active': False,
                'over': False,
                'config': default_config,
            }
        
        session['games'][game_id] = initial_state
    
    return session['games'][game_id]


def create_game_engine(game_id: str, game_state: dict):
    """Create a game engine instance from game state."""
    game_class = GameRegistry.get_game(game_id)
    if game_class is None:
        return None
    
    config = game_state.get('config', {})
    engine = game_class(**config)
    engine.score = game_state.get('score', 0)
    engine.current_round = game_state.get('current_round', 0)
    
    # Try to restore game-specific state
    if hasattr(engine, 'deserialize_state'):
        engine.deserialize_state(game_state)
    
    return engine


def extract_config_from_form(game_class, request_form):
    """Extract configuration values from form data."""
    config = {}
    default_config = game_class.get_default_config()
    
    for key in default_config.keys():
        if key in request_form:
            values = request_form.getlist(key)
            value = values[-1] if isinstance(values, list) and values else request_form.get(key)
            if value is not None:
                # Try to convert to appropriate type
                default_value = default_config[key]
                # Handle bool before int (bool is subclass of int)
                if isinstance(default_value, bool):
                    config[key] = str(value).lower() in ('1', 'true', 'yes', 'on')
                elif isinstance(default_value, int):
                    config[key] = int(value)
                elif isinstance(default_value, float):
                    config[key] = float(value)
                else:
                    config[key] = value
            else:
                config[key] = default_config[key]
        else:
            config[key] = default_config[key]
    
    return config


@app.route('/')
def index():
    """Game selection page."""
    games = GameRegistry.list_game_info()
    return render_template('index.html', games=games)


@app.route('/game/<game_id>', methods=['GET', 'POST'])
def game(game_id):
    """Main game route for a specific game."""
    # Check if game exists
    game_class = GameRegistry.get_game(game_id)
    if game_class is None:
        return redirect(url_for('index'))
    default_config = game_class.get_default_config() if hasattr(game_class, 'get_default_config') else {}
    
    game_state = get_or_create_game_state(game_id)
    if game_state is None:
        return redirect(url_for('index'))

    ui = WebUI()
    
    # Toggle debug UI via ?debug=1/0 (persisted in session)
    if 'debug' in request.args:
        val = request.args.get('debug', '0').lower()
        session['show_debug'] = val in ('1', 'true', 'yes', 'on')
    
    # Create game engine with current state
    engine = create_game_engine(game_id, game_state)
    if engine is None:
        return redirect(url_for('index'))
    
    # Get handler for this game
    handler = HandlerRegistry.get_handler(game_id, engine)

    # If coming fresh from index (fresh=1), reset to initial config screen
    if request.args.get('fresh') == '1':
        default_config = game_class.get_default_config()
        if handler:
            initial_state = handler.get_initial_state(default_config)
        else:
            initial_state = {
                'score': 0,
                'current_round': 0,
                'active': False,
                'over': False,
                'config': default_config,
            }
        initial_state['active'] = False
        initial_state['over'] = False
        session['games'][game_id] = initial_state
        session['history'] = []
        game_state = initial_state
        engine = create_game_engine(game_id, game_state)
        handler = HandlerRegistry.get_handler(game_id, engine)

    if request.method == 'POST':
        if 'action' in request.form:
            if request.form['action'] == 'restart':
                # Reset state so the config screen shows instead of looping on game over
                session['history'] = []
                config = game_state.get('config', game_class.get_default_config())
                if handler:
                    fresh_state = handler.get_initial_state(config)
                else:
                    fresh_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': config,
                    }
                fresh_state['active'] = False
                fresh_state['over'] = False
                session['games'][game_id] = fresh_state
                return redirect(url_for('game', game_id=game_id))
            
            if request.form['action'] == 'skip_round' and game_state.get('active') and handler and hasattr(handler, 'handle_skip_round'):
                handler.handle_skip_round(game_state)
                return redirect(url_for('game', game_id=game_id))
            
            if request.form['action'] == 'start_game':
                # Get custom settings from form
                config = extract_config_from_form(game_class, request.form)
                
                # Get initial state from handler
                if handler:
                    initial_state = handler.get_initial_state(config)
                else:
                    initial_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': True,
                        'over': False,
                        'config': config,
                    }
                initial_state['active'] = True
                initial_state['over'] = False
                
                session['games'][game_id] = initial_state
                session['history'] = []
                
                # Generate the first number
                engine = game_class(**config)
                if hasattr(engine, 'start_round'):
                    state = engine.start_round()
                    if state and handler:
                        handler.save_state_to_session(initial_state, state)
                        # Also save to engine attributes if needed
                        if hasattr(state, 'current_number'):
                            session['current_number'] = state.current_number
                        elif hasattr(engine, '_current_number'):
                            session['current_number'] = engine._current_number
                        if hasattr(state, 'number1'):
                            session['games'][game_id]['number1'] = state.number1
                        if hasattr(state, 'number2'):
                            session['games'][game_id]['number2'] = state.number2
                
                return redirect(url_for('game', game_id=game_id))
        
        # AJAX JSON handling for rounding game (no page reload)
        if request.is_json and game_id == 'rounding':
            data = request.get_json(silent=True) or {}
            action = data.get('action')
            def build_response(messages_list, extra=None):
                gs = session['games'][game_id]
                hist = session.get('history', [])
                resp = {
                    "game_active": gs.get('active', False),
                    "game_over": gs.get('over', False),
                    "score": gs.get('score', 0),
                    "current_round": gs.get('current_round', 0),
                    "total_rounds": gs.get('config', {}).get('rounds', gs.get('current_round', 0)),
                    "number": gs.get('current_number'),
                    "factor": gs.get('config', {}).get('factor', default_config.get('factor', 10)),
                    "max_number": gs.get('config', {}).get('max_number', default_config.get('max_number', 100)),
                    "show_axis": gs.get('config', {}).get('show_axis', default_config.get('show_axis', True)),
                    "messages": messages_list,
                    "history": list(reversed(hist)) if hist else []
                }
                if extra:
                    resp.update(extra)
                return jsonify(resp)

            if action == 'start_game':
                def _to_int(val, default):
                    try:
                        return int(val)
                    except (TypeError, ValueError):
                        return default
                cfg = {
                    "rounds": _to_int(data.get("rounds"), default_config.get("rounds", 10)),
                    "max_number": _to_int(data.get("max_number"), default_config.get("max_number", 100)),
                    "factor": _to_int(data.get("factor"), default_config.get("factor", 10)),
                    "show_axis": bool(data.get("show_axis", default_config.get("show_axis", True))),
                }
                session['history'] = []
                if handler:
                    initial_state = handler.get_initial_state(cfg)
                else:
                    initial_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': cfg,
                        'current_number': None,
                    }
                initial_state['config'] = cfg
                initial_state['active'] = True
                initial_state['over'] = False
                session['games'][game_id] = initial_state
                engine = create_game_engine(game_id, initial_state)
                try:
                    state = engine.start_round()
                    if handler and state:
                        handler.save_state_to_session(initial_state, state)
                    ui.display_round(state)
                    if state and hasattr(state, "current_number"):
                        initial_state["current_number"] = getattr(state, "current_number", None)
                        session['current_number'] = initial_state["current_number"]
                    session['games'][game_id] = initial_state
                    session.modified = True
                    msgs = ui.get_messages(); ui.clear_messages()
                    return build_response(msgs, {"started": True, "config": cfg})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

            if action == 'restart':
                cfg = game_state.get('config', {})
                if handler:
                    initial_state = handler.get_initial_state(cfg)
                else:
                    initial_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': cfg,
                        'current_number': None,
                    }
                initial_state['active'] = True
                initial_state['over'] = False
                session['history'] = []
                session['games'][game_id] = initial_state
                engine = create_game_engine(game_id, initial_state)
                try:
                    state = engine.start_round()
                    if handler and state:
                        handler.save_state_to_session(initial_state, state)
                    ui.display_round(state)
                    if state and hasattr(state, "current_number"):
                        initial_state["current_number"] = getattr(state, "current_number", None)
                        session['current_number'] = initial_state["current_number"]
                    session['games'][game_id] = initial_state
                    session.modified = True
                    msgs = ui.get_messages(); ui.clear_messages()
                    return build_response(msgs, {"started": True, "config": cfg})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            
            if action == 'reset_to_config':
                cfg = game_state.get('config', default_config)
                if handler:
                    fresh_state = handler.get_initial_state(cfg)
                else:
                    fresh_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': cfg,
                        'current_number': None,
                    }
                fresh_state['active'] = False
                fresh_state['over'] = False
                session['history'] = []
                session['current_number'] = None
                session['games'][game_id] = fresh_state
                session.modified = True
                return build_response([], {"config": cfg, "game_active": False, "game_over": False})

            elif action == 'answer' and game_state['active']:
                answer = str(data.get('answer', '')).strip()
                session['last_answer'] = answer
                if handler:
                    handler.save_pre_answer_state(game_state)
                is_correct, state = engine.submit_answer(answer)
                ui.display_result(is_correct)
                if 'history' not in session:
                    session['history'] = []
                if handler:
                    history_entry = handler.create_history_entry(answer, state, is_correct)
                else:
                    history_entry = {'answer': answer, 'is_correct': is_correct}
                session['history'].append(history_entry)
                game_state['score'] = engine.score
                game_state['current_round'] = engine.current_round
                new_state = engine.start_round()
                if new_state is None:
                    ui.display_game_over(state)
                    game_state['active'] = False
                    game_state['over'] = True
                    session['current_number'] = None
                else:
                    if handler:
                        handler.save_state_to_session(game_state, new_state)
                        handler.setup_post_answer_ui(ui, new_state)
                    game_state['active'] = True
                    game_state['over'] = False
                session['games'][game_id] = game_state
                msgs = ui.get_messages(); ui.clear_messages()
                return build_response(msgs)

        # AJAX JSON handling for addition game (no page reload)
        if request.is_json and game_id == 'addition':
            data = request.get_json(silent=True) or {}
            action = data.get('action')
            def build_response(messages_list, extra=None):
                gs = session['games'][game_id]
                hist = session.get('history', [])
                resp = {
                    "game_active": gs.get('active', False),
                    "game_over": gs.get('over', False),
                    "score": gs.get('score', 0),
                    "current_round": gs.get('current_round', 0),
                    "total_rounds": gs.get('config', {}).get('rounds', gs.get('current_round', 0)),
                    "number1": gs.get('number1'),
                    "number2": gs.get('number2'),
                    "messages": messages_list,
                    "history": list(reversed(hist[-5:])) if hist else []
                }
                if extra:
                    resp.update(extra)
                return jsonify(resp)

            if action == 'start_game':
                # Create new game with provided config
                def _to_int(val, default):
                    try:
                        return int(val)
                    except (TypeError, ValueError):
                        return default
                cfg = {
                    "rounds": _to_int(data.get("rounds"), default_config.get("rounds", 10)),
                    "max_number": _to_int(data.get("max_number"), default_config.get("max_number", 50)),
                }
                session['history'] = []
                if handler:
                    initial_state = handler.get_initial_state(cfg)
                else:
                    initial_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': cfg,
                    }
                initial_state['config'] = cfg
                initial_state['active'] = True
                initial_state['over'] = False
                session['games'][game_id] = initial_state
                engine = create_game_engine(game_id, initial_state)
                try:
                    state = engine.start_round()
                    if handler and state:
                        handler.save_state_to_session(initial_state, state)
                    # Ensure numbers are persisted for addition
                    if state and hasattr(state, "number1"):
                        initial_state["number1"] = getattr(state, "number1", None)
                    if state and hasattr(state, "number2"):
                        initial_state["number2"] = getattr(state, "number2", None)
                    session['games'][game_id] = initial_state
                    # Only call display_round for games that implement the rounding UI expectations
                    if game_id == 'rounding' and state is not None and hasattr(state, 'current_number'):
                        ui.display_round(state)
                    session.modified = True
                    msgs = ui.get_messages(); ui.clear_messages()
                    return build_response(msgs, {"started": True, "config": cfg})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

            if action == 'restart':
                # Reset state using existing config
                cfg = game_state.get('config', {})
                if handler:
                    initial_state = handler.get_initial_state(cfg)
                else:
                    initial_state = {
                        'score': 0,
                        'current_round': 0,
                        'active': False,
                        'over': False,
                        'config': cfg,
                    }
                initial_state['active'] = True
                initial_state['over'] = False
                session['history'] = []
                session['games'][game_id] = initial_state
                engine = create_game_engine(game_id, initial_state)
                try:
                    state = engine.start_round()
                    if handler and state:
                        handler.save_state_to_session(initial_state, state)
                    # Persist numbers for addition
                    if state and hasattr(state, "number1"):
                        initial_state["number1"] = getattr(state, "number1", None)
                    if state and hasattr(state, "number2"):
                        initial_state["number2"] = getattr(state, "number2", None)
                    session['games'][game_id] = initial_state
                    # Only display_round for rounding game
                    if game_id == 'rounding' and state is not None and hasattr(state, 'current_number'):
                        ui.display_round(state)
                    session.modified = True
                    msgs = ui.get_messages(); ui.clear_messages()
                    return build_response(msgs, {"started": True, "config": cfg})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

            elif action == 'answer' and game_state['active']:
                answer = str(data.get('answer', '')).strip()
                session['last_answer'] = answer
                if handler:
                    handler.save_pre_answer_state(game_state)
                is_correct, state = engine.submit_answer(answer)
                ui.display_result(is_correct)
                if 'history' not in session:
                    session['history'] = []
                if handler:
                    history_entry = handler.create_history_entry(answer, state, is_correct)
                else:
                    history_entry = {
                        'answer': answer,
                        'is_correct': is_correct
                    }
                session['history'].append(history_entry)
                game_state['score'] = engine.score
                game_state['current_round'] = engine.current_round
                new_state = engine.start_round()
                if new_state is None:
                    ui.display_game_over(state)
                    game_state['active'] = False
                    game_state['over'] = True
                else:
                    if handler:
                        handler.save_state_to_session(game_state, new_state)
                        handler.setup_post_answer_ui(ui, new_state)
                session['games'][game_id] = game_state
                msgs = ui.get_messages(); ui.clear_messages()
                return build_response(msgs)

        elif 'answer' in request.form and game_state['active']:
            # Debug capture of raw submit payload
            try:
                session['last_submit_payload'] = request.form.to_dict(flat=True)
            except Exception:
                session['last_submit_payload'] = {}
            session['debug_payload'] = request.form.get('debug_payload')
            answer = request.form['answer']
            session['last_answer'] = answer
            
            # Save pre-answer state (for history)
            if handler:
                handler.save_pre_answer_state(game_state)
            
            # Process the answer
            is_correct, state = engine.submit_answer(answer)
            # Fallback: if the engine says incorrect but counts/pay match the best combo exactly, treat as correct
            try:
                lr = engine.get_last_result()
                if (
                    not is_correct
                    and lr
                    and lr.get("counts") == lr.get("best_combo")
                    and lr.get("user_total") == lr.get("pay_total")
                ):
                    is_correct = True
                    engine.score += 1
                    engine.current_round += 1
                    if hasattr(engine, "_awaiting_retry"):
                        engine._awaiting_retry = False
                    state = engine.get_game_state()
            except Exception:
                pass
            try:
                session['engine_last_result'] = engine.get_last_result()
            except Exception:
                session['engine_last_result'] = {}
            try:
                session['engine_submit_debug'] = getattr(engine, "_last_result", {})
            except Exception:
                session['engine_submit_debug'] = {}
            ui.display_result(is_correct)
            
            # Add to history (game-specific)
            if 'history' not in session:
                session['history'] = []
            
            if handler:
                history_entry = handler.create_history_entry(answer, state, is_correct)
            else:
                # Fallback generic history
                history_entry = {
                    'answer': answer,
                    'is_correct': is_correct
                }
            session['history'].append(history_entry)
            
            # Update session state
            game_state['score'] = engine.score
            game_state['current_round'] = engine.current_round
            
            # Start next round or end game
            new_state = engine.start_round()
            if new_state is None:
                ui.display_game_over(state)
                game_state['active'] = False
                game_state['over'] = True
            else:
                # Save game-specific state
                if handler:
                    handler.save_state_to_session(game_state, new_state)
                    handler.setup_post_answer_ui(ui, new_state)
                else:
                    # Fallback: try to save common state attributes
                    if hasattr(new_state, 'current_number'):
                        game_state['current_number'] = new_state.current_number
                        session['current_number'] = new_state.current_number
    
    elif request.method == 'GET':
        # If no active game, show the input form for new game settings
        if not game_state['active'] and not game_state['over']:
            # The template already shows the form when no active game
            pass
        else:
            # Show welcome and round info when game is active
            if game_state['active'] and not game_state['over']:
                if handler:
                    handler.setup_ui_display(ui, game_state)
    
    # Save game state
    session['games'][game_id] = game_state
    # Get messages to display
    messages = ui.get_messages()
    ui.clear_messages()
    show_debug = session.get('show_debug', False)
    
    # Fallback: if there are no messages but we have a current number in the session,
    # ensure the round info is displayed so the template has content to render.
    # Only do this for rounding game since other games handle display differently
    if (not messages) and game_id == 'rounding' and session.get('current_number') is not None:
        try:
            game_state_obj = engine.get_game_state()
            ui.display_round(game_state_obj)
            messages = ui.get_messages()
            ui.clear_messages()
        except (AttributeError, TypeError):
            # If anything goes wrong here, swallow the error and continue
            pass
    
    # Get game info for template
    game_info = GameRegistry.get_game_info(game_id)
    
    # Try to use game-specific template, fallback to generic game.html
    template_name = f'game_{game_id}.html'
    
    try:
        return render_template(
            template_name,
            messages=messages,
            game_active=game_state['active'],
            game_over=game_state['over'],
            session=session,
            show_debug=show_debug,
            game_id=game_id,
            game_info=game_info,
            game_config=game_state.get('config', {}),
            default_config=game_class.get_default_config(),
            engine=engine
        )
    except TemplateNotFound:
        # Fallback to generic template
        return render_template(
            'game.html',
            messages=messages,
            game_active=game_state['active'],
            game_over=game_state['over'],
            session=session,
            show_debug=show_debug,
            game_id=game_id,
            game_info=game_info,
            game_config=game_state.get('config', {}),
            default_config=game_class.get_default_config(),
            engine=engine
        )


if __name__ == '__main__':
    app.run(debug=True)
