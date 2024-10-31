import json
import sqlite3
from recipes import recipes  

# Hàm kết nối với cơ sở dữ liệu
def connect_db(db_name):
    return sqlite3.connect(db_name)

# Tạo bảng recipes trong db
def create_recipes_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        recipe_id INTEGER PRIMARY KEY,
        name TEXT,
        image TEXT, 
        rating REAL,
        cooking_time INTEGER,
        ingredients TEXT,
        steps TEXT,
        carbs REAL,
        protein REAL,
        fat REAL,
        calories REAL
    )
    """)
    conn.commit()

# Lưu công thức vào cơ sở dữ liệu
def insert_recipe(conn, recipe):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO recipes (
        recipe_id,
        name,
        image,  
        rating,
        cooking_time,
        ingredients,
        steps,
        carbs,
        protein,
        fat,
        calories
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recipe['recipe_id'],
        recipe['name'],
        recipe['image'],  
        recipe['rating'],
        recipe['cooking_time'],
        json.dumps(recipe['ingredients']),  
        json.dumps(recipe['steps']),        
        recipe['carbs'],
        recipe['protein'],
        recipe['fat'],
        recipe['calories']
    ))
    conn.commit()

# Hàm import các công thức vào cơ sở dữ liệu
# -> chỉ dùng 1 lần khi cần import các công thức vào db
def import_recipes_to_db(db_name):
    conn = connect_db(db_name)
    create_recipes_table(conn) # Có thể không dùng

    for recipe in recipes:  
        insert_recipe(conn, recipe)

    conn.close()

# Hàm để trả về đúng định dạng unicode
# Do lưu tiếng việt vào db nên cần decode unicode
def decode_unicode(text):
    decoded_text = json.loads(text)
    return json.dumps(decoded_text, ensure_ascii=False, indent=4)

# Hàm mẫu lấy thông tin từ db theo user_id với decode unicode
def get_recipes_from_db(user_id):
    conn = connect_db('../nutrihome.db')
    cursor = conn.cursor()

    # select gì thì ghi ra 
    cursor.execute("SELECT ingredients FROM recipes WHERE recipe_id = ?",(user_id,))
    ingredients = cursor.fetchone()
    if ingredients:
        ingredients = ingredients[0]  
        print(decode_unicode(ingredients))
    conn.close()

# Lấy tất cả công thức từ cơ sở dữ liệu
def get_all_recipes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT recipe_id, name, protein, fat, carbs, calories FROM recipes")
    return cursor.fetchall()

# Gửi yêu cầu đến API Gemini AI để lấy thực đơn
# def get_meal_plan_from_gemini(user_info):
#     API_KEY = "AIzaSyDm6U8EtD-6jnz554Eom88etiqjqkYr490"
#     API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
#     headers = {
#         'Content-Type': 'application/json'
#     }
    
#     if not available_meals:
#         print("Không có món ăn nào trong database.")
#         return []

#     # Iterate over each user's data and prepare requests
#     meal_plans = []
#     for user in user_info:
#         daily_protein = user['daily_protein']
#         daily_fat = user['daily_fat']
#         daily_carbs = user['daily_carbs']
#         daily_calories = user['daily_calories']

#         # Nội dung yêu cầu gửi đến API
#         data = {
#             "contents": [
#                 {
#                     "parts": [
#                         {
#                             "text": f"Xây dựng thực đơn 1 ngày cho một người gồm 3 bữa sáng, trưa, tối, với lượng chất cần thiết mỗi ngày là: {daily_protein}g protein, {daily_fat}g fat, {daily_carbs}g carbs và {daily_calories} calories. Chỉ sử dụng các món: {', '.join(available_meals)} và chỉ trả về recipe_id các món của từng bữa dưới dạng json, mỗi bữa tối đa 5 món."
#                         }
#                     ]
#                 }
#             ]
#         }

#         response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})
        
#         if response.status_code == 200:
#             response_data = response.json()
#             # Add the response data to the list
#             meal_plans.append({
#                 "user_id": user['user_id'],
#                 "meal_plan": response_data
#             })
#         else:
#             print(f"Lỗi khi gọi API Gemini cho user_id {user['user_id']}: {response.status_code}")
#             print(response.text)

#     return meal_plans
