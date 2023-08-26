import dataclasses
import datetime
import json
import time
from typing import Any, Self

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36"
    + "(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}


def _content_to_property(content: str) -> dict:
    return {"type": "rich_text", "rich_text": [{"type": "text", "text": {"content": content}}]}


def _property_to_content(property: dict) -> str:
    return property["rich_text"][0]["plain_text"]


@dataclasses.dataclass
class Movie:
    imdb_id: str
    title: str
    original_title: str
    release_date: datetime.date | None
    duration_in_sec: int | None
    poster: str | None
    director: str
    actors: str
    genres: list[str]
    rating: int | None = None
    watched: bool = False
    watched_date: datetime.date | None = None
    cinema: bool = False
    comment: str = ""

    def __post_init__(self):
        if not self.watched:
            assert self.watched_date is None
            assert not self.cinema
            assert self.rating is None
        if self.rating is not None:
            assert 0 <= self.rating <= 10

    @property
    def to_notion(self) -> dict[str, Any]:
        duration = "" if self.duration_in_sec is None else time.strftime("%-Hh%M", time.gmtime(self.duration_in_sec))
        properties = {
            "IMDb id": {"type": "title", "title": [{"type": "text", "text": {"content": self.imdb_id}}]},
            "Title": _content_to_property(self.title),
            "Rating": {"type": "number", "number": self.rating},
            "Watched": {"type": "checkbox", "checkbox": self.watched},
            "Original title": _content_to_property(self.original_title),
            "Duration": _content_to_property(duration),
            "Genres": {"type": "multi_select", "multi_select": [{"name": genre} for genre in self.genres]},
            "Director": _content_to_property(self.director),
            "Actors": _content_to_property(self.actors),
            "Comment": _content_to_property(self.comment),
            "Cinema": {"type": "checkbox", "checkbox": self.cinema},
        }
        if self.release_date is not None:
            properties["Release date"] = {"type": "date", "date": {"start": self.release_date.strftime("%Y-%m-%d")}}
        if self.watched_date is not None:
            properties["Watched date"] = {"type": "date", "date": {"start": self.watched_date.strftime("%Y-%m-%d")}}
        if self.poster is None:
            return {"properties": properties}
        return {"properties": properties, "cover": {"type": "external", "external": {"url": self.poster}}}

    @classmethod
    def from_notion(cls, entry: dict) -> Self:
        poster = entry["cover"]["external"]["url"]
        properties = entry["properties"]
        duration_split = properties["Duration"]["rich_text"][0]["plain_text"].split("h")
        if duration_split != [""]:
            hours, minutes = properties["Duration"]["rich_text"][0]["plain_text"].split("h")
            duration_in_sec = int(hours) * 3600 + int(minutes) * 60
        else:
            duration_in_sec = None
        date = (
            None
            if properties["Watched date"]["date"] is None
            else datetime.datetime.strptime(properties["Watched date"]["date"]["start"], "%Y-%m-%d").date()
        )
        release_date = (
            None
            if properties["Release date"]["date"] is None
            else datetime.datetime.strptime(properties["Release date"]["date"]["start"], "%Y-%m-%d").date()
        )
        return cls(
            imdb_id=properties["IMDb id"]["title"][0]["text"]["content"],
            title=_property_to_content(properties["Title"]),
            original_title=_property_to_content(properties["Original title"]),
            release_date=release_date,
            duration_in_sec=duration_in_sec,
            poster=poster,
            director=_property_to_content(properties["Director"]),
            actors=_property_to_content(properties["Actors"]),
            genres=[genre["name"] for genre in properties["Genres"]["multi_select"]],
            rating=properties["Rating"]["number"],
            watched=properties["Watched"]["checkbox"],
            watched_date=date,
            cinema=properties["Cinema"]["checkbox"],
            comment=_property_to_content(properties["Comment"]),
        )

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
        if movie_dict["release_date"] is not None:
            movie_dict["release_date"] = datetime.datetime.strptime(movie_dict["release_date"], "%Y-%m-%d").date()
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
        release_date = (
            None
            if data["releaseDate"] is None
            else datetime.date(data["releaseDate"]["year"], data["releaseDate"]["month"], data["releaseDate"]["day"])
        )
        genres = [genre["text"] for genre in data["genres"]["genres"]]

        creds = {}
        for cred in data["principalCredits"]:
            creds[cred["category"]["text"]] = ", ".join([name["name"]["nameText"]["text"] for name in cred["credits"]])
        director = creds["Director"] if "Director" in creds else creds["Directors"] if "Directors" in creds else ""
        actors = "" if "Stars" not in creds else creds["Stars"]
        return cls(
            imdb_id=imdb_id,
            title=data["titleText"]["text"],
            original_title=data["originalTitleText"]["text"],
            release_date=release_date,
            duration_in_sec=duration,
            poster=poster,
            director=director,
            actors=actors,
            genres=genres,
        )
