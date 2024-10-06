# Copyright 2024 Charles Theall Jr
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import pathlib
import sqlite3
import tempfile
import unittest
import zoneinfo

from typing import Union

import todo

MODULE_DIR = pathlib.Path(__file__).parent


def sqlite3_setup():
    """ Perform setup for test using SQLite3.

        Creates a temporary database file and loads the database schema and test data into it.

        :returns: The name of the temporary database file.
    """
    db = tempfile.mkstemp("todo_cli_sqlite3")[1]

    try:
        with sqlite3.connect(db) as conn:
            conn.executescript(todo.sql.sqlite3.CREATE_TODO_TABLE)
            with open(MODULE_DIR.joinpath("test_data.sql"), "r") as f:
                conn.executescript(f.read())

    except Exception as e:
        remove_file(db)  # remove file on exception
        raise  # continue raising the exception

    return db


def json_setup():
    """ Perform setup for test using JSON.

        Copies the test_data.json file to a temporary file.

        :returns: The name of the temporary file.
    """
    db = tempfile.mkstemp("todo_cli_json")[1]

    with open(MODULE_DIR.joinpath("test_data.json"), "r") as src:
        with open(db, "w") as out:
            out.write(src.read())

    return db


def remove_file(name: Union[str, pathlib.Path]):
    """ Remove file.

        :param str name: name of file to remove.
    """
    if name:
        os.remove(name)


def remove_dir(name:  Union[str, pathlib.Path]):
    """ Remove directory and all its contents.

        :param str name: name of directory to remove, can be a filename in which case the parent directory is removed.
    """
    if name:
        p = pathlib.Path(name)
        if p.is_file():
            p = p.parent
        # Remove all files within directory (this assumes the directory does not contains sub-directories)
        for f in p.iterdir():
            f.unlink()
        p.rmdir()


