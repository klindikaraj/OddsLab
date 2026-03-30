<?php
// php/index.php
// ============================================
// OddsLab — Router Principale
// ============================================

session_start();

// Autoload classi
require_once __DIR__ . '/classes/Database.php';
require_once __DIR__ . '/classes/Auth.php';

// Gestione logout
if (isset($_GET['action']) && $_GET['action'] === 'logout') {
    $auth = new Auth();
    $auth->logout();
    header('Location: index.php?page=login');
    exit;
}

// Routing
$page = $_GET['page'] ?? '';

// Se non loggato, mostra solo login/register
if (!Auth::isLoggedIn() && !in_array($page, ['login', 'register'], true)) {
    $page = 'login';
}

// Se loggato e nessuna pagina specificata → dashboard
if (Auth::isLoggedIn() && $page === '') {
    $page = 'dashboard';
}

// Mappa pagine consentite
$allowedPages = [
    'login',
    'register',
    'dashboard',
    'valuebets',
    'match',
    'bankroll',
    'tracker',
    'settings',
];

// Mappa pagina → file
$pageMap = [
    'login'     => 'login.php',
    'register'  => 'register.php',
    'dashboard' => 'dashboard.php',
    'valuebets' => 'valuebets.php',
    'match'     => 'match_detail.php',
    'bankroll'  => 'bankroll.php',
    'tracker'   => 'tracker.php',
    'settings'  => 'settings.php',
];

// Carica la pagina
if (in_array($page, $allowedPages, true) && isset($pageMap[$page])) {
    $filePath = __DIR__ . '/pages/' . $pageMap[$page];

    if (file_exists($filePath)) {
        require $filePath;
    } else {
        http_response_code(404);
        echo '<h1>404 — Pagina non trovata</h1>';
        echo '<p>Il file ' . htmlspecialchars($pageMap[$page]) . ' non esiste.</p>';
        echo '<a href="index.php">Torna alla home</a>';
    }
} else {
    // Pagina non valida → redirect
    header('Location: index.php?page=' . (Auth::isLoggedIn() ? 'dashboard' : 'login'));
    exit;
}