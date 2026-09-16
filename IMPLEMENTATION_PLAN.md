# Piano operativo ufficiale per LUMEN

## Stato del documento

Questo documento definisce il lavoro approvabile per la prossima fase del progetto. Il team non deve implementare le funzioni descritte qui finché il piano non riceve approvazione.

Branch di pianificazione: `codex/implementation-plan-e262998`.

Baseline verificata:

- architettura: frontend statico in `public/`, API FastAPI in `api/index.py`, calcoli nei moduli Python;
- branch di partenza: `main` al commit `b40838303222bed86942a7ed6e6091507ecc55dc`;
- deployment verificato: ambiente Production, stato `success`, stesso commit, URL `https://lumen-g27-8lpm8wqtu-lumen-g27.vercel.app`;
- test locali: 9 test superati con Python 3.11;
- verifica ufficiale: GitHub Actions con Python 3.12;
- limite funzionale principale: manca il pannello esplicito CMO contro CFO previsto come M3.

## Obiettivo

Trasformare l'attuale calcolatore in uno strumento aziendale comprensibile, verificabile e utilizzabile da un manager non tecnico. L'app deve aiutare a scegliere prezzo, posizionamento, canale iniziale e momento del lancio, mostrando il compromesso tra gli obiettivi del CMO e quelli del CFO.

Il risultato centrale resta un solo verdetto: `GO`, `CONDITIONAL` oppure `NO-GO`. Il team conserverà le regole correnti del verdetto finché una modifica non riceve una motivazione documentata, test dedicati e approvazione.

## Vincoli architetturali

Il team manterrà questa separazione:

| Livello | Responsabilità |
| --- | --- |
| `public/index.html` | struttura accessibile della pagina e controlli utente |
| `public/styles.css` | presentazione, stati visivi, layout responsive e stampa |
| `public/app.js` | stato temporaneo della sessione, chiamate API e rendering |
| `api/index.py` | validazione delle richieste e serializzazione di risultati aggregati |
| moduli Python esistenti | formule, regole decisionali e accesso ai dati approvati |
| nuovo modulo Python dedicato, se necessario | posizionamento, sensibilità, timing e alternative calcolate |

Il JavaScript non conterrà formule economiche, soglie decisionali, classificazioni competitive o logica per migliorare uno scenario. Il browser potrà conservare fino a tre scenari soltanto per la durata della pagina aperta.

L'API continuerà a restituire risultati aggregati. Nessun endpoint servirà file CSV, righe del questionario o identificativi.

Tutti i testi visibili nell'app useranno un inglese aziendale semplice, adatto a un manager non tecnico. L'interfaccia non sarà bilingue. La documentazione interna, compreso questo piano, può restare in italiano.

## Contratto informativo comune

Ogni metrica mostrata nell'interfaccia avrà questi campi:

- nome completo e acronimo, quando esiste;
- valore e unità di misura;
- stato `favorevole`, `da monitorare` oppure `critico`;
- soglia e confronto, se il modello possiede una soglia approvata;
- spiegazione in linguaggio aziendale;
- dettaglio espandibile con formula, fonte, assunzioni e limiti.

Le tre metriche che guidano il verdetto useranno le soglie esistenti: LTV:CAC 3,0, payback scelto dall'utente e indice di accettabilità 35%. Lo stato visivo non cambierà il verdetto:

- `critico`: la metrica non supera la propria soglia;
- `da monitorare`: la metrica supera la soglia ma costituisce il fattore decisivo del verdetto, oppure non possiede una soglia ufficiale;
- `favorevole`: la metrica supera la soglia e non costituisce il fattore decisivo.

Per una metrica senza soglia, l'interfaccia mostrerà `da monitorare` insieme alla frase "Nessuna soglia decisionale approvata". Il team non inventerà soglie per ottenere un colore favorevole o critico.

Ogni controllo espandibile userà un'etichetta esplicita, per esempio "Come è stato calcolato?", e funzionerà con tastiera e lettore di schermo. Un comando globale permetterà di espandere o chiudere tutte le spiegazioni.

## Contratti delle nuove analisi

