# Cigav Math Games WordPress plugin

This is the production, browser-facing Math Games application. New gameplay,
visual, routing, and usage-statistics work belongs in this plugin. The Flask
application in the repository root is retained only as a historical reference;
changes to it do not change the WordPress site.

The plugin is self-contained and does not require Python, Flask, a WordPress
page, or the active WordPress theme. It creates two small WordPress database
tables for anonymous usage statistics.

## Public route

The plugin renders one standalone application at:

```text
/math-games/
/math-games/stats/
```

Individual games use URL fragments such as `#game/rounding`. Fragments stay in
the browser and do not create additional WordPress routes. Statistics use the
separate `/math-games/stats/` route to avoid conflicting with site-wide pages.

## iPhone display modes

On iPhone, the in-browser **Focus mode** fills the available browser viewport,
but iOS does not allow it to remove the browser address bar. For an
address-bar-free experience, use the browser's **Add to Home Screen** action and
open Math Games from its Home Screen icon. Desktop browsers and supported
tablets continue to use the native Fullscreen API.

## Isolation and indexing

- The active WordPress theme, header, footer, and global front-end assets are
  not loaded.
- Plugin CSS and JavaScript load only on `/math-games/`.
- The route sends `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet`.
- The document also includes a matching robots meta tag.
- The route is not a WordPress post and is not added to WordPress sitemaps,
  navigation, search, feeds, or the REST API.
- Gameplay state exists only in the current browser tab and resets on reload.
- The plugin records only anonymous game-session totals: game type, start and
  completion time, answered-question count, and duration. It does not store
  names, accounts, IP addresses, player profiles, or answer content.
- The read-only statistics page is available without authentication.

## Games

- Rounding Game
- Addition Game
- Money Match
- Money Compare
- Change Game

The Python and Flask runtime has been replaced with client-side JavaScript so
the plugin works on standard PHP-only WordPress hosting.

## Usage statistics

`/math-games/stats/` provides lifetime totals, daily activity, weekly and
monthly trends, per-game usage, recent activity, and 7/30/90-day or all-time
filters. The database tables are created automatically when version 1.5.0 or
newer runs; no manual migration is required. The plugin also refreshes its
rewrite rules once after the update, so the statistics route does not require
deactivation/reactivation or a Permalinks save.

## Installation

1. Upload `cigav-math-games.zip` in **WordPress Admin > Plugins > Add New >
   Upload Plugin**.
2. Activate **Cigav Math Games**.
3. Visit `/math-games/` or `/math-games/stats/`.
4. If the URL returns a 404, visit **Settings > Permalinks** and click
   **Save Changes** once.

Do not add the route to the main site's menus if it should remain unlinked.
