# Math Games

## Current production application: WordPress plugin

The production, browser-facing Math Games application is the WordPress plugin
in [`wordpress-plugin/cigav-math-games`](wordpress-plugin/cigav-math-games/).
It is the source of truth for new gameplay, visual, routing, and usage
statistics work. Package and deploy that plugin for the live site.

The plugin serves:

- `/math-games/` — the games portal
- `/math-games/stats/` — anonymous, read-only usage statistics

It uses browser JavaScript for gameplay and WordPress database tables for
anonymous aggregate usage statistics. It does not create player accounts,
profiles, or leaderboards.

## Flask application: reference only

The Python/Flask files at the repository root (`web_app.py`, `math_games/`,
`game_handlers/`, and `templates/`) are retained as a historical reference and
for local experimentation. They are **not** the deployed WordPress app and
changes there do not change the WordPress plugin.

When adding a user-facing feature, implement it in the WordPress plugin unless
there is an explicit request to update the legacy Flask reference too.
