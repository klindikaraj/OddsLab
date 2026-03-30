<?php
// php/pages/login.php
$pageTitle = 'Login';

require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $auth   = new Auth();
    $result = $auth->login(
        trim($_POST['username'] ?? ''),
        $_POST['password'] ?? ''
    );

    if ($result['success']) {
        header('Location: index.php?page=dashboard');
        exit;
    }
    $error = $result['message'];
}

include __DIR__ . '/../templates/header.php';
?>

<div class="auth-container">
    <div class="auth-card">
        <div class="text-center mb-4">
            <h2><i class="bi bi-graph-up-arrow text-success"></i> OddsLab</h2>
            <p class="text-muted">Accedi al tuo account</p>
        </div>

        <?php if ($error !== ''): ?>
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> <?= htmlspecialchars($error) ?>
            </div>
        <?php endif; ?>

        <form method="POST" action="index.php?page=login">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" required
                       value="<?= htmlspecialchars($_POST['username'] ?? '') ?>">
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-success w-100">
                <i class="bi bi-box-arrow-in-right"></i> Accedi
            </button>
        </form>

        <div class="text-center mt-3">
            <a href="index.php?page=register" class="text-info">Non hai un account? Registrati</a>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../templates/footer.php'; ?>