"""
Event Logger — writes a permanent record of every action the system takes.
Rows here are NEVER edited or deleted (append-only audit log).
"""

from app import db
from app.models.events import Event


def log_event(action, result, shelf_id=None, item_id=None, order_id=None, notes=None):
    """
    Creates one Event row and saves it immediately.

    action:  'STORE' | 'RETRIEVE' | 'PLACEMENT_FAILED' | 'VALIDATION_ERROR'
    result:  'SUCCESS' | 'FAILURE'
    """
    event = Event(
        action=action,
        result=result,
        shelf_id=shelf_id,
        item_id=item_id,
        order_id=order_id,
        notes=notes,
    )
    db.session.add(event)
    db.session.commit()
    return event
