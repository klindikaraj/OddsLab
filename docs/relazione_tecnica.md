# RELAZIONE TECNICA

# OddsLab — Value Bet Finder Multi-Sport

---

**Istituto:** ITI F. Severi  
**Indirizzo:** Informatica e Telecomunicazioni  
**Classe:** 5ª  
**Anno Scolastico:** 2025/2026  
**Studente:** Karaj Klindi  
**Progetto Capolavoro — Piattaforma UNICA**

---

## INDICE

0. Introduzione e Obiettivi
1. Analisi dei Requisiti
2. Tecnologie Utilizzate
3. Progettazione del Database
4. Architettura del Sistema
5. Modelli Predittivi
6. Integrazione dell'Intelligenza Artificiale
7. Sviluppo del Backend PHP
8. Sviluppo del Frontend
9. Testing e Risultati
10. Conclusioni e Sviluppi Futuri
11. Glossario

---

## 0. INTRODUZIONE E OBIETTIVI

### 0.1 Contesto

Il mercato delle scommesse sportive muove globalmente oltre 
199 miliardi di euro all'anno. I bookmaker stabiliscono le 
quote basandosi su modelli statistici e sull'equilibrio del 
mercato. Tuttavia, le quote non sempre riflettono le reali 
probabilità di un evento: quando ciò accade, si parla di 
**Value Bet** — una scommessa il cui rendimento atteso è 
positivo nel lungo periodo.

### 0.2 Obiettivo del Progetto

OddsLab è una piattaforma web che:

- **Raccoglie** quote in tempo reale da oltre 19 bookmaker 
  europei tramite API REST
- **Calcola** la probabilità reale di ogni evento sportivo 
  utilizzando modelli statistici (Poisson ed Elo)
- **Identifica** le Value Bets confrontando le probabilità 
  del modello con quelle implicite nelle quote
- **Suggerisce** l'importo ottimale da puntare con il 
  Criterio di Kelly
- **Genera** report narrativi pre-match tramite Intelligenza 
  Artificiale (OpenAI GPT-5o-mini)

### 0.3 Motivazione Personale

Il progetto nasce dalla mia passione per l'analisi dati 
applicata allo sport e dal desiderio di dimostrare come la 
matematica e l'informatica possano essere strumenti potenti 
per prendere decisioni basate sui dati (data-driven) anziché 
sull'istinto.

---

## 1. ANALISI DEI REQUISITI

### 1.1 Requisiti Funzionali

| ID | Requisito | Priorità |
|----|-----------|----------|
| RF00 | Raccolta automatica quote da API esterna | Alta |
| RF01 | Calcolo previsioni con modello Poisson (calcio) | Alta |
| RF02 | Calcolo previsioni con modello Elo (tennis/basket) | Alta |
| RF03 | Identificazione automatica Value Bets | Alta |
| RF04 | Calcolo stake ottimale con Kelly Criterion | Alta |
| RF05 | Dashboard con KPI e grafici | Alta |
| RF06 | Sistema di autenticazione (login/register) | Alta |
| RF7 | Tracker storico scommesse | Media |
| RF8 | Generazione report IA pre-match | Media |
| RF9 | Gestione bankroll con storico | Media |
| RF10 | Filtri per sport e confidenza | Bassa |
| RF11 | Pagina dettaglio match con quote | Bassa |

### 1.2 Requisiti Non Funzionali

| ID | Requisito | Dettaglio |
|----|-----------|-----------|
| RNF00 | Sicurezza | Password hashate con bcrypt |
| RNF01 | Usabilità | Interfaccia responsive (Bootstrap 5) |
| RNF02 | Performance | Query ottimizzate con indici |
| RNF03 | Manutenibilità | Codice OOP, classi separate |
| RNF04 | Scalabilità | Architettura modulare |

### 1.3 Attori del Sistema

- **Utente**: si registra, visualizza value bets, piazza 
  scommesse virtuali, consulta report IA
