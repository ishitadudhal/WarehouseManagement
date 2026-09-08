from app import db
from datetime import datetime


class Item(db.Model):
    """
    One row = one physical item registered in the warehouse.
    Status tracks where in the lifecycle the item currently is.
    """
    __tablename__ = 'items'

    id          = db.Column(db.Integer, primary_key=True)

    # Physical properties
    name        = db.Column(db.String(120), nullable=False)
    height      = db.Column(db.Float, nullable=False)   # cm
    width       = db.Column(db.Float, nullable=False)   # cm
    depth       = db.Column(db.Float, nullable=False)   # cm
    weight      = db.Column(db.Float, nullable=True)    # kg (optional)

    # Status
    status      = db.Column(db.String(20), nullable=False, default='REGISTERED')
    # Possible values: REGISTERED | STORED | RETRIEVED

    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Item {self.id} "{self.name}" [{self.status}]>'

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'height':     self.height,
            'width':      self.width,
            'depth':      self.depth,
            'weight':     self.weight,
            'status':     self.status,
            'created_at': self.created_at.isoformat(),
        }
