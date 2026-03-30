<?php
// php/pages/register.php
$pageTitle = 'Registrazione';

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';

$error   = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $auth   = new Auth();
    $result = $auth->register(
        trim($_POST['username'] ?? ''),
        trim($_POST['email'] ?? ''),
        $_POST['password'] ?? '',
        (float) ($_POST['bankroll'] ?? 1000)
    );

    if ($result['success']) {
        $success = 'Account creato! Ora puoi accedere.';
    } else {
        $error = $result['message'];
    }
}

include __DIR__ . '/../templates/header.php';
?>

<div class="auth-container">
    <div class="auth-card">
        <div class="text-center mb-4">
            <h2><i class="bi bi-graph-up-arrow text-success"></i> OddsLab</h2>
            <p class="text-muted">Crea il tuo account</p>
        </div>

        <?php if ($error !== ''): ?>
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> <?= htmlspecialchars($error) ?>
            </div>
        <?php endif; ?>

        <?php if ($success !== ''): ?>
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i> <?= htmlspecialchars($success) ?>
                <br><a href="index.php?page=login" class="alert-link">Vai al login</a>
            </div>
        <?php endif; ?>

        <form method="POST" action="index.php?page=register">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" required minlength="3"
                       value="<?= htmlspecialchars($_POST['username'] ?? '') ?>">
            </div>
            <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="form-control" required
                       value="<?= htmlspecialchars($_POST['email'] ?? '') ?>">
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required minlength="6">
            </div>
            <div class="mb-3">
                <label class="form-label">Bankroll iniziale (€)</label>
                <input type="number" name="bankroll" class="form-control" required
                       min="10" step="10" value="<?= htmlspecialchars($_POST['bankroll'] ?? '1000') ?>">
            </div>
            <button type="submit" class="btn btn-success w-100">
                <i class="bi bi-person-plus"></i> Registrati
            </button>
        </form>

        <div class="text-center mt-3">
            <a href="index.php?page=login" class="text-info">Hai già un account? Accedi</a>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>