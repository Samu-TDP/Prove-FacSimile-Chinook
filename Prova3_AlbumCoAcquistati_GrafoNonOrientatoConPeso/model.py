import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo non orientato e pesato.

        _idMap:
            dizionario AlbumId -> oggetto Album.
            Serve perché il DAO restituisce archi come ID,
            mentre NetworkX userà gli oggetti Album come nodi.

        _bestPath:
            miglior cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior cammino trovato.
        """

        self._graph = nx.Graph()
        self._idMap = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, genre_id):
        """
        Costruisce il grafo della PROVA 3.

        Pattern per grafo non orientato pesato:

        1. Reset del grafo e della idMap.
        2. Carico i nodi dal DAO.
        3. Aggiungo i nodi al grafo.
        4. Creo idMap AlbumId -> Album.
        5. Carico gli archi dal DAO.
        6. Per ogni arco:
           - recupero i due oggetti Album dalla idMap
           - aggiungo l'arco non orientato con weight=peso.
        """

        self._graph.clear()
        self._idMap.clear()

        # 1. Carico i nodi
        albums = DAO.getAllNodes(genre_id)

        # 2. Inserisco i nodi nel grafo e nella idMap
        for album in albums:
            self._graph.add_node(album)
            self._idMap[album.AlbumId] = album

        # 3. Carico gli archi già pesati dal DAO
        archi = DAO.getAllEdges(genre_id)

        # 4. Aggiungo gli archi al grafo
        for arco in archi:

            id1 = arco.id1
            id2 = arco.id2

            # Controllo difensivo:
            # se uno dei due album non è nei nodi, salto.
            if id1 not in self._idMap or id2 not in self._idMap:
                continue

            album1 = self._idMap[id1]
            album2 = self._idMap[id2]

            # Grafo non orientato:
            # album1-album2 e album2-album1 sono lo stesso arco.
            self._graph.add_edge(
                album1,
                album2,
                weight=arco.peso
            )

        return self.getGraphDetails()

    def getGraphDetails(self):
        """
        Restituisce:
        - numero nodi
        - numero archi
        """

        return self._graph.number_of_nodes(), self._graph.number_of_edges()

    def hasGraph(self):
        """
        Serve al Controller per controllare se il grafo è già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    def getNodi(self):
        """
        Restituisce tutti gli album del grafo ordinati per titolo.

        Serve per popolare il dropdown degli album.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda a: a.Title
        )

    def getNodeById(self, album_id):
        """
        Dato un AlbumId, restituisce l'oggetto Album corrispondente.
        """

        return self._idMap.get(album_id, None)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi di peso maggiore.

        In un grafo non orientato, ogni arco compare una sola volta
        dentro self._graph.edges(data=True).

        Ogni elemento restituito è:
        (album1, album2, peso)
        """

        result = []

        for u, v, data in self._graph.edges(data=True):
            peso = data["weight"]
            result.append((u, v, peso))

        result.sort(key=lambda x: x[2], reverse=True)

        return result[:n]

    def getConnectedComponentsInfo(self):
        """
        Calcola le componenti connesse.

        In un grafo non orientato, una componente connessa è un gruppo
        di nodi in cui ogni nodo è raggiungibile dagli altri tramite archi.

        Ritorna:
        - numero componenti
        - dimensione componente maggiore
        - lista nodi della componente maggiore
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
            key=lambda a: a.Title
        )

        return (
            len(componenti),
            len(componente_maggiore),
            nodi_componente_maggiore
        )

    def getAlbumGradoPesatoMassimo(self):
        """
        Questa funzione NON è richiesta esplicitamente dalla traccia,
        ma risponde alla tua idea di 'nodo più influente' nel caso non orientato.

        In un grafo non orientato non esistono entranti e uscenti.
        Quindi una misura sensata è:

        grado pesato = somma dei pesi degli archi incidenti al nodo.

        Esempio:
        Album A collegato a:
        - B con peso 4
        - C con peso 2

        grado pesato(A) = 4 + 2 = 6
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_album = None
        best_grado_pesato = -1

        for album in self._graph.nodes:
            grado_pesato = self._graph.degree(
                album,
                weight="weight"
            )

            if grado_pesato > best_grado_pesato:
                best_grado_pesato = grado_pesato
                best_album = album

        return best_album, best_grado_pesato

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoPesoMassimo(self, album_start, k):
        """
        Punto 2.

        Traccia:
        selezionato un album e un valore K, cercare con ricorsione
        il cammino semplice di peso massimo con al massimo K archi.

        Cammino semplice:
        ogni nodo può comparire una sola volta.

        Con al massimo K archi:
        posso usare 0, 1, 2, ..., K archi.
        Non devo per forza usarne K se non conviene o se non è possibile.

        Però i pesi sono positivi, quindi spesso il migliore userà
        il massimo numero di archi possibile, ma non lo assumiamo.

        Strategia:
        backtracking ricorsivo.

        Stato della ricorsione:
        - parziale: cammino costruito finora
        - peso_attuale: somma pesi degli archi nel cammino
        - k: massimo numero di archi consentito
        """

        self._bestPath = []
        self._bestPeso = 0

        if album_start is None:
            return [], 0

        if album_start not in self._graph.nodes:
            return [], 0

        if k < 0:
            return [], 0

        parziale = [album_start]

        self._ricorsionePesoMassimo(
            parziale=parziale,
            peso_attuale=0,
            k=k
        )

        return self._bestPath, self._bestPeso

    def _ricorsionePesoMassimo(self, parziale, peso_attuale, k):
        """
        Funzione ricorsiva vera.

        Schema classico da memorizzare:

        1. Valuto se il cammino parziale è migliore del best.
        2. Se ho già usato K archi, mi fermo.
        3. Prendo l'ultimo nodo del cammino.
        4. Esploro tutti i vicini.
        5. Se il vicino non è già nel cammino:
           - aggiungo il vicino
           - aggiorno il peso
           - chiamo la ricorsione
           - tolgo il vicino
        """

        # Numero di archi usati dal cammino corrente.
        # Se ho N nodi, ho N-1 archi.
        archi_usati = len(parziale) - 1

        # 1. Aggiorno il best.
        #
        # Criterio principale:
        # peso totale massimo.
        #
        # Criterio secondario:
        # se due cammini hanno stesso peso, tengo quello più lungo.
        if peso_attuale > self._bestPeso:
            self._bestPeso = peso_attuale
            self._bestPath = list(parziale)

        elif peso_attuale == self._bestPeso:
            if len(parziale) > len(self._bestPath):
                self._bestPath = list(parziale)

        # 2. Se ho già usato K archi, non posso espandere oltre.
        if archi_usati == k:
            return

        # 3. Prendo l'ultimo nodo.
        ultimo_nodo = parziale[-1]

        # 4. In un grafo non orientato uso neighbors().
        for vicino in self._graph.neighbors(ultimo_nodo):

            # Vincolo cammino semplice:
            # non posso ripetere nodi.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Scelta
            parziale.append(vicino)

            # Ricorsione
            self._ricorsionePesoMassimo(
                parziale=parziale,
                peso_attuale=peso_attuale + peso_arco,
                k=k
            )

            # Backtracking:
            # tolgo il nodo appena aggiunto per provare altre strade.
            parziale.pop()

    def getPesoCammino(self, cammino):
        """
        Calcola il peso totale di un cammino.

        Se cammino = [A, B, C],
        calcolo:
        peso(A-B) + peso(B-C)
        """

        totale = 0

        for i in range(len(cammino) - 1):
            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]
            totale += peso

        return totale

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
        """

        dettagli = []

        for i in range(len(cammino) - 1):
            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
