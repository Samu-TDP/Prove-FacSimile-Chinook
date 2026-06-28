from database.DB_connect import DBConnect
from model.genre import Genre
from model.customer import Customer
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllGeneri():
        """
        FUNZIONE 1
        ----------
        Serve per popolare il dropdown dei generi.

        Cosa estraggo dal database?
        - GenreId: identificativo del genere
        - Name: nome del genere

        Perché mi serve GenreId?
        Perché quando l'utente seleziona "Rock", nel codice userò il suo ID
        per filtrare le Track appartenenti a quel genere.

        Ritorno:
        lista di oggetti Genre.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT GenreId, Name
            FROM Genre
            ORDER BY Name
        """

        cursor.execute(query)

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
    def getAllNodes(genre_id):
        """
        FUNZIONE 2
        ----------
        Estrae i nodi del grafo.

        Traccia:
        i nodi sono i clienti che hanno acquistato almeno un brano
        appartenente al genere selezionato.

        Percorso logico nel database:

        Customer
            -> Invoice
                -> InvoiceLine
                    -> Track

        Perché?
        - Customer contiene i clienti.
        - Invoice dice quale cliente ha fatto una fattura.
        - InvoiceLine dice quali brani sono stati acquistati in quella fattura.
        - Track contiene GenreId, quindi mi dice il genere del brano.

        Quindi un cliente diventa nodo se:
        esiste almeno una sua InvoiceLine collegata a una Track con GenreId = genre_id.

        Uso DISTINCT perché:
        un cliente può avere comprato tanti brani dello stesso genere,
        ma nel grafo il cliente deve comparire una volta sola.

        Ritorno:
        lista di oggetti Customer.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT c.CustomerId,
                            c.FirstName,
                            c.LastName,
                            c.Country
            FROM Customer c, Invoice i, InvoiceLine il, Track t
            WHERE c.CustomerId = i.CustomerId
              AND i.InvoiceId = il.InvoiceId
              AND il.TrackId = t.TrackId
              AND t.GenreId = %s
            ORDER BY c.LastName, c.FirstName
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            cliente = Customer(
                CustomerId=row["CustomerId"],
                FirstName=row["FirstName"],
                LastName=row["LastName"],
                Country=row["Country"]
            )
            result.append(cliente)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getSpesaClienti(genre_id):
        """
        FUNZIONE 3
        ----------
        Associa a ogni cliente la sua spesa totale nel genere selezionato.

        Traccia:
        per ogni cliente si calcola la spesa nel genere come:
        SUM(UnitPrice * Quantity)

        Percorso logico nel database:

        Invoice
            -> InvoiceLine
                -> Track

        Perché non parto da Customer?
        Perché Invoice contiene già CustomerId.
        Quindi posso raggruppare direttamente per i.CustomerId.

        Ritorno:
        dizionario CustomerId -> spesa

        Esempio:
        {
            1: 17.82,
            2: 12.87,
            3: 25.74
        }

        Questo dizionario sarà usato nel Model per:
        - decidere il verso dell'arco
        - calcolare il peso dell'arco
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return {}

        result = {}
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT i.CustomerId,
                   SUM(il.UnitPrice * il.Quantity) AS spesa
            FROM Invoice i, InvoiceLine il, Track t
            WHERE i.InvoiceId = il.InvoiceId
              AND il.TrackId = t.TrackId
              AND t.GenreId = %s
            GROUP BY i.CustomerId
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            customer_id = row["CustomerId"]
            spesa = float(row["spesa"])

            result[customer_id] = spesa

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllEdges(genre_id):
        """
        FUNZIONE 4
        ----------
        Estrae la relazione grezza dell'arco.

        Traccia:
        esiste un arco tra due clienti se hanno acquistato almeno un artista
        in comune nel genere selezionato.

        Qui NON calcolo:
        - peso
        - verso

        Qui calcolo solo:
        - cliente id1
        - cliente id2

        cioè:
        "questi due clienti devono essere collegati".

        Percorso logico per un cliente:

        Invoice
            -> InvoiceLine
                -> Track
                    -> Album
                        -> Artist

        Per trovare due clienti con artista in comune, faccio lo stesso percorso
        due volte:

        Cliente 1:
        i1 -> il1 -> t1 -> al1

        Cliente 2:
        i2 -> il2 -> t2 -> al2

        Poi impongo:
        al1.ArtistId = al2.ArtistId

        Questo vuol dire:
        i due clienti hanno acquistato almeno un artista in comune.

        Uso:
        i1.CustomerId < i2.CustomerId

        Perché?
        Per evitare duplicati logici.

        Senza questa condizione avrei:
        - cliente 1, cliente 2
        - cliente 2, cliente 1

        Ma qui il DAO non deve ancora orientare.
        Quindi prende la coppia una volta sola.

        Ritorno:
        lista di oggetti Arco(id1, id2)
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT i1.CustomerId AS id1,
                            i2.CustomerId AS id2
            FROM Invoice i1, InvoiceLine il1, Track t1, Album al1,
                 Invoice i2, InvoiceLine il2, Track t2, Album al2
            WHERE i1.InvoiceId = il1.InvoiceId
              AND il1.TrackId = t1.TrackId
              AND t1.AlbumId = al1.AlbumId

              AND i2.InvoiceId = il2.InvoiceId
              AND il2.TrackId = t2.TrackId
              AND t2.AlbumId = al2.AlbumId

              AND t1.GenreId = %s
              AND t2.GenreId = %s

              AND al1.ArtistId = al2.ArtistId

              AND i1.CustomerId < i2.CustomerId
        """

        cursor.execute(query, (genre_id, genre_id))

        for row in cursor:
            arco = Arco(
                id1=row["id1"],
                id2=row["id2"]
            )
            result.append(arco)

        cursor.close()
        conn.close()

        return result
