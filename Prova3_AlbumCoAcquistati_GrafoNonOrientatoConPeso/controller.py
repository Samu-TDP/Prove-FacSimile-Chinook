import flet as ft
from database.DAO import DAO


class Controller:

    def __init__(self, view, model):
        """
        Il Controller collega View e Model.

        Non deve fare query SQL.
        Non deve costruire il grafo.
        Non deve fare ricorsione.

        Deve solo:
        - leggere input dalla View
        - chiamare metodi del Model
        - stampare risultati nella View
        """

        self._view = view
        self._model = model

    def fillDDGeneri(self):
        """
        Popola il dropdown dei generi.

        Il dropdown mostra il nome del genere,
        ma come valore interno salva GenreId.
        """

        generi = DAO.getAllGeneri()

        self._view._ddGenere.options.clear()

        for genere in generi:
            self._view._ddGenere.options.append(
                ft.dropdown.Option(
                    key=str(genere.GenreId),
                    text=genere.Name
                )
            )

        self._view.update_page()

    def handleCreaGrafo(self, e):
        """
        Gestisce il bottone Crea Grafo.

        Flusso:
        1. pulisco output;
        2. leggo genere selezionato;
        3. valido input;
        4. chiamo model.buildGraph;
        5. stampo numero nodi e archi;
        6. stampo componenti connesse;
        7. stampo top 5 archi;
        8. popolo dropdown album per la ricorsione.
        """

        self._view.txt_result.controls.clear()

        genere_scelto = self._view._ddGenere.value

        if genere_scelto is None:
            self._view.create_alert("Seleziona un genere musicale.")
            return

        try:
            genre_id = int(genere_scelto)
        except ValueError:
            self._view.create_alert("Errore nella selezione del genere.")
            return

        try:
            n_nodi, n_archi = self._model.buildGraph(genre_id)
        except Exception as ex:
            self._view.create_alert(f"Errore durante la creazione del grafo: {ex}")
            return

        self._view.txt_result.controls.append(
            ft.Text("Grafo correttamente creato", color="green", weight="bold")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di nodi: {n_nodi}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di archi: {n_archi}")
        )

        num_componenti, dim_max, nodi_comp_max = self._model.getConnectedComponentsInfo()

        self._view.txt_result.controls.append(
            ft.Text(f"Numero componenti connesse: {num_componenti}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Dimensione componente maggiore: {dim_max}")
        )

        # Misura opzionale: non è nella traccia, ma sostituisce l'idea
        # di "nodo più influente" nei grafi non orientati.
        album_best, grado_pesato = self._model.getAlbumGradoPesatoMassimo()

        if album_best is not None:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"Album con grado pesato massimo: {album_best}, valore {grado_pesato}",
                    color="blue",
                    weight="bold"
                )
            )

        self._view.txt_result.controls.append(
            ft.Text("\nTop 5 archi:", weight="bold")
        )

        for u, v, peso in self._model.getTopEdges(5):
            self._view.txt_result.controls.append(
                ft.Text(f"{u} - {v}: {peso}")
            )

        # Popolo il dropdown degli album.
        self._view._ddAlbum.options.clear()

        for album in self._model.getNodi():
            self._view._ddAlbum.options.append(
                ft.dropdown.Option(
                    key=str(album.AlbumId),
                    text=str(album)
                )
            )

        self._view._ddAlbum.disabled = False

        self._view.update_page()

    def handleRicorsione(self, e):
        """
        Gestisce il bottone Cerca Percorso.

        Traccia:
        selezionato un album e un valore K,
        cercare con ricorsione il cammino semplice di peso massimo
        con al massimo K archi.

        Flusso:
        1. controllo che il grafo esista;
        2. leggo album selezionato;
        3. leggo K;
        4. valido K;
        5. recupero oggetto Album dal Model;
        6. chiamo la ricorsione nel Model;
        7. stampo cammino e dettagli.
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        album_scelto = self._view._ddAlbum.value

        if album_scelto is None:
            self._view.create_alert("Seleziona un album di partenza.")
            return

        try:
            album_id = int(album_scelto)
        except ValueError:
            self._view.create_alert("Album selezionato non valido.")
            return

        k_string = self._view._txtK.value

        if k_string is None or k_string.strip() == "":
            self._view.create_alert("Inserisci un valore K.")
            return

        try:
            k = int(k_string)
        except ValueError:
            self._view.create_alert("K deve essere un numero intero.")
            return

        if k < 0:
            self._view.create_alert("K deve essere maggiore o uguale a zero.")
            return

        album_start = self._model.getNodeById(album_id)

        if album_start is None:
            self._view.create_alert("L'album selezionato non è presente nel grafo.")
            return

        try:
            cammino, peso_totale = self._model.cercaCamminoPesoMassimo(
                album_start,
                k
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la ricorsione: {ex}")
            return

        self._view.txt_result.controls.append(
            ft.Text("\nRisultato ricorsione", color="green", weight="bold")
        )

        if len(cammino) == 0:
            self._view.txt_result.controls.append(
                ft.Text("Nessun cammino trovato.")
            )
            self._view.update_page()
            return

        self._view.txt_result.controls.append(
            ft.Text(f"Album di partenza: {album_start}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"K massimo: {k}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero nodi nel cammino: {len(cammino)}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero archi nel cammino: {len(cammino) - 1}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Peso totale del cammino: {peso_totale}")
        )

        self._view.txt_result.controls.append(
            ft.Text("\nSequenza album:", weight="bold")
        )

        for album in cammino:
            self._view.txt_result.controls.append(
                ft.Text(str(album))
            )

        self._view.txt_result.controls.append(
            ft.Text("\nDettaglio archi:", weight="bold")
        )

        dettagli = self._model.getDettagliCammino(cammino)

        for u, v, peso in dettagli:
            self._view.txt_result.controls.append(
                ft.Text(f"{u} - {v} | peso: {peso}")
            )

        self._view.update_page()
