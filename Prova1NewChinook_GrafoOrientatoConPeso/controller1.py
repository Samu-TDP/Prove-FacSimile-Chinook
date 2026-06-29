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
            - legge input dalla View;
            - valida input;
            - chiama il Model;
            - stampa risultati.
        """

        self._view = view
        self._model = model

    def fillDDCountry(self):
        """
        Popola il dropdown Country.

        Il valore salvato è direttamente il nome del Country.
        """

        countries = DAO.getAllCountries()

        self._view._ddCountry.options.clear()

        for country in countries:
            self._view._ddCountry.options.append(
                ft.dropdown.Option(
                    key=country,
                    text=country
                )
            )

        self._view.update_page()

    def fillDDAnno(self):
        """
        Popola il dropdown Anno.

        Gli anni vengono estratti dalla tabella Invoice
        con YEAR(InvoiceDate).
        """

        anni = DAO.getAllYears()

        self._view._ddAnno.options.clear()

        for anno in anni:
            self._view._ddAnno.options.append(
                ft.dropdown.Option(
                    key=str(anno),
                    text=str(anno)
                )
            )

        self._view.update_page()

    def fillDD(self):
        """
        Metodo comodo da chiamare all'avvio.

        Popola entrambi i dropdown iniziali.
        """

        self.fillDDCountry()
        self.fillDDAnno()

    def handleCreaGrafo(self, e):
        """
        Gestisce il pulsante Crea grafo.

        Flusso:
            1. pulisco output;
            2. leggo Country;
            3. leggo Anno;
            4. valido input;
            5. chiamo model.buildGraph(country, anno);
            6. stampo numero nodi e archi;
            7. popolo Start MediaType ed End MediaType.
        """

        self._view.txt_result.controls.clear()

        # ------------------------------------------------------------
        # 1. Leggo Country
        # ------------------------------------------------------------

        country = self._view._ddCountry.value

        if country is None:
            self._view.create_alert("Seleziona un Country.")
            return

        # ------------------------------------------------------------
        # 2. Leggo Anno
        # ------------------------------------------------------------

        anno_value = self._view._ddAnno.value

        if anno_value is None:
            self._view.create_alert("Seleziona un anno.")
            return

        try:
            anno = int(anno_value)
        except ValueError:
            self._view.create_alert("Anno selezionato non valido.")
            return

        # ------------------------------------------------------------
        # 3. Creo grafo
        # ------------------------------------------------------------

        try:
            n_nodi, n_archi = self._model.buildGraph(
                country=country,
                anno=anno
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la creazione del grafo: {ex}")
            return

        # ------------------------------------------------------------
        # 4. Stampo output base
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
        # 5. Popolo dropdown Start/End MediaType
        # ------------------------------------------------------------
        #
        # La traccia dice che dopo aver costruito il grafo bisogna
        # inserire nei dropdown Start ed End tutti i nodi presenti nel grafo.

        self._view._ddStartMediaType.options.clear()
        self._view._ddEndMediaType.options.clear()

        for media_type in self._model.getNodi():

            self._view._ddStartMediaType.options.append(
                ft.dropdown.Option(
                    key=str(media_type.MediaTypeId),
                    text=str(media_type)
                )
            )

            self._view._ddEndMediaType.options.append(
                ft.dropdown.Option(
                    key=str(media_type.MediaTypeId),
                    text=str(media_type)
                )
            )

        self._view._ddStartMediaType.disabled = False
        self._view._ddEndMediaType.disabled = False

        self._view.update_page()

    def handleStampaDettagli(self, e):
        """
        Gestisce il pulsante Stampa dettagli.

        La traccia chiede:
            stampare i 5 MediaType più influenti,
            ordinati per influenza decrescente.

        influenza =
            somma pesi archi uscenti - somma pesi archi entranti
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        dettagli = self._model.getTopInfluenze(5)

        self._view.txt_result.controls.append(
            ft.Text("\nStampa dettagli:", weight="bold")
        )

        for media_type, influenza in dettagli:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"{media_type} - influenza = {influenza}"
                )
            )

        self._view.update_page()

    def handleCercaPercorso(self, e):
        """
        Gestisce il pulsante Cerca percorso.

        Input:
            Start MediaType
            End MediaType
            Lunghezza cammino

        Vincoli:
            - cammino da start a end;
            - lunghezza esatta;
            - rispetto del verso degli archi;
            - nodi non ripetuti;
            - peso totale massimo.
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        # ------------------------------------------------------------
        # 1. Leggo Start MediaType
        # ------------------------------------------------------------

        start_value = self._view._ddStartMediaType.value

        if start_value is None:
            self._view.create_alert("Seleziona lo Start MediaType.")
            return

        # ------------------------------------------------------------
        # 2. Leggo End MediaType
        # ------------------------------------------------------------

        end_value = self._view._ddEndMediaType.value

        if end_value is None:
            self._view.create_alert("Seleziona l'End MediaType.")
            return

        try:
            start_id = int(start_value)
            end_id = int(end_value)
        except ValueError:
            self._view.create_alert("MediaType selezionati non validi.")
            return

        start = self._model.getNodeById(start_id)
        end = self._model.getNodeById(end_id)

        if start is None:
            self._view.create_alert("Start MediaType non presente nel grafo.")
            return

        if end is None:
            self._view.create_alert("End MediaType non presente nel grafo.")
            return

        # ------------------------------------------------------------
        # 3. Leggo lunghezza cammino
        # ------------------------------------------------------------

        lunghezza_string = self._view._txtLunghezza.value

        if lunghezza_string is None or lunghezza_string.strip() == "":
            self._view.create_alert("Inserisci la lunghezza del cammino.")
            return

        try:
            lunghezza = int(lunghezza_string)
        except ValueError:
            self._view.create_alert("La lunghezza deve essere un numero intero.")
            return

        if lunghezza <= 0:
            self._view.create_alert("La lunghezza deve essere un intero positivo.")
            return

        # ------------------------------------------------------------
        # 4. Chiamo la ricorsione
        # ------------------------------------------------------------

        try:
            cammino, peso_totale = self._model.cercaPercorsoOttimo(
                start=start,
                end=end,
                lunghezza=lunghezza
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la ricerca del percorso: {ex}")
            return

        # ------------------------------------------------------------
        # 5. Stampo risultato
        # ------------------------------------------------------------

        if len(cammino) == 0:
            self._view.txt_result.controls.append(
                ft.Text("\nNessun percorso valido trovato.")
            )

            self._view.update_page()
            return

        self._view.txt_result.controls.append(
            ft.Text("\nPercorso ottimo trovato:", color="green", weight="bold")
        )

        dettagli = self._model.getDettagliCammino(cammino)

        testo_percorso = str(cammino[0])

        for u, v, peso in dettagli:
            testo_percorso += f" --({peso})--> {v}"

        self._view.txt_result.controls.append(
            ft.Text(testo_percorso)
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Peso totale percorso = {peso_totale}")
        )

        self._view.update_page()
