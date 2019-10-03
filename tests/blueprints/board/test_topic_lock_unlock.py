"""
:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.services.board import (
    topic_command_service as board_topic_command_service,
)

from tests.helpers import http_client

from .topic_moderation_base import (
    AbstractTopicModerationTest,
    create_category,
    create_topic,
    find_topic,
    setup_admin_with_permission,
)


class TopicLockTest(AbstractTopicModerationTest):

    def setUp(self):
        super().setUp()

        setup_admin_with_permission(self.admin.id, 'board_topic.lock')

        self.category_id = create_category(self.board.id, 1).id

    def test_lock_topic(self):
        topic_before = create_topic(self.category_id, self.user.id, 1)

        assert_topic_is_not_locked(topic_before)

        url = '/board/topics/{}/flags/locked'.format(topic_before.id)
        with http_client(self.app, user_id=self.admin.id) as client:
            response = client.post(url)

        assert response.status_code == 204
        topic_afterwards = find_topic(topic_before.id)
        assert_topic_is_locked(topic_afterwards, self.admin.id)

    def test_unlock_topic(self):
        topic_before = create_topic(self.category_id, self.user.id, 1)
        board_topic_command_service.lock_topic(topic_before, self.admin.id)

        assert_topic_is_locked(topic_before, self.admin.id)

        url = '/board/topics/{}/flags/locked'.format(topic_before.id)
        with http_client(self.app, user_id=self.admin.id) as client:
            response = client.delete(url)

        assert response.status_code == 204
        topic_afterwards = find_topic(topic_before.id)
        assert_topic_is_not_locked(topic_afterwards)


def assert_topic_is_locked(topic, moderator_id):
    assert topic.locked
    assert topic.locked_at is not None
    assert topic.locked_by_id == moderator_id


def assert_topic_is_not_locked(topic):
    assert not topic.locked
    assert topic.locked_at is None
    assert topic.locked_by_id is None
