import datetime
import requests
import sqlite3
import json
import re
import os
from dotenv import load_dotenv


def connect_db(db_name, timeout=30):
    return sqlite3.connect(db_name, timeout=timeout)

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

# Gen ra thực đơn bằng AI
def get_meal_plan_from_gemini(user_info, available_meals):
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")
    headers = {
        'Content-Type': 'application/json'
    }
    
    daily_protein = user_info['daily_protein']
    daily_fat = user_info['daily_fat']
    daily_carbs = user_info['daily_carbs']
    daily_calories = user_info['daily_calories']
    today = datetime.datetime.now().date() 

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"Bạn là một chuyên gia dinh dưỡng. " 
                            f"Hãy tạo thực đơn cho cả tuần (7 ngày) cho một người tính từ ngày {today}, "
                            f"mỗi ngày gồm 3 bữa (sáng, trưa, tối) đáp ứng nhu cầu dinh dưỡng hàng ngày sau: "
                            f"{daily_protein}g protein, {daily_fat}g fat, {daily_carbs}g carbs và {daily_calories} calories. "
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
            response_data = response.json()  # Trả về dữ liệu dưới dạng dict nếu response là JSON
            return response_data
        except json.JSONDecodeError:
            return response.text  # Trả về chuỗi nếu JSON không hợp lệ
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
        print(response.text)
        return None

# Chuyển chuỗi JSON thành dictionary Python
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

# Lấy thông tin người dùng 
def get_user_info(user_id, conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT target_protein, target_carbs, target_fat, target_calories 
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    
    user_data = cursor.fetchone()

    if not user_data:
        return None

    daily_protein = user_data[0]
    daily_carbs = user_data[1]
    daily_fat = user_data[2]
    daily_calories = user_data[3]

    user_info = {
        "daily_protein": daily_protein,
        "daily_carbs": daily_carbs,
        "daily_fat": daily_fat,
        "daily_calories": daily_calories
    }
    return user_info

# Thêm thực đơn hàng tuần vào db
def import_weekly_menu(data, user_id, conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT eating_history_id FROM eating_histories
        ORDER BY eating_history_id DESC
        LIMIT 1
        """
    )
    last_id = cursor.fetchone()
    last_id = last_id[0] if last_id else 0

    for day, meals in data.items():
        for meal_type, recipe_ids in meals.items():
            for recipe_id in recipe_ids:
                last_id += 1
                cursor.execute("""
                    INSERT INTO eating_histories (eating_history_id, user_id, recipe_id, day, meal, eaten)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (last_id, user_id, recipe_id, day, meal_type.lower(), 0))
                
    conn.commit() 
