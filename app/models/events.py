from app import db
from datetime import datetime


class Event(db.Model):
    """
    Permanent audit log. Every action the system takes is recorded here.
    Rows are NEVER deleted or edited — append only.
    """
    __tablename__ = 'events'

    id          = db.Column(db.Integer, primary_key=True)

    action      = db.Column(db.String(20), nullable=False)
    # e.g. 'STORE', 'RETRIEVE', 'PLACEMENT_FAILED', 'VALIDATION_ERROR'

    result      = db.Column(db.String(10), nullable=False)
    # 'SUCCESS' or 'FAILURE'

    shelf_id    = db.Column(db.Integer, db.ForeignKey('shelves.id'), nullable=True)
    item_id     = db.Column(db.Integer, db.ForeignKey('items.id'),   nullable=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'),  nullable=True)

    notes       = db.Column(db.Text, nullable=True)
    # Extra detail, e.g. 'Redirected from L1-x3-y4 to L1-x3-y5'

    timestamp   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Event {self.id} {self.action} [{self.result}] @ {self.timestamp}>'

    def to_dict(self):
        return {
            'id':        self.id,
            'action':    self.action,
            'result':    self.result,
            'shelf_id':  self.shelf_id,
            'item_id':   self.item_id,
            'order_id':  self.order_id,
            'notes':     self.notes,
            'timestamp': self.timestamp.isoformat(),
        }