### Posizionamento competitivo

Il backend confronterà il prezzo scelto con le osservazioni di `competitor_prices_by_channel.csv` per lo stesso canale e per il formato confrontabile, quando disponibile. La risposta conserverà nome del concorrente, posizionamento dichiarato nel CSV, fascia osservata e distanza dal prezzo LUMEN.

Le parole "accessibile", "premium" e "molto premium" saranno etichette manageriali derivate dalle fasce e dai posizionamenti presenti nel file, non affermazioni generali sul mercato tedesco. In caso di sovrapposizione tra fasce, l'app dichiarerà la sovrapposizione. Se il CSV non contiene un concorrente per il canale scelto, l'app non ne stimerà il prezzo.

### Prospettive CMO e CFO

Il pannello CMO userà soltanto l'indice di accettabilità del prezzo, la posizione rispetto alle fasce osservate dei concorrenti e la coerenza con l'obiettivo premium descritto nel brief. Il pannello CFO userà contributo unitario e mensile, LTV:CAC, payback e superamento delle soglie.

Il team non introdurrà una metrica nel pannello CMO o altrove senza formula, fonte e significato approvati e documentati.

Entrambi i pannelli commenteranno lo stesso scenario e lo stesso verdetto. Sotto il verdetto generale l'app mostrerà fattore decisivo, rischio principale e compromesso accettato.

### Confronto di scenari e canali

L'app partirà con un solo scenario. L'utente potrà aggiungerne un secondo e un terzo, duplicare uno scenario, modificarlo e rimuoverlo. Il limite resterà tre.

Il backend accetterà una richiesta di confronto con un massimo di tre scenari validi e restituirà risultati completi e differenze aggregate. Il comando "Confronta i canali" costruirà tre scenari con prezzo, mese e orizzonte uguali e con i tre canali ufficiali. Il frontend non ricalcolerà differenze economiche.

### Sensibilità del prezzo

Il backend valuterà punti discreti dentro `OBSERVED_PRICE_SUPPORT`. Non userà ricerca binaria, perché l'accettabilità non è monotona sotto EUR 2,10.

L'algoritmo dividerà i punti consecutivi in intervalli con lo stesso verdetto e restituirà l'intervallo contiguo che contiene il prezzo selezionato, oltre ai cambi di verdetto più vicini. Il prezzo scelto sarà valutato sempre, anche quando non coincide con la griglia.

Prima di fissare il passo della griglia, il team misurerà la latenza con passi di EUR 0,01, EUR 0,02 e EUR 0,05. Ogni richiesta di sensibilità avrà un limite esplicito di 250 valutazioni di prezzo. Il confronto di più scenari calcolerà la sensibilità su richiesta per un solo scenario selezionato, così una richiesta non supera il limite.

Il team adotterà il passo più preciso che rispetta il budget misurato. Se EUR 0,01 supera il budget, userà il passo successivo che lo rispetta e ne spiegherà il limite. Documenterà passo, numero di valutazioni, metodo di misura e latenza. La precisione dichiarata nell'interfaccia coinciderà con il passo usato. L'interfaccia chiamerà il risultato "sensibilità del modello", non previsione della domanda.

### Momento del lancio

Il backend restituirà l'indice stagionale del mese scelto, la sua posizione tra i dodici mesi, la variazione del contributo mensile e del payback e la finestra più favorevole nei dati disponibili.

Il confronto terrà fissi prezzo, canale e orizzonte. Il risultato userà soltanto `seasonality_and_weather.csv`; l'app non chiamerà servizi meteorologici.

### Percorso per migliorare lo scenario

Per un risultato `CONDITIONAL` o `NO-GO`, il backend cercherà alternative modificando una variabile alla volta:

- prezzo entro il supporto osservato;
- uno degli altri canali ufficiali;
- uno degli altri undici mesi.

Il ranking privilegerà, nell'ordine, un verdetto migliore, un numero minore di soglie fallite e una minore distanza normalizzata dalle soglie. I criteri di spareggio saranno deterministici e testati. L'app distinguerà ogni alternativa come aggiustamento supportato dal modello. Se nessuna modifica singola migliora il risultato, lo dichiarerà senza generare suggerimenti arbitrari.

