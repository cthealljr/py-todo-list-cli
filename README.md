# Todo List CLI

This project serves as a portfolio piece to demonstrate my Python programming skills.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Overview

A Todo list command-line interface application implemented in Python.

## Features

- Todo list items (name, description, due date, done status)
- Supported Storage:
  - a JSON file
  - a SQLite3 database file

## Installation

Follow these steps to set up the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/cthealljr/py-todo-list-cli.git
   cd py-todo-list-cli
   ```
2. Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3. Install project:
    ```bash
    pip install .
    ```

## Usage

```bash
todo-list --help # show help text
todo-list --db todo.json --db-type json list [--sort-by due_date] [--sort-order asc] # list Todo items, optionally sorted by due_date in ascending order
todo-list --db todo.json --db-type json add "Todo 1" [--description "this is a description of Todo 1"] [--due-date "2024-10-10T17:00"] # add a Todo item, with optional description and due date in UTC
todo-list --db todo.json --db-type json done "Todo 1" # mark Todo item named "Todo 1" as done
```

## License

This project is licensed under the Apache License Version 2.0.
