import datetime
import textwrap

from movies.movie import Movie
from movies.writer import NotionDatabase, SQLiteDatabase

__version__ = 1.0
__all__ = ["Movie", "NotionDatabase", "SQLiteDatabase"]


def version_long() -> str:
    """Returns a long description with version, copyrigth and licence info"""
    return textwrap.dedent(
        f"""\
        movies-{__version__}
        copyright 2023-{datetime.date.today().year} Maxime Poli
        licence GPL3: this is free software, see the source for copying conditions
        """
    )