## Privacy e sicurezza

`data/customer_survey.csv` proviene senza modifiche dal template universitario pubblico `ateliaworkshop-ai/lumen-pricing-case-template`. Il repository conserverà il file e la sua cronologia.

Il runtime non deve caricare `first_name`, `last_name`, `email` o `respondent_id`. Prima della Fase 0 il codice escludeva i primi tre campi e caricava ancora `respondent_id`; la Fase 0 chiude questa lacuna prima delle nuove funzioni.

Ogni fase dovrà rispettare queste condizioni:

- nessun identificativo nel frontend, nelle risposte API o nei log applicativi;
- nessun endpoint per CSV o righe grezze;
- nessun invio a servizi esterni;
- risultati aggregati;
- errori API privi di dettagli che rivelino righe o valori personali.

La documentazione specificherà la provenienza del CSV, la scelta di non usare gli identificativi e la necessità che il proprietario del caso confermi la natura sintetica o autorizzata dei dati. Questa conferma non bloccherà l'implementazione basata sul template fornito.

I test useranno soltanto fixture e sentinelle sintetiche create per la suite. Nessun test copierà nomi, email, identificativi o altri valori personali presenti nel CSV del template.

Il test di non esposizione controllerà almeno:

- assenza delle chiavi `first_name`, `last_name`, `email` e `respondent_id` da `load_all()["customer_survey"]` e dalle risposte API;
- assenza nelle risposte API di ogni valore sentinella sintetico inserito nelle fixture;
- presenza di soli dati aggregati nelle risposte di `/api/scenario` e `/api/compare`;
- risposta HTTP 404, o equivalente sicuro, per tentativi di ottenere file CSV e righe grezze;
- presenza di soli dati aggregati nel pannello qualità dati.

## Ordine di costruzione

Le fasi dipendono l'una dall'altra in questo ordine: `Fase 0 → Fase 1 → Fase 2 → Fase 3 → Postilla 3A → Fase 4 → Fase 5 → Fase 6 → Fase 7`. Ogni fase parte da `main` aggiornata dopo il merge della fase precedente. Il team non prepara in parallelo codice destinato a una fase successiva.

### Fase 0: privacy baseline, prima delle funzioni

**File probabilmente coinvolti**

- `data_loader.py`
- `api/index.py`
- `test_data_loader.py`
- `test_api.py`
- `README.md`
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

Il runtime esclude `respondent_id`, `first_name`, `last_name` ed `email` durante la lettura del questionario. Le API continuano a restituire risultati aggregati e rifiutano richieste di file CSV o righe grezze. La risposta alla voce Data della checklist del README documenta subito la provenienza dal template e la scelta di non usare identificativi.

**Criteri di accettazione**

- `load_all()["customer_survey"]` non contiene le quattro chiavi proibite;
- `/api/scenario` e gli endpoint disponibili non contengono chiavi proibite o sentinelle sintetiche;
- le risposte API contengono soltanto dati aggregati;
- i tentativi di ottenere un CSV o una riga grezza ricevono HTTP 404 o una risposta sicura equivalente;
- i test usano fixture e sentinelle sintetiche e non copiano valori personali dal CSV;
- README risponde alla voce Data prima dell'avvio della Fase 1.

**Test necessari**

- test unitario del filtro delle quattro colonne con DataFrame sintetico;
- test API con sentinelle sintetiche per chiavi e valori;
- test delle route inesistenti per file CSV, dataset e singole righe;
- test dello schema aggregato della risposta;
- controllo documentale della voce Data del README.

**Rischi**

Un test basato soltanto sui nomi delle chiavi può ignorare valori filtrati male. Le sentinelle sintetiche permetteranno di verificare sia lo schema sia il contenuto senza usare dati personali del template.

**Condizione di arresto**

La fase termina dopo test mirati, suite completa, aggiornamenti documentali, prompt log e pull request dedicata. Il team si ferma dopo l'apertura della pull request e non avvia spiegazioni, pannelli o altre funzioni.

