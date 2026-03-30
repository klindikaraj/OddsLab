<?php
// php/pages/settings.php
$pageTitle = 'Impostazioni';

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Bankroll.php';

Auth::requireLogin();

$auth      = new Auth();
$bankrollM = new Bankroll();
$userId    = Auth::getUserId();
$user      = $auth->getUserData($userId);

$message = '';
$error   = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'update_kelly') {
        $kelly = (float) ($_POST['kelly_fraction'] ?? 0.5);
        $result = $bankrollM->updateSettings($userId, $kelly);

        if ($result['success']) {
            $message = $result['message'];
            $user = $auth->getUserData($userId); // Ricarica
        } else {
            $error = $result['message'];
        }
    }

    if ($action === 'update_password') {
        $oldPw  = $_POST['old_password'] ?? '';
        $newPw  = $_POST['new_password'] ?? '';
        $confPw = $_POST['confirm_password'] ?? '';

        if ($newPw !== $confPw) {
            $error = 'Le password non corrispondono';
        } elseif (strlen($newPw) < 6) {
            $error = 'Password minimo 6 caratteri';
        } else {
            // Verifica vecchia password
            $fullUser = Database::getInstance()->fetchOne(
                "SELECT password_hash FROM utenti WHERE id = ?",
                [$userId]
            );

            if ($fullUser !== null && password_verify($oldPw, $fullUser['password_hash'])) {
                $newHash = password_hash($newPw, PASSWORD_DEFAULT);
                Database::getInstance()->execute(
                    "UPDATE utenti SET password_hash = ? WHERE id = ?",
                    [$newHash, $userId]
                );
                $message = 'Password aggiornata';
            } else {
                $error = 'Password attuale non corretta';
            }
        }
    }
}

include __DIR__ . '/../templates/header.php';
include __DIR__ . '/../templates/navbar.php';
?>

<div class="page-container">
    <h4 class="mb-4"><i class="bi bi-gear"></i> Impostazioni</h4>

    <?php if ($message !== ''): ?>
        <div class="alert alert-success"><i class="bi bi-check-circle"></i> <?= htmlspecialchars($message) ?></div>
    <?php endif; ?>
    <?php if ($error !== ''): ?>
        <div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> <?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <div class="row g-4">
        <!-- Info Account -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h6><i class="bi bi-person"></i> Account</h6>
                <table class="table table-borderless text-light mt-3">
                    <tr>
                        <td class="text-muted">Username</td>
                        <td><?= htmlspecialchars($user['username'] ?? '') ?></td>
                    </tr>
                    <tr>
                        <td class="text-muted">Email</td>
                        <td><?= htmlspecialchars($user['email'] ?? '') ?></td>
                    </tr>
                    <tr>
                        <td class="text-muted">Registrato il</td>
                        <td><?= isset($user['created_at']) ? date('d/m/Y', strtotime($user['created_at'])) : 'N/A' ?></td>
                    </tr>
                    <tr>
                        <td class="text-muted">Bankroll iniziale</td>
                        <td>€<?= number_format((float)($user['bankroll_iniziale'] ?? 0), 2) ?></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Kelly Fraction -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h6><i class="bi bi-sliders"></i> Kelly Criterion</h6>
                <form method="POST" class="mt-3">
                    <input type="hidden" name="action" value="update_kelly">
                    <div class="mb-3">
                        <label class="form-label">Frazione Kelly</label>
                        <select name="kelly_fraction" class="form-select bg-dark text-light border-secondary">
                            <option value="0.25" <?= (float)($user['kelly_fraction'] ?? 0) === 0.25 ? 'selected' : '' ?>>
                                Quarter Kelly (25%) — Ultra conservativo
                            </option>
                            <option value="0.50" <?= (float)($user['kelly_fraction'] ?? 0) === 0.50 ? 'selected' : '' ?>>
                                Half Kelly (50%) — Consigliato
                            </option>
                            <option value="0.75" <?= (float)($user['kelly_fraction'] ?? 0) === 0.75 ? 'selected' : '' ?>>
                                Three-Quarter Kelly (75%) — Aggressivo
                            </option>
                            <option value="1.00" <?= (float)($user['kelly_fraction'] ?? 0) === 1.00 ? 'selected' : '' ?>>
                                Full Kelly (100%) — Massimo rischio
                            </option>
                        </select>
                        <small class="text-muted">
                            Più bassa la frazione, più conservative sono le puntate.
                            Half Kelly è il compromesso migliore.
                        </small>
                    </div>
                    <button type="submit" class="btn btn-success">
                        <i class="bi bi-check-lg"></i> Salva
                    </button>
                </form>
            </div>
        </div>

        <!-- Cambio Password -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h6><i class="bi bi-lock"></i> Cambia Password</h6>
                <form method="POST" class="mt-3">
                    <input type="hidden" name="action" value="update_password">
                    <div class="mb-3">
                        <label class="form-label">Password attuale</label>
                        <input type="password" name="old_password" class="form-control bg-dark text-light border-secondary" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Nuova password</label>
                        <input type="password" name="new_password" class="form-control bg-dark text-light border-secondary" required minlength="6">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Conferma nuova password</label>
                        <input type="password" name="confirm_password" class="form-control bg-dark text-light border-secondary" required minlength="6">
                    </div>
                    <button type="submit" class="btn btn-warning">
                        <i class="bi bi-key"></i> Cambia Password
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>