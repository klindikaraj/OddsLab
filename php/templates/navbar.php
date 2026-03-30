<?php
// php/templates/navbar.php
require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';

$currentPage = $_GET['page'] ?? 'dashboard';
?>

<nav class="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-secondary fixed-top">
    <div class="container-fluid">
        <a class="navbar-brand fw-bold" href="index.php?page=dashboard">
            <i class="bi bi-graph-up-arrow text-success"></i> OddsLab
        </a>

        <button class="navbar-toggler" type="button"
                data-bs-toggle="collapse" data-bs-target="#navMain">
            <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navMain">
            <?php if (Auth::isLoggedIn()): ?>
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link <?= $currentPage === 'dashboard' ? 'active' : '' ?>"
                       href="index.php?page=dashboard">
                        <i class="bi bi-speedometer2"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= $currentPage === 'valuebets' ? 'active' : '' ?>"
                       href="index.php?page=valuebets">
                        <i class="bi bi-fire"></i> Value Bets
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= $currentPage === 'tracker' ? 'active' : '' ?>"
                       href="index.php?page=tracker">
                        <i class="bi bi-list-check"></i> Tracker
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link <?= $currentPage === 'bankroll' ? 'active' : '' ?>"
                       href="index.php?page=bankroll">
                        <i class="bi bi-wallet2"></i> Bankroll
                    </a>
                </li>
            </ul>

            <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link <?= $currentPage === 'settings' ? 'active' : '' ?>"
                       href="index.php?page=settings">
                        <i class="bi bi-gear"></i> Impostazioni
                    </a>
                </li>
                <li class="nav-item">
                    <span class="nav-link text-info">
                        <i class="bi bi-person-circle"></i>
                        <?= htmlspecialchars(Auth::getUsername()) ?>
                    </span>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-danger" href="index.php?action=logout">
                        <i class="bi bi-box-arrow-right"></i> Esci
                    </a>
                </li>
            </ul>
            <?php endif; ?>
        </div>
    </div>
</nav>