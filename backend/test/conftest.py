import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


from main import app
from modules.db import get_db
from modules.models import Base, User  # adjust imports
from modules.authenticate import get_current_user  # adjust imports

SQLALCHEMY_DATABASE_URL = "sqlite+pysqlite:///:memory:"
@pytest.fixture(scope="session")
def engine():
    # StaticPool is important for in-memory SQLite to reuse the same connection
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    User.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    User.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def authed_client(client, db_session):
    u = (
        db_session.query(User)
        .filter(User.email == "t@t.com")
        .first()
    )
    if not u:
        u = User(
            email="t@t.com",
            username="testuser",
            password_hash="x",
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

    def override_get_current_user():
        return u

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
