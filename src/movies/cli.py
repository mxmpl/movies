import argparse
import datetime
import os
from enum import StrEnum

from movies import version_long
from movies.database import Database, NotionDatabase, SQLiteDatabase
from movies.movie import Movie


class NotionEnv(StrEnum):
    AUTH = os.environ.get("NOTION_AUTH", "")
    DATABASE = os.environ.get("NOTION_DATABASE", "")


def parser_notion(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("notion", description="add a movie to Notion database")
    parser.add_argument("auth", type=str, help="authentication key")
    parser.add_argument("database_id", type=str, help="database id")


def parser_sqlite(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("sqlite", description="add a movie to SQLite database")
    parser.add_argument("path", type=str, help="path to the database")


def parser_add(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("add", description="add a movie to a database")
    group = parser.add_argument_group("movie")
    group.add_argument("imdb_id", type=str, help="IMDb identifier of the movie")
    group.add_argument("--rating", type=int, help="your rating")
    group.add_argument("--watched", action="store_true")
    group.add_argument("--date", type=str, help="when you watched the movie, formatted %%Y-%%m-%%d")
    group.add_argument("--cinema", action="store_true", help="whether you have seen it at the theater or not")

    subsubparsers = parser.add_subparsers(title="database", help="which database to add movies to", dest="database")
    parser_notion(subsubparsers)
    parser_sqlite(subsubparsers)


def command_add(args: argparse.Namespace) -> None:
    movie = Movie.from_imdb(args.imdb_id)
    movie.watched = args.watched or args.cinema is not None or args.date is not None or args.rating is not None
    if args.date is not None:
        movie.watched_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    movie.cinema = args.cinema
    movie.rating = args.rating
    database: Database
    if args.database == "notion":
        auth = args.auth if args.auth is not None else NotionEnv.AUTH
        database_id = args.database_id if args.database_id is not None else NotionEnv.DATABASE
        if not auth or not database_id:
            raise ValueError(
                "Invalid Notion environment: must set the Notion "
                + "environment variables or provide both --auth and --database_id arguments"
            )
        database = NotionDatabase(auth, database_id)
    elif args.database == "sqlite":
        database = SQLiteDatabase(args.path)
    else:
        raise ValueError("Supported commands are `notion` or `sqlite`")
    database.insert(movie)


def parser_fetch(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("fetch", description="Fetch a Notion database to a new SQLite database")
    parser.add_argument("path", type=str, help="path to the SQLite database")
    parser.add_argument("--auth", type=str, help="Notion authentication key")
    parser.add_argument("--database_id", type=str, help="Notion database id")


def command_fetch(args: argparse.Namespace) -> None:
    auth = args.auth if args.auth is not None else NotionEnv.AUTH
    database_id = args.database_id if args.database_id is not None else NotionEnv.DATABASE
    if not auth or not database_id:
        raise ValueError(
            "Invalid Notion environment: must set the Notion "
            + "environment variables or provide both --auth and --database_id arguments"
        )
    notion = NotionDatabase(auth, database_id)
    movies = notion.fetchall()
    sqlite = SQLiteDatabase(args.path)
    sqlite.insert(movies)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI to add a movie to a Notion or SQLite database using its IMDb identifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V", "--version", action="version", version=version_long(), help="display version and copyright information"
    )
    subparsers = parser.add_subparsers(title="command", help="available commands", dest="command")
    parser_add(subparsers)
    parser_fetch(subparsers)

    args = parser.parse_args()
    if args.command == "add":
        command_add(args)
    elif args.command == "fetch":
        command_fetch(args)
    else:
        raise ValueError("Use either the `add` or `fetch` command")


if __name__ == "__main__":
    main()
