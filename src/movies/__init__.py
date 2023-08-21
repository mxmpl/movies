import datetime
import textwrap

from movies.database import NotionDatabase, SQLiteDatabase
from movies.movie import Movie

__version__ = 1.0
__all__ = ["Movie", "NotionDatabase", "SQLiteDatabase"]


def version_long() -> str:
    """Returns a long description with version, copyright and license info"""
    return textwrap.dedent(
        f"""\
        movies-{__version__}
        copyright 2023-{datetime.date.today().year} Maxime Poli
        license GPL3: this is free software, see the source for copying conditions
        """
    )
