import flet as ft
from database.DAO import DAO


class Controller:

    def __init__(self, view, model):
        self._view = view
        self._model = model

    def fillDDGeneri(self):
        """
        Popola il dropdown dei generi.

        Il dropdown deve mostrare il nome del genere,
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
        Gestisce il pulsante Crea Grafo.

        Il Controller:
        - legge il genere scelto
        - valida l'input
        - chiama il Model
        - stampa il risultato
        - popola il dropdown dei clienti

        Non fa query.
        Non crea archi.
        Non calcola pesi.
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

        cliente, influenza = self._model.getClientePiuInfluente()

        if cliente is not None:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"Cliente più influente: {cliente}, influenza {influenza:.2f}",
                    color="blue",
                    weight="bold"
                )
            )

        self._view.txt_result.controls.append(
            ft.Text("\nTop 5 archi:", weight="bold")
        )

        for u, v, peso in self._model.getTopEdges(5):
            self._view.txt_result.controls.append(
                ft.Text(f"{u} -> {v}: {peso:.2f}")
            )

        # Dopo aver creato il grafo, popolo il dropdown clienti
        # con i nodi effettivamente presenti nel grafo.
        self._view._ddCliente.options.clear()

        for cliente in self._model.getNodi():
            self._view._ddCliente.options.append(
                ft.dropdown.Option(
                    key=str(cliente.CustomerId),
                    text=str(cliente)
                )
            )

        self._view._ddCliente.disabled = False

        self._view.update_page()
