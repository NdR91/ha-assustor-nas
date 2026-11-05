# Piano: identità stabile dei volumi e compatibilità Home Assistant 2026.11

**Obiettivo:** mantenere funzionanti i sensori dei volumi quando cambiano gli indici SNMP e verificare la compatibilità con Home Assistant 2026.11.

**Contesto verificato:** sul NAS AS6604T `/volume2` è attualmente associato all'indice 54; nel registro HA esistono serie precedenti con indici 51 e 56. La dashboard usa l'entità associata a 51. L'installazione usa HA 2026.10.0 e l'integrazione 1.1.0-rc3. I dati sono un'istantanea: non assumere che l'indice 54 resti invariato.

**Vincoli:** conservare entity ID, nomi personalizzati e cronologia quando possibile; non eliminare o fondere automaticamente entità o statistiche; non modificare dashboard o impianto di produzione durante lo sviluppo. Non aumentare la versione minima HA senza necessità verificata. Preservare le modifiche preesistenti nel repository.

## Scelte architetturali

- Usare il mount root normalizzato (`/volumeN`) come identità logica, distinta dall'indice `hrStorageIndex`, che resta un dato temporaneo di polling. Un mount può cambiare nome o essere riutilizzato: non trattarlo come identificativo fisico immutabile.
- Durante ogni ciclo associare un solo record valido a ciascun mount. Non dedurre che due indici storici corrispondano allo stesso volume soltanto dal numero. Se righe discordanti dichiarano lo stesso mount, segnalare l'ambiguità e non scegliere silenziosamente.
- Migrare gli unique ID usando le API del registro entità Home Assistant, prima della creazione delle entità. Conservare l'entity ID della voce scelta; non modificare direttamente i file `.storage`. Verificare l'effettiva continuità di cronologia e statistiche con test di integrazione.
- Per gli impianti preesistenti, ricostruire candidati per config entry, nome originale di volume e metrica. Se esiste un unico candidato affidabile, migrarlo; se vi sono più candidati o il nome manca/non è affidabile, non indovinare: lasciare intatte le voci e presentare istruzioni o un'issue di riparazione per far scegliere quale conservare. Una selezione esplicita può indicare, nel caso dell'utente, la voce usata dalla dashboard. Gestire collisioni e migrazione parziale in modo ripetibile.
- Non cancellare automaticamente i duplicati: potrebbero essere usati da altre dashboard, automazioni o contenere dati storici separati. Documentare come individuarli e rimuoverli facoltativamente dopo verifica e backup.

## Mappa dei file

- `custom_components/ha_asustor_nas_custom_integration/coordinator/coordinator.py`: normalizzazione e aggregazione delle righe volume.
- `custom_components/ha_asustor_nas_custom_integration/sensor.py`: entità indicizzate dal mount stabile e rilevamento successivo.
- Nuovo modulo dedicato alla migrazione del registro e, se necessaria, alla riparazione; integrazione nel setup dopo il primo refresh e prima della piattaforma sensori.
- `tests/`: fixture SNMP anonimizzate, test parser, migrazione, entità e ciclo di vita con Home Assistant.
- `.github/workflows/`, `requirements_test.txt`, `pyproject.toml`: test effettivi e matrice compatibilità.
- `README.md`, traduzioni e note di rilascio: installazione Marketplace/HACS, comportamento migrazione e recupero.

## Attività e criteri di accettazione

### 1. Riproduzione e prove di base

- [ ] Creare fixture anonimizzate da dati osservati e casi sintetici: volume2 con indice 51, poi 54, poi 56; volume1 costante; volumi assenti e valori incompleti.
- [ ] Creare test che dimostrino il difetto attuale: cambio indice genera entità aggiuntive e la vecchia non riceve più valori. Verificare test falliti per la ragione prevista prima di intervenire.
- [ ] Testare le eccezioni del caso reale: tre gruppi di entità con lo stesso nome originale, dashboard che usa il primo e dati SNMP attuali che indicano un altro indice.

### 2. Identità stabile e aggiornamenti