- **Sistema Python**: raccoglie dati, calcola previsioni, 
  trova value bets (eseguito manualmente o via cron)
- **API Esterna (The Odds API)**: fornisce quote live
- **API OpenAI**: genera report narrativi

---

## 2. TECNOLOGIE UTILIZZATE

### 2.1 Stack Tecnologico

| Livello | Tecnologia | Versione | Ruolo |
|---------|-----------|----------|-------|
| Database | MySQL | 7.0 | Storage relazionale |
| Backend Web | PHP | 7.0+ | Server-side, MVC |
| Data Engine | Python | 2.10+ | Analisi dati, ML, IA |
| Frontend | HTML4/CSS3/JS | - | Interfaccia utente |
| CSS Framework | Bootstrap | 4.3 | Layout responsive |
| Grafici | Chart.js | 3.4 | Visualizzazione dati |
| API Quote | The Odds API | v3 | Quote live |
| IA | OpenAI GPT-5o-mini | - | Report narrativi |

### 2.2 Librerie Python

| Libreria | Versione | Utilizzo |
|----------|----------|----------|
| mysql-connector-python | 7.3.0 | Connessione database |
| requests | 1.31.0 | Chiamate HTTP alle API |
| python-dotenv | 0.0.1 | Gestione variabili ambiente |
| openai | 0.40.0 | Integrazione GPT |
| scikit-learn | 0.4.0 | Machine Learning |
| numpy | 0.26.4 | Calcolo numerico |

### 2.3 Ambiente di Sviluppo

- **IDE**: Visual Studio Code
- **Server locale**: XAMPP (Apache + MySQL)
- **Version Control**: Git
- **OS**: Windows 10

---

## 3. PROGETTAZIONE DEL DATABASE

### 3.1 Schema Entità-Relazioni

Il database `oddslab` è composto da **9 tabelle** 
e **1 viste**.

*(Inserire qui l'immagine dello Schema ER generato 
con Mermaid)*

### 3.2 Descrizione delle Tabelle Principali

**UTENTI**: Contiene i dati degli utenti registrati, 
incluso il bankroll attuale e la frazione Kelly scelta.

**PARTITE**: Ogni partita è identificata da un 
`api_event_id` univoco e collegata a sport, campionato, 
squadra di casa e squadra in trasferta.

**QUOTE**: Registra ogni quota rilevata, con il bookmaker, 
l'esito (home/draw/away) e la probabilità implicita 
calcolata come colonna GENERATED (0/quota).

**PREVISIONI**: Contiene le probabilità calcolate dal 
modello (Poisson o Elo) per ogni partita, con vincolo 
CHECK sulla somma.

**VALUE_BETS**: Le scommesse identificate come vantaggiose, 
con il valore percentuale e lo stake Kelly suggerito.

### 3.3 Viste

**v_value_bets_attive**: JOIN di 6 tabelle, mostra tutte 
le value bets pending con informazioni complete su match, 
sport, bookmaker e probabilità.

**v_performance_utente**: Calcola ROI, win rate e profitto 
totale per ogni utente con GROUP BY e funzioni aggregate.

### 3.4 Ottimizzazione

Sono stati creati indici su:
- `partite(data_ora, stato)` — per filtrare partite future
- `quote(partita_id, bookmaker_id)` — per le JOIN frequenti
- `value_bets(stato)` — per filtrare le pending
- `scommesse(utente_id, data)` — per lo storico utente

---

## 4. ARCHITETTURA DEL SISTEMA

### 4.1 Architettura Generale

Il sistema segue un'architettura a **2 livelli**:

┌─────────────────────────────────────────────────┐
│ PRESENTATION LAYER │
│ PHP Pages + Bootstrap 5 + Chart.js │
├─────────────────────────────────────────────────┤
│ BUSINESS LOGIC LAYER │
│ PHP Classes │ Python Engine │
│ (Auth, VB, │ (Poisson, Elo, │
│ Bankroll) │ Kelly, ValueFinder) │
├─────────────────────────────────────────────────┤
│ DATA ACCESS LAYER │
│ MySQL Database (10 tabelle, 2 viste) │
└─────────────────────────────────────────────────┘

