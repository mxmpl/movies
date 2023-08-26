import abc
import dataclasses
import os
import sqlite3

from movies.movie import Movie


@dataclasses.dataclass
class Database(abc.ABC):
    @abc.abstractmethod
    def insert(self, movie: Movie | list[Movie]) -> None:
        """Insert movies in the database"""

    @abc.abstractmethod
    def select(self, imdb_id: str) -> Movie | None:
        """Find the movie by its IMDb identifier"""

    @abc.abstractmethod
    def fetchall(self) -> list[Movie]:
        """Return all movies in the database"""


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

    def fetchall(self) -> list[Movie]:
        cursor = self._cursor.execute("SELECT * FROM movies")
        column_names = [member[0] for member in cursor.description]
        return [Movie.from_sqlite(dict(zip(column_names, row))) for row in list(cursor)]


@dataclasses.dataclass
class NotionDatabase(Database):
    auth: str | None = None
    database_id: str | None = None

    def __post_init__(self):
        if self.auth is None:
            self.auth = os.environ.get("NOTION_AUTH", "")
        if self.database_id is None:
            self.database_id = os.environ.get("NOTION_DATABASE", "")
        if not self.auth or not self.database_id:
            raise ValueError(
                "Invalid Notion environment: must set the Notion "
                + "environment variables or provide both auth and database_id arguments"
            )
        try:
            from notion_client import Client
        except ImportError as error:
            raise ImportError("Install notion_client with `pip install notion-client` to use NotionWriter") from error
        self._client = Client(auth=self.auth)

    def insert(self, movies: Movie | list[Movie]) -> None:
        to_insert = [movies] if isinstance(movies, Movie) else movies
        for movie in to_insert:
            self._client.pages.create(parent={"database_id": self.database_id}, **movie.to_notion)

    def select(self, imdb_id: str) -> Movie | None:
        results = self._client.databases.query(
            **{"database_id": self.database_id, "filter": {"property": "IMDb id", "title": {"equals": imdb_id}}}
        ).get("results")
        if results is None:
            return None
        if len(results) != 1:
            raise ValueError(f"Multiple entries with IMDb id {imdb_id}")
        return Movie.from_notion(results[0])

    def fetchall(self) -> list[Movie]:
        movies, has_more, start_cursor = [], True, None
        while has_more:
            response = self._client.databases.query(database_id=self.database_id, start_cursor=start_cursor)
            movies += [Movie.from_notion(movie) for movie in response["results"]]
            has_more, start_cursor = response["has_more"], response["next_cursor"]
        return movies
