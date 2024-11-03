import datetime
from AI_services import connect_db, get_user_by_family_id, get_recipeId_from_family_member, calculate_total_ingredients, gemini_get_ingredients, import_ingredients

# Hàm để import nguyên liệu cần mua vào database
def shopping_ingredients(family_id, day=datetime.datetime.now().date()):
    conn = connect_db("../nutrihome.db")
    
    family_members = get_user_by_family_id(conn, family_id)
    recipe_id = get_recipeId_from_family_member(conn, family_members, day)
    ingredients = gemini_get_ingredients(calculate_total_ingredients(conn, recipe_id))
    import_ingredients(conn, family_id, day, ingredients)

    conn.close()
