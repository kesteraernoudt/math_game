<?php
/**
 * Standalone anonymous usage statistics document.
 *
 * @package CigavMathGames
 *
 * @var string $charset
 * @var string $stylesheet_url
 * @var string $portal_url
 * @var string $statistics_url
 * @var string $range
 * @var array<string, mixed> $dashboard
 * @var array<string, string> $game_names
 * @var int $activity_max
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('cmg_statistics_duration')) {
    function cmg_statistics_duration($seconds): string
    {
        if ($seconds === null || $seconds === '') {
            return '—';
        }
        $total = max(0, (int) round((float) $seconds));
        $minutes = intdiv($total, 60);
        $remaining = $total % 60;

        return $minutes > 0 ? $minutes . 'm ' . str_pad((string) $remaining, 2, '0', STR_PAD_LEFT) . 's' : $remaining . 's';
    }
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
    <title>Math Games Statistics</title>
    <link rel="stylesheet" href="<?php echo esc_url($stylesheet_url); ?>">
</head>
<body>
    <a class="skip-link" href="#cmg-main">Skip to statistics</a>
    <div class="app-shell">
        <header class="app-header">
            <a class="brand" href="<?php echo esc_url($portal_url); ?>">
                <span class="brand-mark" aria-hidden="true">∑</span>
                <span><strong>Math Games</strong><small>Usage statistics</small></span>
            </a>
            <a class="button button-quiet" href="<?php echo esc_url($portal_url); ?>">All games</a>
        </header>

        <main id="cmg-main" class="app-main stats-page" tabindex="-1">
            <div class="stats-heading">
                <div>
                    <p class="eyebrow">Administration</p>
                    <h1>Usage statistics</h1>
                    <p class="intro">Anonymous, server-side activity across all Math Games.</p>
                </div>
                <nav class="stats-range" aria-label="Statistics date range">
                    <?php foreach (array('7' => '7 days', '30' => '30 days', '90' => '90 days', 'all' => 'All time') as $value => $label) : ?>
                        <a class="stats-range-link<?php echo $range === $value ? ' is-active' : ''; ?>" href="<?php echo esc_url(add_query_arg('range', $value, $statistics_url)); ?>"><?php echo esc_html($label); ?></a>
                    <?php endforeach; ?>
                </nav>
            </div>

            <section class="stats-cards" aria-label="Lifetime totals">
                <article class="stats-card"><span>Games started</span><strong><?php echo esc_html(number_format_i18n((int) $dashboard['lifetime']['started'])); ?></strong></article>
                <article class="stats-card"><span>Games completed</span><strong><?php echo esc_html(number_format_i18n((int) $dashboard['lifetime']['completed'])); ?></strong></article>
                <article class="stats-card"><span>Questions answered</span><strong><?php echo esc_html(number_format_i18n((int) $dashboard['lifetime']['questions'])); ?></strong></article>
                <article class="stats-card"><span>Average duration</span><strong><?php echo esc_html(cmg_statistics_duration($dashboard['lifetime']['average_duration'])); ?></strong></article>
            </section>

            <section class="stats-grid">
                <article class="panel stats-panel">
                    <div class="stats-panel-heading"><h2>Daily activity</h2><span><?php echo esc_html(number_format_i18n((int) $dashboard['selected']['started'])); ?> started in this range</span></div>
                    <div class="stats-activity-wrap">
                        <div class="stats-activity" role="img" aria-label="Daily games started">
                            <?php foreach ($dashboard['activity'] as $point) : $height = max(2, ((int) $point['count'] / $activity_max) * 100); ?>
                                <span class="stats-bar" style="height:<?php echo esc_attr((string) $height); ?>%" title="<?php echo esc_attr($point['date'] . ': ' . $point['count'] . ' games started'); ?>"></span>
                            <?php endforeach; ?>
                        </div>
                    </div>
                    <?php if (!empty($dashboard['activity'])) : ?><div class="stats-axis"><span><?php echo esc_html($dashboard['activity'][0]['date']); ?></span><span><?php echo esc_html($dashboard['activity'][count($dashboard['activity']) - 1]['date']); ?></span></div><?php endif; ?>
                </article>
                <article class="panel stats-panel">
                    <div class="stats-panel-heading"><h2>Running averages</h2></div>
                    <dl class="stats-list">
                        <div><dt>Games per day</dt><dd><?php echo esc_html(number_format_i18n((float) $dashboard['averages']['per_day'], 2)); ?></dd></div>
                        <div><dt>Games per week</dt><dd><?php echo esc_html(number_format_i18n((float) $dashboard['averages']['per_week'], 2)); ?></dd></div>
                        <div><dt>Total play time</dt><dd><?php echo esc_html(cmg_statistics_duration($dashboard['lifetime']['duration_seconds'])); ?></dd></div>
                        <div><dt>Most recent activity</dt><dd><?php echo !empty($dashboard['lifetime']['most_recent']) ? esc_html(gmdate('Y-m-d H:i', strtotime($dashboard['lifetime']['most_recent'] . ' UTC'))) : '—'; ?></dd></div>
                    </dl>
                </article>
            </section>

            <section class="stats-grid stats-trends">
                <article class="panel stats-panel"><div class="stats-panel-heading"><h2>Weekly trends</h2></div><dl class="stats-list"><?php foreach ($dashboard['weekly'] as $row) : ?><div><dt><?php echo esc_html($row['period']); ?></dt><dd><?php echo esc_html(number_format_i18n((int) $row['count'])); ?> games</dd></div><?php endforeach; ?><?php if (empty($dashboard['weekly'])) : ?><p class="stats-empty">No activity in this range.</p><?php endif; ?></dl></article>
                <article class="panel stats-panel"><div class="stats-panel-heading"><h2>Monthly trends</h2></div><dl class="stats-list"><?php foreach ($dashboard['monthly'] as $row) : ?><div><dt><?php echo esc_html($row['period']); ?></dt><dd><?php echo esc_html(number_format_i18n((int) $row['count'])); ?> games</dd></div><?php endforeach; ?><?php if (empty($dashboard['monthly'])) : ?><p class="stats-empty">No activity in this range.</p><?php endif; ?></dl></article>
            </section>

            <section class="panel stats-panel stats-section"><div class="stats-panel-heading"><h2>Usage by game</h2><span>Started / completed</span></div><dl class="stats-list"><?php foreach ($dashboard['by_game'] as $row) : ?><div><dt><?php echo esc_html(isset($game_names[$row['game_id']]) ? $game_names[$row['game_id']] : $row['game_id']); ?></dt><dd><?php echo esc_html(number_format_i18n((int) $row['started']) . ' / ' . number_format_i18n((int) $row['completed'])); ?></dd></div><?php endforeach; ?><?php if (empty($dashboard['by_game'])) : ?><p class="stats-empty">No activity in this range.</p><?php endif; ?></dl></section>

            <section class="panel stats-panel stats-section"><div class="stats-panel-heading"><h2>Recent activity</h2><span>Most recent 20 sessions</span></div><?php if (!empty($dashboard['recent'])) : ?><div class="stats-table-wrap"><table class="stats-table"><thead><tr><th>Started (UTC)</th><th>Game</th><th>Status</th><th>Questions</th><th>Duration</th></tr></thead><tbody><?php foreach ($dashboard['recent'] as $row) : ?><tr><td><?php echo esc_html(gmdate('Y-m-d H:i', strtotime($row['started_at'] . ' UTC'))); ?></td><td><?php echo esc_html(isset($game_names[$row['game_id']]) ? $game_names[$row['game_id']] : $row['game_id']); ?></td><td class="<?php echo $row['completed_at'] ? 'stats-complete' : 'stats-started'; ?>"><?php echo $row['completed_at'] ? 'Completed' : 'Started'; ?></td><td><?php echo esc_html(number_format_i18n((int) $row['questions_answered'])); ?></td><td><?php echo esc_html(cmg_statistics_duration($row['duration_seconds'])); ?></td></tr><?php endforeach; ?></tbody></table></div><?php else : ?><p class="stats-empty">No sessions in this range.</p><?php endif; ?></section>
        </main>

        <footer class="app-footer"><span>© Cigav Productions LLC</span><span>Statistics are anonymous and do not identify players.</span></footer>
    </div>
</body>
</html>
