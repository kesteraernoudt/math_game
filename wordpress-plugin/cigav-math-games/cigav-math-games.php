<?php
/**
 * Plugin Name: Cigav Math Games
 * Description: Provides a standalone, no-index math game portal at /math-games/.
 * Version: 1.1.0
 * Author: Kester Aernoudt
 * License: Proprietary
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

define('CMG_VERSION', '1.1.0');
define('CMG_PLUGIN_FILE', __FILE__);
define('CMG_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('CMG_PLUGIN_URL', plugin_dir_url(__FILE__));

require_once CMG_PLUGIN_DIR . 'includes/class-cmg-router.php';
require_once CMG_PLUGIN_DIR . 'includes/class-cmg-renderer.php';

/**
 * Register the narrowly scoped hooks used by the standalone game portal.
 */
function cmg_boot(): void
{
    $router = new CMG_Router();
    $renderer = new CMG_Renderer($router);

    $router->register_hooks();
    $renderer->register_hooks();
}
add_action('plugins_loaded', 'cmg_boot');

/**
 * Add the route before flushing rules on activation.
 */
function cmg_activate(): void
{
    $router = new CMG_Router();
    $router->add_rewrite_rule();
    flush_rewrite_rules();
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
