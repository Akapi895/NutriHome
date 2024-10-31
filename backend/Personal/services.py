from bs4 import BeautifulSoup
from datetime import datetime
import requests
import sqlite3
import re

# Hàm kết nối với cơ sở dữ liệu
def connect_db(db_name, timeout=100):
    return sqlite3.connect(db_name, timeout=timeout)

# Hàm tính toán tuổi
def calculate_age(date_of_birth):
    today = datetime.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age

# Hàm lấy thông tin người dùng
def get_user_info(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT dob, gender, height, weight, activity_level FROM users WHERE user_id = ?", (user_id,))
    user_info = cursor.fetchone()
   
    if user_info:
        dob, gender, height, weight, activity_level = user_info
        dob = dob.strip()

        try:
            date_of_birth = datetime.strptime(dob, '%Y-%m-%d')
        except ValueError as e:
            print(f"Lỗi định dạng ngày tháng: {e}")
            return None
        
        return {
            'date_of_birth': date_of_birth,
            'gender': gender,
            'height': height,
            'weight': weight,
            'activity_level': activity_level
        }
    else:
        print("User không tồn tại.")
        return None

# Hàm cập nhật thông tin dinh dưỡng của người dùng vào db
def update_user_nutrition(conn, user_id, target_protein, target_carbs, target_fat, target_calories):
    cursor = conn.cursor()
    
    update_query = """
    UPDATE users 
    SET target_protein = ?, target_carbs = ?, target_fat = ?, target_calories = ?
    WHERE user_id = ?
    """
    cursor.execute(update_query, (target_protein, target_carbs, target_fat, target_calories, user_id))
    
    conn.commit()

# Hàm tính toán thông tin dinh dưỡng của người dùng và cập nhật lại vào db
# -> chỉ dùng khi cập nhật thông tin dinh dưỡng của người dùng
def user_calculator(user_id):
    conn = connect_db("../nutrihome.db", timeout=100)  
    
    user_info = get_user_info(conn, user_id)
    
    if user_info:
        date_of_birth = user_info['date_of_birth']
        age = calculate_age(date_of_birth)
        height = user_info['height']
        weight = user_info['weight']
        gender = 'f' if user_info['gender'].lower() == 'female' else 'm'
        activity_level = user_info['activity_level']
        if activity_level == 'low':
            active_level = 1.2
        elif activity_level == 'medium':
            active_level = 1.55
        else:
            active_level = 1.725
        
        url = f'https://www.calculator.net/macro-calculator.html?ctype=metric&cage={age}&csex={gender}&cheightmeter={height}&ckg={weight}&cactivity={active_level}&x=Calculate'

        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
        else:
            print(f"Yêu cầu thất bại: {response.status_code}")
            return

        # Phân tích HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Khởi tạo biến để lưu trữ giá trị
        balanced_protein = balanced_carbs = balanced_fat = None

        for script in soup.find_all('script'):
            if script.string:
                protein_match = re.search(r'var balancedProtein\s*=\s*([0-9.]+);', script.string)
                carbs_match = re.search(r'var balancedCarbs\s*=\s*([0-9.]+);', script.string)
                fat_match = re.search(r'var balancedFat\s*=\s*([0-9.]+);', script.string)

                if protein_match:
                    balanced_protein = round(float(protein_match.group(1))) 
                if carbs_match:
                    balanced_carbs = round(float(carbs_match.group(1))) 
                if fat_match:
                    balanced_fat = round(float(fat_match.group(1)))
        food_energy_str = soup.find(string="Food Energy").find_next().text.split()[0]
        food_energy = int(food_energy_str.replace(',', ''))

        try:
            update_user_nutrition(conn, user_id, balanced_protein, balanced_carbs, balanced_fat, food_energy)
        except:
            print("Cập nhật thông tin người dùng thất bại.")
            return

    else:
        print("Không thể lấy thông tin người dùng.")