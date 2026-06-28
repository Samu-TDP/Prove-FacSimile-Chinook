from dataclasses import dataclass


@dataclass(frozen=True)
class Genre:
    GenreId: int
    Name: str

    def __str__(self):
        return self.Name
