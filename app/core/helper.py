def row2dict(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row._fields}

def rows2dict(rows) -> list[dict]:
    return [row2dict(row) for row in rows]