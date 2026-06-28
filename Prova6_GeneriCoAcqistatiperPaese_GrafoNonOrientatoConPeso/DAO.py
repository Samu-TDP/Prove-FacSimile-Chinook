from database.DB_connect import DBConnect
from model.genre import Genre
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllPaesi():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i paesi presenti nella tabella Customer.

        Serve per popolare il dropdown Paese.

        Query logica:
            SELECT DISTINCT Country
            FROM Customer

        Perché DISTINCT?
        Perché più clienti possono appartenere allo stesso paese,
        ma nel dropdown ogni paese deve comparire una volta sola.

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
    def getAllNodes(country):
        """
        FUNZIONE 2
        ----------
        Estrae i nodi del grafo.

        Traccia:
        i vertici sono i generi musicali acquistati da almeno un cliente
        del paese selezionato.

        Percorso logico nel database:

            Customer
                -> Invoice
                    -> InvoiceLine
                        -> Track
                            -> Genre

        Spiegazione:
        - Customer contiene il Country.
        - Invoice collega ogni fattura a un cliente.
        - InvoiceLine contiene le righe della fattura, quindi i brani acquistati.
        - Track contiene il GenreId.
        - Genre contiene il nome del genere.

        Quindi:
        prendo tutti i generi associati a brani acquistati da clienti
        del paese scelto.

        Uso DISTINCT perché:
        lo stesso genere può essere acquistato tante volte,
        ma nel grafo ogni genere deve essere un solo nodo.

        Ritorna:
            lista di oggetti Genre.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT g.GenreId,
                            g.Name
            FROM Customer c,
                 Invoice i,
                 InvoiceLine il,
                 Track t,
                 Genre g
            WHERE c.CustomerId = i.CustomerId
              AND i.InvoiceId = il.InvoiceId
              AND il.TrackId = t.TrackId
              AND t.GenreId = g.GenreId
              AND c.Country = %s
            ORDER BY g.Name
        """

        cursor.execute(query, (country,))

        for row in cursor:
            genere = Genre(
                GenreId=row["GenreId"],
                Name=row["Name"]
            )

            result.append(genere)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllEdges(country):
        """
        FUNZIONE 3
        ----------
        Estrae direttamente gli archi del grafo.

        Traccia:
        due generi sono collegati se almeno un cliente del paese selezionato
        ha acquistato brani di entrambi i generi.

        Peso:
        numero di clienti distinti che hanno acquistato entrambi i generi.

        Questa funzione ritorna:
            lista di Arco(id1, id2, peso)

        Dove:
        - id1 è il primo GenreId
        - id2 è il secondo GenreId
        - peso è il numero di clienti distinti che hanno acquistato entrambi

        Questa è la versione costruita sul tuo pattern:
        self join tra due catene di acquisto dello stesso cliente.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT t1.GenreId AS id1,
                   t2.GenreId AS id2,
                   COUNT(DISTINCT c.CustomerId) AS peso

            FROM Customer c,
                 Invoice i1,
                 InvoiceLine il1,
                 Track t1,
                 Invoice i2,
                 InvoiceLine il2,
                 Track t2

            WHERE c.CustomerId = i1.CustomerId
              AND i1.InvoiceId = il1.InvoiceId
              AND il1.TrackId = t1.TrackId

              AND c.CustomerId = i2.CustomerId
              AND i2.InvoiceId = il2.InvoiceId
              AND il2.TrackId = t2.TrackId

              AND c.Country = %s

              AND t1.GenreId < t2.GenreId

            GROUP BY t1.GenreId, t2.GenreId

            ORDER BY peso DESC
        """

        """
        Spiegazione della query:

        Customer c:
            rappresenta il cliente del paese selezionato.

        Prima catena:
            c -> i1 -> il1 -> t1

            Questa identifica un primo brano acquistato dal cliente,
            quindi un primo genere t1.GenreId.

        Seconda catena:
            c -> i2 -> il2 -> t2

            Questa identifica un secondo brano acquistato dallo stesso cliente,
            quindi un secondo genere t2.GenreId.

        Le condizioni:
            c.CustomerId = i1.CustomerId
            c.CustomerId = i2.CustomerId

        impongono che entrambe le catene appartengano allo stesso cliente.

        La condizione:
            t1.GenreId < t2.GenreId

        serve per due motivi:
        1. evita coppie dello stesso genere, tipo Rock-Rock;
        2. evita il duplicato logico Rock-Metal e Metal-Rock.

        COUNT(DISTINCT c.CustomerId):
            conta quanti clienti distinti hanno generato quella coppia
            di generi.

        Esempio:
        se 13 clienti USA hanno comprato sia Rock sia Metal,
        allora la query produce:
            id1 = Rock
            id2 = Metal
            peso = 13
        """

        cursor.execute(query, (country,))

        for row in cursor:
            arco = Arco(
                id1=row["id1"],
                id2=row["id2"],
                peso=int(row["peso"])
            )

            result.append(arco)

        cursor.close()
        conn.close()

        return result
