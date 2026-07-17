<?php
/**
 * Standalone document rendering for the math games portal.
 *
 * @package CigavMathGames
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Outputs a complete document without invoking the active WordPress theme.
 */
class CMG_Renderer
{
    /** @var CMG_Router */
    private $router;

    public function __construct(CMG_Router $router)
    {
        $this->router = $router;
    }

    /**
     * Register the standalone renderer.
     */
    public function register_hooks(): void
    {
        add_action('template_redirect', array($this, 'render'));
    }

    /**
     * Render only the plugin-owned route, then stop theme processing.
     */
    public function render(): void
    {
        if (!$this->router->is_math_games_request()) {
            return;
        }

        $charset = $this->get_charset();
        $stylesheet_url = CMG_PLUGIN_URL . 'assets/css/math-games.css?ver=' . rawurlencode(CMG_VERSION);
        $script_url = CMG_PLUGIN_URL . 'assets/js/math-games.js?ver=' . rawurlencode(CMG_VERSION);
        $portal_url = home_url('/math-games/');

        $this->send_standalone_headers($charset);

        require CMG_PLUGIN_DIR . 'templates/math-games-page.php';
        exit;
    }

    /**
     * Prevent indexing, caching, framing by other sites, and MIME sniffing.
     */
    private function send_standalone_headers(string $charset): void
    {
        status_header(200);
        header('Content-Type: text/html; charset=' . $charset);
        header('X-Robots-Tag: noindex, nofollow, noarchive, nosnippet', true);
        header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0', true);
        header('Pragma: no-cache', true);
        header('Expires: Wed, 11 Jan 1984 05:00:00 GMT', true);
        header('X-Content-Type-Options: nosniff', true);
        header('X-Frame-Options: SAMEORIGIN', true);
        header('Referrer-Policy: no-referrer', true);
        header('Permissions-Policy: camera=(), microphone=(), geolocation=()', true);
        header("Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'", true);
    }

    /**
     * Return a safe document charset.
     */
    private function get_charset(): string
    {
        $charset = (string) preg_replace('/[^A-Za-z0-9._-]/', '', (string) get_option('blog_charset'));

        return $charset !== '' ? $charset : 'UTF-8';
    }
}
