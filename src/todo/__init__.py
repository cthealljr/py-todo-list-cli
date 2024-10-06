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

""" A Todo list command-line interface application. """

import argparse
import datetime
import json
import sqlite3
import zoneinfo

import zoneinfo._common

from .sql import sqlite3 as sqlite3_schema


# This function was borrowed from https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
# Copyright 2001-2024 Python Software Foundation
# License: Zero Clause BSD License
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def adapt_bool(v):
    """ Adapt a bool value to integer for sqlite3. """
    return 1 if v else 0

def convert_bool(v):
    """ Convert a bool value from integer to Python bool. """
    return True if v == b"1" else False


sqlite3.register_adapter(bool, adapt_bool)
sqlite3.register_converter("boolean", convert_bool)


class TodoApp:
    """ A Todo list Application. """

    def __init__(self, db: str, db_type: str):
        """ Initialize TODOApp.

            :param str db: path to database file.
            :param str db_type: database file type (json or sqlite3).
        """
        self.db = db
        self.db_type = db_type
        self._todos = {}
        self._conn = None # internal database connection for DB-API 2.0 connections

    def load(self):
        """ Load Todo items from database file.

            :raises ValueError: when self.db_type is an invalid value.
        """
        if self.db_type == "json":
            try:
                with open(self.db, 'r') as f:
                    self._todos = json.load(f)
            except FileNotFoundError:
                pass # File not existing is acceptable as it will be created by self.save()
        elif self.db_type == "sqlite3":
            self._conn = sqlite3.connect(self.db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            self._conn.row_factory = dict_factory
            # Check if database schema exists
            table_check_cur = self._conn.execute("SELECT 1 FROM sqlite_master WHERE name='todo'")
            if table_check_cur.fetchone() is None:
                # Create database schema
                self._conn.executescript(sqlite3_schema.CREATE_TODO_TABLE)
        else:
            raise ValueError("only json or sqlite3 are supported database file types")
        
    def save(self):
        """ Save Todo items back to database file (json only). """
        if self.db_type == "json":
            with open(self.db, 'w') as f:
                json.dump(self._todos, f, indent="\t")

    def close(self):
        """ Close the Todo list application.

            For json: this writes in-memory data back to the original file using self.save

            For sqlite3: this closes the database connection.
        """
        if self.db_type == "json":
            self.save()
        elif self.db_type == "sqlite3":
            self._conn.close()

    def list(self, sort_by: str = "name", sort_order: str = "asc"):
        """ List Todo items.

            :param str sort_by: the Todo item field to sort by (name, description, due_date, done) (default: name)
            :param str sort_order: the order to sort Todo items in (asc for ascending, desc for descending) (default: asc)

            :returns: a list of Todo items, each item is a dictionary and contains the following keys; name, description, due_date, done.

            :raises ValueError: when sort_by or sort_order have invalid values.
        """
        todo_list = []

        if sort_by not in ("name", "description", "done", "due_date"):
            raise ValueError("Invalid sort by, valid values are: [description, done, due_date, name]")
        
        if sort_order not in ("asc", "desc"):
            raise ValueError("Invalid order by, valid values are: [asc, desc]")

        if self.db_type == "json":
            for k in self._todos.keys():
                todo = {"name": k, "due_date": "", "done": False}
                todo.update(self._todos[k])
                todo_list.append(todo)

            todo_list.sort(key=lambda x: x[sort_by], reverse=sort_order=="desc")
        elif self.db_type == "sqlite3":
            sql_sort_by = "name" # sort by name column by default
            # Ensure sort_by is a valid column name and not anything else (e.g. SQL injection)
            if sort_by in ("name", "description", "done", "due_date"):
                sql_sort_by = sort_by

            sql_sort_order = "ASC" # sort in ascending order by default
            # Ensure sort_order is a valid sorting order and not anything else (e.g. SQL injection)
            if sort_order.lower() == "desc":
                sql_sort_order = "DESC"

            todo_list = self._conn.execute(f"{sql.sqlite3.SELECT_ALL_TODO_ITEMS} ORDER BY {sql_sort_by} {sql_sort_order}").fetchall()

        return todo_list

    def add(self, name: str, description: str = "", due_date: datetime.datetime = None):
        """ Add a Todo item.

            :param str name: the name of the Todo item, must be unique among Todo items.
            :param str description: an optional description of the Todo item.
            :param datetime.datetime due_date: an optional due date of the Todo item.

            :raises ValueError: when a Todo item with the requested name already exists.
        """
        due_date_str = ""
        if due_date:
            if due_date.tzinfo:
                if due_date.tzinfo == zoneinfo.ZoneInfo("UTC"):
                    due_date_str = due_date.strftime("%Y-%m-%dT%H:%MZ")
                else:
                    due_date_str = due_date.astimezone(zoneinfo.ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%MZ")
            else:
                # Assume datetime without timezone is UTC
                due_date_str = due_date.strftime("%Y-%m-%dT%H:%MZ")

        if self.db_type == "json":
            if self._todos.get(name, None):
                raise ValueError("A Todo item with the requested name already exists")

            self._todos[name] = {
                "description": description,
                "due_date": due_date_str,
                "done": False,
            }
        elif self.db_type == "sqlite3":
            has_todo_res = self._conn.execute("SELECT 1 FROM todo WHERE name = ?", (name,)).fetchone()
            if has_todo_res:
                raise ValueError("A Todo item with the requested name already exists")

            self._conn.execute(sql.sqlite3.INSERT_TODO_ITEM, (name, description, due_date_str, False,))

    def remove(self, name: str):
        """ Remove a Todo item.
        
            :param str name: the name of the Todo item to remove.
        """
        if self.db_type == "json":
            del self._todos[name]
        elif self.db_type == "sqlite3":
            self._conn.execute(sql.sqlite3.DELETE_TODO_ITEM, (name,))

    def done(self, name: str):
        """ Mark a Todo item as done.

            :param str name: the name of the Todo item to mark as done.

            :raises KeyError: when a Todo item with the given name does not exist.
        """
        if self.db_type == "json":
            # Check if Todo item even exists
            if self._todos.get(name, None) is None:
                raise KeyError("A Todo item with the requested name does not exist")

            self._todos[name]["done"] = True
        elif self.db_type == "sqlite3":
            has_todo_res = self._conn.execute("SELECT 1 FROM todo WHERE name = ?", (name,)).fetchone()
            if has_todo_res is None:
                raise KeyError("A Todo item with the requested name does not exist")
            
            self._conn.execute(sql.sqlite3.UPDATE_TODO_DONE, (True, name,))

def main_cli():
    """ CLI Entry-point. """

    arg_parser = argparse.ArgumentParser(description="A Todo list CLI application")
    sub_parsers = arg_parser.add_subparsers(dest="command")

    # Add command and arguments
    add_cmd = sub_parsers.add_parser("add", description="add a new Todo item.")
    add_cmd.add_argument("name", help="name of new Todo item.")
    add_cmd.add_argument("--description", help="optional description of Todo item.", default="")
    add_cmd.add_argument("--due-date", help="optional due date of Todo item.", default="")

    # Done command and arguments
    done_cmd = sub_parsers.add_parser("done", description="mark a Todo item as done.")
    done_cmd.add_argument("name", help="name of Todo item to mark as done.")

    # List command and arguments
    list_cmd = sub_parsers.add_parser("list", description="list Todo items.")
    list_cmd.add_argument("--sort-by", help="field to sort Todo items by. (default: %(default)s)", default="name", choices=("name", "description", "done", "due_date"))
    list_cmd.add_argument("--sort-order", help="order to sort Todo items in. (default: %(default)s)", default="asc", choices=("asc", "desc"))

    # Remove command and arguments
    rm_cmd = sub_parsers.add_parser("rm", description="remove a Todo item.")
    rm_cmd.add_argument("name", help="name of Todo item to remove.")
    
    # Global Arguments
    arg_parser.add_argument("--db", help="file to read/store Todo items in. (default: %(default)s)", default="./todos.json")
    arg_parser.add_argument("--db-type", help="the type of database file. (default: %(default)s)", default="json", choices=("json", "sqlite3"))
    arg_parser.add_argument("--timezone", help="Timezone to display due dates in and parse due dates from (default: %(default)s)", default="UTC")

    args = arg_parser.parse_args()

    tz = zoneinfo.ZoneInfo(args.timezone)

    app = TodoApp(args.db, args.db_type)
    app.load()

    if args.command == "add":
        due_date = None
        if args.due_date:
            # Parse due date in requested timezone
            due_date = datetime.datetime.strptime(args.due_date, "%Y-%m-%dT%H:%M").replace(tzinfo=tz)

        app.add(args.name, args.description, due_date)
    elif args.command == "done":
        app.done(args.name)
    elif args.command == "list":
        todos = app.list(sort_by=args.sort_by, sort_order=args.sort_order)
        if todos:
            name_max = len("name")
            description_max = len("description")
            due_date_max = len("due date")
            for todo in todos: # Find the maximum length of the fields of the Todo items
                # Process due_date into requested timezone
                due_date_tz = datetime.datetime.strptime(todo["due_date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=zoneinfo.ZoneInfo("UTC")).astimezone(tz).strftime("%Y-%m-%dT%H:%M%z")
                todo["due_date"] = due_date_tz

                name_len, description_len, due_date_len = len(todo["name"]), len(todo["description"]), len(todo["due_date"])
                if name_len > name_max:
                    name_max = name_len
                if description_len > description_max:
                    description_max = description_len
                if due_date_len > due_date_max:
                    due_date_max = due_date_len

            name_header = "Name".ljust(name_max)
            description_header = "Description".ljust(description_max)
            due_date_header = "Due Date".ljust(due_date_max)
            print(name_header, description_header, due_date_header, "Done", sep="  ")
            for todo in todos:
                print(todo["name"].ljust(name_max), todo["description"].ljust(description_max), todo["due_date"].ljust(due_date_max), todo["done"], sep="  ")
    elif args.command == "rm":
        app.remove(args.name)

    app.close()
