import argparse
import datetime
from importlib.metadata import version

from .database import NotionDatabase, SQLiteDatabase
from .movie import Movie


def parser_add(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("add", description="add a movie to a Notion database")
    parser.add_argument("imdb_id", type=str, help="IMDb identifier of the movie")
    parser.add_argument("--rating", type=int, help="your rating")
    parser.add_argument("--watched", action="store_true", help="whether you have seen it or not")
    parser.add_argument("--cinema", action="store_true", help="whether you have seen it at the theater or not")
    parser.add_argument(
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="when you watched the movie, formatted %%Y-%%m-%%d",
    )


def parser_fetch(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("fetch", description="Fetch a Notion database to a new SQLite database")
    parser.add_argument("path", type=str, help="path to the SQLite database")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI to add a movie to a Notion database using its IMDb identifier, "
        + "or fetch a Notion database to a SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=version("movies"), help="display version")
    subparsers = parser.add_subparsers(title="command", help="available commands", dest="command")
    parser_add(subparsers)
    parser_fetch(subparsers)

    args = parser.parse_args()
    if args.command == "add":
        movie = Movie.from_imdb(args.imdb_id)
        movie.watched = args.watched or args.cinema or (args.date is not None) or (args.rating is not None)
        movie.watched_date = args.watched_date
        movie.cinema = args.cinema
        movie.rating = args.rating
        NotionDatabase().insert(movie)
    elif args.command == "fetch":
        movies = NotionDatabase().fetchall()
        sqlite = SQLiteDatabase(args.path)
        sqlite.insert(movies)
    else:
        raise ValueError("Use either the `add` or `fetch` command")


if __name__ == "__main__":
    main()
