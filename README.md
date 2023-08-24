# Personal movie database

Build your own movie database in Notion and SQLite.
This repo provides a CLI to retrieve movies from IMDb and add them to a Notion or SQLite database, with your personal rating, watched date, etc.

## Installation

With pip:

`pip install git+https://github.com/mxmpl/movies.git`

## Usage

There are two commands:
- `movies add`: to add a movie to a database given its IMDb identifier.
- `movies fetch`: to copy a Notion database to a local SQLite database.

Use `movies -h`, `movies add -h` or `movies fetch -h` for more information.

If you don't want to provide your Notion authentication key and database id each time, set the environment variables `NOTION_AUTH` and `NOTION_DATABASE`.
