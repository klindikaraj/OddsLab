<?php
// php/api/generate_report.php

session_start();
require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/ApiClient.php';
require_once __DIR__ . '/../classes/ValueBet.php';

header('Content-Type: application/json; charset=utf-8');

if (!Auth::isLoggedIn()) {
    echo json_encode(['error' => 'Non autenticato']);
    exit;
}

$partitaId = (int) ($_GET['partita_id'] ?? $_POST['partita_id'] ?? 0);

if ($partitaId <= 0) {
    echo json_encode(['error' => 'ID partita non valido']);
    exit;
}

$api    = new ApiClient();
$output = $api->generateReport($partitaId);

// Rileggi il report dal DB
$valueBet = new ValueBet();
$report   = $valueBet->getMatchReport($partitaId);

echo json_encode([
    'success' => true,
    'report'  => $report['testo'] ?? $output,
    'date'    => $report['generato_il'] ?? date('Y-m-d H:i:s'),
]);