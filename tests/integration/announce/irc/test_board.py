"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from byceps.announce.irc import board  # Load signal handlers.
import byceps.blueprints.board.signals as board_signals
from byceps.events.board import (
    BoardPostingCreated,
    BoardPostingHidden,
    BoardPostingUnhidden,
    BoardTopicCreated,
    BoardTopicHidden,
    BoardTopicLocked,
    BoardTopicMoved,
    BoardTopicPinned,
    BoardTopicUnhidden,
    BoardTopicUnlocked,
    BoardTopicUnpinned,
)
from byceps.services.board import (
    category_command_service,
    posting_command_service,
    topic_command_service,
)

from .helpers import (
    assert_submitted_data,
    CHANNEL_ORGA_LOG,
    CHANNEL_PUBLIC,
    mocked_irc_bot,
    now,
)


def test_announce_topic_created(app, topic):
    expected_channels = [CHANNEL_ORGA_LOG, CHANNEL_PUBLIC]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'TheShadow999 hat im "ACME Entertainment Convention"-Forum '
        f'das Thema "Brötchen zum Frühstück" erstellt: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicCreated(
            occurred_at=topic.created_at, topic_id=topic.id, url=expected_link
        )
        board_signals.topic_created.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_hidden(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'versteckt: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicHidden(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_hidden.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_unhidden(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'wieder sichtbar gemacht: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicUnhidden(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_unhidden.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_locked(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum das Thema '
        '"Brötchen zum Frühstück" von TheShadow999 '
        f'geschlossen: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicLocked(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_locked.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_unlocked(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'wieder geöffnet: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicUnlocked(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_unlocked.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_pinned(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'angepinnt: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicPinned(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_pinned.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_unpinned(app, topic, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'wieder gelöst: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicUnpinned(
            occurred_at=now(),
            topic_id=topic.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_unpinned.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_topic_moved(
    app, topic, category, another_category, board, moderator
):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/topics/{topic.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'das Thema "Brötchen zum Frühstück" von TheShadow999 '
        f'aus "Kategorie 1" in "Kategorie 2" verschoben: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardTopicMoved(
            occurred_at=now(),
            topic_id=topic.id,
            old_category_id=category.id,
            new_category_id=another_category.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.topic_moved.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_posting_created(app, posting):
    expected_channels = [CHANNEL_ORGA_LOG, CHANNEL_PUBLIC]
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'TheShadow999 hat im "ACME Entertainment Convention"-Forum '
        'auf das Thema "Brötchen zum Frühstück" '
        f'geantwortet: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardPostingCreated(
            occurred_at=posting.created_at,
            posting_id=posting.id,
            url=expected_link,
        )
        board_signals.posting_created.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_posting_hidden(app, posting, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'eine Antwort von TheShadow999 '
        'im Thema "Brötchen zum Frühstück" '
        f'versteckt: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardPostingHidden(
            occurred_at=now(),
            posting_id=posting.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.posting_hidden.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


def test_announce_posting_unhidden(app, posting, moderator):
    expected_channels = [CHANNEL_ORGA_LOG]
    expected_link = f'http://example.com/board/postings/{posting.id}'
    expected_text = (
        'ElBosso hat im "ACME Entertainment Convention"-Forum '
        'eine Antwort von TheShadow999 '
        'im Thema "Brötchen zum Frühstück" '
        f'wieder sichtbar gemacht: {expected_link}'
    )

    with mocked_irc_bot() as mock:
        event = BoardPostingUnhidden(
            occurred_at=now(),
            posting_id=posting.id,
            moderator_id=moderator.id,
            url=expected_link,
        )
        board_signals.posting_unhidden.send(None, event=event)

        assert_submitted_data(mock, expected_channels, expected_text)


# helpers


@pytest.fixture(scope='module')
def creator(make_user):
    return make_user('TheShadow999')


@pytest.fixture(scope='module')
def moderator(make_user):
    return make_user('ElBosso')


@pytest.fixture(scope='module')
def category(board):
    category = _create_category(board.id, number=1)
    yield category
    category_command_service.delete_category(category.id)


@pytest.fixture(scope='module')
def another_category(board):
    category = _create_category(board.id, number=2)
    yield category
    category_command_service.delete_category(category.id)


@pytest.fixture(scope='module')
def topic(category, creator):
    topic = _create_topic(
        category.id, creator.id, number=192, title='Brötchen zum Frühstück'
    )
    yield topic
    topic_command_service.delete_topic(topic.id)


@pytest.fixture(scope='module')
def posting(topic, creator):
    posting = _create_posting(topic.id, creator.id)
    yield posting
    posting_command_service.delete_posting(posting.id)


def _create_category(board_id, *, number=1):
    slug = f'category-{number}'
    title = f'Kategorie {number}'
    description = f'Hier geht es um Kategorie {number}'

    return category_command_service.create_category(
        board_id, slug, title, description
    )


def _create_topic(category_id, creator_id, *, number=1, title=None):
    if title is None:
        title = f'Thema {number}'
    body = f'Inhalt von Thema {number}'

    topic, _ = topic_command_service.create_topic(
        category_id, creator_id, title, body
    )

    return topic


def _create_posting(topic_id, creator_id, *, number=1):
    body = f'Inhalt von Beitrag {number}.'

    posting, event = posting_command_service.create_posting(
        topic_id, creator_id, body
    )

    return posting