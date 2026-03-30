<?php
// php/pages/bankroll.php
$pageTitle   = 'Bankroll';
$pageScripts = ['bankroll.js'];

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Bankroll.php';

Auth::requireLogin();

$bankrollM = new Bankroll();
$userId    = Auth::getUserId();
$summary   = $bankrollM->getSummary($userId);
$history   = $bankrollM->getHistory($userId, 60);

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <h4 class="mb-4"><i class="bi bi-wallet2"></i> Bankroll Management</h4>

    <!-- KPIs Bankroll -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="kpi-card">
                <div class="kpi-value text-info">€<?= number_format($summary['bankroll_attuale'], 2) ?></div>
                <div class="kpi-label">Bankroll Attuale</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="kpi-card">
                <div class="kpi-value text-muted">€<?= number_format($summary['bankroll_iniziale'], 2) ?></div>
                <div class="kpi-label">Bankroll Iniziale</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="kpi-card">
                <div class="kpi-value <?= $summary['roi_pct'] >= 0 ? 'text-positive' : 'text-negative' ?>">
                    <?= ($summary['roi_pct'] >= 0 ? '+' : '') . $summary['roi_pct'] ?>%
                </div>
                <div class="kpi-label">ROI</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="kpi-card">
                <div class="kpi-value text-warning"><?= $summary['kelly_fraction'] * 100 ?>%</div>
                <div class="kpi-label">Kelly Fraction</div>
            </div>
        </div>
    </div>

        <!-- Grafico Bankroll -->
    <div class="chart-container mb-4">
        <h6><i class="bi bi-graph-up"></i> Andamento Bankroll (60 giorni)</h6>
        <div class="chart-wrapper" style="height: 350px;">
            <canvas id="bankrollDetailChart"></canvas>
        </div>
    </div>
</div>

<script>
    const bankrollDetailHistory = <?= json_encode($history) ?>;
    const bankrollDetailInit = <?= $summary['bankroll_iniziale'] ?>;
</script>

<?php include __DIR__ . '/../templates/footer.php'; ?>