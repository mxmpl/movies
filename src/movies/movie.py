import dataclasses
import datetime
import json
import time
from typing import Self

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36"
    + "(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}


@dataclasses.dataclass
class Movie:
    imdb_id: str
    title: str
    original_title: str
    year: int | None
    duration_in_sec: int | None
    poster: str | None
    rating: int
    director: str | None
    actors: str | None
    genres: list[str] | None
    my_rating: int | None = None
    watched: bool = False
    watched_date: datetime.date | None = None
    cinema: bool = False
    comment: str | None = None

    def __post_init__(self):
        assert 0 <= self.rating <= 10
        if not self.watched:
            assert self.watched_date is None
            assert not self.cinema
            assert self.my_rating is None
        if self.my_rating is not None:
            assert 0 <= self.my_rating <= 10

    @property
    def to_notion(self) -> dict[str, str | int | list[str] | datetime.date | None]:
        return {
            "Title": self.title,
            "IMDb id": self.imdb_id,
            "Rating": self.my_rating,
            "Watched": self.watched,
            "Original title": self.original_title,
            "Year": self.year,
            "Duration": time.strftime("%-Hh%M", time.gmtime(self.duration_in_sec)),
            "Genres": self.genres,
            "Director": self.director,
            "Actors": self.actors,
            "IMDb rating": self.rating,
            "Comment": self.comment,
            "Watched date": self.watched_date,
            "Cinema": self.cinema,
        }

    @property
    def to_sqlite(self) -> tuple:
        movie_dict = dataclasses.asdict(self)
        movie_dict["genres"] = ", ".join(movie_dict["genres"])
        return tuple(movie_dict.values())

    @classmethod
    def from_sqlite(cls, movie_dict: dict) -> Self:
        if movie_dict["genres"] is not None:
            movie_dict["genres"] = movie_dict["genres"].split(", ")
        if movie_dict["watched_date"] is not None:
            movie_dict["watched_date"] = datetime.datetime.strptime(movie_dict["watched_date"], "%Y-%m-%d").date()
        movie_dict["watched"] = bool(movie_dict["watched"])
        movie_dict["cinema"] = bool(movie_dict["cinema"])
        return cls(**movie_dict)

    @classmethod
    def from_imdb(cls, imdb_id: str) -> Self:
        response = requests.get("https://www.imdb.com/title/" + imdb_id, headers=HEADERS)
        if not response.ok:
            response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser").find("script", id="__NEXT_DATA__")
        data = json.loads(soup.string)["props"]["pageProps"]["aboveTheFoldData"]  # type: ignore
        duration = None if data["runtime"] is None else data["runtime"]["seconds"]
        poster = None if data["primaryImage"] is None else data["primaryImage"]["url"]
        year = None if data["releaseYear"] is None else data["releaseYear"]["year"]
        genres = None if data["genres"] is None else [genre["text"] for genre in data["genres"]["genres"]]

        credits = {}
        for credit in data["principalCredits"]:
            credits[credit["category"]["text"]] = ", ".join(
                [name["name"]["nameText"]["text"] for name in credit["credits"]]
            )
        director = None if "Director" not in credits else credits["Director"]
        actors = None if "Stars" not in credits else credits["Stars"]
        return cls(
            imdb_id=imdb_id,
            title=data["titleText"]["text"],
            original_title=data["originalTitleText"]["text"],
            year=year,
            duration_in_sec=duration,
            poster=poster,
            rating=data["ratingsSummary"]["aggregateRating"],
            director=director,
            actors=actors,
            genres=genres,
        )
