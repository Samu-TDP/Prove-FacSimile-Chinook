import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi del Model.

        _graph:
        grafo orientato e pesato.

        _idMap:
        dizionario CustomerId -> oggetto Customer.
        Serve perché il DAO mi restituisce archi come ID,
        ma NetworkX lavora con gli oggetti Customer come nodi.

        _spese:
        dizionario CustomerId -> spesa totale nel genere selezionato.
        Serve per orientare e pesare gli archi.
        """

        self._graph = nx.DiGraph()
        self._idMap = {}
        self._spese = {}

    def buildGraph(self, genre_id):
        """
        Costruisce il grafo della Prova 2.

        Pattern meccanico:

        1. Resetto il grafo.
        2. Carico i nodi dal DAO.
        3. Creo idMap.
        4. Carico il dizionario delle spese.
        5. Carico gli archi grezzi.
        6. Per ogni arco grezzo:
           - recupero i due Customer dalla idMap
           - recupero le due spese
           - calcolo il peso
           - decido il verso
           - aggiungo l'arco al grafo.
        """

        self._graph.clear()
        self._idMap.clear()
        self._spese.clear()

        # 1. Carico i nodi
        clienti = DAO.getAllNodes(genre_id)

        # 2. Aggiungo i nodi al grafo e alla idMap
        for cliente in clienti:
            self._graph.add_node(cliente)
            self._idMap[cliente.CustomerId] = cliente

        # 3. Carico la spesa di ogni cliente
        self._spese = DAO.getSpesaClienti(genre_id)

        # 4. Carico le relazioni grezze degli archi
        archi_grezzi = DAO.getAllEdges(genre_id)

        # 5. Costruisco davvero gli archi del grafo
        for arco in archi_grezzi:

            id1 = arco.id1
            id2 = arco.id2

            # Controllo difensivo:
            # se per qualche motivo uno dei due clienti non è tra i nodi,
            # salto quell'arco.
            if id1 not in self._idMap or id2 not in self._idMap:
                continue

            cliente1 = self._idMap[id1]
            cliente2 = self._idMap[id2]

            spesa1 = self._spese.get(id1, 0)
            spesa2 = self._spese.get(id2, 0)

            # Peso richiesto dalla traccia:
            # spesa(A) + spesa(B)
            peso = spesa1 + spesa2

            # Verso richiesto dalla traccia:
            # dal cliente con spesa maggiore a quello con spesa minore.
            if spesa1 > spesa2:
                self._graph.add_edge(
                    cliente1,
                    cliente2,
                    weight=peso
                )

            elif spesa2 > spesa1:
                self._graph.add_edge(
                    cliente2,
                    cliente1,
                    weight=peso
                )

            else:
                # In caso di parità, aggiungo entrambi gli archi.
                self._graph.add_edge(
                    cliente1,
                    cliente2,
                    weight=peso
                )

                self._graph.add_edge(
                    cliente2,
                    cliente1,
                    weight=peso
                )

        return self.getGraphDetails()

    def getGraphDetails(self):
        """
        Restituisce:
        - numero di nodi
        - numero di archi
        """

        return self._graph.number_of_nodes(), self._graph.number_of_edges()

    def getNodi(self):
        """
        Restituisce tutti i nodi del grafo ordinati per cognome e nome.

        Serve per popolare il dropdown clienti.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda c: (c.LastName, c.FirstName)
        )

    def getNodeById(self, customer_id):
        """
        Dato un CustomerId, restituisce l'oggetto Customer corrispondente.
        """

        return self._idMap.get(customer_id, None)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi ordinati per peso decrescente.

        Ogni elemento è:
        (cliente_partenza, cliente_arrivo, peso)
        """

        result = []

        for u, v, data in self._graph.edges(data=True):
            peso = data["weight"]
            result.append((u, v, peso))

        result.sort(key=lambda x: x[2], reverse=True)

        return result[:n]

    def getClientePiuInfluente(self):
        """
        Influenza = somma pesi archi uscenti - somma pesi archi entranti.

        In un grafo orientato:
        - out_degree(cliente, weight="weight") somma i pesi uscenti
        - in_degree(cliente, weight="weight") somma i pesi entranti
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_cliente = None
        best_influenza = -float("inf")

        for cliente in self._graph.nodes:

            peso_uscente = self._graph.out_degree(cliente, weight="weight")
            peso_entrante = self._graph.in_degree(cliente, weight="weight")

            influenza = peso_uscente - peso_entrante

            if influenza > best_influenza:
                best_influenza = influenza
                best_cliente = cliente

        return best_cliente, best_influenza
