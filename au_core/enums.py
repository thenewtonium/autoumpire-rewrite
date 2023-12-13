"""
enums.py

Defines the various enum types used by AutoUmpire
"""

from enum import Enum

class NiceEnum(Enum):
    """
    Base enum class with a nicer __repr__ function
    """
    def __repr__(self) -> str:
        """
        :return: the value of the enum instance
        """
        return self.value

class RegType(NiceEnum):
    """
    Registration type enum
    Values are
        FULL - a Full Player
        POLICE - a member of the Police
    """
    FULL = "Full Player"
    POLICE = "Police"

class WaterStatus(NiceEnum):
    """
    Water Weapons Status enum
    Values are
        NONE - No Water
        CARE - Water With Care
        FULL - Full Water
    """
    NONE = "No Water"
    CARE = "Water With Care"
    FULL = "Full Water"

class College(NiceEnum):
    """
    College enum
    Gives possible college options, including NONE for "The Real World"
    """
    NONE = "The Real World"
    CHRISTS = "Christ's"
    CHURCHILL = "Churchill"
    CLARE = "Clare"
    CLARE_HALL = "Clare Hall"
    CORPUS = "Corpus Christi"
    DARWIN = "Darwin"
    DOWNING = "Downing"
    EMMA = "Emmanuel"
    FITZ = "Fitzwilliam"
    GIRTON = "Girton"
    CAUIS = "Gonville & Caius"
    HOMERTON = "Homerton"
    HUGHES = "Hughes Hall"
    JESUS = "Jesus"
    KINGS = "King's"
    LCAV = "Lucy Cavendish"
    MAGD = "Magdalene"
    MEDWARDS = "Murray Edwards"
    NEWNHAM = "Newnham"
    PEM = "Pembroke"
    PETERHOUSE = "Peterhouse"
    QUEENS = "Queens'"
    ROBO = "Robinson"
    SELWYN = "Selwyn"
    SIDNEY = "Sidney Sussex"
    CATZ = "St Catharine's"
    EDDIES = "St Edmund's"
    JOHNS = "St John's"
    TRIN = "Trinity"
    TIT_HALL = "Trinity Hall"
    WOLFSON = "Wolfson"