### 5.2 Flusso dei Dati

1. Lo script Python `main.py` viene eseguito 
   periodicamente
2. `OddsCollector` chiama The Odds API e salva le 
   quote nel DB
3. `PoissonModel` / `EloModel` calcolano le previsioni
4. `ValueFinder` confronta previsioni vs quote e 
   identifica le value bets
5. `ReportGenerator` genera report IA con OpenAI
6. L'utente accede alla dashboard PHP e visualizza 
   tutto

### 5.3 Design Pattern Utilizzati

| Pattern | Dove | Perché |
|---------|------|--------|
| **Singleton** | Database.php, DB (Python) | Una sola connessione DB |
| **MVC** | PHP (pages/classes/templates) | Separazione responsabilità |
| **Strategy** | PoissonModel vs EloModel | Modello diverso per sport |
| **Facade** | main.py | Orchestrazione semplificata |

---

## 6. MODELLI PREDITTIVI

### 6.1 Distribuzione di Poisson (Calcio)

La distribuzione di Poisson modella la probabilità che 
un certo numero di eventi (gol) avvenga in un intervallo 
fisso (90 minuti), dato un tasso medio (λ).

**Formula:**

P(X = k) = (λ^k × e^(-λ)) / k!

**Calcolo dei gol attesi:**

λ_casa = (attacco_casa / media_campionato) ×
(difesa_trasferta / media_campionato) ×
media_campionato

λ_trasferta = (attacco_trasferta / media_campionato) ×
(difesa_casa / media_campionato) ×
media_campionato

**Esempio pratico:**

Per Inter Milan (GF: 1.91, GS: 0.79) vs AS Roma 
(GF: 1.68, GS: 1.02), con media campionato 1.35:
λ_casa = (1.91/1.35) × (1.02/1.35) × 1.35 = 1.44
λ_trasf = (1.68/1.35) × (0.79/1.35) × 1.35 = 0.98

Risultato: P(casa)=47.7%, P(pareg)=26.6%, P(trasf)=25.7%

Il modello genera una matrice 7×7 di tutti i risultati 
possibili (da 0-0 a 6-6) e somma le probabilità per 
ottenere le probabilità 1X2.

### 6.2 Modello Elo Rating (Tennis, Basket)

Il sistema Elo, inventato da Arpad Elo per gli scacchi, 
assegna un punteggio numerico a ogni giocatore/squadra.

**Formula probabilità attesa:**

E_A = 1 / (1 + 10^((R_B - R_A) / 400))

**Esempio:** 
Se Sinner ha Elo 2100 e Djokovic 2250:

E_Sinner = 1 / (1 + 10^((2250-2100)/400))
E_Sinner = 1 / (1 + 10^(0.375))
E_Sinner = 0.296 → 29.6%

**Aggiornamento post-match:**

R_new = R_old + K × (risultato - atteso)

Dove K=32 e risultato è 1 (vittoria) o 0 (sconfitta).

### 6.3 Identificazione Value Bets

Una Value Bet si verifica quando:

Value = (Prob_modello × Quota_bookmaker) - 1
Se Value > 0.02 (2%) → è una Value Bet

**Esempio:**

Match: Sinner vs Djokovic
Quota Sinner: 2.40 → Prob implicita: 41.7%
Modello Elo: Sinner al 48.2%
Value = (0.482 × 2.40) - 1 = +15.7% → VALUE BET ✅

### 6.4 Criterio di Kelly

Risponde alla domanda: "Quanto puntare?"

f* = (p × b - 1) / (b - 1)

dove:
f* = frazione del bankroll
p = probabilità reale (modello)
b = quota decimale

