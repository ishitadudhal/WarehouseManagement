"""
Run this ONCE after setting up the database.
It creates all 200 shelf rows in the database (2 layers x 7 rows x 8 cols).
Height class is assigned per row based on the warehouse reference diagram.
"""

from app import create_app, db
from app.models.shelves import Shelf

# Height class per row (from reference diagram Abbildung 2.5)
# Row 1–2: 32 cm (big items), Row 3–5: 20 cm, Row 6–7: 15 cm (small items)
HEIGHT_CLASS = {
    1: 32, 2: 32,
    3: 20, 4: 20, 5: 20,
    6: 15, 7: 15,
}

app = create_app()

with app.app_context():
    # Only seed if shelves table is empty
    if Shelf.query.count() > 0:
        print("Shelves already seeded — skipping.")
    else:
        shelves = []
        for layer in [1, 2]:
            for x in range(1, 8):      # rows 1–7
                for y in range(1, 9):  # cols 1–8
                    shelves.append(Shelf(
                        x=x,
                        y=y,
                        layer=layer,
                        height_class=HEIGHT_CLASS[x],
                        is_occupied=False,
                        item_id=None,
                    ))
        db.session.add_all(shelves)
        db.session.commit()
        print(f"Seeded {len(shelves)} shelf positions.")
