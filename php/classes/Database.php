<?php
// php/classes/Database.php

class Database
{
    private static ?Database $instance = null;
    private PDO $pdo;

    private function __construct()
    {
        $config = require __DIR__ . '/../config/database.php';

        $dsn = sprintf(
            'mysql:host=%s;dbname=%s;charset=%s',
            $config['host'],
            $config['dbname'],
            $config['charset']
        );

        $this->pdo = new PDO($dsn, $config['user'], $config['password'], [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
    }

    public static function getInstance(): Database
    {
        if (self::$instance === null) {
            self::$instance = new Database();
        }
        return self::$instance;
    }

    public function getConnection(): PDO
    {
        return $this->pdo;
    }

    /**
     * Esegue una SELECT e ritorna tutte le righe.
     * @param string $query
     * @param array<int|string, mixed> $params
     * @return array<int, array<string, mixed>>
     */
    public function fetchAll(string $query, array $params = []): array
    {
        $stmt = $this->pdo->prepare($query);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }

    /**
     * Esegue una SELECT e ritorna una sola riga.
     * @param string $query
     * @param array<int|string, mixed> $params
     * @return array<string, mixed>|null
     */
    public function fetchOne(string $query, array $params = []): ?array
    {
        $stmt = $this->pdo->prepare($query);
        $stmt->execute($params);
        $row = $stmt->fetch();
        return $row !== false ? $row : null;
    }

    /**
     * Esegue INSERT/UPDATE/DELETE.
     * @param string $query
     * @param array<int|string, mixed> $params
     * @return int lastInsertId per INSERT, rowCount per UPDATE/DELETE
     */
    public function execute(string $query, array $params = []): int
    {
        $stmt = $this->pdo->prepare($query);
        $stmt->execute($params);

        if (stripos(trim($query), 'INSERT') === 0) {
            return (int) $this->pdo->lastInsertId();
        }
        return $stmt->rowCount();
    }

    /**
     * Esegue SELECT COUNT(*) AS n e ritorna il numero.
     */
    public function count(string $query, array $params = []): int
    {
        $row = $this->fetchOne($query, $params);
        if ($row !== null && isset($row['n'])) {
            return (int) $row['n'];
        }
        return 0;
    }

    // Impedisce clonazione e deserializzazione
    private function __clone() {}
    public function __wakeup()
    {
        throw new \Exception("Cannot unserialize singleton");
    }
}