import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali.

        _graph:
            grafo orientato e pesato.

        _idMap:
            dizionario PlaylistId -> oggetto Playlist.
            Serve perché il DAO restituisce ID, mentre NetworkX usa oggetti.

        _numBrani:
            dizionario PlaylistId -> numero di brani del genere.
            Serve per decidere il verso degli archi.

        _braniPerPlaylist:
            dizionario PlaylistId -> set di TrackId.
            Serve per calcolare il peso degli archi.

        _bestPath:
            migliore cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del migliore cammino.
            Non è il criterio principale, ma lo uso in caso di parità
            tra cammini con stesso numero di nodi.
        """

        self._graph = nx.DiGraph()
        self._idMap = {}
        self._numBrani = {}
        self._braniPerPlaylist = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, genre_id):
        """
        Costruisce il grafo orientato e pesato della PROVA 5.

        Pattern meccanico:

        1. Reset.
        2. Carico i nodi.
        3. Creo idMap.
        4. Carico il numero di brani per playlist.
        5. Carico i brani contenuti in ogni playlist.
        6. Carico gli archi grezzi.
        7. Per ogni arco grezzo:
           - recupero i due nodi
           - calcolo il peso come numero di brani condivisi
           - confronto il numero di brani delle due playlist
           - decido il verso
           - aggiungo l'arco o i due archi.
        """

        self._graph.clear()
        self._idMap.clear()
        self._numBrani.clear()
        self._braniPerPlaylist.clear()

        # 1. Nodi = playlist che contengono almeno un brano del genere.
        playlists = DAO.getAllNodes(genre_id)

        for playlist in playlists:
            self._graph.add_node(playlist)
            self._idMap[playlist.PlaylistId] = playlist

        # 2. Valore del nodo per orientare l'arco.
        # PlaylistId -> numero di brani del genere.
        self._numBrani = DAO.getNumeroBraniPlaylist(genre_id)

        # 3. Brani contenuti in ogni playlist.
        # PlaylistId -> set di TrackId.
        self._braniPerPlaylist = DAO.getBraniPerPlaylist(genre_id)

        # 4. Archi grezzi: coppie di playlist che condividono almeno un brano.
        archi_grezzi = DAO.getAllEdges(genre_id)

        for arco in archi_grezzi:

            id1 = arco.id1
            id2 = arco.id2

            # Controllo difensivo:
            # un arco ha senso solo se entrambi gli ID sono nodi del grafo.
            if id1 not in self._idMap or id2 not in self._idMap:
                continue

            playlist1 = self._idMap[id1]
            playlist2 = self._idMap[id2]

            # Numero di brani del genere contenuti nelle due playlist.
            # Serve per decidere il verso.
            num1 = self._numBrani.get(id1, 0)
            num2 = self._numBrani.get(id2, 0)

            # Set di brani del genere contenuti nelle due playlist.
            brani1 = self._braniPerPlaylist.get(id1, set())
            brani2 = self._braniPerPlaylist.get(id2, set())

            # Peso richiesto dalla traccia:
            # numero di brani condivisi.
            brani_condivisi = brani1.intersection(brani2)
            peso = len(brani_condivisi)

            # Controllo difensivo:
            # getAllEdges dovrebbe già garantire peso > 0.
            # Però lo tengo per sicurezza.
            if peso == 0:
                continue

            # Verso richiesto:
            # playlist con più brani del genere -> playlist con meno brani.
            if num1 > num2:
                self._graph.add_edge(
                    playlist1,
                    playlist2,
                    weight=peso
                )

            elif num2 > num1:
                self._graph.add_edge(
                    playlist2,
                    playlist1,
                    weight=peso
                )

            else:
                # In caso di parità, aggiungo entrambi gli archi.
                self._graph.add_edge(
                    playlist1,
                    playlist2,
                    weight=peso
                )

                self._graph.add_edge(
                    playlist2,
                    playlist1,
                    weight=peso
                )

        return self.getGraphDetails()

    def getGraphDetails(self):
        """
        Restituisce:
        - numero nodi
        - numero archi
        """

        return self._graph.number_of_nodes(), self._graph.number_of_edges()

    def getNodi(self):
        """
        Restituisce i nodi del grafo.

        Serve per popolare il dropdown delle playlist
        dopo la creazione del grafo.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda p: (p.Name, p.PlaylistId)
        )

    def getNodeById(self, playlist_id):
        """
        Dato un PlaylistId, restituisce l'oggetto Playlist corrispondente.
        """

        return self._idMap.get(playlist_id, None)

    def getNumeroBrani(self, playlist):
        """
        Restituisce il numero di brani del genere selezionato
        presenti nella playlist.
        """

        return self._numBrani.get(playlist.PlaylistId, 0)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi di peso maggiore.

        Ogni elemento è:
        (playlist_partenza, playlist_arrivo, peso)
        """

        result = []

        for u, v, data in self._graph.edges(data=True):
            peso = data["weight"]
            result.append((u, v, peso))

        result.sort(key=lambda x: x[2], reverse=True)

        return result[:n]

    def getPlaylistPiuInfluente(self):
        """
        Influenza = somma pesi archi uscenti - somma pesi archi entranti.

        In un DiGraph:
        out_degree(nodo, weight="weight") somma i pesi uscenti.
        in_degree(nodo, weight="weight") somma i pesi entranti.
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_playlist = None
        best_influenza = -float("inf")

        for playlist in self._graph.nodes:

            peso_uscente = self._graph.out_degree(
                playlist,
                weight="weight"
            )

            peso_entrante = self._graph.in_degree(
                playlist,
                weight="weight"
            )

            influenza = peso_uscente - peso_entrante

            if influenza > best_influenza:
                best_influenza = influenza
                best_playlist = playlist

        return best_playlist, best_influenza

    def hasGraph(self):
        """
        Serve al Controller per controllare se il grafo è già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoDecrescente(self, playlist_start):
        """
        Punto 2.

        Traccia:
        selezionata una Playlist, trovare il cammino semplice più lungo
        tale che ogni arco successivo abbia peso strettamente decrescente.

        Cammino semplice:
        un nodo non può comparire due volte.

        Peso strettamente decrescente:
        se percorro archi con pesi:
        100, 50, 20
        va bene.

        se percorro:
        100, 100
        non va bene, perché non è strettamente decrescente.

        Strategia:
        uso backtracking ricorsivo.

        Stato della ricorsione:
        - parziale: lista dei nodi già nel cammino
        - ultimo_peso: peso dell'ultimo arco inserito

        All'inizio non ho ancora usato archi.
        Quindi imposto ultimo_peso = infinito.
        In questo modo il primo arco sarà sempre accettabile,
        perché qualunque peso reale sarà minore di infinito.
        """

        self._bestPath = []
        self._bestPeso = 0

        if playlist_start is None:
            return [], 0

        if playlist_start not in self._graph.nodes:
            return [], 0

        parziale = [playlist_start]

        self._ricorsioneDecrescente(
            parziale=parziale,
            ultimo_peso=float("inf")
        )

        return self._bestPath, self._bestPeso

    def _ricorsioneDecrescente(self, parziale, ultimo_peso):
        """
        Funzione ricorsiva vera.

        Schema classico:
        1. Valuto se il parziale corrente è migliore del best.
        2. Prendo l'ultimo nodo.
        3. Guardo i successori, cioè i nodi raggiungibili con archi uscenti.
        4. Per ogni successore:
           - controllo che non sia già nel cammino
           - controllo che il peso sia strettamente minore del precedente
           - append
           - ricorsione
           - pop
        """

        # 1. Aggiorno il best.
        #
        # Criterio principale:
        # cammino con più nodi.
        #
        # Criterio secondario:
        # se due cammini hanno stesso numero di nodi,
        # tengo quello con peso totale maggiore.
        peso_parziale = self.getPesoCammino(parziale)

        if len(parziale) > len(self._bestPath):
            self._bestPath = list(parziale)
            self._bestPeso = peso_parziale

        elif len(parziale) == len(self._bestPath):
            if peso_parziale > self._bestPeso:
                self._bestPath = list(parziale)
                self._bestPeso = peso_parziale

        # 2. Prendo l'ultimo nodo del cammino.
        ultimo_nodo = parziale[-1]

        # 3. In un grafo orientato devo seguire il verso degli archi.
        # successors(ultimo_nodo) restituisce i nodi raggiungibili
        # dagli archi uscenti da ultimo_nodo.
        for vicino in self._graph.successors(ultimo_nodo):

            # Vincolo cammino semplice:
            # non posso visitare due volte lo stesso nodo.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Vincolo della traccia:
            # ogni arco successivo deve avere peso strettamente decrescente.
            if peso_arco < ultimo_peso:

                # Scelta
                parziale.append(vicino)

                # Ricorsione
                self._ricorsioneDecrescente(
                    parziale=parziale,
                    ultimo_peso=peso_arco
                )

                # Backtracking:
                # rimuovo il nodo per provare altri cammini.
                parziale.pop()

    def getPesoCammino(self, cammino):
        """
        Calcola la somma dei pesi degli archi di un cammino.

        Se il cammino è:
        [A, B, C]

        sommo:
        peso A->B + peso B->C
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
        Trasforma un cammino in una lista di dettagli.

        Input:
        [A, B, C]

        Output:
        [
            (A, B, peso_A_B),
            (B, C, peso_B_C)
        ]

        Serve al Controller per stampare bene il risultato.
        """

        dettagli = []

        for i in range(len(cammino) - 1):
            u = cammino[i]
            v = cammino[i + 1]
            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
