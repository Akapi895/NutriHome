import datetime
import requests
import sqlite3
import json
import re
import os
from dotenv import load_dotenv


def connect_db(db_name, timeout=30):
    return sqlite3.connect(db_name, timeout=timeout)

# Lấy ra những món ăn đã được lưu trước trong tuần này (gồm 7 ngày)
def get_current_meal(conn, user_id, day=datetime.datetime.now().date()):
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT family_id
        FROM users WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    family_id = int(result[0]) if result and result[0] is not None else None

    cursor.execute("""
        SELECT recipe_id
        FROM family_base
        WHERE family_id = ? AND day >= ?
    """, (family_id, day))
    recipes = cursor.fetchall()
    current_meal = [recipe[0] for recipe in recipes]

    meal_details = []
    for recipe_id in current_meal:
        cursor.execute("""
            SELECT name, carbs, protein, fat, calories
            FROM recipes
            WHERE recipe_id = ?
        """, (recipe_id,))
        recipe = cursor.fetchone()
        if recipe:
            name, carbs, protein, fat, calories = recipe
            meal_details.append(f"Tên món có id {recipe_id} là {name}, với lượng chất dinh dưỡng là {carbs}g carbs, {protein}g protein, {fat}g fat và {calories} calories")
    
    if meal_details:
        meal_details_str = "; ".join(meal_details)
    else: meal_details_str = ""
    return meal_details_str

# Lấy thông tin cá nhân của user
def get_user_info(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_protein, target_fat, target_carbs, target_calories, disease, allergen
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    user_info = cursor.fetchone()
    if user_info:
        user_info = {
            'target_protein': user_info[0],
            'target_fat': user_info[1],
            'target_carbs': user_info[2],
            'target_calories': user_info[3],
            'disease': user_info[4],
            'allergen': user_info[5]
        }
        return user_info
    else:
        print(f"Không tìm thấy thông tin cá nhân của user {user_id}")
        return None

# Gen ra thực đơn bằng AI 
def personal_menu(user_id, user_info, available_meals, current_meal):
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")
    headers = {
        'Content-Type': 'application/json'
    }
    
    target_protein = user_info['target_protein']
    target_fat = user_info['target_fat']
    target_carbs = user_info['target_carbs']
    target_calories = user_info['target_calories']
    disease = user_info['disease']
    allergen = user_info['allergen']
    today = datetime.datetime.now().date() 

    prompt = f"""Bạn là một chuyên gia dinh dưỡng chuyên xây dựng thực đơn.  
                Hãy bổ sung thực đơn tuần (7 ngày) cho tôi từ những món ăn đã có sẵn: {current_meal}. 
                Thực đơn sau khi bổ sung cần đáp ứng lượng chất cần thiết của cá nhân tôi lần lượt là 
                {target_protein}g protein, {target_fat}g fat, {target_carbs}g carbs và {target_calories} calories. 
                Sử dụng chỉ các món ăn có sẵn sau đây (với thông tin dinh dưỡng được cung cấp dưới dạng JSON, 
                bao gồm lượng calo, protein, carbs, fat cho mỗi món): {available_meals}. 
                Hạn chế tối đa sự lặp lại món ăn trong cùng một ngày và trong cả tuần, tính toán để phù hợp với sở thích ăn uống của độ tuổi của tôi.
                Thực đơn cần cân đối đủ đạm, tinh bột, chất béo và chất xơ; không nên chỉ có một nhóm thực phẩm. 
                Bữa sáng cần nhanh gọn, đủ chất dinh dưỡng với protein, chất xơ, và tinh bột, 
                thường có một trong các món sau: bánh mì, phở, bún, cháo, xôi, bánh cuốn, mì, cơm.  
                Bữa trưa cần đủ đạm, rau xanh, và tinh bột, tránh thức ăn quá dầu mỡ. 
                Bữa tối nên nhẹ nhàng, ít tinh bột và dầu mỡ, tập trung vào rau xanh và đạm dễ tiêu. 
                Trả về kết quả ở định dạng JSON, chứa thông tin chi tiết gồm cả các món ăn được bổ sung và các món ăn đã có, 
                không giải thích hay có thông tin gì thêm. 
                Không cần thêm \n hoặc \t vào kết quả trả về. 
                Với eaten mặc định bằng 0, user_id là {user_id} lấy trong thông tin cá nhân của tôi. 
                Kết quả trả về dưới dạng các object, ví dụ gồm: "user_id": 1, "recipe_id": 34, "day": '2024-11-09', "meal": "lunch", "eaten": 0.
                """
    if disease:
        prompt += f"Tôi có bệnh {disease}. "
    if allergen:
        prompt += f" Tôi dị ứng với {allergen}."
    if disease or allergen:
        prompt += " Hãy đề cử món ăn phù hợp."

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (prompt)
                    }
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})
    
    if response.status_code == 200:
        try:
            clean_string = response.json()['candidates'][0]['content']['parts'][0]['text'][7:-3]
            if type(clean_string) == str:
                data = json.loads(clean_string)
                return data
            else:
                print("String không hợp lệ")
                return None
        except json.JSONDecodeError:
            return response.text  
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        print(response.text)
        return None

# Lấy thông tin các món ăn được gợi ý chung
def get_available_meals(conn, user_id, day=datetime.datetime.now().date()):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT recipe_id FROM eating_histories
        WHERE user_id = ? AND day >= ? AND eaten = 0
    """, (user_id, day))
    recipes = cursor.fetchall()
    available_meals = [recipe[0] for recipe in recipes]
    return available_meals


def bonus_meal(user_id):
    conn = connect_db("../../nutrihome.db")
    available_meals = get_available_meals(conn, user_id)
    current_meal = get_current_meal(conn, user_id)
    user_info = get_user_info(conn, user_id)

    bonus_meal_plan = personal_menu(user_id, user_info, available_meals, current_meal)

    cursor = conn.cursor()
    insert_query = """
    INSERT INTO eating_histories (user_id, recipe_id, day, meal, eaten) 
    VALUES (:user_id, :recipe_id, :day, :meal, :eaten)
    """
    try:
        cursor.executemany(insert_query, bonus_meal_plan)
        conn.commit()
    except sqlite3.Error as e:
        print("Lỗi khi chèn dữ liệu:", e)

def delete_eating_histories():
    conn = connect_db("../../nutrihome.db")
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM eating_histories;
    """)
    conn.commit()
    
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'family_base';")
    conn.commit()

    cursor.execute("""
        VACUUM;
    """)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # delete_eating_histories()
    bonus_meal(1)