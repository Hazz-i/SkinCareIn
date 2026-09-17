# services/dashboard_service.py
from sqlalchemy.orm import Session
from models.user import User
from models.product import Product
from models.education import EducationArticle
from models.article import NewsArticle
from helper.ingredients import get_avoided_ingredients_for_skin, get_skin_health_tips
from core.logger import log_action

class DashboardService:
    @staticmethod
    def get_dashboard_data(db: Session, user: User) -> dict:
        """
        Aggregate personalized user data, dermatological guidance, filtered product recommendations,
        and recent content feeds for the mobile dashboard.
        """
        # 1. Format User Summary
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        display_name = full_name if full_name else user.username
        
        user_summary = {
            "id": user.id,
            "name": display_name,
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "skin_type": user.skin_type,
            "avoided_ingredients": user.avoided_ingredients or [],
            "is_onboarded": user.is_onboarded
        }

        # 2. Dermatological Care Tips & Warnings
        effective_skin_type = (user.skin_type or "normal").lower()
        skin_health_tips = get_skin_health_tips(effective_skin_type)
        dermatological_warnings = get_avoided_ingredients_for_skin(effective_skin_type)

        # 3. Product Recommendations with Negative Ingredient Filtering
        avoided_list = [item.strip().lower() for item in (user.avoided_ingredients or []) if item.strip()]

        # Query candidates matching skin type or general catalog
        candidate_query = db.query(Product)
        if user.skin_type:
            skin_matched = candidate_query.filter(Product.type.ilike(f"%{user.skin_type}%")).all()
            if skin_matched:
                candidate_products = skin_matched
            else:
                candidate_products = candidate_query.limit(20).all()
        else:
            candidate_products = candidate_query.limit(20).all()

        safe_products = []
        for prod in candidate_products:
            prod_ingredients = (prod.ingredients or "").lower()
            
            # Check if any user-avoided ingredient is in the product ingredients
            is_unsafe = False
            for avoided in avoided_list:
                if avoided in prod_ingredients:
                    is_unsafe = True
                    break
            
            if not is_unsafe:
                safe_products.append(prod)
            
            if len(safe_products) >= 6:
                break

        # 4. Recent Education Articles
        recent_edus = db.query(EducationArticle).order_by(EducationArticle.id.desc()).limit(3).all()
        educations_payload = [
            {
                "id": edu.id,
                "title": edu.title,
                "link": edu.link,
                "image_url": edu.image_url,
                "date": edu.date,
                "category": edu.category
            }
            for edu in recent_edus
        ]

        # 5. Recent News Articles
        recent_news_items = db.query(NewsArticle).order_by(NewsArticle.id.desc()).limit(3).all()
        news_payload = [
            {
                "id": news.id,
                "title": news.title,
                "link": news.link,
                "image_url": news.image_url,
                "date": news.date,
                "category": news.category
            }
            for news in recent_news_items
        ]

        log_action("api", f"Aggregated dashboard data for user {user.email} (skin: {user.skin_type}, safe products: {len(safe_products)})")

        return {
            "user_summary": user_summary,
            "skin_health_tips": skin_health_tips,
            "dermatological_warnings": dermatological_warnings,
            "recommended_products": safe_products,
            "recent_educations": educations_payload,
            "recent_news": news_payload
        }
