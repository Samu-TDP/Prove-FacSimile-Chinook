from database.DB_connect import DBConnect
from model.genre import Genre
from model.playlist import Playlist
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllGeneri():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i generi musicali dal database.

        Serve per popolare il dropdown dei generi.

        Query:
        SELECT GenreId, Name
        FROM Genre

        Cosa salvo:
        ogni riga diventa un oggetto Genre.

        Ritorno:
        lista di Genre.
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
        i nodi sono le Playlist che contengono almeno un brano
        del genere selezionato.

        Percorso logico nel database:

        Playlist
            -> PlaylistTrack
                -> Track
                    -> Genre

        Perché?
        - Playlist contiene le playlist.
        - PlaylistTrack collega ogni playlist ai suoi brani.
        - Track contiene GenreId, quindi permette di filtrare per genere.

        Condizione:
        t.GenreId = genre_id

        Uso DISTINCT perché:
        una playlist può contenere tanti brani dello stesso genere,
        ma nel grafo deve comparire una sola volta.

        Ritorno:
        lista di oggetti Playlist.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT p.PlaylistId,
                            p.Name
            FROM Playlist p, PlaylistTrack pt, Track t
            WHERE p.PlaylistId = pt.PlaylistId
              AND pt.TrackId = t.TrackId
              AND t.GenreId = %s
            ORDER BY p.Name, p.PlaylistId
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            playlist = Playlist(
                PlaylistId=row["PlaylistId"],
                Name=row["Name"]
            )
            result.append(playlist)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getNumeroBraniPlaylist(genre_id):
        """
        FUNZIONE 3
        ----------
        Associa a ogni playlist il numero di brani del genere selezionato.

        Questo valore serve nel Model per decidere il verso dell'arco.

        Traccia:
        il verso va dalla playlist con più brani del genere
        verso quella con meno brani.

        Quindi mi serve un dizionario:

        PlaylistId -> numero di brani del genere

        Esempio:
        {
            1: 1297,
            8: 1297,
            5: 621,
            16: 14
        }

        Query:
        conto i TrackId distinti per ogni PlaylistId.

        COUNT(DISTINCT pt.TrackId):
        conta quanti brani diversi del genere selezionato
        sono presenti in quella playlist.

        GROUP BY pt.PlaylistId:
        crea una riga per ogni playlist.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return {}

        result = {}
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT pt.PlaylistId,
                   COUNT(DISTINCT pt.TrackId) AS numBrani
            FROM PlaylistTrack pt, Track t
            WHERE pt.TrackId = t.TrackId
              AND t.GenreId = %s
            GROUP BY pt.PlaylistId
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            playlist_id = row["PlaylistId"]
            num_brani = int(row["numBrani"])

            result[playlist_id] = num_brani

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getBraniPerPlaylist(genre_id):
        """
        FUNZIONE 4
        ----------
        Estrae quali brani del genere selezionato sono contenuti
        in ciascuna playlist.

        Questo serve nel Model per calcolare il peso dell'arco.

        Traccia:
        peso arco = numero di brani condivisi.

        Per calcolarlo facilmente in Python voglio questa struttura:

        PlaylistId -> insieme di TrackId

        Esempio:
        {
            1: {10, 11, 12, 13},
            8: {10, 11, 20},
            5: {100, 101}
        }

        Poi nel Model posso fare:

        brani_comuni = brani_playlist_1.intersection(brani_playlist_2)
        peso = len(brani_comuni)

        Questa funzione NON crea archi.
        Prepara solo i dati necessari per calcolare il peso.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return {}

        result = {}
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT pt.PlaylistId,
                   pt.TrackId
            FROM PlaylistTrack pt, Track t
            WHERE pt.TrackId = t.TrackId
              AND t.GenreId = %s
            ORDER BY pt.PlaylistId, pt.TrackId
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            playlist_id = row["PlaylistId"]
            track_id = row["TrackId"]

            if playlist_id not in result:
                result[playlist_id] = set()

            result[playlist_id].add(track_id)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllEdges(genre_id):
        """
        FUNZIONE 5
        ----------
        Estrae la relazione grezza degli archi.

        Traccia:
        due playlist sono collegate se condividono almeno un brano
        del genere selezionato.

        Qui NON calcolo:
        - verso
        - peso

        Qui calcolo solo:
        - id1
        - id2

        cioè:
        "queste due playlist sono collegate perché condividono almeno un brano".

        Percorso logico:

        PlaylistTrack pt1 rappresenta la prima playlist.
        PlaylistTrack pt2 rappresenta la seconda playlist.
        Track t serve per filtrare il genere.

        Condizione fondamentale:
        pt1.TrackId = pt2.TrackId

        Significa:
        la playlist 1 e la playlist 2 contengono lo stesso brano.

        Condizione sul genere:
        pt1.TrackId = t.TrackId
        t.GenreId = genre_id

        Significa:
        il brano condiviso appartiene al genere selezionato.

        Condizione anti-duplicati:
        pt1.PlaylistId < pt2.PlaylistId

        Serve per evitare:
        - 1, 8
        - 8, 1

        Qui il DAO non deve ancora orientare.
        Prende la coppia una sola volta.

        SELECT DISTINCT:
        serve perché due playlist possono condividere molti brani.
        Ma qui voglio solo sapere che la coppia esiste.
        Il peso verrà calcolato nel Model con getBraniPerPlaylist.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT pt1.PlaylistId AS id1,
                            pt2.PlaylistId AS id2
            FROM PlaylistTrack pt1, PlaylistTrack pt2, Track t
            WHERE pt1.TrackId = pt2.TrackId
              AND pt1.TrackId = t.TrackId
              AND t.GenreId = %s
              AND pt1.PlaylistId < pt2.PlaylistId
        """

        cursor.execute(query, (genre_id,))

        for row in cursor:
            arco = Arco(
                id1=row["id1"],
                id2=row["id2"]
            )
            result.append(arco)

        cursor.close()
        conn.close()

        return result
