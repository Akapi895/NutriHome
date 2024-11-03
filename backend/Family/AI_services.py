from collections import defaultdict
from dotenv import load_dotenv
import requests
import datetime
import sqlite3
import json
import os


def connect_db(db_name, timeout=30):
    return sqlite3.connect(db_name, timeout=timeout)

def get_user_by_family_id(conn, family_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id 
        FROM users
        WHERE family_id = ?
    """, (family_id,))
    users = cursor.fetchall()
    users = [user[0] for user in users]
    return users

def get_recipeId_from_family_member(conn, family_member, day=datetime.datetime.now().date()):
    cursor = conn.cursor()

    placeholders = ', '.join(['?'] * len(family_member))
    query = f"""
        SELECT recipe_id
        FROM eating_histories
        WHERE user_id IN ({placeholders})
        AND day BETWEEN ? AND ?
    """
    day = datetime.date.today()

    start_date = start_date = day - datetime.timedelta(days=1)
    end_date = start_date + datetime.timedelta(days=7)

    cursor = conn.cursor()
    cursor.execute(query, family_member + [start_date, end_date])
    recipes = cursor.fetchall()
    
    return [recipe[0] for recipe in recipes]


def calculate_total_ingredients(conn, recipe_ids):
    cursor = conn.cursor()
    placeholders = ', '.join(['?'] * len(recipe_ids))
    
    query = f"""
        SELECT recipe_id, ingredients
        FROM recipes
        WHERE recipe_id IN ({placeholders})
    """
    cursor.execute(query, recipe_ids)
    ingredients_map = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    
    # Tạo dictionary để lưu trữ tổng lượng nguyên liệu cần dùng
    total_ingredients = defaultdict(lambda: defaultdict(float))
    
    # Tính toán nguyên liệu cho mỗi lần xuất hiện của recipe_id
    for recipe_id in recipe_ids:
        if recipe_id in ingredients_map:
            ingredients = ingredients_map[recipe_id]
            for item in ingredients:
                name = item['name']
                quantity = item['quantity']
                unit = item['unit']

                total_ingredients[(name, unit)]['quantity'] += quantity
                total_ingredients[(name, unit)]['unit'] = unit
    
    # Chuyển kết quả tổng hợp thành danh sách JSON
    result = [
        {"name": name, "quantity": data['quantity'], "unit": data['unit']}
        for (name, unit), data in total_ingredients.items()
    ]
    
    return json.dumps(result, ensure_ascii=False, indent=2)

def gemini_get_ingredients(ingredients):
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")
    headers = {
        'Content-Type': 'application/json'
    }



    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Bạn là một chuyên gia dinh dưỡng. " 
                            f"Với tổng lượng nguyên liệu sau: {json.dumps(ingredients)}, "
                            f"hãy gợi ý danh sách nguyên liệu cần mua cho bữa ăn tuần này, bao gồm các điều chỉnh cần thiết (thay thế, bổ sung, hoặc loại bỏ). "
                            f"Bỏ qua các gia vị cơ bản như muối, đường, dầu ăn, nước mắm, nước tương, tương ớt, nước sôi, và nước lạnh. "
                            f"Ghi rõ tên từng loại rau, đổi tên 'cơm' thành 'gạo'. "
                            f"Trả về kết quả ở định dạng JSON, chỉ bao gồm tên nguyên liệu cần mua, "
                            f"Trả về kết quả định dạng JSON, chỉ gồm tên nguyên liệu ('name'), đơn vị ('unit'), và số lượng ('quantity')."
                        )
                    }
                ]
            }
        ]
    }

    api_response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})
    try:
        candidates = api_response.json().get('candidates', [])
        if not candidates:
            return []

        ingredients_text = candidates[0]['content']['parts'][0]['text']
        
        start_idx = ingredients_text.find('[')
        end_idx = ingredients_text.rfind(']') + 1
        ingredients_json = ingredients_text[start_idx:end_idx]
        
        ingredients_list = json.loads(ingredients_json)
        
        formatted_ingredients = [
            {
                "name": item["name"],
                "unit": item["unit"],
                "quantity": item["quantity"]
            }
            for item in ingredients_list
        ]
        
        return formatted_ingredients
    
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print("Lỗi khi định dạng ingredients:", e)
        return []
    
def import_ingredients(conn, family_id, day, ingredients):
    cursor = conn.cursor()
    
    # Chuyển ingredients thành JSON để lưu vào cột suggested_ingredients
    ingredients_json = json.dumps({"suggested_ingredients": ingredients}, ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO suggested_ingredients (family_id, day, suggested_ingredients)
        VALUES (?, ?, ?)
    """, (family_id, day, ingredients_json))
    
    conn.commit()