from database.DB_connect import DBConnect
from model.media_type import MediaType
from model.composer import Composer
from model.track_info import TrackInfo
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllMediaTypes():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i MediaType dal database.

        A cosa serve?
        Serve per popolare il dropdown MediaType.

        Tabella usata:
            MediaType

        Campi estratti:
            MediaTypeId
            Name

        Output:
            lista di oggetti MediaType

        Esempio:
            [
                MediaType(1, "MPEG audio file"),
                MediaType(2, "Protected AAC audio file"),
                ...
            ]
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT MediaTypeId,
                   Name
            FROM MediaType
            ORDER BY Name
        """

        cursor.execute(query)

        for row in cursor:
            media_type = MediaType(
                MediaTypeId=row["MediaTypeId"],
                Name=row["Name"]
            )

            result.append(media_type)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllNodes(media_type_id, durata_ms):
        """
        FUNZIONE 2
        ----------
        Estrae i nodi del grafo.

        Traccia:
            i nodi sono tutti i compositori presenti nella colonna Composer
            della tabella Track, considerando solo i brani validi.

        Un brano è valido se:
            - MediaTypeId = media_type_id scelto dall'utente
            - Milliseconds >= durata_ms
            - Composer non è NULL
            - Composer non è stringa vuota

        Problema importante:
            nel database non esiste una tabella Composer.
            Il compositore è una stringa ripetuta in tante righe della tabella Track.

        Quindi:
            la query estrae i brani validi.
            Python raggruppa questi brani per compositore.

        Struttura dati temporanea:
            dizionario:

            {
                "Franz Joseph Haydn": Composer(...),
                "Ludwig van Beethoven": Composer(...),
                ...
            }

        Ogni oggetto Composer contiene anche:
            tracks = lista dei suoi brani validi.

        Output:
            lista di oggetti Composer.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        # Dizionario temporaneo.
        #
        # Chiave:
        #   nome compositore
        #
        # Valore:
        #   oggetto Composer
        compositore_to_oggetto = {}

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT TrackId,
                   Name,
                   Composer,
                   Milliseconds
            FROM Track
            WHERE MediaTypeId = %s
              AND Milliseconds >= %s
              AND Composer IS NOT NULL
              AND Composer <> ''
            ORDER BY Composer, Name
        """

        cursor.execute(query, (media_type_id, durata_ms))

        for row in cursor:

            # 1. Leggo il nome del compositore dalla riga SQL.
            nome_compositore = row["Composer"]

            # 2. Creo un oggetto TrackInfo per il brano corrente.
            brano_corrente = TrackInfo(
                TrackId=row["TrackId"],
                Name=row["Name"],
                Milliseconds=row["Milliseconds"]
            )

            # 3. Se questo compositore non è ancora stato creato,
            #    creo il nodo Composer e lo salvo nel dizionario.
            if nome_compositore not in compositore_to_oggetto:

                nuovo_compositore = Composer(
                    Name=nome_compositore
                )

                compositore_to_oggetto[nome_compositore] = nuovo_compositore

            # 4. Recupero l'oggetto Composer corrispondente.
            compositore = compositore_to_oggetto[nome_compositore]

            # 5. Aggiungo il brano valido alla lista dei brani del compositore.
            compositore.tracks.append(brano_corrente)

        cursor.close()
        conn.close()

        # Il dizionario contiene:
        # nome_compositore -> oggetto Composer
        #
        # A me serve una lista di oggetti Composer.
        result = list(compositore_to_oggetto.values())

        result.sort(
            key=lambda compositore: compositore.Name
        )

        return result

    @staticmethod
    def getAllEdges(media_type_id, durata_ms):
        """
        FUNZIONE 3
        ----------
        Estrae direttamente gli archi pesati del grafo.

        Traccia:
            due compositori sono collegati se esiste almeno una playlist
            che contiene almeno un brano valido del primo compositore
            e almeno un brano valido del secondo compositore.

        Peso:
            numero di playlist distinte in cui compaiono entrambi.

        Brano valido:
            - MediaTypeId = media_type_id
            - Milliseconds >= durata_ms
            - Composer non nullo
            - Composer non vuoto

        Tabelle usate:
            Track t1
            PlaylistTrack pt1
            Track t2
            PlaylistTrack pt2

        Idea della query:
            t1 rappresenta un brano del primo compositore.
            t2 rappresenta un brano del secondo compositore.

            pt1 dice in quali playlist compare t1.
            pt2 dice in quali playlist compare t2.

        Condizione fondamentale:
            pt1.PlaylistId = pt2.PlaylistId

        Significa:
            i due brani compaiono nella stessa playlist.

        Condizione:
            t1.Composer < t2.Composer

        Serve per:
            1. evitare Composer-Composer uguali;
            2. evitare doppioni nel grafo non orientato.

        Esempio:
            Haydn - Beethoven
            Beethoven - Haydn

            sono lo stesso arco.
            Con < ne tengo solo uno.

        Perché COUNT(DISTINCT pt1.PlaylistId)?
            Se nella stessa playlist ci sono 3 brani di Haydn
            e 2 brani di Beethoven, la join produrrebbe molte combinazioni.
            Ma quella playlist deve contare una sola volta.

            Quindi NON uso COUNT(*).
            Uso COUNT(DISTINCT PlaylistId).

        Output:
            lista di Arco(id1, id2, peso)
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT t1.Composer AS id1,
                   t2.Composer AS id2,
                   COUNT(DISTINCT pt1.PlaylistId) AS peso

            FROM Track t1,
                 Track t2,
                 PlaylistTrack pt1,
                 PlaylistTrack pt2

            WHERE t1.TrackId = pt1.TrackId
              AND t2.TrackId = pt2.TrackId

              AND pt1.PlaylistId = pt2.PlaylistId

              AND t1.Composer IS NOT NULL
              AND t2.Composer IS NOT NULL
              AND t1.Composer <> ''
              AND t2.Composer <> ''

              AND t1.Composer < t2.Composer

              AND t1.MediaTypeId = %s
              AND t2.MediaTypeId = %s

              AND t1.Milliseconds >= %s
              AND t2.Milliseconds >= %s

            GROUP BY t1.Composer,
                     t2.Composer

            ORDER BY peso DESC
        """

        cursor.execute(
            query,
            (
                media_type_id,
                media_type_id,
                durata_ms,
                durata_ms
            )
        )

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
