from datetime import datetime, timedelta
import sqlite3
import os
import easyocr 
import json
from dotenv import load_dotenv
import requests
# Connect to the SQLite database
DATABASE = os.path.join(os.path.dirname(os.getcwd()), 'nutrihome3.db')
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_start_of_week():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week

def get_weekly_menu_service(user_id):
    conn = get_db_connection()
    
    # Ngày bắt đầu của tuần hiện tại (Thứ Hai) và 7 ngày tiếp theo
    start_of_week = get_start_of_week()
    end_of_week = start_of_week + timedelta(days=6)

    # Tạo cấu trúc dữ liệu cho thực đơn cả tuần
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_menu = {day.lower(): {"breakfast": [], "lunch": [], "dinner": []} for day in days_of_week}

    # Truy vấn tất cả các bữa ăn của người dùng trong tuần hiện tại
    meals = conn.execute("""
    SELECT r.recipe_id, r.name, r.image, eh.meal, eh.day
    FROM eating_histories eh
    JOIN recipes r ON eh.recipe_id = r.recipe_id  
    WHERE eh.user_id = ? AND eh.day BETWEEN ? AND ?
    """, (user_id, start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d'))).fetchall()

    # Phân loại bữa ăn theo từng ngày trong tuần
    for meal in meals:
        meal_date_str = meal['day']
        
        # Kiểm tra và chuyển đổi chuỗi ngày, bỏ qua bất kỳ phần giờ nào nếu có
        try:
            meal_date = datetime.strptime(meal_date_str.strip(), '%Y-%m-%d')
            day_of_week = meal_date.strftime('%a').lower()  # Lấy tên ngày trong tuần (mon, tue, ...)
        except ValueError:
            print(f"Lỗi định dạng ngày cho giá trị: {meal_date_str}")
            continue

        # Thêm thông tin bữa ăn vào thực đơn của từng ngày
        meal_data = {
            "recipe_id": meal['recipe_id'],
            "name": meal['name'],
            "image": meal['image']
        }

        if meal['meal'] == 'breakfast':  
            weekly_menu[day_of_week]['breakfast'].append(meal_data)
        elif meal['meal'] == 'lunch':
            weekly_menu[day_of_week]['lunch'].append(meal_data)
        elif meal['meal'] == 'dinner':
            weekly_menu[day_of_week]['dinner'].append(meal_data)

    conn.close()

    # Định dạng lại dữ liệu cho JSON theo yêu cầu
    ordered_weekly_menu = [{day: weekly_menu[day]} for day in weekly_menu]
    
    return {
        "status": "success",
        "data": {
            "menu": ordered_weekly_menu
        }
    }, 200

def get_daily_nutrition_service(user_id):
    conn = get_db_connection()
    nutrition = conn.execute("""
        SELECT SUM(carbs) as carbs, SUM(protein) as protein, SUM(fat) as fat, SUM(calories) as calories
        FROM eating_histories
        JOIN recipes ON eating_histories.recipe_id = recipes.recipe_id
        WHERE user_id = ? AND date(day) = date('now')
    """, (user_id,)).fetchone()
    conn.close()

    if nutrition:
        return {
            'status': 'success',
            'data': {
                'calories': nutrition['calories'],
                'nutrients': {
                    'carbs': nutrition['carbs'],
                    'protein': nutrition['protein'],
                    'fat': nutrition['fat']
                }
            }
        }, 200
    else:
        return {'status': 'error', 'message': 'Unable to load nutritional information.'}, 404

def upload_receipt_service(file):
    # Thêm logic xử lý file nếu cần, giả sử chỉ trả về mẫu dữ liệu
    

    # Khởi tạo EasyOCR reader
    reader = easyocr.Reader(['vi'])

    # Đọc và nhận dạng văn bản từ ảnh
    image_path = 'openAI/receipt.png'
    results = reader.readtext(image_path, detail=0) 

    all_text = ''
    for idx, text in enumerate(results, 1):
        all_text += text + " "

    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL")

    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""You are given the receipt: {all_text}
                        Please list all the name of dishes. You just need to list, do not need to explain.
                        Example: 
                        "Pho ga, 
                        Pho, 
                        Bun cha"
                        """
                
                    }
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(data), params={"key": API_KEY})

    if response.status_code == 200:
        response_data = response.json()
        print(response_data['candidates'][0]['content']['parts'][0]['text'])
        recipes = response_data['candidates'][0]['content']['parts'][0]['text'].split('\n')
        print(recipes)
    else:
        print(f"Lỗi khi gọi API Gemini: {response.status_code}")
    