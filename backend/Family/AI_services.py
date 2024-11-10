from dotenv import load_dotenv
from datetime import datetime
import requests
import datetime
import sqlite3
import json
import os
import re

def connect_db(db_name, timeout=30):
    return sqlite3.connect(db_name, timeout=timeout)

# Lấy thông tin của thành viên gia đình dưới định dạng string
def get_members_info(conn, family_id):
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            user_id, gender, dob, weight, height, 
            activity_level, target_protein, 
            target_fat, target_carbs, target_calories
        FROM users
        WHERE family_id = {family_id}
    """)
    users_info = cursor.fetchall()
    user_info_strings = []
    for user in users_info:
        user_id, gender, dob, weight, height, activity_level, target_protein, target_fat, target_carbs, target_calories = user
        user_info_string = (
            f"Người dùng có user_id {user_id} là {gender} sinh ngày {dob.strip()}, "
            f"cao {height}cm, nặng {weight}kg, với mức năng động {activity_level}, "
            f"có lượng dưỡng chất cần thiết mỗi ngày là {target_protein}g protein, {target_fat}g fat, "
            f"{target_carbs}g carbs, {target_calories} calories"
        )
        user_info_strings.append(user_info_string)
    
    # Join all user info strings with a semicolon and a space
    result = '; '.join(user_info_strings)
    return result

# AI tạo thực đơn chung cho cả gia đình
# ROLE: AI
def AI_family_meal(family_info, available_meals):
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")

    headers = {
        'Content-Type': 'application/json',
    }

    today = datetime.datetime.now().date()

    available_meals_str = json.dumps(available_meals, ensure_ascii=False)

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""Bạn là một chuyên gia dinh dưỡng.
                            Hãy xây dựng thực đơn 1 tuần (7 ngày) cho gia đình bắt đầu từ ngày {today} với thông tin cá nhân từng thành viên: {family_info}.
                            Tuy nhiên, không cần phải đạt đủ lượng dưỡng chất cho từng thành viên, 
                            mà chỉ cần thỏa mãn yêu cầu về dinh dưỡng tối thiểu và tất cả thành viên cùng ăn được. 
                            Mỗi ngày gồm 3 bữa (sáng, trưa, tối) đáp ứng nhu cầu dinh dưỡng hàng ngày sau: 
                            Sử dụng chỉ các món ăn có sẵn sau đây (với thông tin dinh dưỡng được cung cấp dưới dạng JSON, 
                            bao gồm lượng calo, protein, carbs, fat cho mỗi món): {available_meals_str}. 
                            Yêu cầu bổ sung:
                            Mỗi trưa và bữa tối có 3-5 món, bữa sáng: 1-2 món. 
                            Hạn chế tối đa sự lặp lại món ăn trong cùng một ngày và trong cả tuần. 
                            Thực đơn cần cân đối đủ đạm, tinh bột, chất béo và chất xơ; không nên chỉ có một nhóm thực phẩm để đảm bảo dinh dưỡng và năng lượng. 
                            Bữa sáng cần nhanh gọn, đủ chất dinh dưỡng với protein, chất xơ, và tinh bột để duy trì năng lượng, 
                            bữa sáng thường có một trong các món sau: bánh mì, phở, bún, cháo, xôi, bánh cuốn, mì, cơm. 
                            Bữa trưa cần đủ đạm, rau xanh, và tinh bột, tránh thức ăn quá dầu mỡ. 
                            Bữa tối nên nhẹ nhàng, ít tinh bột và dầu mỡ, tập trung vào rau xanh và đạm dễ tiêu. 
                            Trả về kết quả ở định dạng JSON. 
                            'eaten' mặc định bằng 0. Không cần thêm \n hoặc \t vào kết quả trả về.
                            Kết quả trả về dưới dạng các object gồm: "recipe_id": 34, "day": '2024-11-09', "meal": "lunch", "eaten": 0, 
                            """
                    }
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})
    
    if response.status_code == 200:
        response_data = response.json()
        clean_string = response_data['candidates'][0]['content']['parts'][0]['text'][7:-3]
        # return clean_string
        if type(clean_string) == str:
                data = json.loads(clean_string)
                return data
        else:
            print("String không hợp lệ")
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        return None

# Hàm lấy tất cả các công thức nấu ăn từ db
def get_all_recipes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT recipe_id, name, protein, fat, carbs, calories FROM recipes")
    recipes = cursor.fetchall()
    
    def format_recipes(recipes):
        formatted_recipes = []
        for recipe in recipes:
            formatted_recipes.append(f"ID: {recipe[0]}, Name: {recipe[1]}, Protein: {recipe[2]}g, Fat: {recipe[3]}g, Carbs: {recipe[4]}g, Calories: {recipe[5]}")
        return "\n".join(formatted_recipes)
    
    return format_recipes(recipes)

