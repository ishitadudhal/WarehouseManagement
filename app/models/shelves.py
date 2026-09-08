from app import db


class Shelf(db.Model):
    """
    One row = one physical shelf position in the warehouse.
    This IS the Administration Shell (AAS) for each shelf.
    Total rows: 200 (2 layers × 7 rows × 8 cols = 112, but only 100 addressable)
    """
    __tablename__ = 'shelves'

    id            = db.Column(db.Integer, primary_key=True)

    # Position
    x             = db.Column(db.Integer, nullable=False)   # row    (1–7)
    y             = db.Column(db.Integer, nullable=False)   # column (1–8)
    layer         = db.Column(db.Integer, nullable=False)   # 1 = Front/North, 2 = Back/South

    # Constraints
    height_class  = db.Column(db.Integer, nullable=False)   # 15, 20, or 32 (cm)

    # State
    is_occupied   = db.Column(db.Boolean, nullable=False, default=False)
    item_id       = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)

    # Relationship
    item          = db.relationship('Item', backref='shelf', foreign_keys=[item_id])

    def __repr__(self):
        status = 'OCCUPIED' if self.is_occupied else 'FREE'
        return f'<Shelf L{self.layer} x={self.x} y={self.y} [{status}]>'

    def to_dict(self):
        return {
            'id':           self.id,
            'x':            self.x,
            'y':            self.y,
            'layer':        self.layer,
            'height_class': self.height_class,
            'is_occupied':  self.is_occupied,
            'item_id':      self.item_id,
        }
