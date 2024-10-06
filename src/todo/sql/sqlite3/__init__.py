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

# SQL Statement to create the todo table.
CREATE_TODO_TABLE = """CREATE TABLE todo (
    'name' TEXT,
    'description' TEXT,
    'done' BOOLEAN,
    'due_date' TEXT
)"""

# SQL Statement to Insert a new record into the todo table.
INSERT_TODO_ITEM = "INSERT INTO todo (name, description, due_date, done) VALUES (?, ?, ?, ?)"

# SQL Statement to Update the done field of a todo record.
UPDATE_TODO_DONE = "UPDATE todo SET done = ? WHERE name = ?"

# SQL Statement to Delete a record from the todo table.
DELETE_TODO_ITEM = "DELETE FROM todo WHERE name = ?"

# SQL Statement to list all todo records.
SELECT_ALL_TODO_ITEMS = "SELECT name, description, due_date, done FROM todo"
