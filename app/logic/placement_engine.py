"""
Placement Engine — decides which shelf a new item should go to.

Logic (from System_Architecture.docx section 5.3):
1. Try the shelf that was specifically requested.
2. If taken, find the nearest free shelf in the same height class on the same layer.
3. If still nothing, try the other layer with the same height class.
4. If still nothing, try a taller height class (item fits in a bigger space).
5. If no suitable shelf is found anywhere, return None (caller handles the error).

"Nearest" = smallest Manhattan Distance: |x1 - x2| + |y1 - y2|
"""

from app.models.shelves import Shelf

# Height classes ordered smallest to biggest.
# Used for step 4: "try a taller height class"
HEIGHT_CLASSES = [15, 20, 32]


def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def find_shelf(target_x, target_y, target_layer, height_class):
    """
    Main entry point. Returns a Shelf object to use, or None if nothing is available.
    """

    # Step 1 — try the exact requested shelf
    requested = Shelf.query.filter_by(
        x=target_x, y=target_y, layer=target_layer, is_occupied=False
    ).first()
    if requested:
        return requested

    # Step 2 — nearest free shelf, same height class, same layer
    nearest = _nearest_free_shelf(
        target_x, target_y, layer=target_layer, height_class=height_class
    )
    if nearest:
        return nearest

    # Step 3 — same height class, other layer
    other_layer = 2 if target_layer == 1 else 1
    nearest = _nearest_free_shelf(
        target_x, target_y, layer=other_layer, height_class=height_class
    )
    if nearest:
        return nearest

    # Step 4 — try taller height classes, either layer
    bigger_classes = [h for h in HEIGHT_CLASSES if h > height_class]
    for bigger in bigger_classes:
        nearest = _nearest_free_shelf(target_x, target_y, layer=None, height_class=bigger)
        if nearest:
            return nearest

    # Step 5 — nothing found anywhere
    return None


def _nearest_free_shelf(target_x, target_y, layer, height_class):
    """
    Finds the closest free shelf matching height_class (and layer, if given).
    'Closest' is measured with Manhattan Distance from the target position.
    """
    query = Shelf.query.filter_by(is_occupied=False, height_class=height_class)
    if layer is not None:
        query = query.filter_by(layer=layer)

    candidates = query.all()
    if not candidates:
        return None

    best = min(
        candidates,
        key=lambda s: manhattan_distance(target_x, target_y, s.x, s.y)
    )
    return best