**Risultato della Fase 0, 2026-09-16**

- il runtime esclude `respondent_id`, `first_name`, `last_name` ed `email`;
- FastAPI restituisce un errore 422 senza riecheggiare input non valido;
- i test usano sentinelle sintetiche e verificano l'assenza di chiavi e valori proibiti;
- le route di file e righe grezze provate dai test restituiscono 404;
- `httpx` è dichiarato nelle dipendenze per eseguire gli stessi test HTTP in locale e nel CI Python 3.12;
- README documenta origine del CSV e trattamento dei quattro identificativi;
- 5 test mirati e 11 test completi passano localmente con Python 3.11; il CI Python 3.12 resta gate ufficiale.

### Fase 1: spiegazioni, metodologia e testi manageriali

**File probabilmente coinvolti**

- `api/index.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `constants.py`
- `test_api.py`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

L'API aggiunge metadati aggregati per nome, unità, stato, soglia, spiegazione, formula, fonte, assunzioni e limiti. L'interfaccia presenta una vista sintetica e dettagli espandibili. Il comando globale apre o chiude tutte le sezioni metodologiche.

**Criteri di accettazione**

- nessun acronimo compare senza nome completo alla prima occorrenza;
- ogni metrica rispetta il contratto informativo comune;
- i dettagli funzionano con mouse, tastiera e tecnologie assistive;
- i testi spiegano il significato aziendale senza cambiare le formule;
- le soglie mostrate coincidono con quelle usate da `verdict.py`.

**Test necessari**

- test API sullo schema dei metadati;
- test sui tre stati e sul caso senza soglia ufficiale;
- test manuale da tastiera per apertura singola e globale;
- controllo responsive su viewport mobile e desktop.

**Rischi**

Una risposta API troppo verbosa può duplicare contenuti statici. Il team centralizzerà definizioni e fonti in Python o in una struttura condivisa, senza copiarle tra endpoint.

**Condizione di arresto**

La fase termina quando l'attuale scenario singolo dispone di spiegazioni complete. Il team non introduce grafici, nuove metriche o modifiche al verdetto.

**Risultato della Fase 1, 2026-09-16**

- API restituisce metadati aggregati per sei metriche, con stato, confronto, spiegazione, formula, fonte, assunzioni e limiti;
- frontend usa questi metadati per dettagli accessibili e controlli globali di apertura e chiusura;
- testi dell'app restano in inglese aziendale semplice;
- README documenta l'esplicabilità e l'assenza di calcoli nel browser;
- 4 test API, 12 test completi e il controllo sintattico JavaScript passano localmente con Python 3.11; CI Python 3.12 resta gate ufficiale.

### Fase 2: posizionamento competitivo e pannello CMO/CFO

**File probabilmente coinvolti**

- nuovo `decision_support.py`, se la logica renderebbe `api/index.py` troppo esteso;
- `data_loader.py`
- `api/index.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- nuovo `test_decision_support.py`
- `test_api.py`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

L'app colloca il prezzo nella fascia osservata per il canale e mostra le due prospettive CMO e CFO sotto un unico verdetto. Il riepilogo nomina fattore decisivo, rischio e compromesso.

**Criteri di accettazione**

- concorrenti, prezzi e posizionamenti provengono dal CSV;
- l'app segnala fasce sovrapposte o osservazioni mancanti;
- CMO e CFO non producono verdetti separati;
- il pannello riusa metriche già calcolate;
- il verdetto resta identico a quello restituito oggi per gli stessi input.

**Test necessari**

- test per ciascun canale e per dati concorrente mancanti;
- test sui confini e sulle sovrapposizioni delle fasce;
- test di regressione delle regole `GO`, `CONDITIONAL` e `NO-GO`;
- test API che verifica un solo verdetto.

**Rischi**

Le etichette accessibile, premium e molto premium possono sembrare dati di mercato. La risposta dovrà collegarle alle fasce osservate e mostrare la fonte.

**Condizione di arresto**

La fase termina con il pannello M3 funzionante. Il team non aggiunge mappe di brand, competitor esterni o punteggi di percezione inventati.

