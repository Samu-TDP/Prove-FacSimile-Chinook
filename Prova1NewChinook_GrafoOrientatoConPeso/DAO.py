from database.DB_connect import DBConnect
from model.media_type import MediaType


class DAO:

    @staticmethod
    def getAllCountries():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i Country presenti nella tabella Customer.

        Serve per popolare il dropdown Country.

        Tabella usata:
            Customer

        Campo estratto:
            Country

        Perché DISTINCT?
            Perché più clienti possono appartenere allo stesso Country,
            ma nel dropdown ogni Country deve comparire una sola volta.

        Ritorna:
            lista di stringhe.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT Country
            FROM Customer
            WHERE Country IS NOT NULL
            ORDER BY Country
        """

        cursor.execute(query)

        for row in cursor:
            result.append(row["Country"])

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllYears():
        """
        FUNZIONE 2
        ----------
        Estrae tutti gli anni in cui esiste almeno una Invoice.

        Serve per popolare il dropdown Anno.

        Tabella usata:
            Invoice

        Campo usato:
            InvoiceDate

        Funzione SQL:
            YEAR(InvoiceDate)

        Ritorna:
            lista di interi.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT YEAR(InvoiceDate) AS anno
            FROM Invoice
            ORDER BY anno
        """

        cursor.execute(query)

        for row in cursor:
            result.append(int(row["anno"]))

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllNodes(country, anno):
        """
        FUNZIONE 3
        ----------
        Estrae tutti i nodi del grafo.

        Traccia:
            i nodi sono tutti i record presenti nella tabella MediaType.

        Quindi attenzione:
            anche un MediaType che non ha vendite nel Country/Anno selezionato
            deve essere comunque aggiunto come nodo.

        In più, per ogni nodo MediaType, la traccia chiede di salvare
        un dizionario aggiuntivo:

            mese -> lista di coppie (CustomerId, InvoiceLineId)

        relative agli acquisti di quel MediaType nel Country e nell'Anno
        selezionati.

        Questa funzione fa quindi due passaggi:

        PASSAGGIO A:
            carica tutti i MediaType.

        PASSAGGIO B:
            carica gli acquisti filtrati per Country e Anno
            e li inserisce dentro il dizionario acquisti_per_mese
            del MediaType corretto.

        Ritorna:
            lista di oggetti MediaType.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        cursor = conn.cursor(dictionary=True)

        # ------------------------------------------------------------
        # PASSAGGIO A: carico tutti i MediaType
        # ------------------------------------------------------------

        idMap = {}

        query_media_type = """
            SELECT MediaTypeId,
                   Name
            FROM MediaType
            ORDER BY Name
        """

        cursor.execute(query_media_type)

        for row in cursor:
            media_type = MediaType(
                MediaTypeId=row["MediaTypeId"],
                Name=row["Name"]
            )

            idMap[media_type.MediaTypeId] = media_type

        # ------------------------------------------------------------
        # PASSAGGIO B: carico gli acquisti nel Country/Anno selezionato
        # ------------------------------------------------------------
        #
        # Percorso logico:
        #
        # Customer
        #   -> Invoice
        #       -> InvoiceLine
        #           -> Track
        #               -> MediaType
        #
        # Da InvoiceDate estraggo il mese con MONTH(InvoiceDate).
        #
        # Per ogni riga SQL ottengo:
        # - MediaTypeId
        # - mese
        # - CustomerId
        # - InvoiceLineId
        #
        # Poi salvo:
        # media_type.acquisti_per_mese[mese].append((CustomerId, InvoiceLineId))

        query_acquisti = """
            SELECT t.MediaTypeId AS MediaTypeId,
                   MONTH(i.InvoiceDate) AS mese,
                   c.CustomerId AS CustomerId,
                   il.InvoiceLineId AS InvoiceLineId
            FROM Customer c,
                 Invoice i,
                 InvoiceLine il,
                 Track t
            WHERE c.CustomerId = i.CustomerId
              AND i.InvoiceId = il.InvoiceId
              AND il.TrackId = t.TrackId
              AND c.Country = %s
              AND YEAR(i.InvoiceDate) = %s
            ORDER BY t.MediaTypeId, mese, c.CustomerId, il.InvoiceLineId
        """

        cursor.execute(query_acquisti, (country, anno))

        for row in cursor:
            media_type_id = row["MediaTypeId"]
            mese = int(row["mese"])
            customer_id = row["CustomerId"]
            invoice_line_id = row["InvoiceLineId"]

            # Recupero il MediaType già creato nel PASSAGGIO A.
            media_type = idMap[media_type_id]

            # Se è la prima volta che incontro quel mese per quel MediaType,
            # creo la lista vuota.
            if mese not in media_type.acquisti_per_mese:
                media_type.acquisti_per_mese[mese] = []

            # Aggiungo la coppia richiesta dalla traccia.
            media_type.acquisti_per_mese[mese].append(
                (customer_id, invoice_line_id)
            )

        cursor.close()
        conn.close()

        result = list(idMap.values())

        result.sort(
            key=lambda mt: mt.Name
        )

        return result

    @staticmethod
    def getVenditeMediaType(country, anno):
        """
        FUNZIONE 4
        ----------
        Calcola il numero di vendite di ogni MediaType nell'anno selezionato
        e nel Country selezionato.

        Traccia:
            per numero di vendite si intende il numero di righe distinte
            della tabella InvoiceLine, NON la quantità acquistata.

        Quindi:
            vendite = COUNT(DISTINCT InvoiceLineId)

        Percorso logico:
            Customer
                -> Invoice
                    -> InvoiceLine
                        -> Track
                            -> MediaType

        Ritorna:
            dizionario:

            {
                MediaTypeId: numero_vendite,
                MediaTypeId: numero_vendite,
                ...
            }

        Esempio:
            {
                1: 41,
                2: 13,
                4: 28
            }

        Questo dizionario serve nel Model per:
            - decidere il verso degli archi;
            - calcolare il peso degli archi.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return {}

        result = {}

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT t.MediaTypeId AS MediaTypeId,
                   COUNT(DISTINCT il.InvoiceLineId) AS vendite
            FROM Customer c,
                 Invoice i,
                 InvoiceLine il,
                 Track t
            WHERE c.CustomerId = i.CustomerId
              AND i.InvoiceId = il.InvoiceId
              AND il.TrackId = t.TrackId
              AND c.Country = %s
              AND YEAR(i.InvoiceDate) = %s
            GROUP BY t.MediaTypeId
        """

        cursor.execute(query, (country, anno))

        for row in cursor:
            media_type_id = row["MediaTypeId"]
            vendite = int(row["vendite"])

            result[media_type_id] = vendite

        cursor.close()
        conn.close()

        return result
