from database.DB_connect import DBConnect
from model.customer import Customer
from model.invoice import Invoice


class DAO:

    @staticmethod
    def getAllCustomers():
        """
        FUNZIONE 1
        ----------
        Estrae tutti i clienti dal database.

        A cosa serve?
        Serve per popolare il dropdown dei clienti.

        Tabella usata:
            Customer

        Campi estratti:
            CustomerId
            FirstName
            LastName
            Country

        Cosa ritorna?
            Una lista di oggetti Customer.

        Perché salvo CustomerId?
            Nel dropdown l'utente vede nome e cognome,
            ma nel codice devo usare CustomerId per recuperare
            le invoice di quel cliente.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT CustomerId,
                   FirstName,
                   LastName,
                   Country
            FROM Customer
            ORDER BY LastName, FirstName
        """

        cursor.execute(query)

        for row in cursor:
            customer = Customer(
                CustomerId=row["CustomerId"],
                FirstName=row["FirstName"],
                LastName=row["LastName"],
                Country=row["Country"]
            )

            result.append(customer)

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def getAllNodes(customer_id):
        """
        FUNZIONE 2
        ----------
        Estrae i nodi del grafo.

        Traccia:
            i vertici sono tutte le Invoice del cliente selezionato.

        Tabella usata:
            Invoice

        Campi estratti:
            InvoiceId
            CustomerId
            InvoiceDate
            Total

        Condizione:
            CustomerId = customer_id

        Perché ordino per InvoiceDate?
            Perché il grafo è temporale.
            Nel Model devo confrontare le invoice dalla più vecchia
            alla più recente.

        Cosa ritorna?
            Una lista di oggetti Invoice.

        Nota:
            InvoiceDate nel database è DATETIME.
            Lo salvo direttamente nella dataclass Invoice come datetime.
        """

        conn = DBConnect.get_connection()

        if conn is None:
            return []

        result = []

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT InvoiceId,
                   CustomerId,
                   InvoiceDate,
                   Total
            FROM Invoice
            WHERE CustomerId = %s
            ORDER BY InvoiceDate, InvoiceId
        """

        cursor.execute(query, (customer_id,))

        for row in cursor:
            invoice = Invoice(
                InvoiceId=row["InvoiceId"],
                CustomerId=row["CustomerId"],
                InvoiceDate=row["InvoiceDate"],
                Total=float(row["Total"])
            )

            result.append(invoice)

        cursor.close()
        conn.close()

        return result
