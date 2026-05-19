import random
import re
import string
from typing import Any, Callable, List, Optional, Tuple


PRINTABLE_ASCII = string.ascii_letters + string.digits + string.punctuation + " \t\n"

# Tokens are chosen from the four sample programs: numeric strings, dotted
# format inputs, the nested FDU branch prefix, and small HTML fragments.
DICTIONARY_TOKENS = [
    "0",
    "1",
    "-1",
    "10",
    "NaN",
    "inf",
    "3.14",
    ".",
    "%d",
    "{Key}",
    "F",
    "FD",
    "FDU",
    "FDUP",
    "FDUPLA",
    "FDUPLAB",
    "FDUQLAB",
    "FDUQLAC",
    "L",
    "LA",
    "LAB",
    "<",
    ">",
    "</",
    "<html>",
    "</html>",
    "<script>",
    "&amp;",
]

NUMERIC_BOUNDARY_TOKENS = [
    "0",
    "1",
    "-1",
    "2",
    "10",
    "100",
    "255",
    "256",
    "1024",
    "2147483647",
    "-2147483648",
    "3.14",
    "1e309",
    "NaN",
    "inf",
    "-inf",
]

STRUCTURE_PAIRS = [
    ("(", ")"),
    ("[", "]"),
    ("{", "}"),
    ("<", ">"),
    ("'", "'"),
    ('"', '"'),
    ("<html>", "</html>"),
    ("<script>", "</script>"),
    ("{", ": %d}"),
]

REPEATABLE_TOKENS = [
    ".",
    "%",
    "%d",
    "{Key}",
    "FDU",
    "LAB",
    "<",
    ">",
    "</",
    "&amp;",
    "0",
    "1",
]

INTERESTING_VALUES = {
    1: [0x00, 0x01, 0x7F, 0x80, 0xFF, ord("0"), ord("A"), ord("?")],
    2: [0x0000, 0x0001, 0x00FF, 0x7FFF, 0x8000, 0xFFFF],
    4: [0x00000000, 0x00000001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF],
}

NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _to_bytes(s: str) -> bytearray:
    return bytearray(s.encode("utf-8", errors="surrogatepass"))


def _from_bytes(data: bytearray) -> str:
    # latin-1 keeps every byte representable, so a byte-level mutation is never
    # accidentally lost because of UTF-8 decode errors.
    return bytes(data).decode("latin-1")


def insert_random_character(s: str) -> str:
    """Insert one random printable character at a random position."""
    pos = random.randint(0, len(s))
    random_char = random.choice(PRINTABLE_ASCII)
    return s[:pos] + random_char + s[pos:]


def replace_random_character(s: str) -> str:
    """Replace one character while keeping the input length stable."""
    if not s:
        return insert_random_character(s)

    pos = random.randrange(len(s))
    random_char = random.choice(PRINTABLE_ASCII)
    return s[:pos] + random_char + s[pos + 1:]


def delete_random_character(s: str) -> str:
    """Delete one random character. Empty inputs stay unchanged."""
    if not s:
        return s

    pos = random.randrange(len(s))
    return s[:pos] + s[pos + 1:]


def delete_random_block(s: str) -> str:
    """Delete a short random character block."""
    if not s:
        return s

    start = random.randrange(len(s))
    max_len = min(16, len(s) - start)
    block_len = random.randint(1, max_len)
    return s[:start] + s[start + block_len:]


def duplicate_random_block(s: str) -> str:
    """Duplicate a short existing block to stress length and repeated fields."""
    if not s:
        return insert_random_character(s)

    start = random.randrange(len(s))
    block_len = random.randint(1, min(16, len(s) - start))
    block = s[start:start + block_len]
    insert_pos = random.randint(0, len(s))
    return s[:insert_pos] + block + s[insert_pos:]


def insert_structure_pair(s: str) -> str:
    """Wrap or split input with a paired structure such as braces or HTML tags."""
    left, right = random.choice(STRUCTURE_PAIRS)
    if not s:
        return left + right

    start = random.randint(0, len(s))
    end = random.randint(start, len(s))
    return s[:start] + left + s[start:end] + right + s[end:]


def repeat_interesting_token(s: str) -> str:
    """Insert repeated high-value tokens to stress parsers and branch checks."""
    token = random.choice(REPEATABLE_TOKENS)
    repeat_count = random.randint(2, 8)
    pos = random.randint(0, len(s))
    return s[:pos] + (token * repeat_count) + s[pos:]


def flip_random_bits(s: str) -> str:
    """
    Flip 1, 2, or 4 adjacent bits, following AFL-style bitflip mutation.
    """
    if not s:
        return s

    data = _to_bytes(s)
    total_bits = len(data) * 8
    width = random.choice([1, 2, 4])
    if total_bits < width:
        return s

    bit_index = random.randint(0, total_bits - width)
    for offset in range(width):
        current_bit = bit_index + offset
        byte_index = current_bit // 8
        bit_offset = current_bit % 8
        data[byte_index] ^= 1 << (7 - bit_offset)

    return _from_bytes(data)