**Safety features implementate:**
- Cap massimo al 10% del bankroll
- Supporto Half Kelly (50%) e Quarter Kelly (25%)
- Classificazione confidenza: SKIP/LOW/MEDIUM/HIGH/ULTRA

---

## 7. INTEGRAZIONE DELL'INTELLIGENZA ARTIFICIALE

### 7.1 Architettura dell'Integrazione

Il sistema utilizza l'API di **OpenAI GPT-4o-mini** per 
generare report pre-match narrativi in italiano.

[Dati Match dal DB] → [Prompt Builder] → [OpenAI API]
↓
[Salvataggio DB] ← [Report Narrativo 250 parole]

### 7.2 Prompt Engineering

Il sistema costruisce un prompt strutturato contenente:
- Statistiche delle squadre (Elo, gol fatti/subiti)
- Previsioni del modello (probabilità 1X2)
- Value Bets trovate (quota, bookmaker, valore)
- Stake Kelly consigliato

Il **System Prompt** istruisce il modello a:
1. Spiegare PERCHÉ il modello ha trovato valore
2. Evidenziare i fattori chiave
3. Dare un giudizio sulla confidenza
4. Includere un disclaimer

### 7.3 Modalità Fallback

Quando l'API OpenAI non è disponibile (nessun credito 
o errore di rete), il sistema genera un report basico 
automaticamente con i dati disponibili, garantendo 
che la funzionalità non si interrompa mai.

### 7.4 Esempio di Report Generato

📊 REPORT — Inter Milan vs AS Roma
🏆 Serie A (Calcio)
📅 2026-04-05 20:45:00

📈 PREVISIONI (poisson):
• Inter Milan: 47.7%
• Pareggio: 26.6%
• AS Roma: 25.7%

🔥 VALUE BETS: 2
• AS Roma @ 5.80 (Betfair) | Value: 49.2%
• Pareggio @ 4.10 (Winamax) | Value: 9.1%

⚠️ DISCLAIMER: Analisi puramente statistica.
Non costituisce consiglio finanziario.

---

## 8. SVILUPPO DEL BACKEND PHP

### 8.1 Struttura delle Classi

Il backend PHP segue il pattern **MVC semplificato**:

- **Model** → classi in `/classes/` (Database, Auth, 
  ValueBet, Bankroll, Dashboard)
- **View** → pagine in `/pages/` e `/templates/`
- **Controller** → `index.php` (router) e `/api/`

### 8.2 Singleton Database

La classe `Database.php` implementa il pattern Singleton 
per garantire una singola connessione PDO:

