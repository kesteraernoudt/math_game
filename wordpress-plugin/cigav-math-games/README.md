# Cigav Math Games WordPress plugin

This plugin ports the browser-facing behavior of the `math_game` Flask project
to a self-contained WordPress plugin. It does not require Python, Flask, a
database table, a WordPress page, or the active WordPress theme.

## Public route

The plugin renders one standalone application at:

```text
/math-games/
```

Individual games use URL fragments such as `#game/rounding`. Fragments stay in
the browser and do not create additional WordPress routes.

## Isolation and indexing

- The active WordPress theme, header, footer, and global front-end assets are
  not loaded.
- Plugin CSS and JavaScript load only on `/math-games/`.
- The route sends `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet`.
- The document also includes a matching robots meta tag.
- The route is not a WordPress post and is not added to WordPress sitemaps,
  navigation, search, feeds, or the REST API.
- No game data is written to the WordPress database or server filesystem.
- Game state exists only in the current browser tab and resets on reload.

## Games

- Rounding Game
- Addition Game
- Money Match
- Change Game

The Python and Flask runtime has been replaced with client-side JavaScript so
the plugin works on standard PHP-only WordPress hosting.

## Installation

1. Upload `cigav-math-games.zip` in **WordPress Admin > Plugins > Add New >
   Upload Plugin**.
2. Activate **Cigav Math Games**.
3. Visit `/math-games/`.
4. If the URL returns a 404, visit **Settings > Permalinks** and click
   **Save Changes** once.

Do not add the route to the main site's menus if it should remain unlinked.
