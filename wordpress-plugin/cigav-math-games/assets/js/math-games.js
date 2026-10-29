(function () {
    'use strict';

    const app = document.querySelector('[data-cmg-app]');
    if (!app) {
        return;
    }

    const view = app.querySelector('[data-view]');
    const backButton = app.querySelector('[data-back-button]');
    const fullscreenButton = app.querySelector('[data-fullscreen-button]');
    const homeLink = app.querySelector('[data-home-link]');
    const installHint = app.querySelector('[data-install-hint]');
    const usageEndpoint = app.dataset.usageEndpoint || '';
    const previewBaseUrl = app.dataset.previewBaseUrl || '';

    const gameCatalog = {
        rounding: {
            name: 'Rounding Game',
            description: 'Round a number up or down to the nearest multiple.',
            icon: '≈',
            color: '#63b3ff'
        },
        addition: {
            name: 'Addition Game',
            description: 'Build confidence by solving addition problems.',
            icon: '+',
            color: '#58d68d'
        },
        money: {
            name: 'Money Match',
            description: 'Choose bills to pay for everyday items.',
            icon: '$',
            color: '#f7b955'
        },
        change: {
            name: 'Change Game',
            description: 'Work out the exact change a customer should receive.',
            icon: '¢',
            color: '#c59cff'
        },
        money_compare: {
            name: 'Money Compare',
            description: 'Decide which stack of bills and coins is worth more or less.',
            icon: '⚖',
            color: '#f7b955'
        }
    };

    const items = [
        ['Burger Meal', 7, 18, '#f25f4c', '🍔'],
        ['Taco Trio', 5, 18, '#ff8c42', '🌮'],
        ['Pizza Box', 12, 30, '#d7263d', '🍕'],
        ['Chicken Basket', 9, 24, '#f2b134', '🍗'],
        ['Grocery Apples', 3, 12, '#5f0f40', '🍎'],
        ['Cereal Box', 4, 16, '#2ec4b6', '🥣'],
        ['Orange Juice', 3, 12, '#ff9f1c', '🧃'],
        ['Veggie Basket', 6, 18, '#0ead69', '🥕'],
        ['Family Taco Pack', 18, 38, '#f97316', '🌯'],
        ['Party Sub Tray', 24, 45, '#f59e0b', '🥪'],
        ['Sushi Platter', 22, 48, '#2563eb', '🍣'],
        ['Steak Dinner', 25, 50, '#b91c1c', '🥩'],
        ['Seafood Bucket', 20, 50, '#0ea5e9', '🦐'],
        ['BBQ Feast', 28, 50, '#ea580c', '🍖'],
        ['Grocery Cart', 25, 50, '#059669', '🛒'],
        ['Picnic Pack', 15, 40, '#4f46e5', '🧺'],
        ['Veggie Burger', 7, 16, '#3b8c5a', '🥗'],
        ['Falafel Wrap', 6, 15, '#2f855a', '🧆'],
        ['Tofu Stir Fry', 10, 22, '#14b8a6', '🍲'],
        ['Veggie Sushi Roll', 8, 18, '#0ea5e9', '🥒'],
        ['Caprese Salad', 6, 14, '#ef4444', '🥬'],
        ['Mediterranean Bowl', 12, 26, '#f59e0b', '🥗'],
        ['Soda', 2, 6, '#2563eb', '🥤'],
        ['Popcorn Bucket', 4, 12, '#f59e0b', '🍿'],
        ['Chocolate Candy', 3, 10, '#7c3aed', '🍫'],
        ['Gummy Candy', 3, 10, '#10b981', '🍬'],
        ['Cupcake', 4, 12, '#f472b6', '🧁'],
        ['Slice of Cake', 5, 14, '#fb7185', '🍰']
    ].map(function (item) {
        return {
            name: item[0],
            min: item[1],
            max: item[2],
            color: item[3],
            emoji: item[4]
        };
    });

    let game = null;
    let nextRoundTimer = null;
    let fullscreenFallbackActive = false;
    let usageQueue = Promise.resolve();

    const AUTO_ADVANCE_DELAY = 1200;

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function randomInt(min, max) {
        const low = Math.ceil(min);
        const high = Math.floor(max);
        return Math.floor(Math.random() * (high - low + 1)) + low;
    }

    function clampNumber(value, min, max, fallback) {
        const parsed = Number(value);
        if (!Number.isFinite(parsed)) {
            return fallback;
        }
        return Math.min(max, Math.max(min, parsed));
    }

    function formatMoneyFromCents(cents) {
        return '$' + (cents / 100).toFixed(2);
    }

    function createUsageSessionId() {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return window.crypto.randomUUID();
        }
        return 'cmg-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 14);
    }

    function sendUsageEvent(action, payload) {
        if (!usageEndpoint || !window.fetch) {
            return;
        }
        // Keep event order without ever waiting for analytics in the game UI.
        usageQueue = usageQueue.catch(function () {}).then(function () {
            return window.fetch(usageEndpoint + action, {
                method: 'POST',
                credentials: 'same-origin',
                keepalive: true,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            }).catch(function () {});
        });
    }

    function startUsageSession() {
        game.usageSessionId = createUsageSessionId();
        game.usageCompleted = false;
        sendUsageEvent('start', {session_id: game.usageSessionId, game_id: game.id});
    }

    function recordResolvedQuestion() {
        if (!game || !game.usageSessionId) {
            return;
        }
        sendUsageEvent('question', {session_id: game.usageSessionId, question_number: game.round});
    }

    function completeUsageSession() {
        if (!game || !game.usageSessionId || game.usageCompleted) {
            return;
        }
        game.usageCompleted = true;
        sendUsageEvent('complete', {session_id: game.usageSessionId});
    }

    function currentRoute() {
        const match = window.location.hash.match(/^#game\/(rounding|addition|money|change|money_compare)$/);
        return match ? match[1] : null;
    }

    function goHome() {
        if (window.location.hash) {
            window.location.hash = '';
        } else {
            game = null;
            render();
        }
    }

    function openGame(gameId) {
        window.location.hash = 'game/' + gameId;
    }

    function route() {
        const gameId = currentRoute();
        if (!gameId) {
            game = null;
        } else if (!game || game.id !== gameId) {
            game = {
                id: gameId,
                phase: 'setup',
                config: null,
                score: 0,
                round: 0,
                current: null,
                selection: {},
                feedback: null,
                previousFeedback: null,
                history: []
            };
        }
        render();
    }

    function render() {
        if (nextRoundTimer) {
            window.clearTimeout(nextRoundTimer);
            nextRoundTimer = null;
        }
        backButton.hidden = !game;
        if (!game) {
            renderHome();
            return;
        }

        if (game.phase === 'setup') {
            renderSetup();
        } else if (game.phase === 'finished') {
            renderSummary();
        } else {
            renderPlay();
        }
    }

    function renderHome() {
        const cards = Object.keys(gameCatalog).map(function (id) {
            const details = gameCatalog[id];
            return '<article class="game-card" style="--card-color:' + details.color + ';--card-accent:' + details.color + '">' +
                renderGamePreview(id) +
                '<h2>' + escapeHtml(details.name) + '</h2>' +
                '<p>' + escapeHtml(details.description) + '</p>' +
                '<button class="button" type="button" data-open-game="' + id + '">Play game</button>' +
                '</article>';
        }).join('');

        view.innerHTML = '<section class="hero">' +
            '<p class="eyebrow">Choose a challenge</p>' +
            '<h1>Everyday math, made playable.</h1>' +
            '<p class="intro">Practice rounding, addition, paying with bills, making change, and comparing money values. Choose a game, adjust the difficulty, and start when you are ready.</p>' +
            '</section>' +
            '<section class="game-grid" aria-label="Available math games">' + cards + '</section>';

        view.querySelectorAll('[data-open-game]').forEach(function (button) {
            button.addEventListener('click', function () {
                openGame(button.dataset.openGame);
            });
        });
    }

    function renderGamePreview(gameId) {
        if (gameId === 'rounding' || gameId === 'addition' || gameId === 'money') {
            return '<div class="game-preview"><img src="' + previewBaseUrl + gameId + '.png" alt="' +
                escapeHtml(gameCatalog[gameId].name + ' game preview') + '"></div>';
        }

        if (gameId === 'change') {
            return '<div class="game-preview game-preview-change" aria-label="Change Game preview">' +
                '<div class="preview-item"><span aria-hidden="true">🍔</span><small>Total due</small><strong>$8.72</strong></div>' +
                '<div class="preview-payment"><span>$10</span><b>→</b><span>28¢</span></div>' +
                '<p>Make the exact change</p>' +
                '</div>';
        }

        return '<div class="game-preview game-preview-compare" aria-label="Money Compare preview">' +
            '<p>Which stack is worth more?</p><div class="preview-stacks">' +
            '<span class="preview-stack"><i>$20</i><i>$5</i><b>Stack A</b></span>' +
            '<span class="preview-stack"><i>$10</i><i>25¢</i><b>Stack B</b></span>' +
            '</div></div>';
    }

    function headingHtml() {
        const details = gameCatalog[game.id];
        return '<header class="game-heading">' +
            '<p class="eyebrow">Math game</p>' +
            '<h1>' + escapeHtml(details.name) + '</h1>' +
            '<p class="intro">' + escapeHtml(details.description) + '</p>' +
            '</header>';
    }

    function renderSetup() {
        let fields = '';

        if (game.id === 'rounding') {
            fields = numberField('rounds', 'Questions', 10, 1, 30, 'How many questions to play.') +
                numberField('max-number', 'Largest number', 100, 10, 10000, 'Numbers are selected from 1 to this value.') +
                numberField('factor', 'Round to nearest', 10, 2, 1000, 'For example, choose 10 for the nearest ten.') +
                checkField('show-axis', 'Show number line', 'Display the lower and upper multiples.', true);
        } else if (game.id === 'addition') {
            fields = numberField('rounds', 'Questions', 10, 1, 30, 'How many addition problems to play.') +
                numberField('max-number', 'Largest addend', 50, 5, 10000, 'Each number can be as large as this value.');
        } else if (game.id === 'money') {
            fields = numberField('rounds', 'Items', 8, 1, 30, 'How many purchases to complete.') +
                numberField('max-price', 'Maximum item price', 50, 5, 500, 'Whole-dollar item prices stay under this amount.') +
                numberField('tax-rate', 'Sales tax (%)', 9.38, 0, 30, 'Used only when sales tax is enabled.', '0.01') +
                selectField('bill-limit', 'Available bills', [
                    ['easy', 'Unlimited'],
                    ['intermediate', 'Limited'],
                    ['challenge', 'Random wallet']
                ], 'Controls how many bills are available.') +
                checkField('show-tax', 'Include sales tax', 'Add tax before calculating the payment target.', false) +
                checkField('minimal', 'Require fewest bills', 'Require the smallest possible number of bills.', false) +
                checkField('allow-overpay', 'Allow overpayment', 'Accept a payment above the whole-dollar target. This can reduce the number of bills needed.', false);
        } else if (game.id === 'money_compare') {
            fields = numberField('rounds', 'Questions', 8, 1, 30, 'How many money stacks to compare.') +
                numberField('max-amount', 'Maximum stack value', 50, 1, 500, 'No stack will be worth more than this dollar amount.');
        } else {
            fields = numberField('rounds', 'Purchases', 8, 1, 30, 'How many change problems to complete.') +
                numberField('max-price', 'Maximum item price', 50, 5, 500, 'Whole-dollar item prices stay under this amount.') +
                numberField('tax-rate', 'Sales tax (%)', 9.38, 0, 30, 'Used only when sales tax is enabled.', '0.01') +
                checkField('show-tax', 'Include sales tax', 'Add tax before calculating the change.', true) +
                checkField('minimal', 'Require fewest bills and coins', 'The change value and denomination combination must both be optimal.', false);
        }

        view.innerHTML = headingHtml() +
            '<section class="panel setup-panel">' +
            '<h2>Game settings</h2>' +
            '<p>Change these options or keep the defaults.</p>' +
            '<form data-setup-form>' +
            '<div class="settings-grid">' + fields + '</div>' +
            '<div class="button-row">' +
            '<button class="button" type="submit">Start game</button>' +
            '<button class="button button-quiet" type="button" data-cancel>Cancel</button>' +
            '</div>' +
            '</form>' +
            '</section>';

        view.querySelector('[data-setup-form]').addEventListener('submit', startGame);
        view.querySelector('[data-cancel]').addEventListener('click', goHome);
    }

    function numberField(id, label, value, min, max, help, step) {
        return '<div class="field">' +
            '<label for="cmg-' + id + '">' + escapeHtml(label) + '</label>' +
            '<input id="cmg-' + id + '" name="' + id + '" type="number" value="' + value + '" min="' + min + '" max="' + max + '" step="' + (step || '1') + '" required>' +
            '<small>' + escapeHtml(help) + '</small>' +
            '</div>';
    }

    function selectField(id, label, options, help) {
        const optionHtml = options.map(function (option) {
            return '<option value="' + option[0] + '">' + escapeHtml(option[1]) + '</option>';
        }).join('');
        return '<div class="field">' +
            '<label for="cmg-' + id + '">' + escapeHtml(label) + '</label>' +
            '<select id="cmg-' + id + '" name="' + id + '">' + optionHtml + '</select>' +
            '<small>' + escapeHtml(help) + '</small>' +
            '</div>';
    }

    function checkField(id, label, help, checked) {
        return '<label class="check-field" for="cmg-' + id + '">' +
            '<input id="cmg-' + id + '" name="' + id + '" type="checkbox"' + (checked ? ' checked' : '') + '>' +
            '<span><strong>' + escapeHtml(label) + '</strong>' + escapeHtml(help) + '</span>' +
            '</label>';
    }

    function startGame(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const value = function (name) {
            return form.elements[name] ? form.elements[name].value : '';
        };
        const checked = function (name) {
            return Boolean(form.elements[name] && form.elements[name].checked);
        };

        if (game.id === 'rounding') {
            game.config = {
                rounds: Math.round(clampNumber(value('rounds'), 1, 30, 10)),
                maxNumber: Math.round(clampNumber(value('max-number'), 10, 10000, 100)),
                factor: Math.round(clampNumber(value('factor'), 2, 1000, 10)),
                showAxis: checked('show-axis')
            };
        } else if (game.id === 'addition') {
            game.config = {
                rounds: Math.round(clampNumber(value('rounds'), 1, 30, 10)),
                maxNumber: Math.round(clampNumber(value('max-number'), 5, 10000, 50))
            };
        } else if (game.id === 'money') {
            game.config = {
                rounds: Math.round(clampNumber(value('rounds'), 1, 30, 8)),
                maxPrice: Math.round(clampNumber(value('max-price'), 5, 500, 50)),
                taxRate: clampNumber(value('tax-rate'), 0, 30, 9.38) / 100,
                showTax: checked('show-tax'),
                requireMinimal: checked('minimal'),
                allowOverpay: checked('allow-overpay'),
                billLimitMode: value('bill-limit') || 'easy'
            };
        } else if (game.id === 'money_compare') {
            game.config = {
                rounds: Math.round(clampNumber(value('rounds'), 1, 30, 8)),
                maxAmount: Math.round(clampNumber(value('max-amount'), 1, 500, 50))
            };
        } else {
            game.config = {
                rounds: Math.round(clampNumber(value('rounds'), 1, 30, 8)),
                maxPrice: Math.round(clampNumber(value('max-price'), 5, 500, 50)),
                taxRate: clampNumber(value('tax-rate'), 0, 30, 9.38) / 100,
                showTax: checked('show-tax'),
                requireMinimal: checked('minimal')
            };
        }

        game.phase = 'playing';
        game.score = 0;
        game.round = 0;
        game.history = [];
        game.feedback = null;
        game.previousFeedback = null;
        game.selection = {};
        game.moneyCompareNonMixedRounds = 0;
        game.current = createRound();
        startUsageSession();
        render();
    }

    function chooseItem(maxPrice) {
        const item = items[randomInt(0, items.length - 1)];
        let high = Math.min(item.max, maxPrice);
        let low = Math.min(item.min, maxPrice);
        if (high < 1) {
            high = 1;
        }
        if (low > high) {
            low = Math.max(1, high);
        }
        return {
            name: item.name,
            color: item.color,
            emoji: item.emoji,
            priceCents: randomInt(low, high) * 100
        };
    }

    function createRound() {
        if (game.id === 'rounding') {
            const number = randomInt(1, game.config.maxNumber);
            const lower = Math.floor(number / game.config.factor) * game.config.factor;
            return {
                number: number,
                lower: lower,
                upper: lower + game.config.factor
            };
        }

        if (game.id === 'addition') {
            return {
                number1: randomInt(1, game.config.maxNumber),
                number2: randomInt(1, game.config.maxNumber)
            };
        }

        if (game.id === 'money') {
            return createMoneyRound();
        }

        if (game.id === 'money_compare') {
            return createMoneyCompareRound();
        }

        return createChangeRound();
    }

    function moneyCountsTotal(counts) {
        return Object.keys(counts).reduce(function (total, denom) {
            return total + Number(denom) * counts[denom];
        }, 0);
    }

    function createMoneyCompareRound() {
        // Intentional contrasts keep the questions teachable: value beats piece count.
        const patterns = [
            {left: {2000: 1}, right: {500: 3, 100: 2}, mixed: false},
            {left: {1000: 1}, right: {100: 3}, mixed: false},
            {left: {500: 1}, right: {100: 4}, mixed: false},
            {left: {100: 1}, right: {25: 4, 10: 1}, mixed: false},
            {left: {25: 4, 10: 1}, right: {100: 1}, mixed: false},
            {left: {1000: 1, 25: 2}, right: {500: 2, 10: 2}, mixed: true},
            {left: {500: 1, 100: 4, 25: 3}, right: {1000: 1, 10: 2}, mixed: true},
            {left: {100: 1, 25: 3}, right: {25: 4, 10: 2}, mixed: true},
            {left: {25: 4}, right: {25: 3, 10: 2}, mixed: false}
        ];
        const cap = game.config.maxAmount * 100;
        const choices = patterns.filter(function (pattern) {
            return Math.max(moneyCountsTotal(pattern.left), moneyCountsTotal(pattern.right)) <= cap &&
                moneyCountsTotal(pattern.left) !== moneyCountsTotal(pattern.right);
        });
        const mixedChoices = choices.filter(function (pattern) { return pattern.mixed; });
        const preferred = game.moneyCompareNonMixedRounds >= 1 && mixedChoices.length ? mixedChoices : choices;
        const chosen = preferred.length ? preferred[randomInt(0, preferred.length - 1)] : patterns[8];
        game.moneyCompareNonMixedRounds = chosen.mixed ? 0 : (game.moneyCompareNonMixedRounds || 0) + 1;
        const swap = Math.random() < 0.5;
        const left = swap ? chosen.right : chosen.left;
        const right = swap ? chosen.left : chosen.right;
        const comparison = Math.random() < 0.5 ? 'higher' : 'lower';
        const leftTotal = moneyCountsTotal(left);
        const rightTotal = moneyCountsTotal(right);
        return {
            left: left,
            right: right,
            leftTotalCents: leftTotal,
            rightTotalCents: rightTotal,
            comparison: comparison,
            correctSide: comparison === 'higher' ? (leftTotal > rightTotal ? 'left' : 'right') :
                (leftTotal < rightTotal ? 'left' : 'right')
        };
    }

    function createMoneyRound() {
        let item;
        let available;
        let target;
        for (let attempt = 0; attempt < 30; attempt += 1) {
            item = chooseItem(game.config.maxPrice);
            const taxCents = game.config.showTax ? Math.round(item.priceCents * game.config.taxRate) : 0;
            item.taxCents = taxCents;
            item.totalDueCents = item.priceCents + taxCents;
            target = Math.ceil(item.totalDueCents / 100);
            available = generateBillLimits(target, game.config.billLimitMode);
            if (bestMoneyCombo(target, available, game.config.allowOverpay)) {
                break;
            }
        }
        game.selection = {20: 0, 10: 0, 5: 0, 1: 0};
        if (!bestMoneyCombo(target, available, game.config.allowOverpay)) {
            available = {20: Math.max(1, Math.ceil(target / 20)), 10: 2, 5: 3, 1: 4};
        }
        item.available = available || {20: 2, 10: 2, 5: 3, 1: 5};
        return item;
    }

    function generateBillLimits(target, mode) {
        if (mode === 'easy') {
            return {20: 999, 10: 999, 5: 999, 1: 999};
        }
        if (mode === 'intermediate') {
            return {20: Math.max(1, Math.ceil(target / 20)), 10: 2, 5: 3, 1: 4};
        }
        const scale = Math.max(4, Math.ceil(target / 20));
        for (let attempt = 0; attempt < 20; attempt += 1) {
            const limits = {
                20: randomInt(0, scale + 2),
                10: randomInt(0, Math.max(4, Math.ceil(scale / 2))),
                5: randomInt(0, 5),
                1: randomInt(0, 9)
            };
            const capacity = limits[20] * 20 + limits[10] * 10 + limits[5] * 5 + limits[1];
            if (capacity >= target) {
                return limits;
            }
        }
        return {20: 2, 10: 2, 5: 3, 1: 5};
    }

    function createChangeRound() {
        const item = chooseItem(game.config.maxPrice);
        item.taxCents = game.config.showTax ? Math.round(item.priceCents * game.config.taxRate) : 0;
        item.totalDueCents = item.priceCents + item.taxCents;
        const payment = pickPayment(item.totalDueCents);
        item.payCounts = payment.counts;
        item.payTotalCents = payment.total;
        item.changeDueCents = payment.total - item.totalDueCents;
        item.bestChange = greedyCounts(item.changeDueCents, [1000, 500, 100, 25, 10, 5, 1]);
        item.available = {1000: 5, 500: 5, 100: 20, 25: 20, 10: 20, 5: 20, 1: 40};
        game.selection = {1000: 0, 500: 0, 100: 0, 25: 0, 10: 0, 5: 0, 1: 0};
        return item;
    }

    function pickPayment(totalDueCents) {
        const denoms = [2000, 1000, 500, 100];
        for (let attempt = 0; attempt < 40; attempt += 1) {
            const wallet = {2000: randomInt(1, 3), 1000: randomInt(0, 2), 500: randomInt(0, 2), 100: randomInt(0, 3)};
            const capacity = denoms.reduce(function (sum, denom) {
                return sum + denom * wallet[denom];
            }, 0);
            if (capacity < totalDueCents) {
                continue;
            }
            let best = null;
            for (let c20 = 0; c20 <= wallet[2000]; c20 += 1) {
                for (let c10 = 0; c10 <= wallet[1000]; c10 += 1) {
                    for (let c5 = 0; c5 <= wallet[500]; c5 += 1) {
                        for (let c1 = 0; c1 <= wallet[100]; c1 += 1) {
                            const counts = {2000: c20, 1000: c10, 500: c5, 100: c1};
                            const total = c20 * 2000 + c10 * 1000 + c5 * 500 + c1 * 100;
                            const billCount = c20 + c10 + c5 + c1;
                            if (total < totalDueCents) {
                                continue;
                            }
                            if (!best || total < best.total || (total === best.total && billCount < best.billCount) ||
                                (total === best.total && billCount === best.billCount && c20 > best.counts[2000])) {
                                best = {counts: counts, total: total, billCount: billCount};
                            }
                        }
                    }
                }
            }
            if (best) {
                return best;
            }
        }
        const payTotal = Math.ceil(totalDueCents / 100) * 100;
        return {counts: greedyCounts(payTotal, denoms), total: payTotal};
    }

    function greedyCounts(amount, denoms) {
        let remaining = amount;
        const result = {};
        denoms.forEach(function (denom) {
            result[denom] = Math.floor(remaining / denom);
            remaining %= denom;
        });
        return result;
    }

    function renderPlay() {
        let problemHtml = '';
        if (game.id === 'rounding') {
            problemHtml = renderRounding();
        } else if (game.id === 'addition') {
            problemHtml = renderAddition();
        } else if (game.id === 'money') {
            problemHtml = renderMoney();
        } else if (game.id === 'money_compare') {
            problemHtml = renderMoneyCompare();
        } else {
            problemHtml = renderChange();
        }

        view.innerHTML = headingHtml() +
            '<div class="game-layout">' +
            '<section class="panel play-panel">' + renderHud() + problemHtml + '</section>' +
            renderHistory() +
            '</div>' +
            renderCurrentOptions();

        bindPlayEvents();
    }

    function renderHud() {
        const completed = game.round;
        const total = game.config.rounds;
        const percent = Math.min(100, Math.round((completed / total) * 100));
        return '<div class="hud" aria-label="Game progress">' +
            '<div class="hud-item"><span>Question</span><strong>' + Math.min(completed + 1, total) + ' / ' + total + '</strong></div>' +
            '<div class="hud-item"><span>Score</span><strong>' + game.score + '</strong></div>' +
            '<div class="hud-item"><span>Completed</span><strong>' + completed + '</strong></div>' +
            '</div>' +
            '<div class="progress" aria-label="' + percent + '% complete"><span style="width:' + percent + '%"></span></div>';
    }

    function renderCurrentOptions() {
        if (!game || !game.config) {
            return '';
        }

        const config = game.config;
        let options;
        if (game.id === 'rounding') {
            options = [
                ['Questions', config.rounds],
                ['Largest number', config.maxNumber],
                ['Round to nearest', config.factor],
                ['Number line', config.showAxis ? 'Shown' : 'Hidden']
            ];
        } else if (game.id === 'addition') {
            options = [
                ['Questions', config.rounds],
                ['Largest addend', config.maxNumber]
            ];
        } else if (game.id === 'money') {
            const billModes = {easy: 'Unlimited', intermediate: 'Limited', challenge: 'Random wallet'};
            options = [
                ['Items', config.rounds],
                ['Maximum price', '$' + config.maxPrice],
                ['Sales tax', config.showTax ? formatPercent(config.taxRate) : 'Off'],
                ['Available bills', billModes[config.billLimitMode] || config.billLimitMode],
                ['Fewest bills required', config.requireMinimal ? 'Yes' : 'No'],
                ['Overpayment allowed', config.allowOverpay ? 'Yes' : 'No']
            ];
        } else if (game.id === 'money_compare') {
            options = [
                ['Questions', config.rounds],
                ['Maximum stack value', '$' + config.maxAmount]
            ];
        } else {
            options = [
                ['Purchases', config.rounds],
                ['Maximum price', '$' + config.maxPrice],
                ['Sales tax', config.showTax ? formatPercent(config.taxRate) : 'Off'],
                ['Fewest bills and coins required', config.requireMinimal ? 'Yes' : 'No']
            ];
        }

        const rows = options.map(function (option) {
            return '<div><dt>' + escapeHtml(option[0]) + '</dt><dd>' + escapeHtml(option[1]) + '</dd></div>';
        }).join('');
        return '<details class="game-options"><summary>Game options</summary><dl>' + rows + '</dl></details>';
    }

    function formatPercent(rate) {
        return (rate * 100).toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1') + '%';
    }

    function renderRounding() {
        const current = game.current;
        const position = (current.number - current.lower) / game.config.factor;
        const axis = game.config.showAxis ? '<div class="number-line" aria-label="Number line from ' + current.lower + ' to ' + current.upper + '">' +
            '<div class="number-line-track"></div>' +
            '<div class="number-line-point" style="--position:' + position + '"></div>' +
            '<span class="number-line-label">' + current.lower + '</span>' +
            '<span class="number-line-label">' + current.upper + '</span>' +
            '</div>' : '';
        const disabled = game.feedback && game.feedback.needsNext ? ' disabled' : '';
        return '<div class="problem-card">' +
            '<p class="problem-label">Round to the nearest ' + game.config.factor + '</p>' +
            '<div class="big-number">' + current.number + '</div>' +
            axis +
            '<div class="choice-grid">' +
            '<button class="choice-button" type="button" data-round-answer="down"' + disabled + '><span>Round down</span><strong>' + current.lower + '</strong></button>' +
            '<button class="choice-button" type="button" data-round-answer="up"' + disabled + '><span>Round up</span><strong>' + current.upper + '</strong></button>' +
            '</div>' +
            '</div>' + renderFeedback();
    }

    function renderAddition() {
        const disabled = game.feedback && game.feedback.needsNext ? ' disabled' : '';
        return '<div class="problem-card">' +
            '<p class="problem-label">Find the sum</p>' +
            '<div class="equation">' + game.current.number1 + ' + ' + game.current.number2 + '</div>' +
            '<form class="answer-form" data-addition-form>' +
            '<label class="field-label" for="cmg-answer">Your answer</label>' +
            '<input class="answer-input" id="cmg-answer" name="answer" type="number" inputmode="numeric" autocomplete="off" required' + disabled + '>' +
            '<button class="button" type="submit"' + disabled + '>Check answer</button>' +
            '</form>' +
            '</div>' + renderFeedback();
    }

    function renderMoney() {
        const item = game.current;
        const target = Math.ceil(item.totalDueCents / 100) * 100;
        const locked = Boolean(game.feedback && game.feedback.needsNext);
        const disabled = locked ? ' disabled' : '';
        return renderItemStage(item) +
            '<p class="money-question">Build a payment of ' + formatMoneyFromCents(target) +
            (item.totalDueCents !== target ? ' to cover the amount due.' : '.') + '</p>' +
            renderDenominations([20, 10, 5, 1], false) +
            '<div class="total-strip"><span>Your payment</span><strong>' + formatMoneyFromCents(selectionTotalDollars() * 100) + '</strong></div>' +
            '<div class="button-row" style="margin-top:16px">' +
            '<button class="button" type="button" data-submit-money' + disabled + '>Check payment</button>' +
            '<button class="button button-secondary" type="button" data-clear-counts' + disabled + '>Clear</button>' +
            '<button class="button button-quiet" type="button" data-skip' + disabled + '>Skip item</button>' +
            '</div>' + renderFeedback();
    }

    function renderMoneyCompare() {
        const current = game.current;
        const disabled = game.feedback && game.feedback.needsNext ? ' disabled' : '';
        return '<div class="money-compare-question">Which stack is worth <strong>' + comparisonLabel(current.comparison) + '</strong>?</div>' +
            '<div class="money-compare-grid">' +
            renderMoneyCompareStack('left', 'Stack A', current.left, disabled) +
            renderMoneyCompareStack('right', 'Stack B', current.right, disabled) +
            '</div><p class="money-compare-hint">Count the value of the bills and coins — not only how many pieces there are.</p>' +
            '<div class="button-row"><button class="button button-quiet" type="button" data-skip' + disabled + '>Skip question</button></div>' +
            renderFeedback();
    }

    function renderMoneyCompareStack(side, title, counts, disabled) {
        const denoms = [2000, 1000, 500, 100, 25, 10, 5, 1];
        const pieces = denoms.filter(function (denom) { return counts[denom]; }).map(function (denom) {
            const label = denominationLabel(denom);
            const tokens = Array(counts[denom]).fill('').map(function () {
                return renderMoneyToken(denom, true, 'compare-money-token');
            }).join('');
            return '<span class="compare-money-piece"><span class="compare-money-images">' + tokens + '</span>' +
                '<span><strong>' + counts[denom] + ' ' + (denom < 100 ? 'coins' : 'bills') + '</strong></span></span>';
        }).join('');
        return '<button class="money-stack money-stack-' + side + '" type="button" data-compare-answer="' + side + '"' + disabled +
            ' aria-label="Choose ' + title + '"><span class="money-stack-title">' + title + ' — tap anywhere to choose</span>' +
            '<span class="compare-money-list">' + pieces + '</span></button>';
    }

    function renderChange() {
        const item = game.current;
        const locked = Boolean(game.feedback && game.feedback.needsNext);
        const disabled = locked ? ' disabled' : '';
        return renderItemStage(item) +
            '<div class="payment-display" aria-label="Customer payment">' + paymentTokens(item.payCounts) + '</div>' +
            '<p class="money-question">The customer pays ' + formatMoneyFromCents(item.payTotalCents) + '. Build the exact change.</p>' +
            renderDenominations([1000, 500, 100, 25, 10, 5, 1], true) +
            '<div class="total-strip"><span>Your change</span><strong>' + formatMoneyFromCents(selectionTotalCents()) + '</strong></div>' +
            '<div class="button-row" style="margin-top:16px">' +
            '<button class="button" type="button" data-submit-change' + disabled + '>Check change</button>' +
            '<button class="button button-secondary" type="button" data-clear-counts' + disabled + '>Clear</button>' +
            '<button class="button button-quiet" type="button" data-skip' + disabled + '>Skip purchase</button>' +
            '</div>' + renderFeedback();
    }

    function renderItemStage(item) {
        return '<div class="problem-card item-stage">' +
            '<div class="item-visual" style="--item-color:' + item.color + '" role="img" aria-label="' + escapeHtml(item.name) + '">' + item.emoji + '</div>' +
            '<div class="item-details">' +
            '<p class="problem-label">Purchase</p>' +
            '<h2>' + escapeHtml(item.name) + '</h2>' +
            '<dl class="receipt">' +
            '<div><dt>Price</dt><dd>' + formatMoneyFromCents(item.priceCents) + '</dd></div>' +
            (game.config.showTax ? '<div><dt>Sales tax</dt><dd>' + formatMoneyFromCents(item.taxCents) + '</dd></div>' : '') +
            '<div><dt>Total due</dt><dd>' + formatMoneyFromCents(item.totalDueCents) + '</dd></div>' +
            '</dl>' +
            '</div>' +
            '</div>';
    }

    function renderDenominations(denoms, centsMode) {
        const locked = Boolean(game.feedback && game.feedback.needsNext);
        const cards = denoms.map(function (denom) {
            const count = game.selection[denom] || 0;
            const max = game.current.available[denom];
            const label = centsMode ? denominationLabel(denom) : '$' + denom;
            const availability = max >= 999 ? 'Available: unlimited' : 'Available: ' + max;
            return '<div class="denomination">' +
                renderMoneyToken(denom, centsMode, '') +
                '<div class="counter">' +
                '<button type="button" data-count="' + denom + '" data-delta="-1" aria-label="Remove one ' + label + '"' + (locked || count <= 0 ? ' disabled' : '') + '>−</button>' +
                '<output aria-label="' + label + ' count">' + count + '</output>' +
                '<button type="button" data-count="' + denom + '" data-delta="1" aria-label="Add one ' + label + '"' + (locked || count >= max ? ' disabled' : '') + '>+</button>' +
                '</div>' +
                '<p class="availability">' + availability + '</p>' +
                '</div>';
        }).join('');
        return '<div class="denomination-grid' + (centsMode ? ' change-grid' : '') + '">' + cards + '</div>';
    }

    function renderMoneyToken(denom, centsMode, extraClass) {
        const cents = centsMode ? denom : denom * 100;
        const isCoin = cents < 100;
        const value = isCoin ? cents : cents / 100;
        const label = denominationLabel(cents);
        const className = (isCoin ? 'coin-token coin-' : 'bill-token bill-') + value;
        return '<div class="money-token ' + className + (extraClass ? ' ' + extraClass : '') + '" role="img" aria-label="' +
            escapeHtml(label + (isCoin ? ' coin' : ' bill')) + '">' +
            '<span class="money-token-label">' + escapeHtml(label) + '</span>' +
            '</div>';
    }

    function denominationLabel(cents) {
        if (cents >= 100) {
            return '$' + (cents / 100);
        }
        return cents + '¢';
    }

    function paymentTokens(counts) {
        const labels = [];
        [2000, 1000, 500, 100].forEach(function (denom) {
            const count = counts[denom] || 0;
            if (count > 0) {
                labels.push('<div class="payment-token">' +
                    renderMoneyToken(denom, true, 'money-token-compact') +
                    '<strong>' + count + ' × $' + (denom / 100) + '</strong>' +
                    '</div>');
            }
        });
        return labels.join('') || '<span class="payment-empty">Exact payment</span>';
    }

    function renderFeedback() {
        if (game.feedback) {
            return renderFeedbackCard(game.feedback, 'Current answer', true);
        }
        if (game.previousFeedback) {
            return renderFeedbackCard(
                game.previousFeedback,
                game.previousFeedback.archiveLabel || 'Previous answer',
                false
            );
        }
        return '<div aria-live="polite"></div>';
    }

    function renderFeedbackCard(feedback, label, announce) {
        if (!feedback) {
            return '<div aria-live="polite"></div>';
        }
        const liveAttributes = announce ? ' role="status" aria-live="polite"' : '';
        return '<aside class="previous-feedback ' + (feedback.correct ? 'correct' : 'incorrect') + '" aria-label="' +
            escapeHtml(label) + '"' + liveAttributes + '>' +
            '<div class="previous-feedback-heading">' +
            '<span>' + escapeHtml(label) + '</span>' +
            '<strong>' + escapeHtml(feedback.title) + '</strong>' +
            '</div>' +
            '<dl class="previous-feedback-details">' +
            '<div><dt>Asked</dt><dd>' + escapeHtml(feedback.question || 'Current question') + '</dd></div>' +
            '<div><dt>Your answer</dt><dd>' + escapeHtml(feedback.answer || 'No answer') + '</dd></div>' +
            '</dl>' +
            '<p class="previous-feedback-result">' + escapeHtml(feedback.message) + '</p>' +
            '</aside>';
    }

    function renderPreviousFeedback() {
        if (!game || !game.previousFeedback) {
            return '';
        }
        return renderFeedbackCard(
            game.previousFeedback,
            game.previousFeedback.archiveLabel || 'Previous answer',
            false
        );
    }

    function archiveCurrentFeedback(label) {
        if (!game || !game.feedback) {
            return;
        }
        game.previousFeedback = Object.assign({}, game.feedback, {
            archiveLabel: label || 'Previous answer'
        });
    }

    function renderHistory() {
        let content = '<p class="empty-history">Your answers will appear here as you play.</p>';
        if (game.history.length) {
            content = '<ol class="history-list">' + game.history.slice().reverse().slice(0, 10).map(function (entry) {
                return '<li class="' + (entry.correct ? 'correct' : 'incorrect') + '">' +
                    '<span class="result-icon" aria-hidden="true">' + (entry.correct ? '✓' : '×') + '</span>' +
                    '<span>' + escapeHtml(entry.text) + '</span>' +
                    '</li>';
            }).join('') + '</ol>';
        }
        return '<aside class="panel side-panel"><h2>Recent answers</h2>' + content + '</aside>';
    }

    function bindPlayEvents() {
        view.querySelectorAll('[data-round-answer]').forEach(function (button) {
            button.addEventListener('click', function () {
                submitRounding(button.dataset.roundAnswer);
            });
        });

        view.querySelectorAll('[data-compare-answer]').forEach(function (button) {
            button.addEventListener('click', function () {
                submitMoneyCompare(button.dataset.compareAnswer);
            });
        });

        const additionForm = view.querySelector('[data-addition-form]');
        if (additionForm) {
            additionForm.addEventListener('submit', function (event) {
                event.preventDefault();
                submitAddition(additionForm.elements.answer.value);
            });
            if (!game.feedback) {
                additionForm.elements.answer.focus();
            }
        }

        view.querySelectorAll('[data-count]').forEach(function (button) {
            button.addEventListener('click', function () {
                const denom = Number(button.dataset.count);
                const delta = Number(button.dataset.delta);
                const max = game.current.available[denom];
                game.selection[denom] = Math.max(0, Math.min(max, (game.selection[denom] || 0) + delta));
                if (game.feedback && !game.feedback.needsNext) {
                    archiveCurrentFeedback('Previous attempt');
                    game.feedback = null;
                }
                render();
            });
        });

        const submitMoney = view.querySelector('[data-submit-money]');
        if (submitMoney) {
            submitMoney.addEventListener('click', submitMoneyAnswer);
        }
        const submitChange = view.querySelector('[data-submit-change]');
        if (submitChange) {
            submitChange.addEventListener('click', submitChangeAnswer);
        }
        const clear = view.querySelector('[data-clear-counts]');
        if (clear) {
            clear.addEventListener('click', function () {
                if (game.feedback && !game.feedback.needsNext) {
                    archiveCurrentFeedback('Previous attempt');
                }
                Object.keys(game.selection).forEach(function (key) {
                    game.selection[key] = 0;
                });
                game.feedback = null;
                render();
            });
        }
        const skip = view.querySelector('[data-skip]');
        if (skip) {
            skip.addEventListener('click', skipRound);
        }
        if (game.feedback && game.feedback.needsNext) {
            nextRoundTimer = window.setTimeout(nextRound, AUTO_ADVANCE_DELAY);
        }
    }

    function submitRounding(answer) {
        if (game.feedback && game.feedback.needsNext) {
            return;
        }
        const current = game.current;
        const correctAnswer = (current.number - current.lower) < (current.upper - current.number) ? 'down' : 'up';
        const correct = answer === correctAnswer;
        if (correct) {
            game.score += 1;
        }
        game.round += 1;
        recordResolvedQuestion();
        game.history.push({
            correct: correct,
            text: current.number + ' → ' + (answer === 'down' ? current.lower : current.upper)
        });
        const destination = correctAnswer === 'down' ? current.lower : current.upper;
        const selectedDestination = answer === 'down' ? current.lower : current.upper;
        game.feedback = {
            correct: correct,
            title: correct ? 'Correct!' : 'Not quite.',
            message: current.number + ' rounds ' + correctAnswer + ' to ' + destination + '.',
            question: 'Round ' + current.number + ' to the nearest ' + game.config.factor + '.',
            answer: 'Rounded ' + answer + ' to ' + selectedDestination + '.',
            needsNext: true
        };
        render();
    }

    function submitAddition(rawAnswer) {
        if (game.feedback && game.feedback.needsNext) {
            return;
        }
        const answer = Number(rawAnswer);
        const total = game.current.number1 + game.current.number2;
        const correct = Number.isFinite(answer) && answer === total;
        if (correct) {
            game.score += 1;
        }
        game.round += 1;
        recordResolvedQuestion();
        game.history.push({
            correct: correct,
            text: game.current.number1 + ' + ' + game.current.number2 + ' = ' + (rawAnswer || 'blank')
        });
        game.feedback = {
            correct: correct,
            title: correct ? 'Correct!' : 'Not quite.',
            message: game.current.number1 + ' + ' + game.current.number2 + ' = ' + total + '.',
            question: 'Find ' + game.current.number1 + ' + ' + game.current.number2 + '.',
            answer: rawAnswer === '' ? 'No answer' : rawAnswer,
            needsNext: true
        };
        render();
    }

    function selectionTotalDollars() {
        return [20, 10, 5, 1].reduce(function (sum, denom) {
            return sum + denom * (game.selection[denom] || 0);
        }, 0);
    }

    function selectionTotalCents() {
        return [1000, 500, 100, 25, 10, 5, 1].reduce(function (sum, denom) {
            return sum + denom * (game.selection[denom] || 0);
        }, 0);
    }

    function bestMoneyCombo(target, available, allowOverpay) {
        const max20 = Math.min(available[20], Math.ceil(target / 20));
        const max10 = Math.min(available[10], Math.ceil(target / 10));
        const max5 = Math.min(available[5], Math.ceil(target / 5));
        let best = null;
        for (let c20 = 0; c20 <= max20; c20 += 1) {
            for (let c10 = 0; c10 <= max10; c10 += 1) {
                for (let c5 = 0; c5 <= max5; c5 += 1) {
                    const subtotal = c20 * 20 + c10 * 10 + c5 * 5;
                    const c1 = Math.max(0, target - subtotal);
                    if ((!allowOverpay && subtotal > target) || c1 > available[1]) {
                        continue;
                    }
                    const combo = {20: c20, 10: c10, 5: c5, 1: c1};
                    const total = subtotal + c1;
                    const billCount = c20 + c10 + c5 + c1;
                    if (total < target || (!allowOverpay && total !== target)) {
                        continue;
                    }
                    if (!best || billCount < best.billCount ||
                        (billCount === best.billCount && total < best.total) ||
                        (billCount === best.billCount && total === best.total && c20 > best.combo[20])) {
                        best = {combo: combo, total: total, billCount: billCount};
                    }
                }
            }
        }
        return best;
    }

    function submitMoneyAnswer() {
        if (game.feedback && game.feedback.needsNext) {
            return;
        }
        const item = game.current;
        const target = Math.ceil(item.totalDueCents / 100);
        const best = bestMoneyCombo(target, item.available, game.config.allowOverpay);
        const userTotal = selectionTotalDollars();
        const userBillCount = countMoneyPieces(game.selection, [20, 10, 5, 1]);
        const valueValid = userTotal >= target && (game.config.allowOverpay || userTotal === target);
        const minimalValid = !game.config.requireMinimal || (best && userBillCount === best.billCount);
        const correct = valueValid && minimalValid;

        game.history.push({
            correct: correct,
            text: escapeHistoryMoney(game.selection, false) + ' = $' + userTotal
        });

        if (correct) {
            game.score += 1;
            game.round += 1;
            recordResolvedQuestion();
            game.feedback = {
                correct: true,
                title: 'Payment accepted!',
                message: 'You built a valid payment of $' + userTotal + ' using ' + pluralize(userBillCount, 'bill') + '.',
                question: moneyQuestionDescription(item, target),
                answer: moneyComboDescription(game.selection, false) + ' = $' + userTotal,
                needsNext: true
            };
        } else {
            let hint;
            if (userTotal < target) {
                hint = 'Your payment is $' + userTotal + '. Add $' + (target - userTotal) + ' to reach the $' + target + ' target.';
            } else if (!game.config.allowOverpay && userTotal > target) {
                hint = 'This game requires exactly $' + target + '. Remove $' + (userTotal - target) + ' from your payment.';
            } else if (game.config.requireMinimal && best) {
                hint = 'This payment uses ' + pluralize(userBillCount, 'bill') + '. The fewest possible is ' +
                    pluralize(best.billCount, 'bill') + ' (for example, ' + moneyComboDescription(best.combo, false) + ').';
            } else {
                hint = 'Check the selected options below and adjust your payment.';
            }
            game.feedback = {
                correct: false,
                title: 'Try that item again.',
                message: hint,
                question: moneyQuestionDescription(item, target),
                answer: moneyComboDescription(game.selection, false) + ' = $' + userTotal,
                needsNext: false
            };
        }
        render();
    }

    function submitChangeAnswer() {
        if (game.feedback && game.feedback.needsNext) {
            return;
        }
        const total = selectionTotalCents();
        const denoms = [1000, 500, 100, 25, 10, 5, 1];
        const userPieceCount = countMoneyPieces(game.selection, denoms);
        const bestPieceCount = countMoneyPieces(game.current.bestChange, denoms);
        let correct = total === game.current.changeDueCents;
        if (correct && game.config.requireMinimal) {
            correct = userPieceCount === bestPieceCount;
        }

        game.history.push({
            correct: correct,
            text: escapeHistoryMoney(game.selection, true) + ' = ' + formatMoneyFromCents(total)
        });

        if (correct) {
            game.score += 1;
            game.round += 1;
            recordResolvedQuestion();
            game.feedback = {
                correct: true,
                title: 'Correct change!',
                message: 'The customer receives ' + formatMoneyFromCents(game.current.changeDueCents) + '.',
                question: changeQuestionDescription(game.current),
                answer: moneyComboDescription(game.selection, true) + ' = ' + formatMoneyFromCents(total),
                needsNext: true
            };
        } else {
            let message;
            if (total < game.current.changeDueCents) {
                message = 'Your change is ' + formatMoneyFromCents(game.current.changeDueCents - total) + ' short. The exact change is ' +
                    formatMoneyFromCents(game.current.changeDueCents) + '.';
            } else if (total > game.current.changeDueCents) {
                message = 'Your change is ' + formatMoneyFromCents(total - game.current.changeDueCents) + ' too high. The exact change is ' +
                    formatMoneyFromCents(game.current.changeDueCents) + '.';
            } else {
                message = 'The value is correct, but it uses ' + pluralize(userPieceCount, 'piece') + '. The fewest possible is ' +
                    pluralize(bestPieceCount, 'piece') + ': ' + moneyComboDescription(game.current.bestChange, true) + '.';
            }
            game.feedback = {
                correct: false,
                title: 'Try that purchase again.',
                message: message,
                question: changeQuestionDescription(game.current),
                answer: moneyComboDescription(game.selection, true) + ' = ' + formatMoneyFromCents(total),
                needsNext: false
            };
        }
        render();
    }

    function submitMoneyCompare(answer) {
        if (game.feedback && game.feedback.needsNext) {
            return;
        }
        const current = game.current;
        const correct = answer === current.correctSide;
        if (correct) {
            game.score += 1;
        }
        game.round += 1;
        recordResolvedQuestion();
        game.history.push({
            correct: correct,
            text: 'Stack ' + (answer === 'left' ? 'A' : 'B') + ' chosen — A: ' +
                formatMoneyFromCents(current.leftTotalCents) + ', B: ' + formatMoneyFromCents(current.rightTotalCents)
        });
        game.feedback = {
            correct: correct,
            title: correct ? 'Correct!' : 'Not quite.',
            message: 'Stack ' + (current.correctSide === 'left' ? 'A' : 'B') + ' is worth ' + comparisonLabel(current.comparison) +
                ': A is ' + formatMoneyFromCents(current.leftTotalCents) + ' and B is ' + formatMoneyFromCents(current.rightTotalCents) + '.',
            question: 'Which stack is worth ' + comparisonLabel(current.comparison) + '?',
            answer: 'Stack ' + (answer === 'left' ? 'A' : 'B'),
            needsNext: true
        };
        render();
    }

    function countMoneyPieces(counts, denoms) {
        return denoms.reduce(function (sum, denom) {
            return sum + (counts[denom] || 0);
        }, 0);
    }

    function pluralize(count, singular) {
        return count + ' ' + singular + (count === 1 ? '' : 's');
    }

    function moneyComboDescription(counts, centsMode) {
        const denoms = centsMode ? [1000, 500, 100, 25, 10, 5, 1] : [20, 10, 5, 1];
        const parts = [];
        denoms.forEach(function (denom) {
            const count = counts[denom] || 0;
            if (count > 0) {
                parts.push(count + ' × ' + (centsMode ? denominationLabel(denom) : '$' + denom));
            }
        });
        return parts.join(' + ') || 'no money';
    }

    function moneyQuestionDescription(item, target) {
        return item.name + ': total due ' + formatMoneyFromCents(item.totalDueCents) +
            '; build a payment of $' + target + '.';
    }

    function comparisonLabel(comparison) {
        return comparison === 'higher' ? 'more' : 'less';
    }

    function changeQuestionDescription(item) {
        return item.name + ': total due ' + formatMoneyFromCents(item.totalDueCents) +
            '; customer paid ' + formatMoneyFromCents(item.payTotalCents) +
            '; return the exact change.';
    }

    function escapeHistoryMoney(counts, centsMode) {
        const denoms = centsMode ? [1000, 500, 100, 25, 10, 5, 1] : [20, 10, 5, 1];
        const parts = [];
        denoms.forEach(function (denom) {
            if ((counts[denom] || 0) > 0) {
                parts.push(counts[denom] + '×' + (centsMode ? denominationLabel(denom) : '$' + denom));
            }
        });
        return parts.join(' + ') || 'No money selected';
    }

    function skipRound() {
        game.history.push({correct: false, text: 'Question skipped'});
        game.previousFeedback = {
            correct: false,
            title: 'Question skipped',
            message: 'No answer was submitted for this question.',
            question: currentQuestionDescription(),
            answer: 'Skipped',
            archiveLabel: game.round + 1 >= game.config.rounds ? 'Final answer' : 'Previous answer'
        };
        game.round += 1;
        if (game.round >= game.config.rounds) {
            game.phase = 'finished';
        } else {
            game.feedback = null;
            game.current = createRound();
        }
        render();
    }

    function nextRound() {
        archiveCurrentFeedback(game.round >= game.config.rounds ? 'Final answer' : 'Previous answer');
        if (game.round >= game.config.rounds) {
            game.phase = 'finished';
        } else {
            game.feedback = null;
            game.current = createRound();
        }
        render();
    }

    function currentQuestionDescription() {
        if (game.id === 'rounding') {
            return 'Round ' + game.current.number + ' to the nearest ' + game.config.factor + '.';
        }
        if (game.id === 'addition') {
            return 'Find ' + game.current.number1 + ' + ' + game.current.number2 + '.';
        }
        if (game.id === 'money') {
            return moneyQuestionDescription(game.current, Math.ceil(game.current.totalDueCents / 100));
        }
        if (game.id === 'money_compare') {
            return 'Which stack is worth ' + comparisonLabel(game.current.comparison) + '?';
        }
        return changeQuestionDescription(game.current);
    }

    function renderSummary() {
        completeUsageSession();
        const total = game.config.rounds;
        const percentage = Math.round((game.score / total) * 100);
        let message = 'Nice work finishing the game.';
        if (percentage === 100) {
            message = 'Perfect score. Every answer was correct.';
        } else if (percentage >= 75) {
            message = 'Strong work. You handled most of the questions correctly.';
        } else if (percentage < 50) {
            message = 'Practice builds confidence. Try another round when you are ready.';
        }

        view.innerHTML = headingHtml() +
            '<section class="panel summary-panel">' +
            '<p class="eyebrow">Game complete</p>' +
            '<h2>Your score</h2>' +
            '<div class="summary-score">' + game.score + ' / ' + total + '</div>' +
            '<p class="summary-message">' + escapeHtml(message) + '</p>' +
            '<div class="button-row">' +
            '<button class="button" type="button" data-play-again>Play again</button>' +
            '<button class="button button-secondary" type="button" data-summary-home>Choose another game</button>' +
            '</div>' +
            '</section>' +
            renderPreviousFeedback() +
            renderCurrentOptions();

        view.querySelector('[data-play-again]').addEventListener('click', function () {
            game.phase = 'setup';
            game.config = null;
            game.history = [];
            game.previousFeedback = null;
            render();
        });
        view.querySelector('[data-summary-home]').addEventListener('click', goHome);
    }

    homeLink.addEventListener('click', function (event) {
        event.preventDefault();
        goHome();
    });
    backButton.addEventListener('click', goHome);
    window.addEventListener('hashchange', route);

    function nativeFullscreenElement() {
        return document.fullscreenElement || document.webkitFullscreenElement || null;
    }

    function nativeFullscreenSupported() {
        return Boolean(app.requestFullscreen || app.webkitRequestFullscreen);
    }

    function focusModeRequired() {
        return /iPhone|iPod/.test(window.navigator.userAgent) || !nativeFullscreenSupported();
    }

    function isStandaloneMode() {
        return Boolean(window.navigator.standalone) ||
            (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches);
    }

    function setFullscreenFallback(active) {
        fullscreenFallbackActive = active;
        app.classList.toggle('is-fullscreen-fallback', active);
        document.documentElement.classList.toggle('cmg-fullscreen-fallback', active);
        document.body.classList.toggle('cmg-fullscreen-fallback', active);
        updateFullscreenButton();
    }

    function updateFullscreenButton() {
        if (isStandaloneMode()) {
            fullscreenButton.hidden = true;
            return;
        }
        fullscreenButton.hidden = false;
        const active = Boolean(nativeFullscreenElement()) || fullscreenFallbackActive;
        const focusMode = focusModeRequired();
        fullscreenButton.textContent = active ? (focusMode ? 'Exit focus mode' : 'Exit full screen') :
            (focusMode ? 'Focus mode' : 'Full screen');
        fullscreenButton.setAttribute('aria-pressed', active ? 'true' : 'false');
    }

    function enterFullscreen() {
        if (focusModeRequired()) {
            setFullscreenFallback(true);
            return;
        }
        const request = app.requestFullscreen || app.webkitRequestFullscreen;
        if (!request) {
            setFullscreenFallback(true);
            return;
        }

        try {
            const result = request.call(app);
            if (result && typeof result.catch === 'function') {
                result.catch(function () {
                    setFullscreenFallback(true);
                });
            }
        } catch (error) {
            setFullscreenFallback(true);
        }
    }

    function exitFullscreen() {
        if (fullscreenFallbackActive) {
            setFullscreenFallback(false);
            return;
        }
        const exit = document.exitFullscreen || document.webkitExitFullscreen;
        if (nativeFullscreenElement() && exit) {
            exit.call(document);
        }
    }

    fullscreenButton.addEventListener('click', function () {
        if (nativeFullscreenElement() || fullscreenFallbackActive) {
            exitFullscreen();
        } else {
            enterFullscreen();
        }
    });

    document.addEventListener('fullscreenchange', updateFullscreenButton);
    document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
    app.classList.toggle('is-standalone', isStandaloneMode());
    if (installHint && /iPhone|iPad|iPod/.test(window.navigator.userAgent) && !isStandaloneMode()) {
        installHint.hidden = false;
    }
    updateFullscreenButton();

    route();
}());
