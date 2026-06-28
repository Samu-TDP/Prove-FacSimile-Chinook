from dataclasses import dataclass


@dataclass
class Arco:
    id1: int
    id2: int
    peso: int

    def __str__(self):
        return f"{self.id1} - {self.id2}: {self.peso}"
