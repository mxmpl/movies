import abc
import dataclasses
import sqlite3

from movies.movie import Movie


@dataclasses.dataclass
class Database(abc.ABC):
    @abc.abstractmethod
    def insert(self, pages: Movie | list[Movie]) -> None:
        """Insert movies in the database"""

    @abc.abstractmethod
    def select(self, imdb_id: str) -> Movie | None:
        """Find the movie by its IMDb identifier"""


@dataclasses.dataclass
class SQLiteDatabase(Database):
    path: str

    def __post_init__(self):
        self._connection = sqlite3.connect(self.path)
        self._cursor = self._connection.cursor()
        fields = Movie.__dataclass_fields__.keys()
        self._insert_cmd = f"INSERT INTO movies VALUES({', '.join(['?']*len(fields))})"
        table_names = self._cursor.execute("SELECT name FROM sqlite_master").fetchone()
        if table_names is None or "movies" not in table_names:
            print(table_names)
            self._cursor.execute(f"CREATE TABLE movies({', '.join(fields)})")

    def insert(self, movies: Movie | list[Movie]) -> None:
        if isinstance(movies, Movie):
            params = [movies.to_sqlite]
        else:
            params = [page.to_sqlite for page in movies]
        self._cursor.executemany(self._insert_cmd, params)
        self._connection.commit()

    def select(self, imdb_id: str) -> Movie | None:
        cursor = self._cursor.execute("SELECT * FROM movies WHERE imdb_id=?", (imdb_id,))
        column_names = [member[0] for member in cursor.description]
        rows = list(cursor)
        if not rows:
            return None
        if len(rows) != 1:
            raise ValueError(f"Multiple entries with IMDb id {imdb_id}")
        return Movie.from_sqlite(dict(zip(column_names, rows[0])))


@dataclasses.dataclass
class NotionDatabase(Database):
    auth: str
    database_id: str

    def __post_init__(self):
        try:
            from notion_client import Client
        except ImportError as error:
            raise ImportError("Install notion_client with `pip install notion-client` to use NotionWriter") from error
        self._client = Client(auth=self.auth)

    def insert(self, movies: Movie | list[Movie]) -> None:
        if isinstance(movies, Movie):
            params = [movies.to_notion]
        else:
            params = [page.to_notion for page in movies]
        self._client.pages.create(parent={"database_id": self.database_id}, properties=params)

    def select(self, imdb_id: str) -> Movie | None:
        return None  # TODO: query Notion database