# Hàm lấy tên và nguyên liệu từ các recipe_id của general_meal
def get_recipe_details(general_meal, conn):
    cursor = conn.cursor()
    
    recipe_ids = [meal['recipe_id'] for meal in general_meal]
    
    placeholders = ",".join("?" * len(recipe_ids))
    query = f"""
    SELECT name, ingredients
    FROM recipes
    WHERE recipe_id IN ({placeholders})
    """
    cursor.execute(query, recipe_ids)
    results = cursor.fetchall()
        
    recipe_list = []
    for name, ingredients in results:
        ingredients_data = json.loads(ingredients)
        
        recipe_dict = {
            "name": name,
            "ingredients": ingredients_data
        }
        recipe_list.append(recipe_dict)
    
    return json.dumps(recipe_list, ensure_ascii=False)

# AI gợi ý nguyên liệu cần mua cho thực đơn gia đình
# ROLE: AI
def AI_shopping(final_ingredients):
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")
    headers = {
        'Content-Type': 'application/json'
    }
    
    today = datetime.datetime.now().date() 

    data = {
    "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"""Bạn là một chuyên gia dinh dưỡng. 
                            Hãy gợi ý nguyên liệu cần mua cho thực đơn 1 tuần của gia đình, 
                            Các món ăn và nguyên liệu được liệt kê dưới dạng JSON như sau: {final_ingredients}. 
                            Yêu cầu bổ sung: 
                            Bỏ qua các gia vị như mắm, muối, tiêu, dầu ăn, hạt nêm, tương ớt, đường, gia vị khác. 
                            Trả về kết quả dưới dạng JSON, chỉ chứa tên nguyên liệu, số lượng và đơn vị, không giải thích hay có thông tin gì thêm. 
                            Ví dụ kết quả trả về: {{ "suggested_ingredients": [ {{ "name": "Trứng", "unit": "quả", "quantity": 37 }}, {{ "name": "Cà chua", "unit": "trái", "quantity": 10 }}, {{ "name": "Hành lá", "unit": "cây", "quantity": 66 }} ] }}
                            Không cần thêm \n hoặc \t vào kết quả trả về.
                            """
                        )
                    }
                ]
            }
        ]
    }


    response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})
    
    if response.status_code == 200:
        try:
            response_data = response.json()  
            text_response = response_data['candidates'][0]['content']['parts'][0]['text'][7:-3]
            data = json.loads(text_response)
            return data
        except json.JSONDecodeError:
            return response.text  
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        print(response.text)
        return None
  
# import các món ăn chung cho gia đình vào eating_histories cho từng member
def insert_family_meal_to_db(family_id, general_meal, conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id FROM users
        WHERE family_id = ?
    """, (family_id,))
    
    user_ids = [user[0] for user in cursor.fetchall()]

    insert_query = """
    INSERT INTO eating_histories (user_id, recipe_id, day, meal, eaten) 
    VALUES (:user_id, :recipe_id, :day, :meal, :eaten)
    """
    
    try:
        for user_id in user_ids:
            for meal in general_meal:
                cursor.execute(insert_query, {
                    'user_id': user_id,
                    'recipe_id': meal['recipe_id'],
                    'day': meal['day'],
                    'meal': meal['meal'],
                    'eaten': meal.get('eaten', 0)  
                })
        conn.commit()
    except sqlite3.Error as e:
        print("Lỗi khi chèn dữ liệu:", e)
    finally:
        cursor.close() 

# Hàm chính để tạo thực đơn gia đình
def get_simple_family_meal(family_id):
    conn = connect_db("../nutrihome.db")

    family_info = get_members_info(conn, family_id)
    available_meals = get_all_recipes(conn)
    general_meal = AI_family_meal(family_info, available_meals)
    
    insert_family_meal_to_db(family_id, general_meal, conn)
   
    # Creating shopping list
    recipe_details = get_recipe_details(general_meal, conn)
    json_shopping_list = AI_shopping(recipe_details)
    
    cursor = conn.cursor()
    today = datetime.datetime.now().date()
    cursor.execute("""
        INSERT INTO suggested_ingredients (family_id, day, suggested_ingredients)
        VALUES (?, ?, ?)
    """, (family_id, today, json.dumps(json_shopping_list)))
    conn.commit()

    conn.close()