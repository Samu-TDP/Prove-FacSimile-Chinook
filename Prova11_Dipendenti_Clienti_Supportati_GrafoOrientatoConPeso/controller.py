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
            - chiama metodi del Model;
            - stampa risultati nella View.
        """

        self._view = view
        self._model = model

    def fillDDPaesi(self):
        """
        Popola il dropdown dei paesi.

        Il dropdown mostra direttamente il nome del paese.
        Anche la key è il nome del paese.

        Esempio:
            key = "USA"
            text = "USA"
        """

        paesi = DAO.getAllPaesi()

        self._view._ddPaese.options.clear()

        for paese in paesi:
            self._view._ddPaese.options.append(
                ft.dropdown.Option(
                    key=paese,
                    text=paese
                )
            )

        self._view.update_page()

    def handleCreaGrafo(self, e):
        """
        Gestisce il bottone Crea Grafo.

        Flusso:
            1. pulisco output;
            2. leggo paese selezionato;
            3. controllo input;
            4. chiamo model.buildGraph(country);
            5. stampo numero nodi e archi;
            6. stampo dipendente più influente;
            7. stampo top 5 archi;
            8. popolo dropdown Employee per la ricorsione.
        """

        self._view.txt_result.controls.clear()

        paese = self._view._ddPaese.value

        if paese is None:
            self._view.create_alert("Seleziona un paese.")
            return

        try:
            n_nodi, n_archi = self._model.buildGraph(paese)
        except Exception as ex:
            self._view.create_alert(f"Errore durante la creazione del grafo: {ex}")
            return

        self._view.txt_result.controls.append(
            ft.Text("Grafo correttamente creato", color="green", weight="bold")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Paese selezionato: {paese}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di nodi: {n_nodi}")
        )

        self._view.txt_result.controls.append(
            ft.Text(f"Numero di archi: {n_archi}")
        )

        employee, influenza = self._model.getEmployeePiuInfluente()

        if employee is not None:
            self._view.txt_result.controls.append(
                ft.Text(
                    f"Dipendente più influente: {employee}, influenza {influenza:.2f}",
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

        # Popolo il dropdown dei dipendenti con i nodi del grafo.
        self._view._ddEmployee.options.clear()

        for employee in self._model.getNodi():

            fatturato = self._model.getFatturato(employee)

            self._view._ddEmployee.options.append(
                ft.dropdown.Option(
                    key=str(employee.EmployeeId),
                    text=f"{employee} - fatturato {fatturato:.2f}"
                )
            )

        self._view._ddEmployee.disabled = False

        self._view.update_page()

    def handleRicorsione(self, e):
        """
        Gestisce il bottone Ricorsione.

        Flusso:
            1. controllo che il grafo sia stato creato;
            2. leggo dipendente selezionato;
            3. recupero l'oggetto Employee dal Model;
            4. chiamo model.cercaCamminoDecrescente(employee_start);
            5. stampo il cammino trovato.
        """

        if not self._model.hasGraph():
            self._view.create_alert("Prima devi creare il grafo.")
            return

        employee_scelto = self._view._ddEmployee.value

        if employee_scelto is None:
            self._view.create_alert("Seleziona un dipendente di partenza.")
            return

        try:
            employee_id = int(employee_scelto)
        except ValueError:
            self._view.create_alert("Dipendente selezionato non valido.")
            return

        employee_start = self._model.getNodeById(employee_id)

        if employee_start is None:
            self._view.create_alert("Il dipendente selezionato non è presente nel grafo.")
            return

        try:
            cammino, peso_totale = self._model.cercaCamminoDecrescente(
                employee_start
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
            ft.Text(f"Dipendente di partenza: {employee_start}")
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
            ft.Text("\nSequenza dipendenti:", weight="bold")
        )

        for employee in cammino:

            fatturato = self._model.getFatturato(employee)

            self._view.txt_result.controls.append(
                ft.Text(f"{employee} - fatturato supportato {fatturato:.2f}")
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
