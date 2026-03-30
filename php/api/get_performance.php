<?php
// php/api/get_performance.php

session_start();
require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Dashboard.php';
require_once __DIR__ . '/../classes/Bankroll.php';

header('Content-Type: application/json; charset=utf-8');

if (!Auth::isLoggedIn()) {
    echo json_encode(['error' => 'Non autenticato']);
    exit;
}

$userId = Auth::getUserId();
$days   = (int) ($_GET['days'] ?? 30);

$dashboard = new Dashboard();
$bankroll  = new Bankroll();

$kpis    = $dashboard->getKPIs($userId);
$history = $bankroll->getHistory($userId, $days);
$bySport = $dashboard->getValueBetsBySport();

echo json_encode([
    'success' => true,
    'kpis'    => $kpis,
    'history' => $history,
    'by_sport' => $bySport,
]);