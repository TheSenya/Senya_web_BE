from app.config.logger import logger


def row2dict(row) -> dict | None:
    """Convert a SQLAlchemy Row to a dictionary"""
    if row is None:
        return {}

    return row._asdict()

def rows2dict(rows) -> list[dict] | list:
    """Convert a list of SQLAlchemy Rows/Models to a list of dictionaries"""
    if rows is None:
        return []
    return [row2dict(row) for row in rows]