**Risultato della Fase 2, 2026-09-16**

- API confronta il prezzo selezionato con i concorrenti osservati nello stesso canale e formato;
- pannelli CMO e CFO riusano lo stesso scenario e lo stesso verdetto;
- nessun concorrente, soglia o verdetto aggiuntivo viene inventato;
- 4 test API, 12 test completi e controllo sintattico JavaScript passano localmente con Python 3.11; CI Python 3.12 resta gate ufficiale.

### Fase 3: confronto di massimo tre scenari e confronto canali

**File probabilmente coinvolti**

- `api/index.py`
- eventuale `decision_support.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `test_api.py`
- eventuale `test_decision_support.py`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

L'utente gestisce da uno a tre scenari, può duplicarli e confrontarli. Il comando "Confronta i canali" prepara i tre canali ufficiali con gli altri input invariati. Il browser conserva lo stato soltanto finché la pagina resta aperta.

**Criteri di accettazione**

- il flusso con un solo scenario resta quello predefinito;
- il quarto scenario viene rifiutato nell'interfaccia e dall'API;
- la duplicazione copia tutti gli input e crea un elemento modificabile indipendente;
- la rimozione non può lasciare zero scenari;
- differenze e verdetti provengono dal backend;
- refresh e chiusura della pagina eliminano lo stato.

**Test necessari**

- test API con uno, due, tre e quattro scenari;
- test per input non validi in uno degli scenari;
- test sulle differenze aggregate;
- test manuali di aggiunta, duplicazione, modifica e rimozione;
- test del comando per i tre canali.

**Rischi**

Tre schede complete possono rendere la pagina illeggibile su mobile. Il confronto userà un riepilogo compatto e permetterà di aprire i dettagli di ciascuno scenario.

**Condizione di arresto**

La fase termina al confronto in memoria di tre scenari. Il team non aggiunge account, URL condivisibili, database, cronologia o esportazione dati.

**Risultato della Fase 3, 2026-09-16**

- `/api/compare` accetta da uno a tre scenari e restituisce risultati e differenze aggregate calcolati dal backend;
- l'interfaccia parte con un solo scenario, ne può duplicare fino a tre, modificare o rimuovere le copie e blocca il quarto;
- il comando "Compare channels" genera i tre canali ufficiali mantenendo invariati prezzo, mese e orizzonte;
- lo stato rimane solo nel browser fino a refresh o chiusura; nessun account, database, cronologia o esportazione è stato aggiunto;
- la checklist README documenta ora la scelta di storage temporaneo.

### Postilla 3A: scenario selezionato come baseline del confronto

Questa postilla completa il confronto prima della Fase 4. Lo Scenario 1 resta selezionato per impostazione predefinita, ma l'utente può scegliere uno qualunque degli scenari presenti come baseline. Il verdetto, le metriche, il posizionamento competitivo e i pannelli CMO/CFO mostrano sempre lo scenario selezionato. Gli altri scenari mostrano differenze rispetto a quella baseline.

**Interazione e presentazione**

- ogni scheda scenario offre un controllo esplicito in inglese, per esempio `Use as baseline`;
- la scheda selezionata mantiene fondo bianco, bordo più evidente e indicazione testuale `Selected baseline`;
- le schede non selezionate usano fondo grigio chiaro e testo secondario più tenue, ma conservano contrasto leggibile;
- colore e contrasto non sono l'unico segnale: stato selezionato, controllo e testo devono essere percepibili anche da tastiera e tecnologie assistive;
- il riepilogo del confronto conserva l'ordine Scenario 1, 2 e 3 e identifica chiaramente la baseline;
- quando cambia la selezione dopo una valutazione, il frontend invia una nuova richiesta con gli input correnti. Non ricalcola differenze economiche nel browser.

**Contratto API**

`/api/compare` accetta `baseline_index` insieme agli scenari, con valore predefinito `0`. Il backend verifica che l'indice appartenga alla lista ricevuta, calcola tutte le differenze rispetto allo scenario selezionato e restituisce `baseline_index` nella risposta. Lo scenario baseline ha differenze pari a zero. L'ordine degli scenari non cambia.

**File probabilmente coinvolti**

- `api/index.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `test_api.py`
- `test_public_app.py`
- `README.md`, se la checklist richiede un chiarimento sull'interazione
- `IMPLEMENTATION_PLAN.md`
- prompt log della postilla

