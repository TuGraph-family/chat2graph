from app.core.dal.database import Do, engine


def drop_db() -> None:
    """Drop database tables."""
    Do.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    drop_db()
