import networkx as nx
from database.DAO import DAO


class Model:

    def __init__(self):
        """
        Attributi principali del Model.

        _graph:
            grafo orientato e pesato.
            Uso nx.DiGraph() perché gli archi hanno un verso:
            invoice vecchia -> invoice recente.

        _idMap:
            dizionario InvoiceId -> oggetto Invoice.
            Serve perché nel dropdown salvo solo l'ID,
            mentre NetworkX usa gli oggetti Invoice come nodi.

        _bestPath:
            miglior cammino trovato dalla ricorsione.

        _bestPeso:
            peso totale del miglior cammino trovato.
        """

        self._graph = nx.DiGraph()
        self._idMap = {}

        self._bestPath = []
        self._bestPeso = 0

    def buildGraph(self, customer_id, k):
        """
        Costruisce il grafo della PROVA 7.

        Input:
            customer_id = cliente selezionato
            k = massimo numero di giorni tra due invoice

        Nodi:
            tutte le invoice del cliente selezionato.

        Arco:
            esiste un arco da invoice_vecchia a invoice_recente se:

                0 < giorni_tra_invoice <= k

        Verso:
            sempre dalla invoice più vecchia alla invoice più recente.

        Peso:
            (Total invoice vecchia + Total invoice recente) / giorni_tra_invoice

        Pattern meccanico:
            1. reset grafo e idMap
            2. carico invoice dal DAO
            3. aggiungo nodi
            4. ordino invoice per data
            5. doppio ciclo sulle coppie
            6. calcolo giorni
            7. se giorni validi, calcolo peso e aggiungo arco
        """

        self._graph.clear()
        self._idMap.clear()

        # ------------------------------------------------------------
        # 1. Carico dal DAO tutte le invoice del cliente selezionato
        # ------------------------------------------------------------

        invoices = DAO.getAllNodes(customer_id)

        # ------------------------------------------------------------
        # 2. Aggiungo le invoice come nodi del grafo
        # ------------------------------------------------------------

        for invoice in invoices:
            self._graph.add_node(invoice)
            self._idMap[invoice.InvoiceId] = invoice

        # ------------------------------------------------------------
        # 3. Ordino le invoice per data
        # ------------------------------------------------------------
        #
        # Il DAO le ha già ordinate, ma lo rifaccio qui per sicurezza.
        # Così nel doppio ciclo:
        # - invoices_ordinate[i] è più vecchia
        # - invoices_ordinate[j] è più recente

        invoices_ordinate = sorted(
            invoices,
            key=lambda inv: inv.InvoiceDate
        )

        # ------------------------------------------------------------
        # 4. Creo gli archi temporali
        # ------------------------------------------------------------

        for i in range(len(invoices_ordinate)):

            invoice_vecchia = invoices_ordinate[i]

            for j in range(i + 1, len(invoices_ordinate)):

                invoice_recente = invoices_ordinate[j]

                # Differenza temporale in giorni.
                # InvoiceDate è già datetime, quindi posso sottrarre direttamente.
                giorni = (
                    invoice_recente.InvoiceDate - invoice_vecchia.InvoiceDate
                ).days

                # La traccia dice:
                # distanza temporale maggiore di zero.
                # Quindi se giorni == 0 non creo arco.
                if giorni <= 0:
                    continue

                # Siccome le invoice sono ordinate per data,
                # se supero K posso interrompere il ciclo interno.
                # Le invoice successive saranno ancora più lontane.
                if giorni > k:
                    break

                # Peso richiesto dalla traccia.
                peso = (invoice_vecchia.Total + invoice_recente.Total) / giorni

                # Aggiungo arco orientato:
                # invoice vecchia -> invoice recente.
                self._graph.add_edge(
                    invoice_vecchia,
                    invoice_recente,
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
        Restituisce tutte le invoice presenti nel grafo,
        ordinate per data.

        Serve per popolare il dropdown delle invoice.
        """

        return sorted(
            list(self._graph.nodes),
            key=lambda inv: inv.InvoiceDate
        )

    def getNodeById(self, invoice_id):
        """
        Dato un InvoiceId, restituisce l'oggetto Invoice corrispondente.

        Esempio:
            invoice_id = 316
            ritorna oggetto Invoice 316
        """

        return self._idMap.get(invoice_id, None)

    def getTopEdges(self, n=5):
        """
        Restituisce i primi n archi con peso maggiore.

        Ogni elemento restituito è:
            (invoice_partenza, invoice_arrivo, peso)

        Perché uso edges(data=True)?
            Perché devo leggere anche il peso salvato nell'attributo "weight".
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

    def getInvoicePiuInfluente(self):
        """
        Calcola la invoice più influente.

        Formula richiesta:

            influenza = somma pesi uscenti - somma pesi entranti

        In NetworkX:
            out_degree(nodo, weight="weight")
                somma i pesi degli archi uscenti.

            in_degree(nodo, weight="weight")
                somma i pesi degli archi entranti.
        """

        if self._graph.number_of_nodes() == 0:
            return None, 0

        best_invoice = None
        best_influenza = -float("inf")

        for invoice in self._graph.nodes:

            peso_uscente = self._graph.out_degree(
                invoice,
                weight="weight"
            )

            peso_entrante = self._graph.in_degree(
                invoice,
                weight="weight"
            )

            influenza = peso_uscente - peso_entrante

            if influenza > best_influenza:
                best_influenza = influenza
                best_invoice = invoice

        return best_invoice, best_influenza

    # ------------------------------------------------------------------
    # RICORSIONE
    # ------------------------------------------------------------------

    def cercaCamminoDecrescente(self, invoice_start):
        """
        Punto 2 della PROVA 7.

        Obiettivo:
            trovare un cammino semplice di peso totale massimo
            partendo dalla invoice selezionata.

        Vincoli:
            1. Il cammino parte dalla invoice selezionata.
            2. Il cammino deve seguire il verso degli archi.
            3. Una invoice non può comparire due volte.
            4. I pesi degli archi devono essere strettamente decrescenti.

        Esempio valido:
            0.39 -> 0.22 -> 0.10

        Esempio non valido:
            0.39 -> 0.39
            perché il secondo peso non è minore del primo.
        """

        self._bestPath = []
        self._bestPeso = -1

        if invoice_start is None:
            return [], 0

        if invoice_start not in self._graph.nodes:
            return [], 0

        parziale = [invoice_start]

        # All'inizio non ho ancora percorso archi.
        # Metto ultimo_peso = infinito così il primo arco sarà sempre ammesso.
        self._ricorsioneDecrescente(
            parziale=parziale,
            ultimo_peso=float("inf"),
            peso_attuale=0
        )

        if len(self._bestPath) == 0:
            return [], 0

        return self._bestPath, self._bestPeso

    def _ricorsioneDecrescente(self, parziale, ultimo_peso, peso_attuale):
        """
        Funzione ricorsiva vera.

        Stato della ricorsione:
            parziale:
                lista delle invoice nel cammino corrente.

            ultimo_peso:
                peso dell'ultimo arco attraversato.

            peso_attuale:
                somma dei pesi degli archi nel cammino corrente.

        Pattern:
            1. aggiorno il best;
            2. prendo ultimo nodo;
            3. esploro i successori;
            4. controllo vincoli;
            5. append;
            6. ricorsione;
            7. pop.
        """

        # ------------------------------------------------------------
        # 1. Aggiorno il best
        # ------------------------------------------------------------
        #
        # Criterio principale:
        #   peso totale massimo.
        #
        # Criterio secondario:
        #   se due cammini hanno stesso peso, tengo quello più lungo.

        if peso_attuale > self._bestPeso:
            self._bestPeso = peso_attuale
            self._bestPath = list(parziale)

        elif peso_attuale == self._bestPeso:
            if len(parziale) > len(self._bestPath):
                self._bestPath = list(parziale)

        # ------------------------------------------------------------
        # 2. Prendo l'ultimo nodo del cammino
        # ------------------------------------------------------------

        ultimo_nodo = parziale[-1]

        # ------------------------------------------------------------
        # 3. Esploro solo i successori
        # ------------------------------------------------------------
        #
        # Siccome il grafo è orientato, devo rispettare il verso.
        # successors(ultimo_nodo) restituisce solo i nodi raggiungibili
        # con archi uscenti da ultimo_nodo.

        for vicino in self._graph.successors(ultimo_nodo):

            # Vincolo cammino semplice:
            # non posso ripetere la stessa invoice.
            if vicino in parziale:
                continue

            peso_arco = self._graph[ultimo_nodo][vicino]["weight"]

            # Vincolo dei pesi strettamente decrescenti.
            if peso_arco < ultimo_peso:

                # Scelta:
                # aggiungo il vicino al cammino corrente.
                parziale.append(vicino)

                # Ricorsione:
                # continuo da vicino.
                self._ricorsioneDecrescente(
                    parziale=parziale,
                    ultimo_peso=peso_arco,
                    peso_attuale=peso_attuale + peso_arco
                )

                # Backtracking:
                # tolgo il nodo appena aggiunto per provare altri cammini.
                parziale.pop()

    def getDettagliCammino(self, cammino):
        """
        Trasforma un cammino in una lista di dettagli.

        Input:
            [Invoice 98, Invoice 121, Invoice 143]

        Output:
            [
                (Invoice 98, Invoice 121, peso_98_121),
                (Invoice 121, Invoice 143, peso_121_143)
            ]

        Serve al Controller per stampare il percorso arco per arco.
        """

        dettagli = []

        for i in range(len(cammino) - 1):

            u = cammino[i]
            v = cammino[i + 1]

            peso = self._graph[u][v]["weight"]

            dettagli.append((u, v, peso))

        return dettagli