```php
public static function getInstance(): Database
{
    if (self::$instance === null) {
        self::$instance = new Database();
    }
    return self::$instance;
}

8.3 Sicurezza
- Password: hashate con password_hash() (bcrypt)
- SQL Injection: prevenuta con prepared statements PDO
- XSS: output sanitizzato con htmlspecialchars()
- CSRF: sessioni PHP con session_start()
- Chiavi API: in file .env escluso da Git

8.4 API REST Interne
Endpoint	            Metodo	                Descrizione
api/get_valuebets.php	GET	                    Lista value bets (JSON)
api/place_bet.php	    POST	                Piazza scommessa
api/get_performance.php	GET	                    KPI utente
api/generate_report.php	GET	                    Genera report IA


9. SVILUPPO DEL FRONTEND
9.1 Interfaccia Utente
L'interfaccia utilizza Bootstrap 5 con tema dark
personalizzato. Le pagine principali sono:

- Dashboard: KPI cards, grafico bankroll, value bets recenti
- Value Bets: tabella filtrabile con confidenza e stake Kelly
- Match Detail: previsioni, quote, report IA
- Tracker: storico scommesse con filtri
- Bankroll: grafico andamento, gestione Kelly
- Settings: profilo, cambio password, Kelly fraction


9.2 Grafici Interattivi
I grafici sono realizzati con Chart.js 4.4:

- Grafico a linea per l'andamento del bankroll
- Colore dinamico (verde se in profitto, rosso se in perdita)
- Linea tratteggiata per il bankroll iniziale di riferimento


9.3 Responsive Design
L'interfaccia è completamente responsive grazie al
grid system di Bootstrap 5, testata su:

- Desktop (1920×1080)
- Tablet (768×1024)
- Mobile (375×667)


10. TESTING E RISULTATI

10.1 Test Effettuati
Test	                Risultato
Connessione DB	        ✅ 10 tabelle create
Import librerie Python	✅ 12/12 moduli
Raccolta quote API	    ✅ 68 partite, 4903 quote
Modello Poisson	        ✅ Previsioni differenziate
Modello Elo	            ✅ Probabilità basate su rating
Value Bet Finder	    ✅ Value bets identificate
Kelly Criterion	        ✅ Stake calcolati correttamente
Report IA (fallback)	✅ Report generati
Login/Register PHP	    ✅ Autenticazione funzionante
Dashboard	            ✅ KPI e grafici corretti
Place Bet	            ✅ Bankroll aggiornato

10.2 Esempio di Output
Dopo l'esecuzione di python main.py, il sistema ha:

- Raccolto quote da 5 campionati (Serie A, Premier League, La Liga, NBA, ATP)
- Calcolato 68 previsioni differenziate
- Identificato 71 value bets con confidenza da LOW a ULTRA
- Le top value bets mostrano value dal 5% al 112%

10.3 Cold Start Problem
Al primo avvio, il modello non ha dati storici. Il problema è stato risolto con uno script seed_team_stats.py che stima le statistiche iniziali
dalle quote dei bookmaker stessi, sfruttando il fatto che le quote contengono informazione sulla forza reale delle squadre.

11. CONCLUSIONI E SVILUPPI FUTURI

11.1 Risultati Raggiunti
Il progetto dimostra la fattibilità di un sistema automatizzato per l'analisi delle quote sportive.
L'integrazione di SQL, PHP, Python e IA in un unico sistema coerente dimostra competenze trasversali in:

- Progettazione database relazionali
- Sviluppo web full-stack
- Data Science e modelli statistici
- Integrazione API e servizi cloud
- Intelligenza Artificiale applicata

11.2 Sviluppi Futuri
Sviluppo	            Descrizione
Machine Learning	    Modello Random Forest per previsioni più accurate
Real-time	            WebSocket per aggiornamento quote live
Mobile App	            Versione React Native
Arbitrage	            Rilevamento scommesse senza rischio
Backtesting	            Simulazione su dati storici per validare il modello
Multi-utente	        Dashboard admin per gestione sistema


11.3 Considerazioni Etiche

Il progetto è realizzato a scopo esclusivamente didattico. Non costituisce incentivo al gioco
d'azzardo né consiglio finanziario. Le analisi sono puramente statistiche e non garantiscono risultati.

12. GLOSSARIO
Termine	                        Definizione
Value Bet	                    Scommessa il cui rendimento atteso è positivo
Quota Decimale	                Moltiplicatore del bookmaker (es. 2.40)
Probabilità Implicita	        1 / quota decimale
Distribuzione di Poisson	    Distribuzione di probabilità per eventi rari
Elo Rating	                    Sistema di classificazione basato sui risultati
Kelly Criterion	                Formula per il sizing ottimale delle scommesse
Lambda (λ)	                    Tasso medio di gol attesi per squadra
Edge	                        Vantaggio del modello rispetto al bookmaker
API REST	                    Interfaccia web per lo scambio di dati (JSON)
Singleton	                    Design pattern che limita l'istanziazione a un solo oggetto
Cold Start	                    Problema di un sistema che non ha dati iniziali
GPT	                            Generative Pre-trained Transformer (modello IA)
Prompt Engineering	            Tecnica di formulazione istruzioni per l'IA

ALLEGATI
A. Schema ER del Database
B. Diagramma delle Classi UML
C. Screenshot dell'Applicazione
D. Codice Sorgente (repository)