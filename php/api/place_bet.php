<?php
// php/api/place_bet.php

session_start();
require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/Bankroll.php';

header('Content-Type: application/json; charset=utf-8');

if (!Auth::isLoggedIn()) {
    echo json_encode(['error' => 'Non autenticato']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['error' => 'Metodo non consentito']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

if ($input === null) {
    // Fallback a POST tradizionale
    $input = $_POST;
}

$valueBetId = (int) ($input['value_bet_id'] ?? 0);
$importo    = (float) ($input['importo'] ?? 0);

if ($valueBetId <= 0 || $importo <= 0) {
    echo json_encode(['error' => 'Parametri non validi']);
    exit;
}

$bankroll = new Bankroll();
$result   = $bankroll->placeBet(Auth::getUserId(), $valueBetId, $importo);

echo json_encode($result);