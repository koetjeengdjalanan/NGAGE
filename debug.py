import pandas as pd
import numpy as np
from pathlib import Path
from helper.filehandler import FileHandler

# data = [
#     pd.DataFrame(
#         np.random.randint(0, 100, size=(100, 2)), columns=["Number1", "Number2"]
#     ),
#     {
#         "two.1": pd.DataFrame(
#             np.random.randint(0, 100, size=(100, 2)), columns=["Number1", "Number2"]
#         ),
#         "two.2": pd.DataFrame(
#             np.random.randint(0, 100, size=(100, 2)), columns=["Number1", "Number2"]
#         ),
#     },
# ]

# # print(type(data[0]).__str__)

# for _ in data:
#     # print(_)
#     match _:
#         case pd.DataFrame():
#             print("DataFrame")
#         case dict():
#             print("Dictionary")

error = [
    '  File "spam.py", line 3, in <module>\n    spam.eggs()\n',
    '  File "eggs.py", line 42, in eggs\n    return "bacon"\n',
]

formatted = ""
for _ in error:
    formatted += _

print(formatted)
