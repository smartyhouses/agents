import pytest
from livekit.agents import tokenize
from livekit.agents.tokenize import basic
from livekit.plugins import nltk

# Download the punkt tokenizer, will only download if not already present
nltk.NltkPlugin().download_files()

TEXT = (
    "Hi! "
    "LiveKit is a platform for live audio and video applications and services. "
    "R.T.C stands for Real-Time Communication... again R.T.C. "
    "Mr. Theo is testing the sentence tokenizer. "
    "This is a test. Another test. "
    "A short sentence. "
    "A longer sentence that is longer than the previous sentence. "
    "f(x) = x * 2.54 + 42. "
    "Hey! Hi! Hello! "
)

EXPECTED_MIN_20 = [
    "Hi! LiveKit is a platform for live audio and video applications and services.",
    "R.T.C stands for Real-Time Communication... again R.T.C.",
    "Mr. Theo is testing the sentence tokenizer.",
    "This is a test. Another test.",
    "A short sentence. A longer sentence that is longer than the previous sentence.",
    "f(x) = x * 2.54 + 42.",
    "Hey! Hi! Hello!",
]

SENT_TOKENIZERS = [
    nltk.SentenceTokenizer(min_sentence_len=20),
    basic.SentenceTokenizer(min_sentence_len=20),
]


@pytest.mark.parametrize("tokenizer", SENT_TOKENIZERS)
def test_sent_tokenizer(tokenizer: tokenize.SentenceTokenizer):
    segmented = tokenizer.tokenize(text=TEXT)
    for i, segment in enumerate(EXPECTED_MIN_20):
        assert segment == segmented[i]


@pytest.mark.parametrize("tokenizer", SENT_TOKENIZERS)
async def test_streamed_sent_tokenizer(tokenizer: tokenize.SentenceTokenizer):
    # divide text by chunks of arbitrary length (1-4)
    pattern = [1, 2, 4]
    text = TEXT
    chunks = []
    pattern_iter = iter(pattern * (len(text) // sum(pattern) + 1))

    for chunk_size in pattern_iter:
        if not text:
            break
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]

    stream = tokenizer.stream()
    for chunk in chunks:
        stream.push_text(chunk)

    stream.end_input()

    for i in range(len(EXPECTED_MIN_20)):
        ev = await stream.__anext__()
        assert ev.token == EXPECTED_MIN_20[i]


WORDS_TEXT = (
    "This is a test. Blabla another test! multiple consecutive spaces:     done"
)
WORDS_EXPECTED = [
    "This",
    "is",
    "a",
    "test",
    "Blabla",
    "another",
    "test",
    "multiple",
    "consecutive",
    "spaces",
    "done",
]

WORD_TOKENIZERS = [basic.WordTokenizer()]


@pytest.mark.parametrize("tokenizer", WORD_TOKENIZERS)
def test_word_tokenizer(tokenizer: tokenize.WordTokenizer):
    tokens = tokenizer.tokenize(text=WORDS_TEXT)
    for i, token in enumerate(WORDS_EXPECTED):
        assert token == tokens[i]


@pytest.mark.parametrize("tokenizer", WORD_TOKENIZERS)
async def test_streamed_word_tokenizer(tokenizer: tokenize.WordTokenizer):
    # divide text by chunks of arbitrary length (1-4)
    pattern = [1, 2, 4]
    text = WORDS_TEXT
    chunks = []
    pattern_iter = iter(pattern * (len(text) // sum(pattern) + 1))

    for chunk_size in pattern_iter:
        if not text:
            break
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]

    stream = tokenizer.stream()
    for chunk in chunks:
        stream.push_text(chunk)

    stream.end_input()

    for i in range(len(WORDS_EXPECTED)):
        ev = await stream.__anext__()
        assert ev.token == WORDS_EXPECTED[i]


HYPHENATOR_TEXT = [
    "Segment",
    "expected",
    "communication",
    "window",
    "welcome",
    "bedroom",
]

HYPHENATOR_EXPECTED = [
    ["Seg", "ment"],
    ["ex", "pect", "ed"],
    ["com", "mu", "ni", "ca", "tion"],
    ["win", "dow"],
    ["wel", "come"],
    ["bed", "room"],
]


def test_hyphenate_word():
    for i, word in enumerate(HYPHENATOR_TEXT):
        hyphenated = basic.hyphenate_word(word)
        assert hyphenated == HYPHENATOR_EXPECTED[i]


REPLACE_TEXT = (
    "This is a test. Hello world, I'm creating this agents..     framework. Once again "
    "framework.  A.B.C"
)
REPLACE_EXPECTED = (
    "This is a test. Hello universe, I'm creating this assistants..     library. Twice again "
    "library.  A.B.C.D"
)

REPLACE_REPLACEMENTS = {
    "world": "universe",
    "framework": "library",
    "a.b.c": "A.B.C.D",
    "once": "twice",
    "agents": "assistants",
}


def test_replace_words():
    replaced = tokenize.utils.replace_words(
        text=REPLACE_TEXT, replacements=REPLACE_REPLACEMENTS
    )
    assert replaced == REPLACE_EXPECTED


async def test_replace_words_async():
    pattern = [1, 2, 4]
    text = REPLACE_TEXT
    chunks = []
    pattern_iter = iter(pattern * (len(text) // sum(pattern) + 1))

    for chunk_size in pattern_iter:
        if not text:
            break
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]

    async def _replace_words_async():
        for chunk in chunks:
            yield chunk

    replaced_chunks = []

    async for chunk in tokenize.utils.replace_words(
        text=_replace_words_async(), replacements=REPLACE_REPLACEMENTS
    ):
        replaced_chunks.append(chunk)

    replaced = "".join(replaced_chunks)
    assert replaced == REPLACE_EXPECTED
