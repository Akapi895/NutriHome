from AI_services import connect_db, get_user_info, get_all_recipes, get_meal_plan_from_gemini, format_meal_plan, import_weekly_menu
import json

# Hàm tạo thực đơn hàng tuần với user_id
def generate_weekly_menu(user_id):
    conn = connect_db("../nutrihome.db")
    cursor = conn.cursor()
    
    user_info = get_user_info(user_id, conn)
    available_meals = get_all_recipes(conn) # str
        
    meal_plans = get_meal_plan_from_gemini(user_info, available_meals) # dict

    if meal_plans:
        try:
            formatted_plan = format_meal_plan(meal_plans)
            if formatted_plan:
                import_weekly_menu(formatted_plan, user_id, conn)
            else:
                print("Failed to format meal plan")
        except json.JSONDecodeError as e:
            print(f"Lỗi phân tích JSON: {e}")
    else:
        print("Failed to get meal plans")
    conn.close()

# Xóa các bản ghi trước một ngày nhất định
def delete_records_before_date(conn, target_date):
    cursor = conn.cursor()
    
    cursor.execute(""" 
        DELETE FROM eating_histories
        WHERE day < ?
    """, (target_date,))
    
    conn.commit()

