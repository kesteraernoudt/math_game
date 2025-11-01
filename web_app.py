from flask import Flask, render_template, request, session, redirect, url_for
from math_games.game_engine import RoundingGameEngine
from math_games.web_ui import WebUI

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management


def get_or_create_game_state():
    """Get or create serializable game state data."""
    if 'game_state' not in session:
        session['game_state'] = {
            'score': 0,
            'current_round': 0,
            'active': False,
            'over': False,
            'current_number': None,
            'max_number': 100,
            'rounds': 10,
            'factor': 10
        }
    return session['game_state']


@app.route('/', methods=['GET', 'POST'])
def game():
    game_state = get_or_create_game_state()
    ui = WebUI()
    # Toggle debug UI via ?debug=1/0 (persisted in session)
    if 'debug' in request.args:
        val = request.args.get('debug', '0').lower()
        session['show_debug'] = val in ('1', 'true', 'yes', 'on')
    
    # Create game engine with current state
    engine = RoundingGameEngine(
        max_number=game_state['max_number'],
        rounds=game_state['rounds'],
        factor=game_state['factor']
    )
    engine.score = game_state['score']
    engine.current_round = game_state['current_round']
    engine._current_number = game_state['current_number']
    
    if request.method == 'POST':
        if 'action' in request.form:
            if request.form['action'] == 'restart':
                # Just clear the session and show the input form
                #session.pop('game_state', None)
                game_state['active'] = False
                game_state['over'] = True
                session['history'] = []
                # Save game state
                session['game_state'] = game_state
                return redirect(url_for('game'))
            if request.form['action'] == 'start_game':
                # Get custom settings or use defaults
                factor = int(request.form.get('factor', 10))
                rounds = int(request.form.get('rounds', 10))
                max_number = int(request.form.get('max_number', 100))
                session.pop('game_state', None)
                session['history'] = []
                # Generate the first number
                engine = RoundingGameEngine(max_number=max_number, rounds=rounds, factor=factor)
                number = engine._generate_number()
                # Set new game state with custom values and first number
                session['game_state'] = {
                    'score': 0,
                    'current_round': 0,
                    'active': True,
                    'over': False,
                    'current_number': number,
                    'max_number': max_number,
                    'rounds': rounds,
                    'factor': factor
                }
                session['current_number'] = number
                return redirect(url_for('game'))
        elif 'answer' in request.form and game_state['active']:
            answer = request.form['answer']
            # Save the number being answered for history
            session['current_number'] = game_state['current_number']
            session['last_answer'] = answer
            # Process the answer
            is_correct, state = engine.submit_answer(answer)
            ui.display_result(is_correct)
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
                game_state['current_number'] = engine._current_number
                session['current_number'] = engine._current_number
                ui.display_round(new_state)
    elif request.method == 'GET':
        # If no active game, show the input form for new game settings
        if not game_state['active'] and not game_state['over']:
            # The template already shows the form when no active game
            pass
        else:
            # Show welcome and round info when game is active
            if game_state['active'] and not game_state['over']:
                ui.display_welcome(engine.rounds, engine.factor)
                ui.display_round(engine.get_game_state())
    
    # Save game state
    session['game_state'] = game_state
    # Get messages to display
    messages = ui.get_messages()
    ui.clear_messages()
    show_debug = session.get('show_debug', False)

    # Fallback: if there are no messages but we have a current number in the session,
    # ensure the round info is displayed so the template has content to render.
    if (not messages) and session.get('current_number') is not None:
        try:
            ui.display_round(engine.get_game_state())
            messages = ui.get_messages()
            ui.clear_messages()
        except Exception:
            # If anything goes wrong here, swallow the error and continue
            # so the template can still render (debug UI will help diagnose).
            pass
    
    return render_template(
        'game.html',
        messages=messages,
        game_active=game_state['active'],
        game_over=game_state['over'],
        session=session,
        show_debug=show_debug
    )


if __name__ == '__main__':
    app.run(debug=True)
