from database.DB_connect import DBConnect
from model.genre import Genre
from model.album import Album
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllGeneri():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i generi musicali.

        Serve per popolare il dropdown iniziale.

        Query:
        SELECT GenreId, Name
        FROM Genre

        Ritorna:
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
        i vertici sono gli album che contengono almeno un brano
        del genere selezionato.

        Percorso logico nel database:

        Album
            -> Track
                -> Genre

        Inoltre collego anche Artist:
        Album
            -> Artist

        Perché collego Artist?
        Non è obbligatorio per il grafo, ma mi permette di salvare
        anche il nome dell'artista dentro la dataclass Album.

        Condizione:
        t.GenreId = genre_id

        Uso DISTINCT perché:
        un album può contenere più tracce dello stesso genere,
        ma nel grafo l'album deve comparire una volta sola.

        Ritorna:
        lista di oggetti Album.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT al.AlbumId,
                            al.Title,
                            ar.ArtistId,
                            ar.Name AS ArtistName
            FROM Album al, Track t, Artist ar
            WHERE al.AlbumId = t.AlbumId
              AND al.ArtistId = ar.ArtistId
              AND t.GenreId = %s
            ORDER BY al.Title
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            album = Album(
                AlbumId=row["AlbumId"],
                Title=row["Title"],
                ArtistId=row["ArtistId"],
                ArtistName=row["ArtistName"]
            )

            result.append(album)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllEdges(genre_id):
        """
        FUNZIONE 3
        ----------
        Estrae gli archi del grafo non orientato.

        Traccia:
        due album sono collegati se almeno una Invoice contiene brani
        appartenenti a entrambi gli album.

        Peso:
        numero di Invoice distinte in cui i due album compaiono insieme.

        Qui posso calcolare direttamente anche il peso nel DAO,
        perché è una semplice aggregazione SQL.

        Percorso logico:

        InvoiceLine il1 -> Track t1 -> Album 1
        InvoiceLine il2 -> Track t2 -> Album 2

        Se:
        il1.InvoiceId = il2.InvoiceId

        vuol dire:
        le due righe fattura appartengono alla stessa Invoice.

        Se:
        t1.AlbumId <> t2.AlbumId

        vuol dire:
        sto confrontando due album diversi.

        Se:
        t1.GenreId = genre_id
        t2.GenreId = genre_id

        vuol dire:
        considero solo brani del genere selezionato.

        Uso:
        t1.AlbumId < t2.AlbumId

        Perché il grafo è non orientato.
        Quindi l'arco Album1-Album2 è lo stesso di Album2-Album1.
        Questa condizione evita di ottenere entrambe le coppie.

        COUNT(DISTINCT il1.InvoiceId):
        conta in quante invoice distinte i due album compaiono insieme.

        Ritorna:
        lista di Arco(id1, id2, peso).
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT t1.AlbumId AS id1,
                   t2.AlbumId AS id2,
                   COUNT(DISTINCT il1.InvoiceId) AS peso
            FROM InvoiceLine il1, Track t1,
                 InvoiceLine il2, Track t2
            WHERE il1.TrackId = t1.TrackId
              AND il2.TrackId = t2.TrackId

              AND il1.InvoiceId = il2.InvoiceId

              AND t1.GenreId = %s
              AND t2.GenreId = %s

              AND t1.AlbumId < t2.AlbumId

            GROUP BY t1.AlbumId, t2.AlbumId
        """

        cursor.execute(query, (genre_id, genre_id))

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
