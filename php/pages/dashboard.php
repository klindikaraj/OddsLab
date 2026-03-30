<?php
// php/pages/dashboard.php
$pageTitle   = 'Dashboard';
$pageScripts = ['charts.js'];

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Dashboard.php';
require_once __DIR__ . '/../classes/Bankroll.php';

Auth::requireLogin();

$dashboard = new Dashboard();
$bankrollM = new Bankroll();
$userId    = Auth::getUserId();

$kpis      = $dashboard->getKPIs($userId);
$recentVB  = $dashboard->getRecentValueBets(5);
$history   = $bankrollM->getHistory($userId, 30);
$bySport   = $dashboard->getValueBetsBySport();
$sysStats  = $dashboard->getSystemStats();

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <h4 class="mb-4"><i class="bi bi-speedometer2"></i> Dashboard</h4>

    <!-- KPI Cards -->
    <div class="row g-3 mb-4">
        <div class="col-lg-3 col-md-6">
            <div class="kpi-card">
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="kpi-value <?= $kpis['bankroll'] >= $kpis['bankroll_init'] ? 'text-positive' : 'text-negative' ?>">
                            €<?= number_format($kpis['bankroll'], 2) ?>
                        </div>
                        <div class="kpi-label">Bankroll</div>
                    </div>
                    <div class="kpi-icon"><i class="bi bi-wallet2"></i></div>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6">
            <div class="kpi-card">
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="kpi-value <?= $kpis['roi'] >= 0 ? 'text-positive' : 'text-negative' ?>">
                            <?= ($kpis['roi'] >= 0 ? '+' : '') . $kpis['roi'] ?>%
                        </div>
                        <div class="kpi-label">ROI</div>
                    </div>
                    <div class="kpi-icon"><i class="bi bi-graph-up-arrow"></i></div>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6">
            <div class="kpi-card">
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="kpi-value text-info"><?= $kpis['win_rate'] ?>%</div>
                        <div class="kpi-label">Win Rate (<?= $kpis['won'] ?>W / <?= $kpis['lost'] ?>L)</div>
                    </div>
                    <div class="kpi-icon"><i class="bi bi-trophy"></i></div>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6">
            <div class="kpi-card">
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="kpi-value text-warning"><?= $kpis['active_vb'] ?></div>
                        <div class="kpi-label">Value Bets Attive</div>
                    </div>
                    <div class="kpi-icon"><i class="bi bi-fire"></i></div>
                </div>
            </div>
        </div>
    </div>

    <div class="row g-3">
        <!-- Grafico Bankroll -->
        <div class="col-lg-8">
            <div class="chart-container">
                <h6 class="mb-3"><i class="bi bi-graph-up"></i> Andamento Bankroll (30 giorni)</h6>
                <div class="chart-wrapper">
                    <canvas id="bankrollChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Stats per Sport -->
        <div class="col-lg-4">
            <div class="chart-container">
                <h6 class="mb-3"><i class="bi bi-pie-chart"></i> Value Bets per Sport</h6>
                <?php if (empty($bySport)): ?>
                    <p class="text-muted">Nessun dato disponibile</p>
                <?php else: ?>
                    <?php foreach ($bySport as $s): ?>
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2"
                             style="background:#21262d; border-radius:8px;">
                            <span><?= $s['icona'] ?> <?= htmlspecialchars($s['sport']) ?></span>
                            <span>
                                <span class="badge bg-secondary"><?= $s['totale'] ?> totali</span>
                                <span class="badge badge-won"><?= (int)$s['vinte'] ?>W</span>
                                <span class="badge badge-lost"><?= (int)$s['perse'] ?>L</span>
                            </span>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>

                <hr class="border-secondary">
                <h6 class="mb-2"><i class="bi bi-database"></i> Sistema</h6>
                <small class="text-muted">
                    Partite: <?= $sysStats['partite'] ?> |
                    Quote: <?= number_format($sysStats['quote']) ?> |
                    Report: <?= $sysStats['report'] ?>
                </small>
            </div>
        </div>
    </div>

    <!-- Value Bets Recenti -->
    <div class="mt-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6><i class="bi bi-fire"></i> Value Bets Attive</h6>
            <a href="index.php?page=valuebets" class="btn btn-outline-success btn-sm">
                Vedi tutte <i class="bi bi-arrow-right"></i>
            </a>
        </div>

        <?php if (empty($recentVB)): ?>
            <div class="alert alert-secondary">
                <i class="bi bi-info-circle"></i> Nessuna value bet attiva.
                Esegui <code>python main.py</code> per aggiornare.
            </div>
        <?php else: ?>
            <div class="table-responsive">
                <table class="table table-dark-custom">
                    <thead>
                        <tr>
                            <th>Match</th>
                            <th>Esito</th>
                            <th>Quota</th>
                            <th>Value</th>
                            <th>Confidenza</th>
                            <th>Book</th>
                            <th>Data</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($recentVB as $vb): ?>
                            <?php
                            $valuePct = (float) $vb['value_pct'];
                            if ($valuePct >= 20) $conf = 'ULTRA';
                            elseif ($valuePct >= 10) $conf = 'HIGH';
                            elseif ($valuePct >= 5) $conf = 'MEDIUM';
                            else $conf = 'LOW';

                            $esitoLabel = match($vb['esito']) {
                                'home' => $vb['casa'],
                                'away' => $vb['trasferta'],
                                'draw' => 'Pareggio',
                                default => $vb['esito'],
                            };
                            ?>
                            <tr>
                                <td>
                                    <?= $vb['sport_icona'] ?>
                                    <strong><?= htmlspecialchars($vb['casa']) ?></strong>
                                    vs
                                    <strong><?= htmlspecialchars($vb['trasferta']) ?></strong>
                                    <br><small class="text-muted"><?= htmlspecialchars($vb['campionato']) ?></small>
                                </td>
                                <td><?= htmlspecialchars($esitoLabel) ?></td>
                                <td><strong><?= $vb['valore_quota'] ?></strong></td>
                                <td class="text-positive fw-bold"><?= $valuePct ?>%</td>
                                <td><span class="badge badge-confidence-<?= $conf ?>"><?= $conf ?></span></td>
                                <td><small><?= htmlspecialchars($vb['bookmaker']) ?></small></td>
                                <td><small><?= date('d/m H:i', strtotime($vb['data_ora'])) ?></small></td>
                                <td>
                                    <a href="index.php?page=match&id=<?= $vb['partita_id'] ?>"
                                       class="btn btn-outline-info btn-sm">
                                        <i class="bi bi-eye"></i>
                                    </a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        <?php endif; ?>
    </div>
</div>

<!-- Dati per i grafici JS -->
<script>
    const bankrollHistory = <?= json_encode($history) ?>;
    const bankrollInit = <?= $kpis['bankroll_init'] ?? 1000 ?>;
</script>

<?php include __DIR__ . '/../templates/footer.php'; ?>