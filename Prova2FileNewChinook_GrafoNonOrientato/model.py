import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo semplice, non orientato e pesato.
            Uso nx.Graph(), perché la traccia dice grafo non orientato.

        _idMap:
            dizionario:
                nome_compositore -> oggetto Composer

            Serve perché:
                - il DAO restituisce gli archi usando i nomi dei compositori;
                - NetworkX usa invece gli oggetti Composer come nodi.

        _bestPath:
            miglior cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior cammino.
        """

        self._graph = nx.Graph()
        self._idMap = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, media_type_id, durata_ms):
        """
        Costruisce il grafo della Prova 2.

        Input:
            media_type_id:
                MediaType scelto dall'utente.

            durata_ms:
                durata minima convertita in millisecondi.

        Nodi:
            compositori dei brani validi.

        Archi:
            due compositori sono collegati se compaiono insieme
            in almeno una playlist.

        Peso:
            numero di playlist distinte comuni.
            In questa versione il peso arriva già dal DAO.

        Pattern meccanico:
            1. reset grafo e idMap;
            2. carico i nodi dal DAO;
            3. aggiungo i nodi al grafo;
            4. creo idMap;
            5. carico gli archi già pesati dal DAO;
            6. aggiungo gli archi al grafo.
        """

        self._graph.clear()
        self._idMap.clear()

        # ------------------------------------------------------------
        # 1. Carico i nodi dal DAO
        # ------------------------------------------------------------

        compositori = DAO.getAllNodes(
            media_type_id=media_type_id,
            durata_ms=durata_ms
        )

        # ------------------------------------------------------------
        # 2. Aggiungo i nodi al grafo e alla idMap
        # ------------------------------------------------------------

        for compositore in compositori:
            self._graph.add_node(compositore)
            self._idMap[compositore.Name] = compositore

        # ------------------------------------------------------------
        # 3. Carico gli archi già pesati dal DAO
        # ------------------------------------------------------------

        archi = DAO.getAllEdges(
            media_type_id=media_type_id,
            durata_ms=durata_ms
        )

        # ------------------------------------------------------------
        # 4. Aggiungo gli archi al grafo
        # ------------------------------------------------------------

        for arco in archi:

            id1 = arco.id1
            id2 = arco.id2
            peso = arco.peso

            # Controllo difensivo:
            # se un compositore non è nei nodi, salto.
            # In teoria non dovrebbe succedere, perché getAllNodes e getAllEdges
            # usano gli stessi filtri.
            if id1 not in self._idMap:
                continue

            if id2 not in self._idMap:
                continue

            compositore1 = self._idMap[id1]
            compositore2 = self._idMap[id2]

            # Grafo non orientato:
            # compositore1-compositore2 è lo stesso arco di compositore2-compositore1.
            self._graph.add_edge(
                compositore1,
                compositore2,
                weight=peso
            )

        return self.getGraphDetails()

    def getGraphDetails(self):
        """
        Restituisce:
            numero nodi
            numero archi
        """

        return self._graph.number_of_nodes(), self._graph.number_of_edges()

    def hasGraph(self):
        """
        Serve al Controller per controllare se il grafo è già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    def getNodi(self):
        """
        Restituisce tutti i compositori presenti nel grafo,
        ordinati alfabeticamente.

        Serve per popolare il dropdown Start Composer.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda compositore: compositore.Name
        )

    def getNodeById(self, composer_name):
        """
        In questa prova non esiste un ComposerId numerico.

        L'identificativo del nodo è direttamente il nome del compositore.
        """

        return self._idMap.get(composer_name, None)

    def getDettagliComponenteMaggiore(self):
        """
        La traccia chiede, alla pressione di Stampa dettagli:

        1. identificare la componente connessa di dimensione maggiore;
        2. stampare tutti i nodi della componente;
        3. ordinare i nodi in ordine decrescente rispetto alla somma
           dei pesi degli archi incidenti.

        In un grafo non orientato:
            degree(nodo, weight="weight")

        restituisce la somma dei pesi degli archi incidenti al nodo.
        """

        if self._graph.number_of_nodes() == 0:
            return 0, []

        # nx.connected_components funziona sui grafi non orientati.
        # Restituisce insiemi di nodi.
        componenti = list(nx.connected_components(self._graph))

        # Ordino le componenti dalla più grande alla più piccola.
        componenti.sort(
            key=lambda componente: len(componente),
            reverse=True
        )

        componente_maggiore = componenti[0]

        result = []

        for compositore in componente_maggiore:

            somma_pesi_incidenti = self._graph.degree(
                compositore,
                weight="weight"
            )

            result.append(
                (compositore, somma_pesi_incidenti)
            )

        # Ordino i compositori della componente maggiore
        # per somma pesi incidenti decrescente.
        result.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return len(componente_maggiore), result

    def getTopEdges(self, n=5):
        """
        Funzione non obbligatoria per la stampa principale,
        ma utile per controllare il grafo.

        Restituisce i primi n archi con peso maggiore.
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

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoCrescentePesoMassimo(self, start):
        """
        Punto 2 della Prova 2.

        Obiettivo:
            trovare un cammino di peso massimo partendo dal compositore scelto.

        Vincoli:
            1. il cammino parte da start;
            2. il grafo è non orientato, quindi posso andare in entrambe le direzioni;
            3. un nodo non può essere attraversato più volte;
            4. i pesi degli archi attraversati devono essere strettamente crescenti;
            5. la somma dei pesi degli archi deve essere massima.

        Strategia:
            backtracking ricorsivo.

        Stato della ricorsione:
            parziale:
                lista di nodi del cammino corrente.

            ultimo_peso:
                peso dell'ultimo arco attraversato.

            peso_attuale:
                somma dei pesi degli archi attraversati finora.
        """

        self._bestPath = []
        self._bestPeso = -1

        if start is None:
            return [], 0

        if start not in self._graph.nodes:
            return [], 0

        parziale = [start]

        # I pesi degli archi sono positivi.
        # Metto ultimo_peso = -1 così il primo arco sarà sempre accettabile.
        self._ricorsioneCrescente(
            parziale=parziale,
            ultimo_peso=-1,
            peso_attuale=0
        )

        if len(self._bestPath) == 0:
            return [], 0

        return self._bestPath, self._bestPeso

    def _ricorsioneCrescente(self, parziale, ultimo_peso, peso_attuale):
        """
        Funzione ricorsiva vera.

        Pattern da memorizzare:

            1. aggiorno il best;
            2. prendo l'ultimo nodo del cammino;
            3. ciclo sui vicini;
            4. controllo che il vicino non sia già nel cammino;
            5. controllo che il peso sia strettamente crescente;
            6. append;
            7. ricorsione;
            8. pop.
        """

        # ------------------------------------------------------------
        # 1. Aggiorno la soluzione migliore
        # ------------------------------------------------------------
        #
        # Criterio principale:
        #   peso totale massimo.
        #
        # Criterio secondario:
        #   a parità di peso, tengo il cammino più lungo.

        if peso_attuale > self._bestPeso:
            self._bestPeso = peso_attuale
            self._bestPath = list(parziale)

        elif peso_attuale == self._bestPeso:
            if len(parziale) > len(self._bestPath):
                self._bestPath = list(parziale)

        # ------------------------------------------------------------
        # 2. Espando il cammino corrente
        # ------------------------------------------------------------

        ultimo_nodo = parziale[-1]

        # Grafo non orientato:
        # uso neighbors().
        for vicino in self._graph.neighbors(ultimo_nodo):

            # Vincolo:
            # il cammino deve essere semplice, quindi non ripeto nodi.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Vincolo:
            # i pesi devono essere strettamente crescenti.
            if peso_arco > ultimo_peso:

                # Scelta:
                # aggiungo il vicino al cammino.
                parziale.append(vicino)

                # Ricorsione:
                # continuo il cammino dal nuovo ultimo nodo.
                self._ricorsioneCrescente(
                    parziale=parziale,
                    ultimo_peso=peso_arco,
                    peso_attuale=peso_attuale + peso_arco
                )

                # Backtracking:
                # rimuovo il vicino per provare altri cammini.
                parziale.pop()

    def getDettagliCammino(self, cammino):
        """
        Trasforma un cammino in dettagli stampabili.

        Input:
            [A, B, C]

        Output:
            [
                (A, B, peso_A_B),
                (B, C, peso_B_C)
            ]

        Serve al Controller per stampare:
            A --(peso)--> B --(peso)--> C
        """

        dettagli = []

        for i in range(len(cammino) - 1):

            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))
