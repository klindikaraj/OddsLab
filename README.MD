# 🔬 OddsLab — Value Bet Finder Multi-Sport

![PHP](https://img.shields.io/badge/PHP-8.0+-777BB4?logo=php)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)

> **Progetto Capolavoro** — ITI F. Severi, Classe 5ª Informatica  
> Piattaforma UNICA, A.S. 2025/2026

---

## 📖 Descrizione

OddsLab è una piattaforma web che **identifica errori nelle quote dei bookmaker**
confrontandole con modelli statistici proprietari. Il sistema:

1. **Raccoglie** quote in tempo reale da 20+ bookmaker tramite The Odds API
2. **Calcola** la probabilità reale con modelli Poisson (calcio) ed Elo (basket)
3. **Trova** le Value Bets — scommesse dove il bookmaker paga più del dovuto
4. **Suggerisce** quanto puntare con il **Criterio di Kelly**
5. **Genera** report pre-match narrativi tramite **Intelligenza Artificiale** (OpenAI)
6. **Aggiorna** i risultati tramite football-data.org (calcio) e balldontlie.io (NBA)

---

## 🏗️ Architettura

```
┌──────────────────┐       ┌──────────────────┐     ┌──────────────────┐
│ The Odds API     │────▶  │ Python Engine    │────▶│ MySQL Database   │
│ (Quote Live)     │       │ - Poisson        │     │ (10 tabelle)     │
│ OpenAI API       │────▶  │ - Elo Rating     │     │                  │
│ (Report IA)      │       │ - Kelly          │     │                  │
│ football-data.org│────▶  │ - Value Finder   │     │                  │
│ balldontlie.io   │       │ - Results        │     │                  │
└──────────────────┘       └──────────────────┘     └────────┬─────────┘
                                                             │
                                                    ┌────────▼─────────┐
                                                    │ PHP Frontend     │
                                                    │ - Dashboard      │
                                                    │ - Value Bets     │
                                                    │ - Bet Tracker    │
                                                    │ - Bankroll Mgmt  │
                                                    └──────────────────┘
```

---

## 🛠️ Stack Tecnologico

| Componente | Tecnologia | Ruolo |
|---|---|---|
| **Database** | MySQL 8.0 | Storage dati, query aggregate, viste |
| **Backend Web** | PHP 8.0+ | Interfaccia utente, autenticazione, API REST |
| **Data Engine** | Python 3.10+ | Raccolta dati, modelli predittivi, IA |
| **Frontend** | Bootstrap 5 + Chart.js | UI responsive, grafici interattivi |
| **IA** | OpenAI GPT-4o-mini | Report pre-match narrativi |
| **Quote** | The Odds API | Quote live multi-bookmaker |
| **Risultati calcio** | football-data.org | Serie A, Premier League, La Liga |
| **Risultati NBA** | balldontlie.io | Risultati e statistiche NBA |

---

## 📁 Struttura Progetto

```
OddsLab/
├── database/           SQL: DDL, seed, viste
├── python/
│   ├── collectors/     Raccolta quote (The Odds API) e risultati
│   ├── models/         Poisson, Elo, Kelly, ValueFinder
│   ├── ai/             Integrazione OpenAI
│   ├── main.py         Orchestratore pipeline
│   ├── settle_bets.py  Liquidazione scommesse e bankroll
│   └── requirements.txt
├── php/
│   ├── classes/        Database, Auth, ValueBet, Bankroll
│   ├── api/            Endpoint REST (JSON)
│   ├── pages/          Pagine web (dashboard, tracker...)
│   ├── templates/      Header, navbar, footer
│   └── assets/         CSS, JS
├── cron/               Script di automazione (bash)
└── docs/               Documentazione tecnica
```

---

## ⚡ Installazione

### Prerequisiti
- XAMPP (Apache + MySQL + PHP 8.0+)
- Python 3.10+
- pip

### Step 1 — Database

Apri phpMyAdmin o un terminale MySQL e lancia in ordine:

```sql
SOURCE database/01_ddl.sql;
SOURCE database/02_seed_data.sql;
SOURCE database/03_views_procedures.sql;
```

### Step 2 — Configurazione Python

```bash
cd python
pip install -r requirements.txt
cp .env.example .env
# Modifica .env con le tue chiavi API
```

### Step 3 — Primo avvio

```bash
cd python
python main.py
```

### Step 4 — Interfaccia Web

Apri: `http://localhost/OddsLab/php/`

Accedi con: `demo` / `test123`

---

## 🔑 API Keys Necessarie

| Servizio | URL | Piano | Uso |
|---|---|---|---|
| **The Odds API** | https://the-odds-api.com | Free (500 req/mese) | Quote live |
| **OpenAI** | https://platform.openai.com | Pay-per-use (~€0.01/report) | Report IA |
| **football-data.org** | https://www.football-data.org | Free forever | Risultati calcio |
| **balldontlie.io** | https://www.balldontlie.io | Free | Risultati NBA |

---

## 📊 Funzionalità Principali

### 🔍 Value Bet Finder
Confronta la probabilità calcolata dal modello con la probabilità implicita
delle quote. Se `(prob_modello × quota) - 1 > 2%`, segnala una Value Bet.

### 🧮 Kelly Criterion
Calcola automaticamente quanto puntare in base al vantaggio trovato:

```
f* = (p × b - 1) / (b - 1)
```

Con safety cap al 10% e supporto per Full / Half / Quarter Kelly.

### 📈 Modello Poisson (Calcio)
Usa la distribuzione di Poisson per calcolare la probabilità di ogni
risultato possibile, basandosi sulle medie gol fatti/subiti delle squadre.

### 🏀 Modello Elo (Basket)
Sistema di rating che predice la probabilità di vittoria basandosi
sulla differenza di punteggio Elo tra le due squadre.

### 🤖 Report IA
OpenAI GPT-4o-mini analizza i dati statistici e genera un report
pre-match di ~250 parole che spiega perché una scommessa è una Value Bet.

### ⚙️ Automazione (cron)
La cartella `cron/` contiene script bash pronti per crontab:
- `fetch_odds.sh` — raccolta quote ogni 6 ore
- `run_models.sh` — previsioni + ricerca value bets
- `update_results.sh` — aggiornamento risultati e bankroll

---

## 👤 Autore

**Karaj Klindi**  
Classe 5ª Informatica — ITI F. Severi  
Anno Scolastico 2025/2026

---

## 📄 Licenza

Progetto realizzato per il "Capolavoro" della piattaforma UNICA.  
Tutti i diritti riservati.
