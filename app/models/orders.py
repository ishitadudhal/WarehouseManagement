from app import db
from datetime import datetime


class Order(db.Model):
    """
    One row = one STORE or RETRIEVE instruction sent to the system.
    Records what was requested vs what actually happened.
    """
    __tablename__ = 'orders'

    id              = db.Column(db.Integer, primary_key=True)

    # What was asked
    action          = db.Column(db.String(10), nullable=False)   # 'STORE' or 'RETRIEVE'
    item_id         = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    target_shelf_id = db.Column(db.Integer, db.ForeignKey('shelves.id'), nullable=True)
    # ^ the shelf the user requested (might differ from assigned)

    # What actually happened
    assigned_shelf_id = db.Column(db.Integer, db.ForeignKey('shelves.id'), nullable=True)
    # ^ the shelf the Placement Engine actually used

    # Status lifecycle
    status          = db.Column(db.String(15), nullable=False, default='PENDING')
    # Possible values: PENDING | IN_PROGRESS | DONE | FAILED

    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at    = db.Column(db.DateTime, nullable=True)

    # Relationships
    item            = db.relationship('Item', backref='orders', foreign_keys=[item_id])
    target_shelf    = db.relationship('Shelf', foreign_keys=[target_shelf_id])
    assigned_shelf  = db.relationship('Shelf', foreign_keys=[assigned_shelf_id])

    def __repr__(self):
        return f'<Order {self.id} {self.action} item={self.item_id} [{self.status}]>'

    def to_dict(self):
        return {
            'id':                 self.id,
            'action':             self.action,
            'item_id':            self.item_id,
            'target_shelf_id':    self.target_shelf_id,
            'assigned_shelf_id':  self.assigned_shelf_id,
            'status':             self.status,
            'created_at':         self.created_at.isoformat(),
            'completed_at':       self.completed_at.isoformat() if self.completed_at else None,
        }
