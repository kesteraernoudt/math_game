<?php
/**
 * Plugin Name: Cigav Math Games
 * Description: Provides a standalone, no-index math game portal and usage statistics at /math-games/.
 * Version: 1.5.2
 * Author: Kester Aernoudt
 * License: Proprietary
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

define('CMG_VERSION', '1.5.2');
define('CMG_PLUGIN_FILE', __FILE__);
define('CMG_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('CMG_PLUGIN_URL', plugin_dir_url(__FILE__));

require_once CMG_PLUGIN_DIR . 'includes/class-cmg-router.php';
require_once CMG_PLUGIN_DIR . 'includes/class-cmg-usage-statistics.php';
require_once CMG_PLUGIN_DIR . 'includes/class-cmg-renderer.php';

/**
 * Register the narrowly scoped hooks used by the standalone game portal.
 */
function cmg_boot(): void
{
    $router = new CMG_Router();
    $usage_statistics = new CMG_Usage_Statistics();
    $renderer = new CMG_Renderer($router, $usage_statistics);

    $router->register_hooks();
    $usage_statistics->maybe_upgrade();
    $usage_statistics->register_hooks();
    $renderer->register_hooks();
    add_action('init', 'cmg_maybe_flush_rewrite_rules', 99);
}
add_action('plugins_loaded', 'cmg_boot');

/** Flush rewrite rules once after a release adds or changes a plugin route. */
function cmg_maybe_flush_rewrite_rules(): void
{
    if (get_option('cmg_rewrite_rules_version') === CMG_VERSION) {
        return;
    }

    flush_rewrite_rules();
    update_option('cmg_rewrite_rules_version', CMG_VERSION, false);
}

/**
 * Add the route before flushing rules on activation.
 */
function cmg_activate(): void
{
    $router = new CMG_Router();
    $router->add_rewrite_rule();
    $usage_statistics = new CMG_Usage_Statistics();
    $usage_statistics->install();
    flush_rewrite_rules();
    update_option('cmg_rewrite_rules_version', CMG_VERSION, false);
}
register_activation_hook(__FILE__, 'cmg_activate');

/**
 * Remove the stale route from WordPress' cached rewrite rules.
 */
function cmg_deactivate(): void
{
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'cmg_deactivate');
