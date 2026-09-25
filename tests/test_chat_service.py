# tests/test_chat_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models.product import Product
from models.user import User
from schemas.chat import ChatMessage
from services.chat_service import ChatService, _extract_keywords

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add_all(
        [
            Product(
                title="MS GLOW Acne Night Cream Niacinamide",
                price="Rp78.500",
                description="Krim malam untuk kulit berjerawat, membantu mengontrol minyak.",
                type="['Home', 'Kecantikan', 'Perawatan Wajah', 'Krim Wajah']",
                brand="ms glow",
                link="https://example.com/night-cream",
            ),
            Product(
                title="NPURE Cica Acne Toner",
                price="Rp89.999",
                description="Toner untuk kulit berminyak dan berjerawat.",
                type="['Home', 'Kecantikan', 'Perawatan Wajah', 'Toner Wajah']",
                brand="npure",
                link="https://example.com/cica-toner",
            ),
            Product(
                title="Azarine Hydrasoothe Sunscreen Gel",
                price="Rp65.000",
                description="Sunscreen ringan untuk semua jenis kulit.",
                type="['Home', 'Kecantikan', 'Perawatan Wajah', 'Sunblock Wajah']",
                brand="azarine",
                link="https://example.com/sunscreen",
            ),
        ]
    )
    db.add(User(email="chat@example.com", username="chatuser", skin_type="oily"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def make_user(db):
    return db.query(User).filter(User.email == "chat@example.com").first()


def select(db, text):
    return ChatService._select_products(
        db, [ChatMessage(role="user", content=text)], make_user(db)
    )


def test_keywords_drop_stopwords_and_short_tokens():
    keywords = _extract_keywords("apa itu niacinamide dan aman ga buat kulit saya?")
    assert "niacinamide" in keywords
    assert "kulit" not in keywords
    assert "apa" not in keywords


def test_product_question_is_grounded_in_the_catalog():
    db = TestingSessionLocal()
    products = select(db, "How much is the MS GLOW Acne Night Cream?")
    assert len(products) >= 1
    assert any("Night Cream" in p.title for p in products)
    assert products[0].link.startswith("https://example.com/")
    db.close()


def test_recommendation_request_is_grounded_by_skin_type():
    db = TestingSessionLocal()
    products = select(db, "Can you recommend a product for oily skin?")
    assert len(products) >= 1
    assert all("Sunscreen Gel" not in p.title for p in products)
    db.close()


def test_follow_up_question_stays_grounded():
    db = TestingSessionLocal()
    messages = [
        ChatMessage(role="user", content="Do you have any MS Glow product for acne?"),
        ChatMessage(role="assistant", content="Yes, here are a couple."),
        ChatMessage(role="user", content="How much is the night cream?"),
    ]
    products = ChatService._select_products(db, messages, make_user(db))
    assert len(products) >= 1
    db.close()


def test_off_topic_question_is_not_grounded():
    db = TestingSessionLocal()
    # Generic words that only exist in descriptions must not drag products in.
    assert select(db, "Who is the president of Indonesia?") == []
    assert select(db, "Write me a Python sorting function") == []
    db.close()


def test_plain_chat_and_theory_do_not_show_the_catalog():
    db = TestingSessionLocal()
    # Small talk and pure skincare theory must not surface a product list.
    assert select(db, "Hi there!") == []
    assert select(db, "Thanks, that helps") == []
    assert select(db, "What is niacinamide and is it safe for sensitive skin?") == []
    db.close()