def arithmetic_random_bytes(s: str) -> str:
    """
    Add a small random delta to 1, 2, or 4 adjacent bytes.
    """
    if not s:
        return s

    data = _to_bytes(s)
    width = random.choice([1, 2, 4])
    if len(data) < width:
        width = 1

    pos = random.randint(0, len(data) - width)
    for i in range(width):
        data[pos + i] = (data[pos + i] + random.randint(-35, 35)) % 256

    return _from_bytes(data)


def interesting_random_bytes(s: str) -> str:
    """
    Replace 1, 2, or 4 adjacent bytes with boundary-like interesting values.
    """
    if not s:
        return s

    data = _to_bytes(s)
    valid_widths = [width for width in INTERESTING_VALUES if len(data) >= width]
    width = random.choice(valid_widths)
    pos = random.randint(0, len(data) - width)
    value = random.choice(INTERESTING_VALUES[width])
    data[pos:pos + width] = value.to_bytes(width, byteorder="big")

    return _from_bytes(data)


def overwrite_with_dictionary_token(s: str) -> str:
    """
    Insert or overwrite with a token likely to trigger sample-program branches.
    """
    token = random.choice(DICTIONARY_TOKENS)
    if not s or random.random() < 0.5:
        pos = random.randint(0, len(s))
        return s[:pos] + token + s[pos:]

    start = random.randrange(len(s))
    end = random.randint(start + 1, len(s))
    return s[:start] + token + s[end:]


def mutate_numeric_token(s: str) -> str:
    """
    Replace an existing numeric token, or insert one if the input has none.
    This directly targets sample programs that parse floats, ints, and lengths.
    """
    token = random.choice(NUMERIC_BOUNDARY_TOKENS)
    matches = list(NUMBER_PATTERN.finditer(s))
    if not matches:
        pos = random.randint(0, len(s))
        return s[:pos] + token + s[pos:]

    match = random.choice(matches)
    return s[:match.start()] + token + s[match.end():]


def havoc_random_insert(s: str) -> str:
    """
    Insert either a copied block from the input or random printable bytes.
    """
    data = _to_bytes(s)
    length = len(data)
    insert_pos = random.randint(0, length)

    if length and random.random() < 0.75:
        insert_len = random.randint(1, min(16, length))
        start_pos = random.randint(0, length - insert_len)
        insert_bytes = data[start_pos:start_pos + insert_len]
    else:
        insert_len = random.randint(1, 16)
        insert_bytes = bytearray(ord(random.choice(PRINTABLE_ASCII)) for _ in range(insert_len))

    return _from_bytes(data[:insert_pos] + insert_bytes + data[insert_pos:])


def havoc_random_replace(s: str) -> str:
    """
    Replace a short block with copied input bytes or random printable bytes.
    """
    if not s:
        return s

    data = _to_bytes(s)
    length = len(data)
    pos = random.randint(0, length - 1)
    replace_len = random.randint(1, min(16, length - pos))

    if length >= replace_len and random.random() < 0.75:
        start = random.randint(0, length - replace_len)
        replace_bytes = data[start:start + replace_len]
    else:
        replace_bytes = bytearray(ord(random.choice(PRINTABLE_ASCII)) for _ in range(replace_len))

    return _from_bytes(data[:pos] + replace_bytes + data[pos + replace_len:])


def random_block_swap(s: str) -> str:
    """Swap two adjacent byte blocks."""
    if not s:
        return s

    data = _to_bytes(s)
    length = len(data)
    if length < 2:
        return s

    first_len = random.randint(1, min(8, length - 1))
    second_len = random.randint(1, min(8, length - first_len))
    start_pos = random.randint(0, length - first_len - second_len)

    block1 = data[start_pos:start_pos + first_len]
    block2 = data[start_pos + first_len:start_pos + first_len + second_len]
    new_data = data[:start_pos] + block2 + block1 + data[start_pos + first_len + second_len:]

    return _from_bytes(new_data)


class Mutator:
    def __init__(self) -> None:
        self.mutators: List[Callable[[str], str]] = [
            insert_random_character,
            replace_random_character,
            delete_random_character,
            delete_random_block,
            duplicate_random_block,
            insert_structure_pair,
            repeat_interesting_token,
            flip_random_bits,
            arithmetic_random_bytes,
            interesting_random_bytes,
            overwrite_with_dictionary_token,
            mutate_numeric_token,
            havoc_random_insert,
            havoc_random_replace,
            random_block_swap,
        ]

    def strategy_names(self) -> List[str]:
        return [mutator.__name__ for mutator in self.mutators]

    def generate_examples(self, inp: Any, count: int = 10, seed: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Generate a small reproducible mutation gallery for reports or PPT pages.
        The global random state is restored when a seed is supplied.
        """
        if count < 0:
            raise ValueError("count must be non-negative")

        state = None
        if seed is not None:
            state = random.getstate()
            random.seed(seed)

        try:
            return [self.mutate_with_strategy(inp) for _ in range(count)]
        finally:
            if state is not None:
                random.setstate(state)

    def mutate_with_strategy(self, inp: Any) -> Tuple[str, str]:
        if not isinstance(inp, str):
            inp = str(inp)

        mutator = random.choice(self.mutators)
        return mutator(inp), mutator.__name__

    def mutate(self, inp: Any) -> str:
        mutated, _ = self.mutate_with_strategy(inp)
        return mutated
