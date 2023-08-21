import argparse
import datetime

from movies import version_long
from movies.database import Database, NotionDatabase, SQLiteDatabase
from movies.movie import Movie


def parser_notion(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("notion", description="add a movie to Notion database")
    parser.add_argument("auth", type=str, help="authentication key")
    parser.add_argument("database_id", type=str, help="database id")


def parser_sqlite(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("sqlite", description="add a movie to SQLite database")
    parser.add_argument("path", type=str, help="Path to the database")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI to add a movie to a Notion or SQLite database using its IMDb identifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V", "--version", action="version", version=version_long(), help="display version and copyright information"
    )
    group = parser.add_argument_group("movie")
    group.add_argument("imdb_id", type=str, help="IMDb identifier of the movie")
    group.add_argument("--rating", type=int, help="your rating")
    group.add_argument("--date", type=str, help="when you watched the movie, formatted %%Y-%%m-%%d")
    group.add_argument("--cinema", type=bool, help="whether you have seen it at the theater or not", default=False)

    subparsers = parser.add_subparsers(title="database", help="which database to add movies to", dest="database")
    parser_notion(subparsers)
    parser_sqlite(subparsers)

    args = parser.parse_args()
    movie = Movie.from_imdb(args.imdb_id)
    movie.watched_date = None if args.date is None else datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    movie.cinema = args.cinema
    movie.my_rating = args.rating
    database: Database
    if args.database == "notion":
        database = NotionDatabase(args.auth, args.database_id)
    else:
        database = SQLiteDatabase(args.path)
    database.insert(movie)


if __name__ == "__main__":
    main()
