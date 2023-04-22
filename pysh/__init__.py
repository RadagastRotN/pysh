from .generator import pipe_from_func
from .main import (sort, uniq, grep, cut, wc,
                   rev, sed,
                   comm,
                   Flags
                   )
from .file_utils import ls, cd, rm, mv, pwd, touch, mkdir, find
from .sources import cat, cat_list
from .drains import echo, to_file, to_list
