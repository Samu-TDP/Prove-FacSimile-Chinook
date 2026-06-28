from database.DB_connect import DBConnect
from model.employee import Employee
from model.arco import Arco


class DAO:

    @staticmethod
    def getAllPaesi():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i paesi presenti nella tabella Customer.

        A cosa serve?
        Serve per popolare il dropdown dei paesi.

        Tabella usata:
            Customer

        Campo estratto:
            Country

        Perché DISTINCT?
            Perché molti clienti possono appartenere allo stesso paese.
            Nel dropdown voglio vedere ogni paese una sola volta.

        Cosa ritorna?
            Una lista di stringhe.

        Esempio:
            ["Brazil", "Canada", "France", "USA", ...]
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
            i vertici sono i dipendenti che supportano almeno un cliente
            del paese selezionato.

        Tabelle usate:
            Employee
            Customer

        Collegamento logico:
            Customer.SupportRepId = Employee.EmployeeId

        Perché?
            In Chinook ogni cliente può essere seguito da un dipendente,
            indicato dal campo SupportRepId della tabella Customer.

        Condizione:
            c.Country = country

        Quindi:
            prendo i dipendenti che supportano almeno un cliente
            appartenente al paese selezionato.

        Uso DISTINCT perché:
            un dipendente può supportare più clienti dello stesso paese,
            ma nel grafo il dipendente deve comparire una sola volta.

        Cosa ritorna?
            Una lista di oggetti Employee.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT e.EmployeeId,
                            e.FirstName,
                            e.LastName,
                            e.Title
            FROM Employee e,
                 Customer c
            WHERE e.EmployeeId = c.SupportRepId
              AND c.Country = %s
            ORDER BY e.LastName, e.FirstName
        """

        cursor.execute(query, (country,))

        for row in cursor:
            employee = Employee(
                EmployeeId=row["EmployeeId"],
                FirstName=row["FirstName"],
                LastName=row["LastName"],
                Title=row["Title"]
            )

            result.append(employee)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getFatturatoEmployee(country):
        """
        FUNZIONE 3
        ----------
        Calcola il fatturato supportato da ogni dipendente
        nel paese selezionato.

        Traccia:
            per ogni dipendente si calcola il fatturato supportato
            come somma delle Invoice dei clienti supportati.

        Tabelle usate:
            Employee
            Customer
            Invoice

        Collegamento logico:
            Employee.EmployeeId = Customer.SupportRepId
            Customer.CustomerId = Invoice.CustomerId

        Quindi:
            prendo tutte le fatture dei clienti supportati da quel dipendente
            e sommo Invoice.Total.

        Condizione:
            c.Country = country

        Cosa ritorna?
            Un dizionario:

            {
                EmployeeId: fatturato,
                EmployeeId: fatturato,
                ...
            }

        Esempio:
            {
                3: 156.42,
                4: 247.17,
                5: 120.03
            }

        Questo dizionario serve nel Model per:
            - decidere il verso dell'arco;
            - calcolare il peso dell'arco.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return {}

        result = {}

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT e.EmployeeId,
                   SUM(i.Total) AS fatturato
            FROM Employee e,
                 Customer c,
                 Invoice i
            WHERE e.EmployeeId = c.SupportRepId
              AND c.CustomerId = i.CustomerId
              AND c.Country = %s
            GROUP BY e.EmployeeId
        """

        cursor.execute(query, (country,))

        for row in cursor:
            employee_id = row["EmployeeId"]
            fatturato = float(row["fatturato"])

            result[employee_id] = fatturato

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllEdges(country):
        """
        FUNZIONE 4
        ----------
        Estrae gli archi grezzi del grafo.

        Traccia:
            due dipendenti sono collegati se i clienti da loro supportati
            hanno acquistato almeno un genere musicale in comune.

        Qui NON calcolo:
            - peso;
            - verso.

        Qui calcolo solo:
            id1, id2

        cioè:
            "questi due dipendenti devono essere collegati".

        Tabelle usate nella prima catena:
            Employee e1
            Customer c1
            Invoice i1
            InvoiceLine il1
            Track t1

        Tabelle usate nella seconda catena:
            Employee e2
            Customer c2
            Invoice i2
            InvoiceLine il2
            Track t2

        Prima catena:
            dipendente 1 -> clienti supportati -> fatture -> righe fattura -> brani -> genere

        Seconda catena:
            dipendente 2 -> clienti supportati -> fatture -> righe fattura -> brani -> genere

        Condizione fondamentale:
            t1.GenreId = t2.GenreId

        Significa:
            i clienti supportati dai due dipendenti hanno acquistato
            almeno un genere musicale in comune.

        Condizione anti-duplicato:
            e1.EmployeeId < e2.EmployeeId

        Perché?
            Perché qui sto ancora creando una relazione grezza.
            Non voglio ottenere sia:
                3 - 4
                4 - 3

            Il verso verrà deciso dopo nel Model.

        Cosa ritorna?
            Lista di oggetti Arco(id1, id2).
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DISTINCT e1.EmployeeId AS id1,
                            e2.EmployeeId AS id2
            FROM Employee e1,
                 Customer c1,
                 Invoice i1,
                 InvoiceLine il1,
                 Track t1,

                 Employee e2,
                 Customer c2,
                 Invoice i2,
                 InvoiceLine il2,
                 Track t2

            WHERE e1.EmployeeId = c1.SupportRepId
              AND c1.CustomerId = i1.CustomerId
              AND i1.InvoiceId = il1.InvoiceId
              AND il1.TrackId = t1.TrackId

              AND e2.EmployeeId = c2.SupportRepId
              AND c2.CustomerId = i2.CustomerId
              AND i2.InvoiceId = il2.InvoiceId
              AND il2.TrackId = t2.TrackId

              AND c1.Country = %s
              AND c2.Country = %s

              AND t1.GenreId = t2.GenreId

              AND e1.EmployeeId < e2.EmployeeId
        """

        cursor.execute(query, (country, country))

        for row in cursor:
            arco = Arco(
                id1=row["id1"],
                id2=row["id2"]
            )

            result.append(arco)

        cursor.close()
        conn.close()

        return result
