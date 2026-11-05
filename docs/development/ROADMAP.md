# Roadmap ASUSTOR NAS per Home Assistant

Situazione al 5 novembre 2026. Priorità e raggruppamenti proposti; le versioni sono obiettivi, non impegni di calendario. Le funzionalità vanno validate senza interrompere l'istanza di produzione.

## Contesto e decisioni

- L'AS6604T osservato usa ADM 5.1.4.RM62; il NUC usa Home Assistant 2026.11.0 e integrazione 1.1.0.
- La 1.1.0 ha corretto l'identità dei volumi e gestisce i duplicati con scelta esplicita. Volume 2 è stato ripristinato sull'installazione dell'utente.
- Non dedicare ora una campagna specifica alla versione minima 2025.12.3: il valore in `hacs.json` resta una compatibilità dichiarata, non verificata; rivalutare in presenza di segnalazioni o incompatibilità accertate. Non aumentarlo senza motivazione e comunicazione.
- Le traduzioni in italiano, spagnolo, francese e tedesco devono essere naturali e coerenti con la terminologia Home Assistant; prevedere revisione linguistica competente, controllo placeholder e layout. Nessuna garanzia di revisione madrelingua senza effettiva verifica.

## Fase 1 — Guidare e supportare gli utenti

1. **Riparazione guidata per duplicati.** Se una migrazione ha più candidati, creare una segnalazione in Impostazioni > Sistema > Riparazioni, con indicazioni chiare e percorso verso la scelta. Conservare il log diagnostico, evitare notifiche ripetute e chiudere la segnalazione solo dopo la risoluzione. Non selezionare o cancellare entità automaticamente. Distinguere i NAS configurati, gestire timeout e restart e verificare la compatibilità con le versioni HA supportate.
2. **Traduzioni.** Italiano, spagnolo, francese e tedesco per configurazione, riparazioni, errori e nomi di entità applicabili; inglese rimane lingua di riferimento. Verificare completezza delle chiavi, segnaposto, coerenza, pluralità e testi visualizzati in HA; revisione linguistica di qualità prima della pubblicazione.
3. **Diagnostica scaricabile.** Aggiungere diagnostica nativa Home Assistant con modello, versione integrazione/ADM, stato del polling, capacità rilevate e motivi di esclusione dei volumi. Oscurare community, eventuali credenziali SNMPv3, IP/host, MAC, seriale e informazioni personali anche nei dati annidati; test di redazione e dati parziali. Evitare dump indiscriminati delle risposte SNMP.

Criterio di uscita: l'utente scopre e risolve i conflitti senza cercare nei log; la diagnostica si scarica dall'integrazione e i test non lasciano passare segreti.

## Fase 2 — Configurazione e affidabilità

1. **Riconfigurazione dall'interfaccia.** Modificare host, porta, community e intervallo con validazione, senza ricreare l'integrazione o perdere i riferimenti esistenti. Gestire timeout, host errato, conflitti tra NAS, valori fuori intervallo e rollback in caso di configurazione non valida; distinguere opzioni e dati di connessione secondo le API HA.
2. **Polling SNMP.** Misurare tempi e numero di richieste; valutare riuso del client e richieste efficienti senza bloccare l'event loop. Gestire timeout, risposte parziali, NAS offline e ripristino senza presentare come attendibili valori mancanti o obsoleti.
3. **Identità.** Verificare la stabilità del NAS in presenza di modifiche a IP e interfacce; definire una migrazione prudente. Per dischi e volumi distinguere identificatore logico, numero di slot e identità fisica, prevenendo duplicati e attribuzioni errate quando un componente cambia o viene sostituito.
4. **Test.** Ampliare copertura di dati SNMP, riavvio, aggiornamenti parziali, più NAS, recovery, opzioni e storico/statistiche. Mantenere i job HA 2026.10 e 2026.11 e aggiungere i test completi di 2026.11 quando il relativo framework compatibile è disponibile; monitorare la beta senza trattare un job non eseguito come compatibilità dimostrata.

Criterio di uscita: modifica dei parametri senza perdere entità; recupero verificato dopo errore SNMP; test ripetibili e nessun blocco dell'event loop rilevato.

## Fase 3 — Salute di volumi e dischi

**Fattibilità osservata sul NAS dell'utente:** la MIB ASUSTOR espone sei righe disco con nome, modello, tipo, stato, temperatura e dimensione; il campo SMART è valorizzato per quattro e vuoto per due. Espone anche due volumi: Volume1 RAID1 e Volume2 RAID5, entrambi con stato `healthy` durante la lettura.

1. **Volumi:** aggiungere tipo RAID e stato, con gestione delle fasi di ricostruzione e degli stati sconosciuti; evitare duplicazioni dei sensori di spazio già esistenti.
2. **Dischi:** aggiungere stato, temperatura e stato SMART quando disponibile; rappresentare `Idle` come stato riportato dal NAS, senza dedurre automaticamente un guasto o il significato esatto. Dati statici quali modello e tipo possono diventare attributi o entità diagnostiche in base alle convenzioni HA.
3. **Compatibilità MIB:** rilevare e testare versioni ADM/MIB diverse; le colonne SMART/temperatura sono diverse nella documentazione ADM 5.1 rispetto a guide precedenti. Non assumere che lo stesso OID abbia sempre lo stesso significato. Non esporre un dato quando il suo significato non è verificato.
4. **Identità e ciclo di vita:** gestire aggiunta, rimozione e sostituzione dischi senza confondere slot e disco; verificare impatto del polling sullo standby dei dischi prima di dichiararlo innocuo.

Limite attuale: nessuna prova che la MIB esponga mappa dischi→array, percentuale/tempo di rebuild o tutti i valori SMART dettagliati. Queste funzioni richiedono ulteriore verifica su modelli/firmware.

Criterio di uscita: sensori verificati contro ADM su hardware reale, stati sconosciuti e valori mancanti gestiti correttamente; nessuna promessa su metriche non esposte.

## Fase 4 — Rete e sicurezza

1. **Interfacce di rete:** per interfacce selezionabili, stato e traffico in ingresso/uscita tramite contatori IF-MIB a 64 bit, con corretta gestione di riavvii, reset/overflow, unità e intervallo di campionamento. Il NAS osservato espone 51 interfacce, incluse bridge e virtuali: filtrare/selezionare per evitare un'esplosione di entità e doppio conteggio. Validare `eth0`/`eth1` e configurazioni particolari con dati reali.
2. **SNMPv3:** ASUSTOR documenta SNMPv3 ma i protocolli di autenticazione e cifratura realmente disponibili devono essere verificati su ADM e su più versioni. Progettare setup protetto con opzioni coerenti con il NAS, nessun segreto nei log o nella diagnostica e test per credenziali errate. La verifica pratica richiede una configurazione v3 autorizzata; non cambiare quella attuale senza coordinamento.

Criterio di uscita: contatori e stati coerenti con il NAS, interfacce virtuali gestibili; SNMPv3 testato effettivamente con le combinazioni dichiarate supportate.

## Fonti

- [Documentazione Home Assistant: Diagnostics](https://contributors.home-assistant.io/core/integrations/diagnostics/)
- [Documentazione Home Assistant: Repairs](https://contributors.home-assistant.io/core/integrations/repairs/)
- [Riconfigurazione e riautenticazione](https://contributors.home-assistant.io/core/integrations/reauth-reconfigure/)
- [ASUSTOR NAS MIB Guide](https://www.asustor.com/en/online/College_topic?topic=271)
- [ASUSTOR SNMP](https://www.asustor.com/online/online_help?id=27&lan=en)