**Criteri di accettazione**

- con uno scenario, quello scenario è sempre la baseline;
- con due o tre scenari, l'utente può selezionare qualsiasi scenario senza cambiarne l'ordine;
- pannelli dettagliati e verdetto appartengono allo scenario selezionato;
- ogni differenza restituita usa lo scenario selezionato come riferimento;
- rimuovendo la baseline, l'interfaccia seleziona il primo scenario rimasto;
- aggiungere o duplicare uno scenario non cambia la baseline esistente;
- selezione e stato visivo funzionano da tastiera e non dipendono soltanto dal colore;
- il browser non contiene formule economiche e non conserva lo stato dopo refresh o chiusura.

**Test necessari**

- test API con `baseline_index` uguale a 0, 1 e 2;
- test API per indice negativo o fuori dalla lista ricevuta;
- test che verifica differenze zero per la baseline e differenze corrette per gli altri scenari;
- test di regressione privacy sulla nuova risposta aggregata;
- smoke test browser per selezione, aggiornamento pannelli e rimozione della baseline;
- controllo tastiera, contrasto e viewport mobile.

**Rischi e limiti**

Un'intera scheda cliccabile può cambiare baseline mentre l'utente modifica un input. La selezione userà quindi un controllo esplicito. Il grigio non userà opacità sull'intera scheda, perché ridurrebbe anche la leggibilità dei campi. La postilla non aggiunge metriche, persistenza, confronto automatico continuo o nuove regole decisionali.

**Condizione di arresto**

La postilla termina quando uno dei tre scenari può guidare sia i pannelli dettagliati sia le differenze backend. Dopo test mirati, suite completa, documentazione, prompt log e pull request, il team si ferma senza iniziare la Fase 4.

**Risultato della Postilla 3A, 2026-09-16**

- `/api/compare` accetta e restituisce `baseline_index`; le differenze restano calcolate dal backend;
- ogni scenario offre `Use as baseline`; pannelli dettagliati e differenze seguono la baseline selezionata;
- baseline selezionata ha fondo bianco e indicazione testuale; le altre schede usano grigio chiaro senza ridurre la leggibilità;
- rimuovere la baseline seleziona il primo scenario rimasto; aggiungere o duplicare conserva la baseline;
- test API, test regressione frontend e smoke test Chrome verificano selezione e richiesta della baseline.

### Fase 4: sensibilità del prezzo e analisi del mese

**File probabilmente coinvolti**

- `acceptance.py`
- `economics.py`
- `verdict.py`, soltanto come dipendenza da riusare;
- `data_loader.py`
- eventuale `decision_support.py`
- `api/index.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `test_acceptance.py`
- `test_economics.py`
- `test_verdict.py`
- eventuale `test_decision_support.py`
- `test_api.py`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

L'app mostra l'intervallo contiguo di prezzo che conserva il verdetto, i cambi più vicini e il confronto del mese scelto con gli altri mesi. Il backend misura più granularità prima di fissare il passo della scansione.

**Criteri di accettazione**

- nessun punto esce da `OBSERVED_PRICE_SUPPORT`;
- nessuna richiesta supera 250 valutazioni di prezzo;
- l'algoritmo trova intervalli non monotoni e disgiunti;
- il risultato distingue risoluzione della griglia e precisione economica;
- la precisione dichiarata nell'interfaccia coincide con il passo della griglia;
- mese, rango stagionale, contributo e payback risultano coerenti;
- il frontend non contiene formule;
- passo, numero di valutazioni, latenza misurata e budget vengono documentati.

**Test necessari**

- test sintetico con verdetti non monotoni;
- test ai limiti EUR 0,62 ed EUR 3,09;
- test con prezzo fuori griglia;
- test del limite di 250 valutazioni;
- test per i dodici mesi e per parità stagionali;
- benchmark ripetibile dei tre passi candidati;
- test API dello schema e dei limiti.

**Rischi**

Una griglia fine può rallentare una funzione Vercel. Il team userà caching dei dati già disponibile e sceglierà il passo dopo il benchmark, senza introdurre una ricerca basata su monotonicità.

**Condizione di arresto**

La fase termina con una risposta entro il budget misurato e una spiegazione dei limiti. Il team non aggiunge forecast, simulazioni Monte Carlo, meteo live o causalità stagionale.

### Fase 5: percorso per migliorare lo scenario

**File probabilmente coinvolti**

- eventuale `decision_support.py`
- `verdict.py`, come regola da riusare;
- `api/index.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- eventuale `test_decision_support.py`
- `test_api.py`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

