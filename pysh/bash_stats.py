from collections import Counter
import sys
from generator import cat

stats = Counter()

for fname in sys.argv[1:]:
    for line in cat(fname):
        stats += Counter(line.split())

