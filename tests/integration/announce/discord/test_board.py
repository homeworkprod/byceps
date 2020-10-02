"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from contextlib import contextmanager

import pytest
from requests_mock import Mocker

from byceps.announce.discord import board  # Load signal handlers.
from byceps.events.board import BoardPostingCreated, BoardTopicCreated
from byceps.services.board import (
    category_command_service,
    posting_command_service,
    topic_command_service,
)
from byceps.services.webhooks import service as webhook_service
from byceps.signals import board as board_signals


WEBHOOK_URL = 'https://webhoooks.test/board'


def test_announce_topic_created(
    webhook_settings, admin_app, board, topic, creator
):
    expected_url = f'https://website.test/board/topics/{topic.id}'
    expected_content = (
        '[Forum] RocketRandy hat das Thema '
        '"Cannot connect to the party network :(" erstellt: '
        f'<{expected_url}>'
    )

    event = BoardTopicCreated(
        occurred_at=topic.created_at,
        initiator_id=creator.id,
        initiator_screen_name=creator.screen_name,
        board_id=board.id,
        topic_id=topic.id,
        topic_creator_id=creator.id,
        topic_creator_screen_name=creator.screen_name,
        topic_title=topic.title,
        url=expected_url,
    )

    with mocked_webhook_receiver() as mock:
        board_signals.topic_created.send(None, event=event)

    assert_request(mock, expected_content)


def test_announce_posting_created(
    webhook_settings, admin_app, board, posting, creator
):
    expected_url = f'https://website.test/board/postings/{posting.id}'
    expected_content = (
        '[Forum] RocketRandy hat auf das Thema '
        '"Cannot connect to the party network :(" geantwortet: '
        f'<{expected_url}>'
    )

    event = BoardPostingCreated(
        occurred_at=posting.created_at,
        initiator_id=creator.id,
        initiator_screen_name=creator.screen_name,
        board_id=board.id,
        posting_creator_id=creator.id,
        posting_creator_screen_name=creator.screen_name,
        posting_id=posting.id,
        topic_id=posting.topic.id,
        topic_title=posting.topic.title,
        topic_muted=posting.topic.muted,
        url=expected_url,
    )

    with mocked_webhook_receiver() as mock:
        board_signals.posting_created.send(None, event=event)

    assert_request(mock, expected_content)


# helpers


@pytest.fixture(scope='module')
def webhook_settings(board):
    scope = 'board'
    scope_id = str(board.id)
    format = 'discord'
    text_prefix = '[Forum] '
    url = WEBHOOK_URL
    enabled = True

    webhook = webhook_service.create_outgoing_webhook(
        scope, scope_id, format, url, enabled, text_prefix=text_prefix
    )

    yield

    webhook_service.delete_outgoing_webhook(webhook.id)


@pytest.fixture(scope='module')
def creator(make_user):
    return make_user('RocketRandy')


@pytest.fixture(scope='module')
def category(board):
    slug = 'support'
    title = 'Support'
    description = f'How can I help you, dear Sir/Madam?'

    category = category_command_service.create_category(
        board.id, slug, title, description
    )

    yield category

    category_command_service.delete_category(category.id)


@pytest.fixture(scope='module')
def topic(category, creator):
    title = 'Cannot connect to the party network :('
    body = 'I think I did not receive an IP address via DHCP. BUT WHY?!'

    topic, _ = topic_command_service.create_topic(
        category.id, creator.id, title, body
    )

    yield topic

    topic_command_service.delete_topic(topic.id)


@pytest.fixture(scope='module')
def posting(topic, creator):
    posting, _ = posting_command_service.create_posting(
        topic.id, creator.id, 'This is nice and all, but check out my website!'
    )

    yield posting

    posting_command_service.delete_posting(posting.id)


@contextmanager
def mocked_webhook_receiver():
    with Mocker() as mock:
        mock.post(WEBHOOK_URL)
        yield mock


def assert_request(mock, expected_content: str) -> None:
    assert mock.called

    history = mock.request_history
    assert len(history) == 1

    actual = mock.last_request.json()

    assert actual == {'content': expected_content}