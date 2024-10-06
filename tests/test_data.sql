-- Copyright 2024 Charles Theall Jr
-- 
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
-- 
--     https://www.apache.org/licenses/LICENSE-2.0
-- 
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

INSERT INTO todo ('name', 'description', 'done', 'due_date')
VALUES
('Todo 1', 'This is a description of Todo 1', 0, '2024-10-10T17:00Z'),
('Todo 2', 'this is a description of Todo 2', 1, ''),
('Todo 3', 'This is a description of Todo 3', 0, '2024-10-08T14:00Z'),
('Todo 4', 'This is a description of Todo 4', 0, '2024-10-20T22:00Z');