class TestTODOApp(unittest.TestCase):
    """ Unit tests for todo.TODOApp. """

    def test_load(self):
        """ Tests for TODOApp.load(). """
        tests = [
            {
                "test_name": "json successful load existing file",
                "db_type": "json",
                "db": MODULE_DIR.joinpath("test_data.json"),
                "exception": None,
                "setup_func": None,
                "expect": {
                    "Todo 1": {
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                    },
                    "Todo 2": {
                        "description": "this is a description of Todo 2",
                        "done": True,
                    },
                    "Todo 3": {
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                    },
                    "Todo 4": {
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                    },
                },
            },
            {
                "test_name": "invalid db_type",
                "db_type": "pgsql",
                "db": "",
                "exception": ValueError("only json or sqlite3 are supported database file types"),
                "setup_func": None,
                "expect": {},
            },
            {
                "test_name": "sqlite3 successful load existing file",
                "db_type": "sqlite3",
                "setup_func": sqlite3_setup,
                "teardown_func": remove_file,
            },
            {
                "test_name": "sqlite3 successful load non-existing file",
                "db_type": "sqlite3",
                "setup_func": lambda: pathlib.Path(tempfile.mkdtemp("todo_cli_sqlite3"), "todo.sqlite3"),
                "teardown_func": remove_dir,
            },
        ]

        for tt in tests:
            with self.subTest(tt["test_name"]):
                db = tt.get("db", None)

                try:
                    if tt.get("setup_func", None):
                        # Call test case specific setup function (if defined)
                        db = tt["setup_func"]()

                    app = todo.TodoApp(db, tt["db_type"])

                    if tt.get("exception", None):
                        with self.assertRaises(type(tt["exception"])) as e:
                            app.load()

                        self.assertEqual(tt["exception"].args,
                                     e.exception.args, "load exception args")
                    else:
                        app.load()

                    if tt["db_type"] == "json":
                        # For JSON file, check internal data
                        self.assertDictEqual(tt["expect"], app._todos)
                    elif tt["db_type"] == "sqlite3":
                        # For SQLite3 database file, check internal connection and use it to check that the schema is as expected
                        self.assertIsInstance(app._conn, sqlite3.Connection)
                        if isinstance(app._conn, sqlite3.Connection):
                            res = app._conn.execute("SELECT sql FROM sqlite_master WHERE name='todo'").fetchone()
                            self.assertEqual(todo.sql.sqlite3.CREATE_TODO_TABLE, res["sql"])
                finally:
                    if tt.get("teardown_func", None):
                        # Call test case specific teardown function (if defined)
                        tt["teardown_func"](db)

    def test_list(self):
        """ Tests for TODOApp.list(). """
        tests = [
            {
                "test_name": "sort by name asc",
                "exception": None,
                "sort_by": "name",
                "sort_order": "asc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                ],
            },
            {
                "test_name": "sort by name desc",
                "exception": None,
                "sort_by": "name",
                "sort_order": "desc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                ],
            },
            {
                "test_name": "sort by description asc",
                "exception": None,
                "sort_by": "description",
                "sort_order": "asc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                ],
            },
            {
                "test_name": "sort by description desc",
                "exception": None,
                "sort_by": "description",
                "sort_order": "desc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                ],
            },
            {
                "test_name": "sort by due_date asc",
                "exception": None,
                "sort_by": "due_date",
                "sort_order": "asc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                ],
            },
            {
                "test_name": "sort by due_date desc",
                "exception": None,
                "sort_by": "due_date",
                "sort_order": "desc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                ],
            },
            {
                "test_name": "sort by done asc",
                "exception": None,
                "sort_by": "done",
                "sort_order": "asc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                ],
            },
            {
                "test_name": "sort by done desc",
                "exception": None,
                "sort_by": "done",
                "sort_order": "desc",
                "setup_func": None,
                "expect": [
                    {
                        "name": "Todo 2",
                        "description": "this is a description of Todo 2",
                        "due_date": "",
                        "done": True,
                    },
                    {
                        "name": "Todo 1",
                        "description": "This is a description of Todo 1",
                        "due_date": "2024-10-10T17:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 3",
                        "description": "This is a description of Todo 3",
                        "due_date": "2024-10-08T14:00Z",
                        "done": False,
                    },
                    {
                        "name": "Todo 4",
                        "description": "This is a description of Todo 4",
                        "due_date": "2024-10-20T22:00Z",
                        "done": False,
                    },
                ],
            },
            {
                "test_name": "sort by invalid desc",
                "exception": ValueError("Invalid sort by, valid values are: [description, done, due_date, name]"),
                "sort_by": "invalid",
                "sort_order": "desc",
                "setup_func": None,
                "expect": [],
            },
            {
                "test_name": "sort by name invalid",
                "exception": ValueError("Invalid order by, valid values are: [asc, desc]"),
                "sort_by": "name",
                "sort_order": "invalid",
                "setup_func": None,
                "expect": [],
            },
        ]

        db_backends = [
            {
                "db_type": "json",
                "db": MODULE_DIR.joinpath("test_data.json"),
            },
            {
                "db_type": "sqlite3",
                "setup_func": sqlite3_setup,
                "teardown_func": remove_file,
            },
        ]

        for db_backend in db_backends:
            for tt in tests:
                with self.subTest(f"{db_backend['db_type']}-{tt['test_name']}"):
                    db = db_backend.get("db", None)

                    try:
                        if db_backend.get("setup_func", None):
                            # Call db backend specific setup function (if defined)
                            db = db_backend["setup_func"]()

                        app = todo.TodoApp(db, db_backend["db_type"])
                        app.load()

                        try:
                            got = []
                            if tt.get("exception", None):
                                with self.assertRaises(type(tt["exception"])) as e:
                                    got = app.list(
                                        sort_by=tt["sort_by"], sort_order=tt["sort_order"])
                                self.assertEqual(
                                    tt["exception"].args, e.exception.args, "list exception args")
                            else:
                                got = app.list(
                                    sort_by=tt["sort_by"], sort_order=tt["sort_order"])
                        finally:
                            app.close()

                        self.assertListEqual(tt["expect"], got)
                    finally:
                        if db_backend.get("teardown_func", None):
                            # Call db backend specific teardown function (if defined)
                            db_backend["teardown_func"](db)

    def test_add(self):
        """ Tests for TODOApp.add(). """
        tests = [
            {
                "test_name": "Todo 5 no description, no due date",
                "input": {
                    "name": "Todo 5",
                },
                "expect": {
                    "description": "",
                    "due_date": "",
                    "done": False,
                },
            },
            {
                "test_name": "Todo 4 already exists",
                "input": {
                    "name": "Todo 4",
                },
                "exception": ValueError("A Todo item with the requested name already exists"),
                "expect": {},
            },
            {
                "test_name": "Todo 5 description, no due date",
                "input": {
                    "name": "Todo 5",
                    "description": "this is a description of Todo 5",
                },
                "expect": {
                    "description": "this is a description of Todo 5",
                    "due_date": "",
                    "done": False,
                },
            },
            {
                "test_name": "Todo 5 no description, due date in UTC",
                "input": {
                    "name": "Todo 5",
                    "due_date": datetime.datetime(2024, 10, 10, 16, 0, tzinfo=zoneinfo.ZoneInfo("UTC")),
                },
                "expect": {
                    "description": "",
                    "due_date": "2024-10-10T16:00Z",
                    "done": False,
                },
            },
            {
                "test_name": "Todo 5 no description, due date in EDT timezone",
                "input": {
                    "name": "Todo 5",
                    "due_date": datetime.datetime(2024, 10, 10, 16, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York")),
                },
                "expect": {
                    "description": "",
                    "due_date": "2024-10-10T20:00Z",
                    "done": False,
                },
            },
            {
                "test_name": "Todo 5 no description, due date without timezone",
                "input": {
                    "name": "Todo 5",
                    "due_date": datetime.datetime(2024, 10, 10, 16, 0),
                },
                "expect": {
                    "description": "",
                    "due_date": "2024-10-10T16:00Z",
                    "done": False,
                },
            },
        ]

        db_backends = [
            {
                "db_type": "json",
                "setup_func": json_setup,
                "teardown_func": remove_file,
            },
            {
                "db_type": "sqlite3",
                "setup_func": sqlite3_setup,
                "teardown_func": remove_file,
            },
        ]

        for db_backend in db_backends:
            for tt in tests:
                with self.subTest(f"{db_backend['db_type']}-{tt['test_name']}"):
                    db = db_backend.get("db", None)

                    try:
                        if db_backend.get("setup_func", None):
                            # Call db backend specific setup function (if defined)
                            db = db_backend["setup_func"]()

                        app = todo.TodoApp(db, db_backend["db_type"])
                        app.load()

                        try:
                            if tt.get("exception", None):
                                with self.assertRaises(type(tt["exception"])) as e:
                                    app.add(**tt["input"])
                                self.assertEqual(
                                    tt["exception"].args, e.exception.args, "add exception args")
                            else:
                                app.add(**tt["input"])

                                if db_backend["db_type"] == "json":
                                    # For JSON, check internal data
                                    self.assertEqual(tt["expect"], app._todos[tt["input"]["name"]])
                                elif db_backend["db_type"] == "sqlite3":
                                    # For SQLite3, check table
                                    tt["expect"]["name"] = tt["input"]["name"]
                                    res = app._conn.execute("SELECT name, description, due_date, done FROM todo WHERE name = ?", (tt["input"]["name"],)).fetchone()
                                    self.assertEqual(tt["expect"], res)
                        finally:
                            app.close()
                    finally:
                        if db_backend.get("teardown_func", None):
                            # Call db backend specific teardown function (if defined)
                            db_backend["teardown_func"](db)

    def test_remove(self):
        """ Tests for TODOApp.remove(). """
        tests = [
            {
                "test_name": "Todo 4",
                "input": {
                    "name": "Todo 4",
                },
            },
        ]

        db_backends = [
            {
                "db_type": "json",
                "setup_func": json_setup,
                "teardown_func": remove_file,
            },
            {
                "db_type": "sqlite3",
                "setup_func": sqlite3_setup,
                "teardown_func": remove_file,
            },
        ]

        for db_backend in db_backends:
            for tt in tests:
                with self.subTest(f"{db_backend['db_type']}-{tt['test_name']}"):
                    db = db_backend.get("db", None)

                    try:
                        if db_backend.get("setup_func", None):
                            # Call db backend specific setup function (if defined)
                            db = db_backend["setup_func"]()

                        app = todo.TodoApp(db, db_backend["db_type"])
                        app.load()

                        try:
                            if tt.get("exception", None):
                                with self.assertRaises(type(tt["exception"])) as e:
                                    app.remove(**tt["input"])
                                self.assertEqual(
                                    tt["exception"].args, e.exception.args, "remove exception args")
                            else:
                                app.remove(**tt["input"])

                                if db_backend["db_type"] == "json":
                                    # For JSON, check internal data
                                    res = app._todos.get(tt["input"]["name"], None)
                                    self.assertIsNone(res)
                                elif db_backend["db_type"] == "sqlite3":
                                    # For SQLite3, check table
                                    res = app._conn.execute("SELECT name, description, due_date, done FROM todo WHERE name = ?", (tt["input"]["name"],)).fetchone()
                                    self.assertIsNone(res)
                        finally:
                            app.close()
                    finally:
                        if db_backend.get("teardown_func", None):
                            # Call db backend specific teardown function (if defined)
                            db_backend["teardown_func"](db)

    def test_done(self):
        """ Tests for TODOApp.done(). """
        tests = [
            {
                "test_name": "Todo 4",
                "input": {
                    "name": "Todo 4",
                },
                "expect": {
                    "description": "This is a description of Todo 4",
                    "due_date": "2024-10-20T22:00Z",
                    "done": True,
                },
            },
            {
                "test_name": "Todo 5 does not exist",
                "input": {
                    "name": "Todo 5",
                },
                "exception": KeyError("A Todo item with the requested name does not exist"),
            },
        ]

        db_backends = [
            {
                "db_type": "json",
                "setup_func": json_setup,
                "teardown_func": remove_file,
            },
            {
                "db_type": "sqlite3",
                "setup_func": sqlite3_setup,
                "teardown_func": remove_file,
            },
        ]

        for db_backend in db_backends:
            for tt in tests:
                with self.subTest(f"{db_backend['db_type']}-{tt['test_name']}"):
                    db = db_backend.get("db", None)

                    try:
                        if db_backend.get("setup_func", None):
                            # Call db backend specific setup function (if defined)
                            db = db_backend["setup_func"]()

                        app = todo.TodoApp(db, db_backend["db_type"])
                        app.load()

                        try:
                            if tt.get("exception", None):
                                with self.assertRaises(type(tt["exception"])) as e:
                                    app.done(**tt["input"])
                                self.assertEqual(
                                    tt["exception"].args, e.exception.args, "done exception args")
                            else:
                                app.done(**tt["input"])

                                if db_backend["db_type"] == "json":
                                    # For JSON, check internal data
                                    self.assertEqual(tt["expect"], app._todos[tt["input"]["name"]])
                                elif db_backend["db_type"] == "sqlite3":
                                    # For SQLite3, check table
                                    tt["expect"]["name"] = tt["input"]["name"]
                                    res = app._conn.execute("SELECT name, description, due_date, done FROM todo WHERE name = ?", (tt["input"]["name"],)).fetchone()
                                    self.assertEqual(tt["expect"], res)
                        finally:
                            app.close()
                    finally:
                        if db_backend.get("teardown_func", None):
                            # Call db backend specific teardown function (if defined)
                            db_backend["teardown_func"](db)
