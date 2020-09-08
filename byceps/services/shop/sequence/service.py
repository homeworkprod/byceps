"""
byceps.services.shop.sequence.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from typing import List, Optional

from ....database import db

from ..shop.transfer.models import ShopID

from .models import NumberSequence as DbNumberSequence
from .transfer.models import NumberSequence, NumberSequenceID, Purpose


def create_sequence(
    shop_id: ShopID,
    purpose: Purpose,
    prefix: str,
    *,
    value: Optional[int] = None,
) -> NumberSequenceID:
    """Create a sequence for that shop and purpose."""
    sequence = DbNumberSequence(shop_id, purpose, prefix, value=value)

    db.session.add(sequence)
    db.session.commit()

    return sequence.id


def delete_sequence(sequence_id: NumberSequenceID) -> None:
    """Delete the sequence."""
    db.session.query(DbNumberSequence) \
        .filter_by(id=sequence_id) \
        .delete()

    db.session.commit()


def _find_sequence(
    sequence_id: NumberSequenceID, purpose: Purpose
) -> Optional[NumberSequence]:
    """Return the number sequence, or `None` if the sequence ID is
    unknown or if the sequence's purpose is not the given one.
    """
    return DbNumberSequence.query \
        .filter_by(id=sequence_id) \
        .filter_by(_purpose=purpose.name) \
        .one_or_none()


class NumberGenerationFailed(Exception):
    """Indicate that generating a prefixed, sequential number has failed."""

    def __init__(self, message: str) -> None:
        self.message = message


def _get_next_sequence_step(
    sequence_id: NumberSequenceID, purpose: Purpose
) -> NumberSequence:
    """Calculate and reserve the next number from this sequence.

    The purpose must be specified to prevent using a sequence of the
    wrong purpose, even though the sequence ID is unique.
    """
    sequence = DbNumberSequence.query \
        .filter_by(id=sequence_id) \
        .filter_by(_purpose=purpose.name) \
        .with_for_update() \
        .one_or_none()

    if sequence is None:
        raise NumberGenerationFailed(
            f'No sequence found for ID "{sequence_id}" '
            f'and purpose "{purpose.name}".'
        )

    sequence.value = DbNumberSequence.value + 1
    db.session.commit()

    return sequence


def _find_number_sequences(
    shop_id: ShopID, purpose: Purpose
) -> List[NumberSequence]:
    sequences = DbNumberSequence.query \
        .filter_by(shop_id=shop_id) \
        .filter_by(_purpose=purpose.name) \
        .all()

    return [_db_entity_to_number_sequence(sequence) for sequence in sequences]


def _db_entity_to_number_sequence(entity: DbNumberSequence) -> NumberSequence:
    return NumberSequence(
        entity.id,
        entity.shop_id,
        entity.purpose,
        entity.prefix,
        entity.value,
    )
