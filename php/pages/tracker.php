<?php
// php/pages/tracker.php
$pageTitle = 'Bet Tracker';

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Bankroll.php';

Auth::requireLogin();

$bankrollM = new Bankroll();
$userId    = Auth::getUserId();
$filter    = $_GET['stato'] ?? 'all';
$bets      = $bankrollM->getBetHistory($userId, $filter !== 'all' ? $filter : null);

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <h4 class="mb-4"><i class="bi bi-list-check"></i> Bet Tracker</h4>

    <!-- Filtri -->
    <div class="mb-4">
        <div class="btn-group">
            <?php foreach (['all' => 'Tutte', 'pending' => '⏳ Pending', 'won' => '✅ Vinte', 'lost' => '❌ Perse'] as $k => $v): ?>
                <a href="index.php?page=tracker&stato=<?= $k ?>"
                   class="btn btn-sm <?= $filter === $k ? 'btn-success' : 'btn-outline-secondary' ?>">
                    <?= $v ?>
                </a>
            <?php endforeach; ?>
        </div>
        <span class="badge bg-secondary ms-2"><?= count($bets) ?> scommesse</span>
    </div>

    <!-- Tabella Scommesse -->
    <?php if (empty($bets)): ?>
        <div class="alert alert-secondary">
            <i class="bi bi-info-circle"></i> Nessuna scommessa trovata.
        </div>
    <?php else: ?>
        <div class="table-responsive">
            <table class="table table-dark-custom">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Match</th>
                        <th>Esito</th>
                        <th>Quota</th>
                        <th>Puntato</th>
                        <th>Profitto</th>
                        <th>Stato</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($bets as $bet): ?>
                        <?php
                        $esitoLabel = match($bet['esito']) {
                            'home' => $bet['casa'],
                            'away' => $bet['trasferta'],
                            'draw' => 'Pareggio',
                            default => $bet['esito'],
                        };

                        $profitto = $bet['profitto_reale'];
                        ?>
                        <tr>
                            <td><small><?= date('d/m/Y H:i', strtotime($bet['data'])) ?></small></td>
                            <td>
                                <?= $bet['sport_icona'] ?>
                                <a href="index.php?page=match&id=<?= $bet['partita_id'] ?>" class="text-info text-decoration-none">
                                    <?= htmlspecialchars($bet['casa']) ?> vs <?= htmlspecialchars($bet['trasferta']) ?>
                                </a>
                            </td>
                            <td><?= htmlspecialchars($esitoLabel) ?></td>
                            <td><?= $bet['valore_quota'] ?></td>
                            <td>€<?= number_format((float)$bet['importo_puntato'], 2) ?></td>
                            <td class="<?= $profitto !== null ? ($profitto >= 0 ? 'text-positive' : 'text-negative') : '' ?>">
                                <?php if ($profitto !== null): ?>
                                    <?= ($profitto >= 0 ? '+' : '') ?>€<?= number_format((float)$profitto, 2) ?>
                                <?php else: ?>
                                    <span class="text-muted">—</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <span class="badge badge-<?= $bet['risultato'] ?>">
                                    <?= ucfirst($bet['risultato']) ?>
                                </span>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
                <tfoot>
                    <tr class="border-top border-secondary">
                        <td colspan="4" class="text-end fw-bold">Totale:</td>
                        <td class="fw-bold">
                            €<?= number_format(array_sum(array_column($bets, 'importo_puntato')), 2) ?>
                        </td>
                        <td class="fw-bold <?= array_sum(array_map(fn($b) => (float)($b['profitto_reale'] ?? 0), $bets)) >= 0 ? 'text-positive' : 'text-negative' ?>">
                            <?php
                            $totalProfit = array_sum(array_map(fn($b) => (float)($b['profitto_reale'] ?? 0), $bets));
                            echo ($totalProfit >= 0 ? '+' : '') . '€' . number_format($totalProfit, 2);
                            ?>
                        </td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
        </div>
    <?php endif; ?>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>