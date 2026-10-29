<?php
/**
 * Anonymous, server-side usage statistics for Cigav Math Games.
 *
 * @package CigavMathGames
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

class CMG_Usage_Statistics
{
    const DB_VERSION = '1.0.0';
    const OPTION_NAME = 'cmg_usage_statistics_db_version';

    /** @var string[] */
    private $game_ids = array('rounding', 'addition', 'money', 'money_compare', 'change');

    public function register_hooks(): void
    {
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }

    /** Create or upgrade the small, plugin-owned statistics tables. */
    public function install(): void
    {
        global $wpdb;

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $charset_collate = $wpdb->get_charset_collate();
        $sessions = $this->sessions_table();
        $questions = $this->questions_table();

        dbDelta("CREATE TABLE {$sessions} (
            session_id varchar(64) NOT NULL,
            game_id varchar(32) NOT NULL,
            started_at datetime NOT NULL,
            completed_at datetime NULL,
            questions_answered bigint(20) unsigned NOT NULL DEFAULT 0,
            duration_seconds bigint(20) unsigned NULL,
            PRIMARY KEY  (session_id),
            KEY game_id (game_id),
            KEY started_at (started_at)
        ) {$charset_collate};");

        dbDelta("CREATE TABLE {$questions} (
            session_id varchar(64) NOT NULL,
            question_number bigint(20) unsigned NOT NULL,
            PRIMARY KEY  (session_id, question_number)
        ) {$charset_collate};");

        update_option(self::OPTION_NAME, self::DB_VERSION, false);
    }

    /** Upgrade only when a plugin release changes this schema. */
    public function maybe_upgrade(): void
    {
        if (get_option(self::OPTION_NAME) !== self::DB_VERSION) {
            $this->install();
        }
    }

    public function register_rest_routes(): void
    {
        register_rest_route('cmg/v1', '/usage/start', array(
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => array($this, 'start_session'),
            'permission_callback' => '__return_true',
        ));
        register_rest_route('cmg/v1', '/usage/question', array(
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => array($this, 'record_question'),
            'permission_callback' => '__return_true',
        ));
        register_rest_route('cmg/v1', '/usage/complete', array(
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => array($this, 'complete_session'),
            'permission_callback' => '__return_true',
        ));
    }

    /** @return WP_REST_Response|WP_Error */
    public function start_session(WP_REST_Request $request)
    {
        $session_id = (string) $request->get_param('session_id');
        $game_id = (string) $request->get_param('game_id');
        if (!$this->is_valid_session_id($session_id) || !in_array($game_id, $this->game_ids, true)) {
            return new WP_Error('cmg_invalid_usage_event', 'Invalid usage event.', array('status' => 400));
        }

        global $wpdb;
        $sessions = $this->sessions_table();
        $wpdb->query($wpdb->prepare(
            "INSERT IGNORE INTO {$sessions} (session_id, game_id, started_at) VALUES (%s, %s, %s)",
            $session_id,
            $game_id,
            current_time('mysql', true)
        ));

        return new WP_REST_Response(array('recorded' => true), 201);
    }

    /** @return WP_REST_Response|WP_Error */
    public function record_question(WP_REST_Request $request)
    {
        $session_id = (string) $request->get_param('session_id');
        $question_number = absint($request->get_param('question_number'));
        if (!$this->is_valid_session_id($session_id) || $question_number < 1 || $question_number > 1000) {
            return new WP_Error('cmg_invalid_usage_event', 'Invalid usage event.', array('status' => 400));
        }

        global $wpdb;
        $sessions = $this->sessions_table();
        $questions = $this->questions_table();
        $exists = $wpdb->get_var($wpdb->prepare(
            "SELECT session_id FROM {$sessions} WHERE session_id = %s",
            $session_id
        ));
        if ($exists === null) {
            return new WP_Error('cmg_unknown_usage_session', 'Unknown game session.', array('status' => 404));
        }

        $inserted = $wpdb->query($wpdb->prepare(
            "INSERT IGNORE INTO {$questions} (session_id, question_number) VALUES (%s, %d)",
            $session_id,
            $question_number
        ));
        if ($inserted === 1) {
            $wpdb->query($wpdb->prepare(
                "UPDATE {$sessions} SET questions_answered = questions_answered + 1 WHERE session_id = %s",
                $session_id
            ));
        }

        return new WP_REST_Response(array('recorded' => true), 200);
    }

    /** @return WP_REST_Response|WP_Error */
    public function complete_session(WP_REST_Request $request)
    {
        $session_id = (string) $request->get_param('session_id');
        if (!$this->is_valid_session_id($session_id)) {
            return new WP_Error('cmg_invalid_usage_event', 'Invalid usage event.', array('status' => 400));
        }

        global $wpdb;
        $sessions = $this->sessions_table();
        $session = $wpdb->get_row($wpdb->prepare(
            "SELECT started_at, completed_at FROM {$sessions} WHERE session_id = %s",
            $session_id
        ));
        if ($session === null) {
            return new WP_Error('cmg_unknown_usage_session', 'Unknown game session.', array('status' => 404));
        }
        if ($session->completed_at !== null) {
            return new WP_REST_Response(array('recorded' => true), 200);
        }

        $started_at = strtotime($session->started_at . ' UTC');
        $duration = $started_at === false ? 0 : max(0, time() - $started_at);
        $wpdb->query($wpdb->prepare(
            "UPDATE {$sessions} SET completed_at = %s, duration_seconds = %d WHERE session_id = %s AND completed_at IS NULL",
            current_time('mysql', true),
            $duration,
            $session_id
        ));

        return new WP_REST_Response(array('recorded' => true), 200);
    }

    /**
     * Build the data model used by the public, read-only statistics page.
     *
     * @param int|null $days Null means all time.
     * @return array<string, mixed>
     */
    public function dashboard($days): array
    {
        global $wpdb;
        $sessions = $this->sessions_table();
        $today = gmdate('Y-m-d');
        $start_date = $days === null ? null : gmdate('Y-m-d', time() - (($days - 1) * DAY_IN_SECONDS));
        $where = '';
        $parameters = array();
        if ($start_date !== null) {
            $where = ' WHERE started_at >= %s';
            $parameters[] = $start_date . ' 00:00:00';
        }

        $lifetime = $wpdb->get_row("SELECT COUNT(*) AS started,
            SUM(completed_at IS NOT NULL) AS completed,
            COALESCE(SUM(questions_answered), 0) AS questions,
            COALESCE(SUM(duration_seconds), 0) AS duration_seconds,
            AVG(duration_seconds) AS average_duration,
            MIN(started_at) AS first_activity,
            MAX(COALESCE(completed_at, started_at)) AS most_recent
            FROM {$sessions}", ARRAY_A);
        $selected_sql = "SELECT COUNT(*) AS started, SUM(completed_at IS NOT NULL) AS completed FROM {$sessions}{$where}";
        $selected = $parameters ? $wpdb->get_row($wpdb->prepare($selected_sql, $parameters), ARRAY_A) : $wpdb->get_row($selected_sql, ARRAY_A);
        $by_game_sql = "SELECT game_id, COUNT(*) AS started, SUM(completed_at IS NOT NULL) AS completed FROM {$sessions}{$where} GROUP BY game_id ORDER BY started DESC, game_id ASC";
        $by_game = $parameters ? $wpdb->get_results($wpdb->prepare($by_game_sql, $parameters), ARRAY_A) : $wpdb->get_results($by_game_sql, ARRAY_A);
        $weekly_sql = "SELECT YEARWEEK(started_at, 3) AS period_key, MIN(DATE(started_at)) AS period_start, COUNT(*) AS count FROM {$sessions}{$where} GROUP BY period_key ORDER BY period_key DESC LIMIT 8";
        $weekly = $parameters ? $wpdb->get_results($wpdb->prepare($weekly_sql, $parameters), ARRAY_A) : $wpdb->get_results($weekly_sql, ARRAY_A);
        $monthly_sql = "SELECT EXTRACT(YEAR_MONTH FROM started_at) AS period_key, COUNT(*) AS count FROM {$sessions}{$where} GROUP BY period_key ORDER BY period_key DESC LIMIT 12";
        $monthly = $parameters ? $wpdb->get_results($wpdb->prepare($monthly_sql, $parameters), ARRAY_A) : $wpdb->get_results($monthly_sql, ARRAY_A);
        $recent_sql = "SELECT game_id, started_at, completed_at, questions_answered, duration_seconds FROM {$sessions}{$where} ORDER BY started_at DESC LIMIT 20";
        $recent = $parameters ? $wpdb->get_results($wpdb->prepare($recent_sql, $parameters), ARRAY_A) : $wpdb->get_results($recent_sql, ARRAY_A);

        $activity_start = $start_date ?: gmdate('Y-m-d', time() - (364 * DAY_IN_SECONDS));
        $daily_rows = $wpdb->get_results($wpdb->prepare(
            "SELECT DATE(started_at) AS day, COUNT(*) AS count FROM {$sessions} WHERE started_at >= %s GROUP BY day ORDER BY day ASC",
            $activity_start . ' 00:00:00'
        ), ARRAY_A);
        $daily_counts = array();
        foreach ($daily_rows as $row) {
            $daily_counts[$row['day']] = (int) $row['count'];
        }
        $activity = array();
        $cursor = new DateTimeImmutable($activity_start, new DateTimeZone('UTC'));
        $end = new DateTimeImmutable($today, new DateTimeZone('UTC'));
        while ($cursor <= $end) {
            $day = $cursor->format('Y-m-d');
            $activity[] = array('date' => $day, 'count' => isset($daily_counts[$day]) ? $daily_counts[$day] : 0);
            $cursor = $cursor->modify('+1 day');
        }

        foreach ($weekly as &$row) {
            $row['period'] = gmdate('o-\\WW', strtotime($row['period_start'] . ' UTC'));
        }
        unset($row);
        $weekly = array_reverse($weekly);
        foreach ($monthly as &$row) {
            $key = (string) $row['period_key'];
            $row['period'] = substr($key, 0, 4) . '-' . substr($key, 4, 2);
        }
        unset($row);
        $monthly = array_reverse($monthly);

        $first_activity = !empty($lifetime['first_activity']) ? strtotime($lifetime['first_activity'] . ' UTC') : false;
        $active_days = $first_activity === false ? 1 : max(1, (int) floor((time() - $first_activity) / DAY_IN_SECONDS) + 1);
        $started = (int) $lifetime['started'];

        return array(
            'lifetime' => $lifetime,
            'selected' => $selected,
            'activity' => $activity,
            'by_game' => $by_game,
            'weekly' => $weekly,
            'monthly' => $monthly,
            'recent' => $recent,
            'averages' => array(
                'per_day' => $started / $active_days,
                'per_week' => $started / max(1, $active_days / 7),
            ),
        );
    }

    private function sessions_table(): string
    {
        global $wpdb;
        return $wpdb->prefix . 'cmg_game_sessions';
    }

    private function questions_table(): string
    {
        global $wpdb;
        return $wpdb->prefix . 'cmg_answered_questions';
    }

    private function is_valid_session_id(string $session_id): bool
    {
        return (bool) preg_match('/^[A-Za-z0-9-]{16,64}$/', $session_id);
    }
}
