<?php
// php/api/get_valuebets.php

session_start();
require_once __DIR__ . '/../classes/Database.php';
require_once __DIR__ . '/../classes/Auth.php';
require_once __DIR__ . '/../classes/ValueBet.php';

header('Content-Type: application/json; charset=utf-8');

if (!Auth::isLoggedIn()) {
    echo json_encode(['error' => 'Non autenticato']);
    exit;
}

$valueBet = new ValueBet();

$sport      = $_GET['sport'] ?? null;
$confidence = $_GET['confidence'] ?? null;
$orderBy    = $_GET['order_by'] ?? 'valore_perc';
$order      = $_GET['order'] ?? 'DESC';

$data = $valueBet->getActive($sport, $confidence, $orderBy, $order);

echo json_encode([
    'success' => true,
    'count'   => count($data),
    'data'    => $data,
]);