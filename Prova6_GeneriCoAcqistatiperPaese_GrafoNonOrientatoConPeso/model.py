import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo non orientato e pesato.

        _idMap:
            dizionario GenreId -> oggetto Genre.

            Serve perché:
            - il DAO restituisce gli archi come id1, id2;
            - NetworkX invece userà come nodi gli oggetti Genre.

        _bestPath:
            miglior cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior cammino trovato.
        """

        self._graph = nx.Graph()
        self._idMap = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, country):
        """
        Costruisce il grafo della PROVA 6.

        Pattern per grafo non orientato pesato:

        1. reset del grafo;
        2. carico i nodi dal DAO;
        3. aggiungo i nodi al grafo;
        4. creo idMap GenreId -> Genre;
        5. carico gli archi dal DAO;
        6. per ogni arco:
            - recupero genere1 e genere2 dalla idMap;
            - aggiungo arco non orientato con peso.
        """

        self._graph.clear()
        self._idMap.clear()

        # ------------------------------------------------------------
        # 1. Caricamento nodi
        # ------------------------------------------------------------

        generi = DAO.getAllNodes(country)

        for genere in generi:
            self._graph.add_node(genere)
            self._idMap[genere.GenreId] = genere

        # ------------------------------------------------------------
        # 2. Caricamento archi già pesati dal DAO
        # ------------------------------------------------------------

        archi = DAO.getAllEdges(country)

        for arco in archi:

            id1 = arco.id1
            id2 = arco.id2
            peso = arco.peso

            # Controllo difensivo:
            # se uno dei due generi non è nei nodi del grafo,
            # non aggiungo l'arco.
            if id1 not in self._idMap or id2 not in self._idMap:
                continue

            genere1 = self._idMap[id1]
            genere2 = self._idMap[id2]

            # Grafo non orientato:
            # genere1-genere2 è uguale a genere2-genere1.
            self._graph.add_edge(
                genere1,
                genere2,
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

    def hasGraph(self):
        """
        Serve al Controller per verificare che il grafo sia già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    def getNodi(self):
        """
        Restituisce tutti i nodi del grafo ordinati per nome.

        Serve per popolare i dropdown:
        - genere iniziale
        - genere finale
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda g: g.Name
        )

    def getNodeById(self, genre_id):
        """
        Dato un GenreId, restituisce l'oggetto Genre corrispondente.
        """

        return self._idMap.get(genre_id, None)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi con peso maggiore.

        Ogni elemento restituito è:
            (genere1, genere2, peso)
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

    def getConnectedComponentsInfo(self):
        """
        Calcola:
        - numero di componenti connesse;
        - dimensione della componente maggiore;
        - nodi della componente maggiore.

        Questa informazione è richiesta dalla traccia della PROVA 6.
        """

        if self._graph.number_of_nodes() == 0:
            return 0, 0, []

        componenti = list(nx.connected_components(self._graph))

        componenti.sort(
            key=lambda c: len(c),
            reverse=True
        )

        componente_maggiore = componenti[0]

        nodi_componente_maggiore = list(componente_maggiore)

        nodi_componente_maggiore.sort(
            key=lambda g: g.Name
        )

        return (
            len(componenti),
            len(componente_maggiore),
            nodi_componente_maggiore
        )

    def getGenereGradoPesatoMassimo(self):
        """
        Funzione opzionale.

        La traccia non chiede il nodo più influente, perché il grafo
        non è orientato.

        Nei grafi non orientati non esistono archi entranti e uscenti.

        Se però vuoi una misura simile, puoi usare il grado pesato:
            somma dei pesi degli archi incidenti al nodo.
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_genere = None
        best_grado_pesato = -1

        for genere in self._graph.nodes:

            grado_pesato = self._graph.degree(
                genere,
                weight="weight"
            )

            if grado_pesato > best_grado_pesato:
                best_grado_pesato = grado_pesato
                best_genere = genere

        return best_genere, best_grado_pesato

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoPesoMassimo(self, start, end, k):
        """
        Punto 2 della PROVA 6.

        Traccia:
        l'utente seleziona genere iniziale, genere finale e inserisce K.
        Bisogna cercare il cammino di peso massimo tra i due generi
        con al massimo K archi.

        Vincoli:
        - il cammino parte da start;
        - il cammino termina in end;
        - il cammino ha al massimo K archi;
        - il cammino è semplice, quindi non ripete nodi;
        - si massimizza la somma dei pesi degli archi.

        Strategia:
        uso ricorsione/backtracking.

        Stato della ricorsione:
        - parziale: lista dei nodi nel cammino corrente;
        - peso_attuale: somma dei pesi del cammino corrente.
        """

        self._bestPath = []
        self._bestPeso = -1

        if start is None or end is None:
            return [], 0

        if start not in self._graph.nodes:
            return [], 0

        if end not in self._graph.nodes:
            return [], 0

        if k < 0:
            return [], 0

        parziale = [start]

        self._ricorsioneCamminoPesoMassimo(
            parziale=parziale,
            end=end,
            k=k,
            peso_attuale=0
        )

        if len(self._bestPath) == 0:
            return [], 0

        return self._bestPath, self._bestPeso

    def _ricorsioneCamminoPesoMassimo(self, parziale, end, k, peso_attuale):
        """
        Funzione ricorsiva vera.

        Schema:

        1. Prendo l'ultimo nodo del cammino.
        2. Se ultimo == end:
            - ho trovato un cammino valido;
            - aggiorno il best;
            - mi fermo.
        3. Se ho già usato K archi:
            - non posso espandere oltre;
            - mi fermo.
        4. Altrimenti esploro tutti i vicini.
        """

        ultimo = parziale[-1]

        archi_usati = len(parziale) - 1

        # Caso base 1:
        # sono arrivato al nodo finale.
        if ultimo == end:

            if peso_attuale > self._bestPeso:
                self._bestPeso = peso_attuale
                self._bestPath = list(parziale)

            elif peso_attuale == self._bestPeso:
                # Criterio secondario:
                # se due cammini hanno stesso peso, scelgo quello più corto.
                # Non è indispensabile, ma rende il risultato stabile.
                if len(self._bestPath) == 0 or len(parziale) < len(self._bestPath):
                    self._bestPath = list(parziale)

            return

        # Caso base 2:
        # ho già raggiunto il massimo numero di archi consentito.
        if archi_usati == k:
            return

        # Espansione:
        # in un grafo non orientato uso neighbors().
        for vicino in self._graph.neighbors(ultimo):

            # Vincolo cammino semplice:
            # non posso ripetere un genere già presente nel cammino.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo][vicino]["weight"]

            # Scelta:
            # aggiungo il vicino al cammino parziale.
            parziale.append(vicino)

            # Ricorsione:
            # continuo a cercare partendo dal nuovo ultimo nodo.
            self._ricorsioneCamminoPesoMassimo(
                parziale=parziale,
                end=end,
                k=k,
                peso_attuale=peso_attuale + peso_arco
            )

            # Backtracking:
            # rimuovo il vicino per provare un'altra strada.
            parziale.pop()

    def getDettagliCammino(self, cammino):
        """
        Trasforma un cammino in dettagli stampabili.

        Se cammino = [Rock, Metal, Latin]

        ritorna:
        [
            (Rock, Metal, peso_Rock_Metal),
            (Metal, Latin, peso_Metal_Latin)
        ]
        """

        dettagli = []

        for i in range(len(cammino) - 1):

            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
