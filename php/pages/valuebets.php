<?php
// php/pages/valuebets.php
$pageTitle   = 'Value Bets';
$pageScripts = ['valuebets.js'];

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/ValueBet.php';
require_once __DIR__ . '/../classes/Bankroll.php';

Auth::requireLogin();

$valueBetM = new ValueBet();
$bankrollM = new Bankroll();
$userId    = Auth::getUserId();

$sport      = $_GET['sport'] ?? null;
$confidence = $_GET['confidence'] ?? null;

$valueBets = $valueBetM->getActive($sport, $confidence);
$sports    = $valueBetM->getSports();

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4><i class="bi bi-fire"></i> Value Bets Attive</h4>
        <span class="badge bg-success fs-6"><?= count($valueBets) ?> trovate</span>
    </div>

    <!-- Filtri -->
    <div class="card bg-dark border-secondary mb-4">
        <div class="card-body">
            <form method="GET" class="row g-2 align-items-end">
                <input type="hidden" name="page" value="valuebets">
                <div class="col-md-3">
                    <label class="form-label small">Sport</label>
                    <select name="sport" class="form-select form-select-sm bg-dark text-light border-secondary">
                        <option value="">Tutti</option>
                        <?php foreach ($sports as $s): ?>
                            <option value="<?= htmlspecialchars($s['nome']) ?>"
                                <?= ($sport === $s['nome']) ? 'selected' : '' ?>>
                                <?= $s['icona'] ?> <?= htmlspecialchars($s['nome']) ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label small">Confidenza</label>
                    <select name="confidence" class="form-select form-select-sm bg-dark text-light border-secondary">
                        <option value="">Tutte</option>
                        <option value="LOW" <?= $confidence === 'LOW' ? 'selected' : '' ?>>🔵 Low</option>
                        <option value="MEDIUM" <?= $confidence === 'MEDIUM' ? 'selected' : '' ?>>🟠 Medium</option>
                        <option value="HIGH" <?= $confidence === 'HIGH' ? 'selected' : '' ?>>🟢 High</option>
                        <option value="ULTRA" <?= $confidence === 'ULTRA' ? 'selected' : '' ?>>🔴 Ultra</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-success btn-sm w-100">
                        <i class="bi bi-funnel"></i> Filtra
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Tabella Value Bets -->
    <?php if (empty($valueBets)): ?>
        <div class="alert alert-secondary">
            <i class="bi bi-info-circle"></i> Nessuna value bet corrisponde ai filtri.
        </div>
    <?php else: ?>
        <div class="table-responsive">
            <table class="table table-dark-custom">
                <thead>
                    <tr>
                        <th>Match</th>
                        <th>Esito</th>
                        <th>Quota</th>
                        <th>Prob. Modello</th>
                        <th>Value</th>
                        <th>Confidenza</th>
                        <th>Kelly</th>
                        <th>Book</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($valueBets as $vb): ?>
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

                        $kelly = $bankrollM->calculateKellyStake($userId, (int)$vb['id']);
                        ?>
                        <tr>
                            <td>
                                <?= $vb['sport_icona'] ?>
                                <strong><?= htmlspecialchars($vb['casa']) ?></strong> vs
                                <strong><?= htmlspecialchars($vb['trasferta']) ?></strong>
                                <br><small class="text-muted">
                                    <?= htmlspecialchars($vb['campionato']) ?> •
                                    <?= date('d/m H:i', strtotime($vb['data_ora'])) ?>
                                </small>
                            </td>
                            <td><strong><?= htmlspecialchars($esitoLabel) ?></strong></td>
                            <td class="fw-bold"><?= $vb['valore_quota'] ?></td>
                            <td><?= $vb['prob_pct'] ?>%</td>
                            <td class="text-positive fw-bold"><?= $valuePct ?>%</td>
                            <td><span class="badge badge-confidence-<?= $conf ?>"><?= $conf ?></span></td>
                            <td>
                                <small>€<?= number_format($kelly['stake'], 2) ?></small>
                                <br><small class="text-muted">(<?= $kelly['kelly_pct'] ?>%)</small>
                            </td>
                            <td><small><?= htmlspecialchars($vb['bookmaker']) ?></small></td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <a href="index.php?page=match&id=<?= $vb['partita_id'] ?>"
                                       class="btn btn-outline-info" title="Dettaglio">
                                        <i class="bi bi-eye"></i>
                                    </a>
                                    <button class="btn btn-outline-success btn-place-bet"
                                            data-vb-id="<?= $vb['id'] ?>"
                                            data-stake="<?= $kelly['stake'] ?>"
                                            data-match="<?= htmlspecialchars($vb['casa'] . ' vs ' . $vb['trasferta']) ?>"
                                            data-esito="<?= htmlspecialchars($esitoLabel) ?>"
                                            data-quota="<?= $vb['valore_quota'] ?>"
                                            title="Piazza scommessa">
                                        <i class="bi bi-cash-coin"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>
</div>

<!-- Modal Piazza Scommessa -->
<div class="modal fade" id="betModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content bg-dark border-secondary">
            <div class="modal-header border-secondary">
                <h5 class="modal-title"><i class="bi bi-cash-coin"></i> Piazza Scommessa</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="betMatchInfo" class="fw-bold"></p>
                <p>Esito: <span id="betEsito" class="text-info"></span>
                   @ <span id="betQuota" class="fw-bold"></span></p>
                <div class="mb-3">
                    <label class="form-label">Importo (€)</label>
                    <input type="number" id="betAmount" class="form-control bg-dark text-light border-secondary"
                           min="1" step="0.50">
                    <small class="text-muted">Kelly suggerisce: €<span id="betKellySuggest"></span></small>
                </div>
            </div>
            <div class="modal-footer border-secondary">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
                <button type="button" class="btn btn-success" id="btnConfirmBet">
                    <i class="bi bi-check-lg"></i> Conferma
                </button>
            </div>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>