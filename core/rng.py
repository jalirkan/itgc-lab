"""String-seeded per-stream RNGs.

Per lab D-007 (adopted in DECISIONS.md D-006): every consumer of randomness
gets its own `random.Random` seeded with "{seed}/{stream}". CPython seeds
str/bytes via SHA-512 (seed version 2), which is stable across platforms and
versions, and the Mersenne Twister itself is platform-independent — so draws
are reproducible bytes-for-bytes anywhere. Separate streams mean adding or
reordering draws in one component can never reshuffle another; in particular
the violation injector (stream "violations") can never perturb the clean
population (DECISIONS.md D-007).
"""

import random


def stream(seed, name: str) -> random.Random:
    """A dedicated RNG for one named stream of one seed."""
    return random.Random("{0}/{1}".format(seed, name))