- [ ] Restituire dati indicizzati per mount root normalizzato, conservando l'indice SNMP solo come metadato; mantenere i filtri anti-duplicati e le unità corrette.
- [ ] Creare chiavi delle quattro metriche volume basate su mount e non su indice; aggiungere dinamicamente un volume rilevato dopo l'avvio senza duplicarlo ai refresh successivi.
- [ ] Testare: riordino, aggiunta/rimozione volume, variazione indice, ritorno dopo indisponibilità, più NAS, conflitti di mount e dati incompleti. Verificare che i valori appartengano sempre al volume corretto.

### 3. Migrazione sicura

- [ ] Definire formato univoco dei nuovi unique ID e testare migrazione di tutte le metriche usando `entity_registry.async_update_entity` o API supportata equivalente. Il setup deve poter attendere una prima lettura affidabile; con NAS offline o volume non visto rimandare la decisione.
- [ ] Testare un candidato univoco, più candidati, nomi personalizzati, entity disabilitate, collisioni con ID già migrati, riavvio dopo migrazione parziale, aggiornamenti ripetuti e più config entry. Non sovrascrivere né eliminare entità in conflitto.
- [ ] Per il caso ambiguo progettare e implementare selezione esplicita o issue di riparazione con istruzioni chiare; le entità preesistenti rimangono intatte finché non c'è una scelta affidabile. Definire anche il comportamento dei nuovi volumi durante l'attesa, evitando creazione ripetuta di duplicati.
- [ ] Verificare che la voce scelta mantenga entity ID e personalizzazioni e che la dashboard che la usa continui a funzionare. Testare cronologia e statistiche con recorder; non promettere la fusione delle statistiche dei duplicati.

### 4. Compatibilità Home Assistant 2026.11

- [ ] Installare ambienti isolati e riproducibili per HA 2026.10 e 2026.11; provare anche la versione minima dichiarata 2025.12.3 solo se compatibile con l'ambiente di test. Determinare Python e dipendenze richiesti da ciascuna versione, senza assumere che una sola versione Python sia sufficiente.
- [ ] Eseguire setup, primo refresh, polling, unload/reload, indisponibilità e ripristino, config flow, registro e migrazione; esaminare warning/deprecazioni. Correggere solo incompatibilità dimostrate e documentarle.
- [ ] Verificare comportamento dei nomi in 2026.11 mantenendo entity ID e nomi personalizzati; aggiungere traduzioni soltanto con test e senza rinominare involontariamente le entità esistenti.
- [ ] Aggiungere CI con test sulle versioni supportate, ultima stabile e beta in job separato; mantenere Hassfest, validazione HACS e lint. Se i vincoli delle dipendenze di test impediscono la matrice, risolverli o documentare le celle non eseguite; non dichiarare compatibilità senza prove.

### 5. Documentazione e verifica finale

- [ ] Aggiornare README: Marketplace integrato da 2026.11, HACS per versioni precedenti, procedura repository personalizzato e prerequisiti. Mantenere `hacs.json` e la versione minima coerenti con ciò che i test dimostrano.
- [ ] Documentare identità basata sul mount, limiti in caso di rinomina/riuso, migrazione, conflitti e gestione volontaria dei duplicati. Note di rilascio con impatti visibili e passaggi richiesti.
- [ ] Eseguire test, lint, Hassfest e controlli compatibilità; registrare comandi, versioni e risultati. Provare prima in ambiente separato con copia dei dati anonimizzata.
- [ ] Per la prova sul NUC: preparare backup verificato, descrivere esattamente la distribuzione e il riavvio richiesto, quindi procedere solo nell'ambito autorizzato dall'utente; verificare dashboard, valore e continuità dopo almeno un cambio indice simulato nell'ambiente di prova. Nessuna cancellazione automatica di entità.

## Fonti

- https://www.home-assistant.io/Changelogs — 2026.11: Marketplace e cambiamenti dei nomi delle entità.
- https://contributors.home-assistant.io/marketplace/how-it-works/ — installazione e migrazione HACS.
- https://contributors.home-assistant.io/marketplace/guides/releases/ — versioni e requisito minimo HA.
- https://contributors.home-assistant.io/marketplace/guides/integrations/ — validazione e test beta delle integrazioni personalizzate.
