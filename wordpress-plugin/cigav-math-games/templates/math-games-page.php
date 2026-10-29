<?php
/**
 * Standalone math games document.
 *
 * @package CigavMathGames
 *
 * @var string $charset
 * @var string $stylesheet_url
 * @var string $script_url
 * @var string $manifest_url
 * @var string $touch_icon_url
 * @var string $portal_url
 * @var string $statistics_url
 * @var string $usage_endpoint
 * @var string $preview_base_url
 */

if (!defined('ABSPATH')) {
    exit;
}
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="<?php echo esc_attr($charset); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
    <meta name="color-scheme" content="dark">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Math Games">
    <title>Math Games</title>
    <link rel="manifest" href="<?php echo esc_url($manifest_url); ?>">
    <link rel="apple-touch-icon" href="<?php echo esc_url($touch_icon_url); ?>">
    <link rel="stylesheet" href="<?php echo esc_url($stylesheet_url); ?>">
    <script src="<?php echo esc_url($script_url); ?>" data-nowprocket defer></script>
</head>
<body>
    <a class="skip-link" href="#cmg-main">Skip to the games</a>

    <div class="app-shell" data-cmg-app data-portal-url="<?php echo esc_url($portal_url); ?>" data-usage-endpoint="<?php echo esc_url($usage_endpoint); ?>" data-preview-base-url="<?php echo esc_url($preview_base_url); ?>">
        <header class="app-header">
            <a class="brand" href="<?php echo esc_url($portal_url); ?>" data-home-link>
                <span class="brand-mark" aria-hidden="true">∑</span>
                <span>
                    <strong>Math Games</strong>
                    <small>Practice at your pace</small>
                </span>
            </a>

            <div class="header-actions">
                <button class="button button-quiet" type="button" data-fullscreen-button>Full screen</button>
                <button class="button button-quiet" type="button" data-back-button hidden>All games</button>
            </div>
        </header>

        <main id="cmg-main" class="app-main" tabindex="-1" data-view></main>

        <footer class="app-footer">
            <span>© Cigav Productions LLC</span>
            <span>Game progress stays in this browser tab.</span>
            <a class="footer-link" href="<?php echo esc_url($statistics_url); ?>">Statistics</a>
            <span class="install-hint" data-install-hint hidden>For an address-bar-free experience, use the browser menu to add Math Games to your Home Screen, then open it from there.</span>
        </footer>
    </div>

    <noscript>
        <div class="noscript-message">JavaScript is required to play these math games.</div>
    </noscript>
</body>
</html>