Per scenari non approvati, l'app presenta alternative calcolate modificando prezzo, canale o mese uno alla volta. Ogni alternativa mostra quale input cambia, il nuovo verdetto e le metriche che migliorano o peggiorano.

**Criteri di accettazione**

- i suggerimenti restano nel supporto osservato e nei valori ufficiali;
- il ranking è deterministico;
- ogni alternativa cambia una sola variabile;
- un risultato `GO` non riceve un percorso correttivo;
- l'app dichiara quando il modello non trova miglioramenti;
- il testo usa il termine "aggiustamento del modello" e non promette un esito commerciale.

**Test necessari**

- test per `CONDITIONAL`, `NO-GO` e `GO`;
- test di spareggio;
- test senza alternative migliori;
- test ai limiti di prezzo;
- test che verifica il vincolo di una variabile per proposta.

**Rischi**

Il ranking può sembrare una raccomandazione strategica completa. L'interfaccia mostrerà anche gli effetti negativi e le assunzioni mantenute fisse.

**Condizione di arresto**

La fase termina con un massimo contenuto di alternative utili per dimensione. Il team non crea un ottimizzatore multi-obiettivo o combinazioni automatiche di più variabili.

### Fase 6: modalità stampa

**File probabilmente coinvolti**

- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `README.md`, per le risposte pertinenti alla checklist
- `IMPLEMENTATION_PLAN.md`
- prompt log della fase

**Comportamento atteso**

Un comando di stampa apre il dialogo del browser. Il foglio stampato include input, verdetto, metriche, prospettive CMO/CFO, compromesso, fonti e timestamp della valutazione. Controlli interattivi e sezioni irrilevanti non compaiono.

**Criteri di accettazione**

- layout leggibile in A4 verticale e orizzontale;
- nessun testo tagliato o pannello sovrapposto;
- colori non indispensabili alla comprensione;
- URL e data della valutazione visibili;
- nessuna libreria o generatore PDF server-side.

**Test necessari**

- anteprima di stampa in Chromium;
- prova con uno e tre scenari;
- prova in scala di grigi;
- controllo di contenuto sensibile assente.

**Rischi**

Le sezioni espandibili possono risultare chiuse nella stampa. Il foglio `@media print` definirà quali dettagli includere e li renderà leggibili senza dipendere dallo stato interattivo.

**Condizione di arresto**

La fase termina quando il browser salva una copia PDF leggibile. Il team non implementa template PDF, invio email o archiviazione.

### Fase 7: documentazione, privacy, test completi e verifica Vercel

**File probabilmente coinvolti**

- `README.md`
- `PROJECT_CONTEXT.md`
- `DATA_CONFIDENTIALITY.md`, soltanto se serve chiarire la provenienza del template senza indebolire le regole;
- `data_loader.py`
- tutti i file `test_*.py` interessati;
- `.github/workflows/tests.yml`, soltanto se la suite richiede un comando aggiuntivo;
- prompt log della sessione corrente.

**Comportamento atteso**

La documentazione riceve una revisione finale della checklist universitaria, descrive il trattamento dei dati e riporta il dominio pubblico definitivo. La fase verifica di nuovo l'esclusione dei quattro identificativi introdotta nella Fase 0. La suite completa passa con Python 3.12 e il deployment Production successivo al merge serve il commit di `main`.

