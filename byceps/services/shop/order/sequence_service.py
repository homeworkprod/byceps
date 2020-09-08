"""
byceps.services.shop.order.sequence_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from typing import List, Optional

from ..sequence import service as sequence_service
from ..sequence.transfer.models import NumberSequence, Purpose
from ..shop.transfer.models import ShopID

from .transfer.models import (
    OrderNumber,
    OrderNumberSequence,
    OrderNumberSequenceID,
)


def create_order_number_sequence(
    shop_id: ShopID, prefix: str, *, value: Optional[int] = None
) -> OrderNumberSequenceID:
    """Create an order number sequence."""
    return sequence_service.create_sequence(
        shop_id, Purpose.order, prefix, value=value
    )


def delete_order_number_sequence(sequence_id: OrderNumberSequenceID) -> None:
    """Delete the order number sequence."""
    sequence_service.delete_sequence(sequence_id)


def find_order_number_sequence(
    sequence_id: OrderNumberSequenceID,
) -> Optional[OrderNumberSequence]:
    """Return the order number sequence, or `None` if the sequence ID
    is unknown or if the sequence's purpose is not order numbers.
    """
    sequence = sequence_service._find_sequence(sequence_id, Purpose.order)

    if sequence is None:
        return None

    return _to_order_number_sequence(sequence)


def find_order_number_sequences_for_shop(
    shop_id: ShopID,
) -> List[OrderNumberSequence]:
    """Return the order number sequences defined for that shop."""
    sequences = sequence_service._find_number_sequences(shop_id, Purpose.order)

    return [_to_order_number_sequence(sequence) for sequence in sequences]


def generate_order_number(sequence_id: OrderNumberSequenceID) -> OrderNumber:
    """Generate and reserve an unused, unique order number from this
    sequence.
    """
    sequence = sequence_service._get_next_sequence_step(
        sequence_id, Purpose.order
    )
    return OrderNumber(f'{sequence.prefix}{sequence.value:05d}')


def _to_order_number_sequence(sequence: NumberSequence) -> OrderNumberSequence:
    return OrderNumberSequence(
        sequence.id,
        sequence.shop_id,
        sequence.prefix,
        sequence.value,
    )
