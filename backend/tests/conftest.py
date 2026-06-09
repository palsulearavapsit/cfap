import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.core.db import get_db
from backend.models.models import Base, Challenge

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    if db.query(Challenge).count() == 0:
        challenges = [
            Challenge(id=1, title="No Plastic Day", description="Avoid single-use plastics for an entire day.", difficulty="Beginner", points=50),
            Challenge(id=2, title="Meat-Free Monday", description="Eat only plant-based meals today.", difficulty="Intermediate", points=100),
            Challenge(id=3, title="Public Transport Week", description="Commute using only public transit.", difficulty="Advanced", points=250),
            Challenge(id=4, title="Zero Waste Weekend", description="Generate zero landfill waste.", difficulty="Expert", points=500),
        ]
        db.add_all(challenges)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

from backend.core.limiter import limiter

@pytest.fixture
def client(db):
    limiter.enabled = False  # Disable slowapi rate limiting during test executions
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
