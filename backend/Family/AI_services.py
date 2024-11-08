from collections import defaultdict
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

# Lấy id các thành viên trong gia đình
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

# Lấy thông tin của thành viên gia đình dưới định dạng string
def get_members_info(conn, family_members):
    users_id = ', '.join(['?'] * len(family_members))
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            gender, dob, weight, height, 
            activity_level, target_protein, 
            target_fat, target_carbs, target_calories
        FROM users
        WHERE user_id IN ({users_id})
    """, family_members)
    users_info = cursor.fetchall()
    user_info_strings = []
    for user in users_info:
        gender, dob, weight, height, activity_level, target_protein, target_fat, target_carbs, target_calories = user
        user_info_string = (
            f"Người {users_info.index(user) + 1} là {gender} sinh ngày {dob.strip()}, "
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
        'Content-Type': 'application/json'
    }
    
    today = datetime.datetime.now().date() 

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Bạn là một chuyên gia dinh dưỡng. " 
                            f"Hãy tạo thực đơn cơ bản nhất cho cả tuần (7 ngày) cho cả gia đình, "
                            f"với thông tin cá nhân từng thành viên: {family_info}. "
                            f"Tuy nhiên, không cần phải đạt đủ lượng dưỡng chất cho từng thành viên, "
                            f"mà chỉ cần thỏa mãn yêu cầu về dinh dưỡng tối thiểu và tất cả thành viên cùng ăn được. "
                            f"Mỗi ngày gồm 3 bữa (sáng, trưa, tối) đáp ứng nhu cầu dinh dưỡng hàng ngày sau: "
                            f"Sử dụng chỉ các món ăn có sẵn sau đây (với thông tin dinh dưỡng được cung cấp dưới dạng JSON, "
                            f"bao gồm lượng calo, protein, carbs, fat cho mỗi món): {available_meals}. "
                            f"Yêu cầu bổ sung:"
                            f"Mỗi bữa có 3-5 món (bữa sáng: 1-2 món). "
                            f"Đa dạng thực đơn: Hạn chế tối đa sự lặp lại món ăn trong cùng một ngày và trong cả tuần. "
                            f"Thực đơn cần cân đối đủ đạm, tinh bột, chất béo và chất xơ; không nên chỉ có một nhóm thực phẩm để đảm bảo dinh dưỡng và năng lượng. "
                            f"Bữa sáng cần nhanh gọn, đủ chất dinh dưỡng với protein, chất xơ, và tinh bột để duy trì năng lượng, "
                            f"bữa sáng thường có một trong các món sau: bánh mì, phở, bún, cháo, xôi, bánh cuốn, mì, cơm. "
                            f"Bữa trưa cần đủ đạm, rau xanh, và tinh bột để cung cấp năng lượng cho buổi chiều, tránh thức ăn quá dầu mỡ dễ gây buồn ngủ. "
                            f"Bữa tối nên nhẹ nhàng, ít tinh bột và dầu mỡ, tập trung vào rau xanh và đạm dễ tiêu để cơ thể thư giãn, dễ ngủ. "
                            f"Trả về kết quả ở định dạng JSON, chỉ bao gồm recipe_id của các món ăn được chọn cho mỗi bữa ăn trong 7 ngày "
                            f"và không chứa thông tin dinh dưỡng của từng món ăn."
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
            return response_data
        except json.JSONDecodeError:
            return response.text  
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        print(response.text)
        return None

def AI_shopping(family_info, final_ingredients):
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
                            Hãy gợi ý nguyên liệu cần mua cho thực đơn gia đình, 
                            với thông tin cá nhân từng thành viên: {family_info}. 
                            Các món ăn và nguyên liệu được liệt kê như sau: {final_ingredients}. 
                            Yêu cầu bổ sung: 
                            Bỏ qua các gia vị như mắm, muối, tiêu, dầu ăn, hạt nêm, tương ớt, đường, gia vị khác. 
                            In ra kết quả dưới dạng JSON, chỉ chứa tên nguyên liệu, số lượng và đơn vị, không giải thích hay có thông tin gì thêm. 
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
            return response_data
        except json.JSONDecodeError:
            return response.text  
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        print(response.text)
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

# Hàm chuyển thực đơn từ dạng text sang JSON
def format_meal_plan(meal_plan):
    text_content = meal_plan['candidates'][0]['content']['parts'][0]['text']
    
    match = re.search(r'```json\n({.*?})\n```', text_content, re.DOTALL)
    if match:
        meal_plan_json = json.loads(match.group(1))
        # print(json.dumps(meal_plan_json, indent=4))
        return meal_plan_json
    else:
        print("Không tìm thấy nội dung JSON trong meal_plan.")
        return None

def format_ingredients(text):
    ingredients = []
    lines = text.splitlines()
    
    for line in lines:
        # Sử dụng regex để tìm tên nguyên liệu và số lượng
        match = re.match(r'\* \*\*(.+?)\*\*:\s*([\d.]+)([a-zA-Z]+)', line)
        
        if match:
            name = match.group(1).strip().lower()  
            quantity = match.group(2).strip()      
            unit = match.group(3).strip()     
            
            ingredients.append({
                "name": name,
                "quantity": quantity,
                "unit": unit
            })
    
    return {"suggested_ingredients": ingredients}

# Hàm chính để chuyển thực đơn gia đình thành lịch sử ăn uống và lưu vào db
def import_family_meal_to_history(general_meal, user_id, conn):
    cursor = conn.cursor()
    for day, meals in general_meal.items():
        for meal_time, recipes in meals.items():
            for recipe_id in recipes:
                cursor.execute("""
                    INSERT INTO eating_histories (user_id, recipe_id, day, meal, eaten)
                    VALUES (?, ?, ?, ?, 0)
                """, (user_id, recipe_id, day, meal_time))
    conn.commit()

# Nguyên liệu cần mua cho thực đơn gia đình
def get_ingredients_from_meal_plan(general_meal, conn):
        cursor = conn.cursor()
        ingredients = defaultdict(lambda: {"quantity": 0, "unit": "g"})
        
        for day, meals in general_meal.items():
            for meal_time, recipes in meals.items():
                for recipe_id in recipes:
                    cursor.execute("SELECT ingredient, quantity, unit FROM recipes WHERE recipe_id = ?", (recipe_id,))
                    recipe_ingredients = cursor.fetchall()
                    for ingredient, quantity, unit in recipe_ingredients:
                        if unit == "g":
                            ingredients[ingredient]["quantity"] += quantity
                        else:
                            # Handle other units if necessary
                            pass
        
        suggested_ingredients = [{"name": name, "quantity": str(info["quantity"]), "unit": info["unit"]} for name, info in ingredients.items()]
        return {"suggested_ingredients": suggested_ingredients}

def format_recipe_details(recipe_name, ingredients_str):
    ingredients_list = json.loads(ingredients_str)
    ingredients_formatted = ', '.join([f"{item['name']} ({item['quantity']} {item['unit']})" for item in ingredients_list])
    return f"Tên món ăn: {recipe_name}; gồm có các nguyên liệu: {ingredients_formatted}"

# Hàm lấy tên và nguyên liệu từ các recipe_id của general_meal
def get_recipe_details(general_meal, conn):
    cursor = conn.cursor()
    recipe_details = {}
    final_recipe_details = ""

    for day, meals in general_meal.items():
        if isinstance(meals, dict):
            for meal_time, recipes in meals.items():
                for recipe_id in recipes:
                    cursor.execute("SELECT name FROM recipes WHERE recipe_id = ?", (recipe_id,))
                    recipe_name = cursor.fetchone()[0]

                    cursor.execute("SELECT ingredients FROM recipes WHERE recipe_id = ?", (recipe_id,))
                    ingredients_json = cursor.fetchone()[0] 

                    if isinstance(ingredients_json, str):
                        ingredients = json.loads(ingredients_json) 
                    else:
                        ingredients = ingredients_json

                    formatted_details = format_recipe_details(recipe_name, ingredients_json)
                    final_recipe_details += formatted_details + "\n"
        else:
            print(f"Expected meals to be a dictionary, but got {type(meals)}")

    return final_recipe_details

def parse_ingredients(text):
    # Loại bỏ các ký tự xuống dòng (\n) để tránh lỗi phân tích
    text = text.replace("\n", " ")
    
    ingredients = []
    lines = text.splitlines()
    
    # Biểu thức chính quy để hỗ trợ cú pháp markdown và các ký tự Unicode
    pattern = re.compile(r'\*\*(.*?)\*\*[:：]\s*([\d.]+)\s*([^\s]+)')

    # Lặp qua từng dòng và kiểm tra xem có khớp với mẫu không
    for line in lines:
        match = pattern.search(line)
        if match:
            name = match.group(1).strip()
            quantity = match.group(2).strip()
            unit = match.group(3).strip()
            
            ingredients.append({
                "name": name,
                "quantity": quantity,
                "unit": unit
            })
    
    result = {
        "suggested_ingredients": ingredients
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

# Hàm chính để tạo thực đơn gia đình
def get_simple_family_meal(family_id, conn):
    family_members = get_user_by_family_id(conn, family_id)
    family_info = get_members_info(conn, family_members)

    available_meals = get_all_recipes(conn)

    raw_meal = AI_family_meal(family_info, available_meals)
    general_meal = format_meal_plan(raw_meal)
    # print(json.dumps(general_meal, ensure_ascii=False, indent=4))

    recipe_details = get_recipe_details(general_meal, conn)
    
    ans = AI_shopping(family_info, recipe_details)

    text_content = ans["candidates"][0]["content"]["parts"][0]["text"]
    text_content = text_content.lstrip("```json").rstrip("```").strip()
    json_content = json.loads(text_content)

    cursor = conn.cursor()
    today = datetime.datetime.now().date()
    cursor.execute("""
        INSERT INTO suggested_ingredients (family_id, day, suggested_ingredients)
        VALUES (?, ?, ?)
    """, (family_id, today, json.dumps(json_content, ensure_ascii=False)))
    conn.commit()
    
    conn.close()

if __name__ == "__main__":
    conn = connect_db("../nutrihome.db")
    get_simple_family_meal(2, conn)
    conn.close()