**Criteri di accettazione**

- README risponde a dati, API key, deployment, file generati, storage, robustezza, spiegabilità e rilevanza aziendale;
- README dichiara assenza di API esterne, API key, database e persistenza;
- README documenta provenienza del CSV e mancato uso degli identificativi;
- "Our Approach" resta in linguaggio aziendale;
- `PROJECT_CONTEXT.md` riflette le decisioni implementate e i limiti;
- il prompt log corrente è completo;
- `python -m compileall .` e `python -m pytest` passano nel CI Python 3.12;
- il deployment Vercel Production riporta `success`, commit di `main` e dominio stabile;
- una verifica del sito pubblico copre caricamento pagina e scenario base.

**Test necessari**

- suite completa Python;
- test di non esposizione dei quattro identificativi;
- test API per risposte aggregate ed errori sicuri;
- test manuali responsive, tastiera e stampa;
- smoke test sull'URL Production dopo il merge;
- confronto tra SHA deployato e SHA di `origin/main`.

**Rischi**

Un URL di deployment specifico non garantisce un dominio stabile. Il team inserirà nel README il dominio pubblico definitivo confermato da Vercel e conserverà l'URL verificato come evidenza del baseline finché l'alias non viene confermato.

**Condizione di arresto**

La fase termina dopo CI verde, merge approvato, deployment Production riuscito e controllo dello SHA. Problemi esterni a questo scope diventeranno task separati.

## Strategia di test e gate di merge

Ogni fase avrà un branch e una pull request dedicati. Il protocollo di arresto seguente è obbligatorio:

1. eseguire i test mirati della fase;
2. eseguire l'intera suite;
3. aggiornare `IMPLEMENTATION_PLAN.md` con decisioni, risultati e limiti emersi;
4. aggiornare README e la documentazione interessata, comprese le risposte pertinenti alla checklist;
5. includere il prompt log della fase;
6. verificare l'assenza di logica aziendale nel JavaScript e di dati non aggregati nelle API;
7. aprire la pull request e attendere GitHub Actions con Python 3.12;
8. fermarsi senza iniziare la fase successiva.

La fase successiva partirà da un nuovo branch creato dopo il merge della fase precedente e dopo l'aggiornamento locale di `main` da `origin/main`. Il team non considera completata una fase se il codice esiste soltanto in locale, se il CI non passa o se la pull request non è stata integrata.

## Documentazione finale

Ogni fase aggiornerà le risposte della checklist del README che il proprio lavoro rende pertinenti. La Fase 7 controllerà completezza e coerenza dell'insieme; non rimanderà alla fine la documentazione delle decisioni prese nelle fasi precedenti.

Il rilascio dovrà documentare:

- dominio Vercel definitivo e commit verificato;
- assenza di API esterne e chiavi API;
- assenza di account, database e persistenza;
- provenienza del CSV dal template universitario;
- esclusione di `first_name`, `last_name`, `email` e `respondent_id` dal runtime;
- uso esclusivo di output aggregati;
- formule, fonti, soglie, assunzioni e limiti;
- limiti della sensibilità del modello e dei suggerimenti calcolati;
- risposta esplicita alla checklist del README;
- prompt log obbligatorio.

## Non obiettivi

- account, autenticazione o profili;
- database, persistenza o cronologia degli scenari;
- chatbot, LLM o testo generato;
- API esterne o meteo live;
- città, quote di mercato o competitor inventati;
- machine learning;
- formule o regole aziendali nel JavaScript;
- cancellazione o riscrittura dei dati originali;
- redesign completo dell'interfaccia;
- generazione PDF server-side;
- modifica di `AGENTS.md` o dei log precedenti.

## Criterio finale di completamento

Il lavoro sarà completo quando un manager potrà valutare da uno a tre scenari, capire il verdetto unico, leggere le prospettive CMO e CFO, confrontare canali, osservare la sensibilità di prezzo e mese, ricevere alternative calcolate e stampare il risultato. Le API dovranno esporre soltanto dati aggregati, la suite dovrà passare con Python 3.12 e Vercel dovrà servire il commit integrato in `main`.
