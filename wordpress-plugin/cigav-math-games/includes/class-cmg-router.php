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
 * Registers and detects the dedicated /math-games/ route.
 */
class CMG_Router
{
    const QUERY_VAR = 'cmg_math_games';
    const ROUTE_PATTERN = '^math-games/?$';

    /**
     * Register WordPress hooks for the custom route.
     */
    public function register_hooks(): void
    {
        add_action('init', array($this, 'add_rewrite_rule'));
        add_filter('query_vars', array($this, 'register_query_var'));
    }

    /**
     * Route /math-games/ to a private query variable.
     */
    public function add_rewrite_rule(): void
    {
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
}
