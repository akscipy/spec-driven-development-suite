def rank_items(items, limit=None):
    """Return a stable priority ranking after validating the complete input."""
    if not isinstance(items, list):
        raise TypeError("items must be a list")
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer or None")
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

    seen_ids = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} must be a dictionary")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"item {index} id must be a nonempty string")
        if item_id in seen_ids:
            raise ValueError(f"item {index} has duplicate id {item_id!r}")
        seen_ids.add(item_id)
        priority = item.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 0:
            raise ValueError(f"item {index} priority must be a nonnegative integer")

    ranked = sorted(items, key=lambda item: item["priority"], reverse=True)
    return ranked if limit is None else ranked[:limit]
