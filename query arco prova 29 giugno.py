#Dataclass arco relazione grezza
#peso calcolato in una funzione dao diversa riguardante la popolarita

SELECT DISTINCT
    c1.CustomerId AS id1,
    c2.CustomerId AS id2

FROM Customer c1,
     Invoice i1,
     InvoiceLine il1,
     Track t1,
     Album al1,
     Artist ar1,

     Customer c2,
     Invoice i2,
     InvoiceLine il2,
     Track t2,
     Album al2,
     Artist ar2

WHERE c1.CustomerId = i1.CustomerId
  AND i1.InvoiceId = il1.InvoiceId
  AND il1.TrackId = t1.TrackId
  AND t1.AlbumId = al1.AlbumId
  AND al1.ArtistId = ar1.ArtistId

  AND c2.CustomerId = i2.CustomerId
  AND i2.InvoiceId = il2.InvoiceId
  AND il2.TrackId = t2.TrackId
  AND t2.AlbumId = al2.AlbumId
  AND al2.ArtistId = ar2.ArtistId

  AND ar1.ArtistId = ar2.ArtistId

  AND c1.CustomerId < c2.CustomerId

ORDER BY c1.CustomerId, c2.CustomerId;
