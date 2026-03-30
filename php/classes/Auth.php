<?php
// php/classes/Auth.php

class Auth
{
    private Database $db;

    public function __construct()
    {
        $this->db = Database::getInstance();
    }

    /**
     * Registra un nuovo utente.
     * @return array{success: bool, message: string, user_id?: int}
     */
    public function register(
        string $username,
        string $email,
        string $password,
        float  $bankroll = 1000.00
    ): array {
        // Validazione
        if (strlen($username) < 3) {
            return ['success' => false, 'message' => 'Username minimo 3 caratteri'];
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return ['success' => false, 'message' => 'Email non valida'];
        }
        if (strlen($password) < 6) {
            return ['success' => false, 'message' => 'Password minimo 6 caratteri'];
        }
        if ($bankroll <= 0) {
            return ['success' => false, 'message' => 'Bankroll deve essere positivo'];
        }

        // Controlla duplicati
        $existing = $this->db->fetchOne(
            "SELECT id FROM utenti WHERE username = ? OR email = ?",
            [$username, $email]
        );

        if ($existing !== null) {
            return ['success' => false, 'message' => 'Username o email già in uso'];
        }

        // Hash password e inserisci
        $hash = password_hash($password, PASSWORD_DEFAULT);

        $userId = $this->db->execute(
            "INSERT INTO utenti (username, email, password_hash, bankroll_iniziale, bankroll_attuale)
             VALUES (?, ?, ?, ?, ?)",
            [$username, $email, $hash, $bankroll, $bankroll]
        );

        return [
            'success' => true,
            'message' => 'Registrazione completata',
            'user_id' => $userId,
        ];
    }

    /**
     * Effettua il login.
     * @return array{success: bool, message: string}
     */
    public function login(string $username, string $password): array
    {
        $user = $this->db->fetchOne(
            "SELECT * FROM utenti WHERE username = ?",
            [$username]
        );

        if ($user === null) {
            return ['success' => false, 'message' => 'Credenziali non valide'];
        }

        if (!password_verify($password, $user['password_hash'])) {
            return ['success' => false, 'message' => 'Credenziali non valide'];
        }

        // Crea sessione
        $_SESSION['user_id']   = (int) $user['id'];
        $_SESSION['username']  = $user['username'];
        $_SESSION['logged_in'] = true;

        return ['success' => true, 'message' => 'Login effettuato'];
    }

    /**
     * Effettua il logout.
     */
    public function logout(): void
    {
        session_unset();
        session_destroy();
    }

    /**
     * Verifica se l'utente è loggato.
     */
    public static function isLoggedIn(): bool
    {
        return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
    }

    /**
     * Ritorna l'ID dell'utente loggato.
     */
    public static function getUserId(): int
    {
        return (int) ($_SESSION['user_id'] ?? 0);
    }

    /**
     * Ritorna lo username dell'utente loggato.
     */
    public static function getUsername(): string
    {
        return $_SESSION['username'] ?? '';
    }

    /**
     * Richiede login, altrimenti reindirizza.
     */
    public static function requireLogin(): void
    {
        if (!self::isLoggedIn()) {
            header('Location: index.php?page=login');
            exit;
        }
    }

    /**
     * Recupera i dati completi dell'utente.
     */
    public function getUserData(int $userId): ?array
    {
        return $this->db->fetchOne(
            "SELECT id, username, email, bankroll_iniziale,
                    bankroll_attuale, kelly_fraction, created_at
             FROM utenti WHERE id = ?",
            [$userId]
        );
    }
}