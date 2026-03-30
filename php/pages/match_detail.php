<?php
// php/pages/match_detail.php
$pageTitle = 'Dettaglio Match';

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/ValueBet.php';

Auth::requireLogin();

$partitaId = (int) ($_GET['id'] ?? 0);
if ($partitaId <= 0) {
    header('Location: index.php?page=dashboard');
    exit;
}

$valueBetM  = new ValueBet();
$match      = $valueBetM->getMatchDetail($partitaId);

if ($match === null) {
    header('Location: index.php?page=dashboard');
    exit;
}

$prediction = $valueBetM->getMatchPrediction($partitaId);
$odds       = $valueBetM->getMatchOdds($partitaId);
$matchVBs   = $valueBetM->getMatchValueBets($partitaId);
$report     = $valueBetM->getMatchReport($partitaId);

// Raggruppa quote per esito
$oddsByOutcome = [];
foreach ($odds as $o) {
    $oddsByOutcome[$o['esito']][] = $o;
}

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <a href="javascript:history.back()" class="btn btn-outline-secondary btn-sm mb-3">
        <i class="bi bi-arrow-left"></i> Indietro
    </a>

    <!-- Match Header -->
    <div class="match-card mb-4">
        <small class="text-muted">
            <?= $match['sport_icona'] ?> <?= htmlspecialchars($match['campionato']) ?>
            • <?= date('d/m/Y H:i', strtotime($match['data_ora'])) ?>
        </small>
        <div class="row align-items-center mt-3">
            <div class="col-5 text-end">
                <div class="team-name"><?= htmlspecialchars($match['casa']) ?></div>
                <small class="text-muted">
                    Elo: <?= $match['elo_casa'] ?? 'N/A' ?> |
                    GF: <?= $match['gf_casa'] ?? 'N/A' ?> |
                    GS: <?= $match['gs_casa'] ?? 'N/A' ?>
                </small>
            </div>
            <div class="col-2 text-center">
                <?php if ($match['stato'] === 'conclusa'): ?>
                    <span class="fs-3 fw-bold">
                        <?= $match['score_casa'] ?> - <?= $match['score_trasferta'] ?>
                    </span>
                <?php else: ?>
                    <span class="vs-badge">VS</span>
                <?php endif; ?>
            </div>
            <div class="col-5 text-start">
                <div class="team-name"><?= htmlspecialchars($match['trasferta']) ?></div>
                <small class="text-muted">
                    Elo: <?= $match['elo_trasf'] ?? 'N/A' ?> |
                    GF: <?= $match['gf_trasf'] ?? 'N/A' ?> |
                    GS: <?= $match['gs_trasf'] ?? 'N/A' ?>
                </small>
            </div>
        </div>
        <div class="mt-2">
            <span class="badge bg-<?= $match['stato'] === 'conclusa' ? 'secondary' : 'success' ?>">
                <?= ucfirst($match['stato']) ?>
            </span>
        </div>
    </div>

    <div class="row g-4">
        <!-- Previsioni Modello -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h6><i class="bi bi-cpu"></i> Previsione Modello
                    <?php if ($prediction): ?>
                        <small class="text-muted">(<?= $prediction['tipo_modello'] ?>)</small>
                    <?php endif; ?>
                </h6>
                <?php if ($prediction): ?>
                    <div class="row text-center mt-3">
                        <div class="col-4">
                            <div class="fs-3 fw-bold text-info"><?= $prediction['prob_casa_pct'] ?>%</div>
                            <small><?= htmlspecialchars($match['casa']) ?></small>
                        </div>
                        <div class="col-4">
                            <div class="fs-3 fw-bold text-warning">
                                <?= $prediction['prob_pareg_pct'] ?? 'N/A' ?>%
                            </div>
                            <small>Pareggio</small>
                        </div>
                        <div class="col-4">
                            <div class="fs-3 fw-bold text-danger"><?= $prediction['prob_trasf_pct'] ?>%</div>
                            <small><?= htmlspecialchars($match['trasferta']) ?></small>
                        </div>
                    </div>
                <?php else: ?>
                    <p class="text-muted">Nessuna previsione disponibile</p>
                <?php endif; ?>
            </div>
        </div>

        <!-- Value Bets -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h6><i class="bi bi-fire"></i> Value Bets</h6>
                <?php if (empty($matchVBs)): ?>
                    <p class="text-muted">Nessuna value bet per questo match</p>
                <?php else: ?>
                    <?php foreach ($matchVBs as $vb): ?>
                        <?php
                        $valuePct = (float) $vb['value_pct'];
                        if ($valuePct >= 20) $conf = 'ULTRA';
                        elseif ($valuePct >= 10) $conf = 'HIGH';
                        elseif ($valuePct >= 5) $conf = 'MEDIUM';
                        else $conf = 'LOW';

                        $esitoLabel = match($vb['esito']) {
                            'home' => $match['casa'],
                            'away' => $match['trasferta'],
                            'draw' => 'Pareggio',
                            default => $vb['esito'],
                        };
                        ?>
                        <div class="d-flex justify-content-between align-items-center p-2 mb-2"
                             style="background:#21262d; border-radius:8px;">
                            <div>
                                <strong><?= htmlspecialchars($esitoLabel) ?></strong>
                                @ <?= $vb['valore_quota'] ?>
                                <small class="text-muted">(<?= htmlspecialchars($vb['bookmaker']) ?>)</small>
                            </div>
                            <div>
                                <span class="badge badge-confidence-<?= $conf ?>">
                                    <?= $conf ?> • <?= $valuePct ?>%
                                </span>
                                <span class="badge bg-<?= $vb['stato'] === 'pending' ? 'warning' : ($vb['stato'] === 'won' ? 'success' : 'danger') ?>">
                                    <?= $vb['stato'] ?>
                                </span>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <!-- Quote Bookmaker -->
    <div class="chart-container mt-4">
        <h6><i class="bi bi-list-ol"></i> Quote Bookmaker</h6>
        <?php if (empty($odds)): ?>
            <p class="text-muted">Nessuna quota disponibile</p>
        <?php else: ?>
            <div class="row g-3 mt-2">
                <?php foreach (['home' => $match['casa'], 'draw' => 'Pareggio', 'away' => $match['trasferta']] as $key => $label): ?>
                    <div class="col-md-4">
                        <h6 class="text-center text-muted"><?= htmlspecialchars($label) ?></h6>
                        <?php if (isset($oddsByOutcome[$key])): ?>
                            <?php foreach (array_slice($oddsByOutcome[$key], 0, 5) as $o): ?>
                                <div class="d-flex justify-content-between p-1 small"
                                     style="border-bottom:1px solid #21262d;">
                                    <span><?= htmlspecialchars($o['bookmaker']) ?></span>
                                    <strong><?= $o['valore_quota'] ?></strong>
                                </div>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <small class="text-muted">N/A</small>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>

    <!-- Report IA -->
    <div class="chart-container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6><i class="bi bi-robot"></i> Report IA</h6>
            <button class="btn btn-outline-info btn-sm" id="btnGenReport" data-id="<?= $partitaId ?>">
                <i class="bi bi-magic"></i> Genera Report
            </button>
        </div>

        <div id="reportContainer">
            <?php if ($report !== null): ?>
                <div class="report-ia"><?= nl2br(htmlspecialchars($report['testo'])) ?></div>
                <small class="text-muted mt-2 d-block">
                    Generato il: <?= date('d/m/Y H:i', strtotime($report['generato_il'])) ?>
                </small>
            <?php else: ?>
                <p class="text-muted">Nessun report generato. Clicca "Genera Report" per crearne uno.</p>
            <?php endif; ?>
        </div>
    </div>
</div>

<script>
document.getElementById('btnGenReport')?.addEventListener('click', async function() {
    const btn = this;
    const partitaId = btn.dataset.id;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generando...';

    try {
        const resp = await fetch('api/generate_report.php?partita_id=' + partitaId);
        const data = await resp.json();

        if (data.success && data.report) {
            document.getElementById('reportContainer').innerHTML =
                '<div class="report-ia">' + data.report.replace(/\n/g, '<br>') + '</div>' +
                '<small class="text-muted mt-2 d-block">Generato il: ' + data.date + '</small>';
        } else {
            alert('Errore nella generazione del report');
        }
    } catch (e) {
        alert('Errore di rete: ' + e.message);
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-magic"></i> Genera Report';
});
</script>

<?php include __DIR__ . '/../templates/footer.php'; ?>