import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo orientato e pesato.
            Uso nx.DiGraph() perché il verso dipende dal fatturato.

        _idMap:
            dizionario EmployeeId -> oggetto Employee.
            Serve perché il DAO restituisce archi come coppie di ID,
            mentre NetworkX lavora con gli oggetti Employee.

        _fatturato:
            dizionario EmployeeId -> fatturato supportato.
            Serve per calcolare peso e verso degli archi.

        _bestPath:
            miglior cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior cammino trovato.
        """

        self._graph = nx.DiGraph()
        self._idMap = {}
        self._fatturato = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, country):
        """
        Costruisce il grafo della PROVA 11.

        Pattern logico:

        1. reset grafo e strutture dati;
        2. carico i nodi dal DAO;
        3. aggiungo i nodi al grafo;
        4. creo idMap EmployeeId -> Employee;
        5. carico il fatturato supportato;
        6. carico gli archi grezzi;
        7. per ogni arco grezzo:
            - recupero i due dipendenti;
            - recupero i due fatturati;
            - calcolo peso = fatturato1 + fatturato2;
            - decido il verso;
            - aggiungo arco orientato.
        """

        self._graph.clear()
        self._idMap.clear()
        self._fatturato.clear()

        # ------------------------------------------------------------
        # 1. Carico i nodi
        # ------------------------------------------------------------

        employees = DAO.getAllNodes(country)

        for employee in employees:
            self._graph.add_node(employee)
            self._idMap[employee.EmployeeId] = employee

        # ------------------------------------------------------------
        # 2. Carico il fatturato per dipendente
        # ------------------------------------------------------------

        self._fatturato = DAO.getFatturatoEmployee(country)

        # ------------------------------------------------------------
        # 3. Carico gli archi grezzi
        # ------------------------------------------------------------

        archi_grezzi = DAO.getAllEdges(country)

        # ------------------------------------------------------------
        # 4. Costruisco gli archi veri del grafo
        # ------------------------------------------------------------

        for arco in archi_grezzi:

            id1 = arco.id1
            id2 = arco.id2

            # Controllo difensivo:
            # un arco ha senso solo se entrambi gli EmployeeId
            # sono effettivamente nodi del grafo.
            if id1 not in self._idMap or id2 not in self._idMap:
                continue

            employee1 = self._idMap[id1]
            employee2 = self._idMap[id2]

            fatturato1 = self._fatturato.get(id1, 0)
            fatturato2 = self._fatturato.get(id2, 0)

            # Peso richiesto dalla traccia:
            # fatturato(A) + fatturato(B)
            peso = fatturato1 + fatturato2

            # Verso richiesto:
            # dipendente con fatturato maggiore -> dipendente con fatturato minore.
            if fatturato1 > fatturato2:

                self._graph.add_edge(
                    employee1,
                    employee2,
                    weight=peso
                )

            elif fatturato2 > fatturato1:

                self._graph.add_edge(
                    employee2,
                    employee1,
                    weight=peso
                )

            else:
                # In caso di parità, inserisco entrambi gli archi.
                self._graph.add_edge(
                    employee1,
                    employee2,
                    weight=peso
                )

                self._graph.add_edge(
                    employee2,
                    employee1,
                    weight=peso
                )

        return self.getGraphDetails()

    def getGraphDetails(self):
        """
        Restituisce:
            numero di nodi
            numero di archi
        """

        return self._graph.number_of_nodes(), self._graph.number_of_edges()

    def hasGraph(self):
        """
        Serve al Controller per controllare se il grafo è già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    def getNodi(self):
        """
        Restituisce i dipendenti presenti nel grafo,
        ordinati per cognome e nome.

        Serve per popolare il dropdown Employee.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda e: (e.LastName, e.FirstName)
        )

    def getNodeById(self, employee_id):
        """
        Dato un EmployeeId, restituisce l'oggetto Employee corrispondente.
        """

        return self._idMap.get(employee_id, None)

    def getFatturato(self, employee):
        """
        Restituisce il fatturato supportato da un dipendente.
        """

        return self._fatturato.get(employee.EmployeeId, 0)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi con peso maggiore.

        Ogni elemento è:
            (employee_partenza, employee_arrivo, peso)
        """

        result = []

        for u, v, data in self._graph.edges(data=True):
            peso = data["weight"]
            result.append((u, v, peso))

        result.sort(
            key=lambda x: x[2],
            reverse=True
        )

        return result[:n]

    def getEmployeePiuInfluente(self):
        """
        Calcola il dipendente più influente.

        Formula:
            influenza = somma pesi archi uscenti - somma pesi archi entranti

        In NetworkX:
            out_degree(employee, weight="weight")
                somma i pesi degli archi uscenti.

            in_degree(employee, weight="weight")
                somma i pesi degli archi entranti.

        Questa misura ha senso solo perché il grafo è orientato.
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_employee = None
        best_influenza = -float("inf")

        for employee in self._graph.nodes:

            peso_uscente = self._graph.out_degree(
                employee,
                weight="weight"
            )

            peso_entrante = self._graph.in_degree(
                employee,
                weight="weight"
            )

            influenza = peso_uscente - peso_entrante

            if influenza > best_influenza:
                best_influenza = influenza
                best_employee = employee

        return best_employee, best_influenza

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoDecrescente(self, employee_start):
        """
        Punto 2 della PROVA 11.

        Traccia:
            selezionato un dipendente di partenza, cercare un cammino
            semplice massimo tale che i pesi degli archi siano
            strettamente decrescenti.

        Interpretazione operativa:
            - criterio principale: cammino con più nodi;
            - criterio secondario: a parità di nodi, peso totale maggiore.

        Vincoli:
            1. si parte dal dipendente scelto;
            2. si rispettano i versi degli archi;
            3. un dipendente non può comparire due volte;
            4. i pesi degli archi devono essere strettamente decrescenti.
        """

        self._bestPath = []
        self._bestPeso = 0

        if employee_start is None:
            return [], 0

        if employee_start not in self._graph.nodes:
            return [], 0

        parziale = [employee_start]

        self._ricorsioneDecrescente(
            parziale=parziale,
            ultimo_peso=float("inf"),
            peso_attuale=0
        )

        return self._bestPath, self._bestPeso

    def _ricorsioneDecrescente(self, parziale, ultimo_peso, peso_attuale):
        """
        Funzione ricorsiva vera.

        Stato:
            parziale:
                cammino corrente.

            ultimo_peso:
                peso dell'ultimo arco attraversato.

            peso_attuale:
                somma dei pesi degli archi nel cammino corrente.

        Pattern da memorizzare:
            aggiorno best;
            prendo ultimo nodo;
            ciclo sui successori;
            controllo vincoli;
            append;
            ricorsione;
            pop.
        """

        # ------------------------------------------------------------
        # 1. Aggiorno la soluzione migliore
        # ------------------------------------------------------------

        if len(parziale) > len(self._bestPath):
            self._bestPath = list(parziale)
            self._bestPeso = peso_attuale

        elif len(parziale) == len(self._bestPath):
            if peso_attuale > self._bestPeso:
                self._bestPath = list(parziale)
                self._bestPeso = peso_attuale

        # ------------------------------------------------------------
        # 2. Espando il cammino
        # ------------------------------------------------------------

        ultimo_nodo = parziale[-1]

        # Grafo orientato:
        # devo seguire solo gli archi uscenti.
        for vicino in self._graph.successors(ultimo_nodo):

            # Vincolo cammino semplice:
            # non posso ripetere un dipendente.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Vincolo:
            # pesi strettamente decrescenti.
            if peso_arco < ultimo_peso:

                # Scelta
                parziale.append(vicino)

                # Ricorsione
                self._ricorsioneDecrescente(
                    parziale=parziale,
                    ultimo_peso=peso_arco,
                    peso_attuale=peso_attuale + peso_arco
                )

                # Backtracking
                parziale.pop()

    def getDettagliCammino(self, cammino):
        """
        Trasforma un cammino in dettagli stampabili.

        Input:
            [Employee A, Employee B, Employee C]

        Output:
            [
                (Employee A, Employee B, peso_A_B),
                (Employee B, Employee C, peso_B_C)
            ]
        """

        dettagli = []

        for i in range(len(cammino) - 1):

            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
