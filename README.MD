# 🔬 OddsLab — Value Bet Finder Multi-Sport

![PHP](https://img.shields.io/badge/PHP-8.0+-777BB4?logo=php)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)

> **Progetto Capolavoro** — ITI G. Severi, Classe 5ª Informatica  
> Piattaforma UNICA, A.S. 2025/2026

---

## 📖 Descrizione

OddsLab è una piattaforma web che **identifica errori nelle quote dei bookmaker** 
confrontandole con modelli statistici proprietari. Il sistema:

1. **Raccoglie** quote in tempo reale da 20+ bookmaker tramite API
2. **Calcola** la probabilità reale con modelli Poisson (calcio) ed Elo (tennis)
3. **Trova** le Value Bets — scommesse dove il bookmaker paga più del dovuto
4. **Suggerisce** quanto puntare con il **Criterio di Kelly**
5. **Genera** report pre-match narrativi tramite **Intelligenza Artificiale** (OpenAI)

---

## 🏗️ Architettura
```
┌──────────────────┐       ┌──────────────────┐     ┌──────────────────┐
│ The Odds API     │────▶ │ Python Engine    │────▶│ MySQL Database   │
│ (Quote Live)     │       │ - Poisson        │     │ (10 tabelle)     │
│                  │       │ - Elo Rating     │     │                  │
│ OpenAI API       │────▶ │ - Kelly          │     │                  │
│ (Report IA)      │       │ - Value Finder   │     │                  │
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
| **API Esterna** | The Odds API | Quote live multi-bookmaker |

---

## 📁 Struttura Progetto
```
OddsLab/
├── database/ SQL: DDL, seed, viste
├── python/
│ ├── collectors/ Raccolta dati da API
│ ├── models/ Poisson, Elo, Kelly, ValueFinder
│ ├── ai/ Integrazione OpenAI
│ └── main.py Orchestratore pipeline
├── php/
│ ├── classes/ Database, Auth, ValueBet, Bankroll
│ ├── api/ Endpoint REST (JSON)
│ ├── pages/ Pagine web (dashboard, tracker...)
│ ├── templates/ Header, navbar, footer
│ └── assets/ CSS, JS, immagini
├── cron/ Script automazione
└── docs/ Documentazione progetto
```

---

## ⚡ Installazione

### Prerequisiti
- XAMPP (Apache + MySQL + PHP 8.0+)
- Python 3.10+
- pip (gestore pacchetti Python)

### Step 1 — Database
-- Apri phpMyAdmin o terminale MySQL
```
SOURCE database/01_ddl.sql;
SOURCE database/02_seed_data.sql;
SOURCE database/03_views_procedures.sql;
```

### Step 2 — Python
```
cd python
pip install -r requirements.txt
cp .env.example .env
Modifica .env con le tue chiavi API
```
### Step 3 — Primo avvio
```
cd python
python main.py
```

### Step 4 — Interfaccia Web
Apri: http://localhost/OddsLab/php/
Registrati o accedi con: demo / test123

## 🔑 API Keys Necessarie
Servizio	    URL	                        Piano
The Odds API	https://the-odds-api.com	Free (500 req/mese)
OpenAI	        https://platform.openai.com	Pay-per-use (~€0.01/report)

## 📊 Funzionalità Principali
#### 🔍 Value Bet Finder
Confronta la probabilità calcolata dal modello con la probabilità implicita
delle quote. Se (prob_modello × quota) - 1 > 2%, segnala una Value Bet.

#### 🧮 Kelly Criterion
Calcola automaticamente quanto puntare in base al vantaggio trovato:
f* = (p × b - 1) / (b - 1)

Con safety cap al 10% e supporto per Full/Half/Quarter Kelly.

#### 📈 Modello Poisson (Calcio)
Usa la distribuzione di Poisson per calcolare la probabilità di ogni
risultato possibile, basandosi sulle medie gol fatti/subiti delle squadre.

#### 🎾 Modello Elo (Tennis / 1v1)
Sistema di rating che predice la probabilità di vittoria basandosi
sulla differenza di punteggio Elo tra i due giocatori.

#### 🤖 Report IA
OpenAI GPT-4o-mini analizza i dati statistici e genera un report
pre-match di 250 parole che spiega perché una scommessa è una Value Bet.

#### 👤 Autore
Karaj Klindi
Classe 5ª Informatica — ITI F. Severi
Anno Scolastico 2025/2026

#### 📄 Licenza
Progetto realizzato per il "Capolavoro" della piattaforma UNICA.
Tutti i diritti riservati.
