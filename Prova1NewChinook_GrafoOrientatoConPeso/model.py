import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo diretto e pesato.
            Uso nx.DiGraph() perché il testo dice grafo diretto.

        _idMap:
            dizionario MediaTypeId -> oggetto MediaType.
            Serve per recuperare i nodi a partire dagli ID dei dropdown.

        _vendite:
            dizionario MediaTypeId -> numero vendite.
            Serve per orientare e pesare gli archi.

        _customerMese:
            dizionario MediaTypeId -> set di coppie (CustomerId, mese).
            Serve per capire se due MediaType condividono almeno
            un cliente nello stesso mese.

        _bestPath:
            miglior percorso trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior percorso.
        """

        self._graph = nx.DiGraph()
        self._idMap = {}
        self._vendite = {}
        self._customerMese = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, country, anno):
        """
        Costruisce il grafo della Prova 1.

        Nodi:
            tutti i MediaType presenti nella tabella MediaType.

        Archi:
            due MediaType sono collegati se esiste almeno un cliente
            del Country selezionato che, nello stesso mese dell'Anno selezionato,
            ha acquistato almeno un brano appartenente a entrambi i MediaType.

        Traduzione pratica:
            per ogni MediaType costruisco un set di coppie:

                (CustomerId, mese)

            Se due MediaType hanno intersezione non vuota, allora esiste arco.

        Verso:
            dal MediaType con più vendite al MediaType con meno vendite.

        Parità:
            inserisco entrambi gli archi.

        Peso:
            vendite(MediaType1) + vendite(MediaType2)
        """

        self._graph.clear()
        self._idMap.clear()
        self._vendite.clear()
        self._customerMese.clear()

        # ------------------------------------------------------------
        # 1. Carico tutti i nodi dal DAO
        # ------------------------------------------------------------

        media_types = DAO.getAllNodes(country, anno)

        for media_type in media_types:
            self._graph.add_node(media_type)
            self._idMap[media_type.MediaTypeId] = media_type

        # ------------------------------------------------------------
        # 2. Carico le vendite dei MediaType
        # ------------------------------------------------------------

        self._vendite = DAO.getVenditeMediaType(country, anno)

        # Dizionario:
        # MediaTypeId -> set di coppie (CustomerId, mese)
        self._customerMese = {}

        for media_type in media_types:

        # Questo set conterrà tutte le coppie (cliente, mese)
        # in cui quel MediaType è stato acquistato.
        coppie_cliente_mese_del_media_type = set()

        # acquisti_per_mese è fatto così:
        # {
        #     1: [(10, 1001), (11, 1002)],
        #     2: [(10, 1003)]
        # }
        for mese in media_type.acquisti_per_mese:

          acquisti_del_mese = media_type.acquisti_per_mese[mese]

          for customer_id, invoice_line_id in acquisti_del_mese:

            # Per la condizione di arco mi interessa solo:
            # stesso cliente + stesso mese.
            coppia_cliente_mese = (customer_id, mese)

            coppie_cliente_mese_del_media_type.add(coppia_cliente_mese)

        self._customerMese[media_type.MediaTypeId] = coppie_cliente_mese_del_media_type


        # Ora confronto tutte le coppie di MediaType.
        for i in range(len(media_types)):

          media_type_1 = media_types[i]
          id1 = media_type_1.MediaTypeId

        for j in range(i + 1, len(media_types)):

          media_type_2 = media_types[j]
          id2 = media_type_2.MediaTypeId

          clienti_mesi_1 = self._customerMese.get(id1, set())
          clienti_mesi_2 = self._customerMese.get(id2, set())

          #CREO L'ARCO CON L'INTERSEZIONE
          clienti_mesi_comuni = clienti_mesi_1.intersection(clienti_mesi_2)

          # Se l'intersezione è vuota, significa:
          # nessun cliente ha comprato entrambi nello stesso mese.
          if len(clienti_mesi_comuni) == 0:
            continue

          vendite1 = self._vendite.get(id1, 0)
          vendite2 = self._vendite.get(id2, 0)

          peso = vendite1 + vendite2

          if vendite1 > vendite2:
            self._graph.add_edge(media_type_1, media_type_2, weight=peso)

          elif vendite2 > vendite1:
            self._graph.add_edge(media_type_2, media_type_1, weight=peso)

          else:
            self._graph.add_edge(media_type_1, media_type_2, weight=peso)
            self._graph.add_edge(media_type_2, media_type_1, weight=peso)

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
        Serve al Controller per verificare se il grafo è già stato creato.
        """

        return self._graph.number_of_nodes() > 0

    def getNodi(self):
        """
        Restituisce tutti i MediaType presenti nel grafo.

        Serve per popolare i dropdown Start MediaType e End MediaType.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda mt: mt.Name
        )

    def getNodeById(self, media_type_id):
        """
        Dato un MediaTypeId, restituisce l'oggetto MediaType corrispondente.
        """

        return self._idMap.get(media_type_id, None)

    def getVendite(self, media_type):
        """
        Restituisce il numero di vendite di un MediaType.
        """

        return self._vendite.get(media_type.MediaTypeId, 0)

    def getTopInfluenze(self, n=5):
        """
        La traccia chiede, alla pressione di Stampa dettagli,
        i 5 MediaType più influenti.

        Formula:
            influenza = somma pesi archi uscenti - somma pesi archi entranti

        In NetworkX:
            out_degree(nodo, weight="weight")
                somma i pesi degli archi uscenti.

            in_degree(nodo, weight="weight")
                somma i pesi degli archi entranti.
        """

        result = []

        for media_type in self._graph.nodes:

            peso_uscente = self._graph.out_degree(
                media_type,
                weight="weight"
            )

            peso_entrante = self._graph.in_degree(
                media_type,
                weight="weight"
            )

            influenza = peso_uscente - peso_entrante

            result.append(
                (media_type, influenza)
            )

        result.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return result[:n]

    def getTopEdges(self, n=5):
        """
        Funzione non richiesta direttamente dalla traccia,
        ma utile per debug.

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

    def cercaPercorsoOttimo(self, start, end, lunghezza):
        """
        Punto 2 della Prova 1.

        Obiettivo:
            trovare un cammino ottimo da start a end.

        Vincoli:
            - il cammino parte da start;
            - il cammino termina in end;
            - la lunghezza è esattamente uguale al valore inserito;
            - lunghezza = numero di archi attraversati;
            - il cammino rispetta il verso degli archi;
            - non ripete nodi;
            - massimizza la somma dei pesi degli archi.

        Strategia:
            backtracking ricorsivo.

        Stato:
            parziale:
                lista dei nodi del cammino corrente.

            peso_attuale:
                somma dei pesi degli archi attraversati finora.
        """

        self._bestPath = []
        self._bestPeso = -1

        if start is None or end is None:
            return [], 0

        if start not in self._graph.nodes:
            return [], 0

        if end not in self._graph.nodes:
            return [], 0

        if lunghezza <= 0:
            return [], 0

        parziale = [start]

        self._ricorsionePercorso(
            parziale=parziale,
            end=end,
            lunghezza=lunghezza,
            peso_attuale=0
        )

        if len(self._bestPath) == 0:
            return [], 0

        return self._bestPath, self._bestPeso

    def _ricorsionePercorso(self, parziale, end, lunghezza, peso_attuale):
        """
        Funzione ricorsiva vera.

        Schema:

        1. Calcolo quanti archi ho già usato.
        2. Se ho usato esattamente 'lunghezza' archi:
            - controllo se sono arrivato a end;
            - se sì, aggiorno il best.
        3. Se non ho ancora raggiunto la lunghezza:
            - prendo l'ultimo nodo;
            - esploro i successori;
            - controllo di non ripetere nodi;
            - append;
            - ricorsione;
            - pop.
        """

        archi_usati = len(parziale) - 1

        # Caso base:
        # ho raggiunto esattamente la lunghezza richiesta.
        if archi_usati == lunghezza:

            ultimo = parziale[-1]

            if ultimo == end:

                if peso_attuale > self._bestPeso:
                    self._bestPeso = peso_attuale
                    self._bestPath = list(parziale)

            return

        # Se ho già superato la lunghezza, mi fermo.
        # In teoria non succede, ma lo lascio per sicurezza.
        if archi_usati > lunghezza:
            return

        ultimo_nodo = parziale[-1]

        # Grafo diretto:
        # devo seguire il verso degli archi.
        for vicino in self._graph.successors(ultimo_nodo):

            # Vincolo:
            # il cammino non può ripetere nodi.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Scelta.
            parziale.append(vicino)

            # Ricorsione.
            self._ricorsionePercorso(
                parziale=parziale,
                end=end,
                lunghezza=lunghezza,
                peso_attuale=peso_attuale + peso_arco
            )

            # Backtracking.
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
        """

        dettagli = []

        for i in range(len(cammino) - 1):

            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
