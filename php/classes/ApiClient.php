<?php
// php/classes/ApiClient.php

class ApiClient
{
    private string $pythonCmd;
    private string $pythonDir;

    public function __construct()
    {
        $config = require __DIR__ . '/../config/app.php';
        $this->pythonCmd = $config['python'];
        $this->pythonDir = $config['python_dir'];
    }

    /**
     * Esegue lo script Python principale.
     */
    public function runPipeline(string $step = ''): string
    {
        $flag = $step !== '' ? " --{$step}" : '';
        $cmd  = sprintf(
            'cd %s && %s main.py%s 2>&1',
            escapeshellarg($this->pythonDir),
            escapeshellcmd($this->pythonCmd),
            $flag
        );

        $output = shell_exec($cmd);
        return $output ?? 'Nessun output';
    }

    /**
     * Genera un report IA per una partita specifica.
     */
    public function generateReport(int $partitaId): string
    {
        $cmd = sprintf(
            'cd %s && %s -c "from ai.report_generator import ReportGenerator; r=ReportGenerator(); print(r.generate(%d))" 2>&1',
            escapeshellarg($this->pythonDir),
            escapeshellcmd($this->pythonCmd),
            $partitaId
        );

        $output = shell_exec($cmd);
        return $output ?? 'Errore nella generazione del report';
    }
}