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

    def fillDDClienti(self):
        """
        Popola il dropdown dei clienti.

        Nel dropdown:
            text = nome e cognome del cliente
            key = CustomerId

        Esempio:
            text = "Luis Goncalves"
            key = "1"

        Quando l'utente seleziona il cliente,
        dal dropdown recupero CustomerId.
        """

        clienti = DAO.getAllCustomers()

        self._view._ddCliente.options.clear()

        for cliente in clienti:
            self._view._ddCliente.options.append(
                ft.dropdown.Option(
                    key=str(cliente.CustomerId),
                    text=str(cliente)
                )
            )

        self._view.update_page()

    def handleCreaGrafo(self, e):
        """
        Gestisce il bottone Crea Grafo.

        Flusso:
            1. pulisco l'area di output;
            2. leggo il cliente selezionato;
            3. leggo K;
            4. valido gli input;
            5. chiamo model.buildGraph(customer_id, k);
            6. stampo numero nodi e archi;
            7. stampo invoice più influente;
            8. stampo top 5 archi;
            9. popolo dropdown invoice per la ricorsione.
        """

        self._view.txt_result.controls.clear()

        # ------------------------------------------------------------
        # 1. Lettura cliente
        # ------------------------------------------------------------

        cliente_scelto = self._view._ddCliente.value

        if cliente_scelto is None:
            self._view.create_alert("Seleziona un cliente.")
            return

        try:
            customer_id = int(cliente_scelto)
        except ValueError:
            self._view.create_alert("Cliente selezionato non valido.")
            return

        # ------------------------------------------------------------
        # 2. Lettura K
        # ------------------------------------------------------------

        k_string = self._view._txtK.value

        if k_string is None or k_string.strip() == "":
            self._view.create_alert("Inserisci un valore K.")
            return

        try:
            k = int(k_string)
        except ValueError:
            self._view.create_alert("K deve essere un numero intero.")
            return

        if k <= 0:
            self._view.create_alert("K deve essere maggiore di zero.")
            return

        # ------------------------------------------------------------
        # 3. Creazione grafo
        # ------------------------------------------------------------

        try:
            n_nodi, n_archi = self._model.buildGraph(
                customer_id=customer_id,
                k=k
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la creazione del grafo: {ex}")
            return

        # ------------------------------------------------------------
        # 4. Stampa risultati del punto 1
        # ------------------------------------------------------------

        self._view.txt_result.controls.append(
            ft.Text("Grafo correttamente creato", color="green", weight="bold")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di nodi: {n_nodi}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di archi: {n_archi}")
        )

        invoice, influenza = self._model.getInvoicePiuInfluente()

        if invoice is not None:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"Invoice più influente: {invoice}, influenza {influenza:.2f}",
                    color="blue",
                    weight="bold"
                )
            )

        self._view.txt_result.controls.append(
            ft.Text("\nTop 5 archi:", weight="bold")
        )

        top_archi = self._model.getTopEdges(5)

        for u, v, peso in top_archi:
            self._view.txt_result.controls.append(
                ft.Text(f"{u} -> {v}: {peso:.2f}")
            )

        # ------------------------------------------------------------
        # 5. Popolo dropdown invoice
        # ------------------------------------------------------------
        #
        # Lo popolo dopo aver creato il grafo,
        # perché deve contenere solo le invoice del cliente selezionato.

        self._view._ddInvoice.options.clear()

        for invoice in self._model.getNodi():
            self._view._ddInvoice.options.append(
                ft.dropdown.Option(
                    key=str(invoice.InvoiceId),
                    text=(
                        f"{invoice} - "
                        f"data {invoice.InvoiceDate.strftime('%Y-%m-%d')} - "
                        f"totale {invoice.Total:.2f}"
                    )
                )
            )

        self._view._ddInvoice.disabled = False

        self._view.update_page()

    def handleRicorsione(self, e):
        """
        Gestisce il bottone Ricorsione.

        Flusso:
            1. controllo che il grafo esista;
            2. leggo la invoice di partenza;
            3. recupero l'oggetto Invoice dal Model;
            4. chiamo model.cercaCamminoDecrescente(invoice_start);
            5. stampo il cammino trovato.
        """

        # ------------------------------------------------------------
        # 1. Controllo che il grafo sia stato creato
        # ------------------------------------------------------------

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        # ------------------------------------------------------------
        # 2. Leggo invoice selezionata
        # ------------------------------------------------------------

        invoice_scelta = self._view._ddInvoice.value

        if invoice_scelta is None:
            self._view.create_alert("Seleziona una invoice di partenza.")
            return

        try:
            invoice_id = int(invoice_scelta)
        except ValueError:
            self._view.create_alert("Invoice selezionata non valida.")
            return

        # ------------------------------------------------------------
        # 3. Recupero oggetto Invoice dal Model
        # ------------------------------------------------------------

        invoice_start = self._model.getNodeById(invoice_id)

        if invoice_start is None:
            self._view.create_alert("La invoice selezionata non è presente nel grafo.")
            return

        # ------------------------------------------------------------
        # 4. Chiamo la ricorsione
        # ------------------------------------------------------------

        try:
            cammino, peso_totale = self._model.cercaCamminoDecrescente(
                invoice_start
            )
        except Exception as ex:
            self._view.create_alert(f"Errore durante la ricorsione: {ex}")
            return

        # ------------------------------------------------------------
        # 5. Stampo risultato
        # ------------------------------------------------------------

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
            ft.Text(f"Invoice di partenza: {invoice_start}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero nodi nel cammino: {len(cammino)}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero archi nel cammino: {len(cammino) - 1}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Peso totale del cammino: {peso_totale:.2f}")
        )

        self._view.txt_result.controls.append(
            ft.Text("\nSequenza invoice:", weight="bold")
        )

        for invoice in cammino:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"{invoice} - "
                    f"data {invoice.InvoiceDate.strftime('%Y-%m-%d')} - "
                    f"totale {invoice.Total:.2f}"
                )
            )

        self._view.txt_result.controls.append(
            ft.Text("\nDettaglio archi:", weight="bold")
        )

        dettagli = self._model.getDettagliCammino(cammino)

        for u, v, peso in dettagli:
            self._view.txt_result.controls.append(
                ft.Text(f"{u} -> {v} | peso: {peso:.2f}")
            )

        self._view.update_page()
