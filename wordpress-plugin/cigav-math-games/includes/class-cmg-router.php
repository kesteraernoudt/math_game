<?php
/**
 * URL routing for the standalone math games portal.
 *
 * @package CigavMathGames
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Registers and detects the dedicated Math Games routes.
 */
class CMG_Router
{
    const QUERY_VAR = 'cmg_math_games';
    const ROUTE_PATTERN = '^math-games/?$';
    const STATS_ROUTE_PATTERN = '^math-games/stats/?$';

    /**
     * Register WordPress hooks for the custom route.
     */
    public function register_hooks(): void
    {
        add_action('init', array($this, 'add_rewrite_rule'));
        add_filter('query_vars', array($this, 'register_query_var'));
    }

    /**
     * Route the game portal and its statistics page to private query values.
     */
    public function add_rewrite_rule(): void
    {
        add_rewrite_rule(
            self::STATS_ROUTE_PATTERN,
            'index.php?' . self::QUERY_VAR . '=stats',
            'top'
        );
        add_rewrite_rule(
            self::ROUTE_PATTERN,
            'index.php?' . self::QUERY_VAR . '=1',
            'top'
        );
    }

    /**
     * Allow WordPress to retain the custom route marker.
     *
     * @param array<string> $query_vars Public query variables.
     * @return array<string>
     */
    public function register_query_var(array $query_vars): array
    {
        $query_vars[] = self::QUERY_VAR;

        return $query_vars;
    }

    /**
     * Determine whether this request belongs to the plugin.
     */
    public function is_math_games_request(): bool
    {
        return (string) get_query_var(self::QUERY_VAR) === '1';
    }

    /** Determine whether this request belongs to the plugin statistics page. */
    public function is_stats_request(): bool
    {
        return (string) get_query_var(self::QUERY_VAR) === 'stats';
    }
}
