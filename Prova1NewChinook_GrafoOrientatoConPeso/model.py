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
