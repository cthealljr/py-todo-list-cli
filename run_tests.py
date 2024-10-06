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

import pathlib
import unittest

if __name__ == '__main__':
    loader = unittest.defaultTestLoader
    suite = loader.discover(pathlib.Path(__file__).parent)
    runner = unittest.TextTestRunner()
    runner.run(suite)
