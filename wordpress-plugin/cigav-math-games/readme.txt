=== Cigav Math Games ===
Contributors: kesteraernoudt
Requires at least: 6.0
Requires PHP: 7.4
Stable tag: 1.5.2
License: Proprietary

A standalone, no-index math game portal at /math-games/.

== Description ==

Provides rounding, addition, payment, money-comparison, and change-making games in a standalone
interface. The plugin does not use the active theme. It stores only anonymous
aggregate game-session statistics on the server; it does not create player profiles.

== Installation ==

1. Upload and activate the plugin.
2. Visit /math-games/.
3. If necessary, save Settings > Permalinks once to refresh rewrite rules.

== Changelog ==

= 1.5.2 =
* Show the full gameplay screenshots in home-card previews instead of cropping them.

= 1.5.1 =
* Replace symbol-only game cards with recognizable gameplay previews.

= 1.5.0 =
* Make the WordPress plugin the documented production source of truth; retain Flask only as a reference.
* Add anonymous server-side session statistics and the read-only /math-games/stats/ dashboard.
* Refresh plugin rewrite rules automatically after the update.

= 1.4.3 =
* Use only the full, unlabelled bill and coin artwork as the Money Compare denomination cue.

= 1.4.2 =
* Preserve the full bill and coin artwork in Money Compare and enlarge each denomination badge.

= 1.4.1 =
* Add Money Compare, with full tappable stacks of repeated bills and coins.
* Add configurable maximum stack value and frequent mixed bill-and-coin comparisons.

= 1.3.1 =
* Keep one complete feedback card in the original bottom position before and after automatic advancement.
* Relabel the same feedback from current to previous without moving or replacing its content.

= 1.3.0 =
* Keep the latest feedback visible after automatic advancement.
* Show the previous question, submitted answer, and result separately to preserve context.
* Retain final-question feedback on the results screen.

= 1.2.0 =
* Correct fewest-bills validation when overpayment is allowed.
* Provide specific feedback for low, excessive, non-exact, and non-minimal answers.
* Add a collapsed game-options review beneath active and completed games.
* Add standalone Home Screen metadata and distinguish iPhone Focus mode from true full screen.

= 1.1.0 =
* Improve the portrait mobile layout and keep full-screen controls accessible.
* Add an iPhone-compatible focus-mode fallback where native full screen is unavailable.
* Advance automatically after completed questions.
* Restore optimized bill and coin artwork in the money games.
* Prevent WP Rocket from delaying the game application script.

= 1.0.0 =
* Initial WordPress conversion of the Flask math game.
