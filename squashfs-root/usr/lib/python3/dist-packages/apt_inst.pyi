
class ArArchive:
    def extract(self) -> None: ...

class DebFile:
    def __init__(self, file: object) -> None: ...
    control: TarFile
    data: TarFile

class TarFile:
    def extractdata(self, member: str) -> bytes: ...
