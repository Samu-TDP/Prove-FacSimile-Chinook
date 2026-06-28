from dataclasses import dataclass


@dataclass(frozen=True)
class Album:
    AlbumId: int
    Title: str
    ArtistId: int
    ArtistName: str

    def __str__(self):
        return self.Title
