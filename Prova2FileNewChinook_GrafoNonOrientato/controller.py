import flet as ft
from database.DAO import DAO


class Controller:

    def __init__(self, view, model):
        """
        Il Controller collega View e Model.

        Non fa query SQL.
        Non costruisce il grafo.
        Non fa ricorsione.

        Compiti:
            - leggere input dalla View;
            - validare input;
            - chiamare metodi del Model;
            - stampare risultati nella View.
        """

        self._view = view
        self._model = model

    def fillDDMediaType(self):
        """
        Popola il dropdown MediaType.

        Il dropdown mostra:
            nome del MediaType

        Ma salva come key:
            MediaTypeId

        Esempio:
            text = "Purchased AAC audio file"
            key = "4"

        Quando l'utente seleziona un'opzione, nel codice recupero
        il MediaTypeId.
        """

        media_types = DAO.getAllMediaTypes()

        self._view._ddMediaType.options.clear()

        for media_type in media_types:
            self._view._ddMediaType.options.append(
                ft.dropdown.Option(
                    key=str(media_type.MediaTypeId),
                    text=media_type.Name
                )
            )

        self._view.update_page()

    def handleCreaGrafo(self, e):
        """
        Gestisce il pulsante Crea grafo.

        Flusso:
            1. pulisco output;
            2. leggo MediaType;
            3. leggo durata minima in minuti;
            4. valido gli input;
            5. converto minuti in millisecondi;
            6. chiamo model.buildGraph();
            7. stampo numero nodi e archi;
            8. popolo dropdown Start Composer.
        """

        self._view.txt_result.controls.clear()

        # ------------------------------------------------------------
        # 1. Lettura MediaType
        # ------------------------------------------------------------

        media_type_value = self._view._ddMediaType.value

        if media_type_value is None:
            self._view.create_alert("Seleziona un MediaType.")
            return

        try:
            media_type_id = int(media_type_value)
        except ValueError:
            self._view.create_alert("MediaType selezionato non valido.")
            return

        # ------------------------------------------------------------
        # 2. Lettura durata minima
        # ------------------------------------------------------------

        durata_string = self._view._txtDurata.value

        if durata_string is None or durata_string.strip() == "":
            self._view.create_alert("Inserisci una durata minima in minuti.")
            return

        try:
            durata_minuti = float(durata_string)
        except ValueError:
            self._view.create_alert("La durata deve essere un numero.")
            return

        if durata_minuti < 0:
            self._view.create_alert("La durata minima deve essere maggiore o uguale a zero.")
            return

        # La tabella Track salva la durata in millisecondi.
        durata_ms = int(durata_minuti * 60 * 1000)

        # ------------------------------------------------------------
        # 3. Creazione grafo
        # ------------------------------------------------------------

        try:
            n_nodi, n_archi = self._model.buildGraph(
                media_type_id=media_type_id,
                durata_ms=durata_ms
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la creazione del grafo: {ex}")
            return

        # ------------------------------------------------------------
        # 4. Stampa output base
        # ------------------------------------------------------------

        self._view.txt_result.controls.append(
            ft.Text("Grafo correttamente creato.", color="green", weight="bold")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero nodi: {n_nodi}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero archi: {n_archi}")
        )

        # ------------------------------------------------------------
        # 5. Popolo dropdown Start Composer
        # ------------------------------------------------------------
        #
        # Lo popolo dopo aver creato il grafo,
        # perché deve contenere solo i compositori presenti nel grafo corrente.

        self._view._ddStartComposer.options.clear()

        for compositore in self._model.getNodi():
            self._view._ddStartComposer.options.append(
                ft.dropdown.Option(
                    key=compositore.Name,
                    text=str(compositore)
                )
            )

        self._view._ddStartComposer.disabled = False

        self._view.update_page()

    def handleStampaDettagli(self, e):
        """
        Gestisce il pulsante Stampa dettagli.

        La traccia chiede:
            - componente connessa maggiore;
            - nodi della componente ordinati per somma pesi incidenti
              in ordine decrescente.

        Non serve fare query.
        Tutto si calcola sul grafo già creato.
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        try:
            dimensione, dettagli = self._model.getDettagliComponenteMaggiore()
        except Exception as ex:
            self._view.create_alert(f"Errore durante il calcolo dei dettagli: {ex}")
            return

        self._view.txt_result.controls.append(
            ft.Text("\nStampa dettagli:", weight="bold")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Componente connessa maggiore: {dimensione} nodi")
        )

        for compositore, somma_pesi in dettagli:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"{compositore} - somma pesi incidenti = {somma_pesi}"
                )
            )

        self._view.update_page()

    def handleCercaPercorso(self, e):
        """
        Gestisce il pulsante Cerca percorso.

        La traccia chiede:
            - selezionare Start Composer;
            - cercare un cammino di peso massimo;
            - non ripetere nodi;
            - attraversare archi con pesi strettamente crescenti;
            - stampare nodi, pesi attraversati e peso totale.
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        # ------------------------------------------------------------
        # 1. Lettura Start Composer
        # ------------------------------------------------------------

        start_value = self._view._ddStartComposer.value

        if start_value is None:
            self._view.create_alert("Seleziona un compositore di partenza.")
            return

        start = self._model.getNodeById(start_value)

        if start is None:
            self._view.create_alert("Il compositore selezionato non è presente nel grafo.")
            return

        # ------------------------------------------------------------
        # 2. Chiamo la ricorsione
        # ------------------------------------------------------------

        try:
            cammino, peso_totale = self._model.cercaCamminoCrescentePesoMassimo(
                start
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la ricerca del percorso: {ex}")
            return

        # ------------------------------------------------------------
        # 3. Stampa risultato
        # ------------------------------------------------------------

        self._view.txt_result.controls.append(
            ft.Text("\nCammino ottimo trovato:", color="green", weight="bold")
        )

        if len(cammino) == 0:
            self._view.txt_result.controls.append(
                ft.Text("Nessun percorso valido trovato.")
            )
            self._view.update_page()
            return

        dettagli = self._model.getDettagliCammino(cammino)

        # Stampa compatta:
        # A --(3)--> B --(4)--> C
        testo_percorso = str(cammino[0])

        for u, v, peso in dettagli:
            testo_percorso += f" --({peso})--> {v}"

        self._view.txt_result.controls.append(
            ft.Text(testo_percorso)
        )

        pesi_attraversati = []

        for u, v, peso in dettagli:
            pesi_attraversati.append(str(peso))

        if len(pesi_attraversati) > 0:
            self._view.txt_result.controls.append(
                ft.Text(f"Pesi attraversati: {', '.join(pesi_attraversati)}")
            )

        self._view.txt_result.controls.append(
            ft.Text(f"Peso totale percorso = {peso_totale}")
        )

        self._view.update_page()
