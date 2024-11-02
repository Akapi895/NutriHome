from flask import Flask, request, jsonify
import sqlite3
import datetime
import json 
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

DATABASE = 'nutrihome.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

#Show personal detail 
def show_personal_detail():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    person = conn.execute(
    '''SELECT fullname,
            user_id,
            username,
            gender,
            weight,
            height,
            dob,
            avatar,
            activity_level  
    FROM users WHERE user_id = ?''',(user_id,)).fetchone ()
    conn.close()
    
    if person:
         return jsonify({
            'status': 'success',
            'data': {
                'user_id': person['user_id'],
                'avatar': person['avatar'],
                'fullname': person['fullname'],
                'username': person['username'],
                'gender': person['gender'],
                'dob': person['dob'],
                'height': person['height'],
                'weight': person['weight'],
                'activity_level': person['activity_level']
            }
        }), 200, {'Content-Type': 'application/json'}
    else:
        return jsonify({'status': 'error', 'message': 'Unavailable user'}), 404
    
#Update personal detail
def update_personal_detail():
        user_id = request.args.get('user_id')
        data = request.json 
        height = data.get('height')
        weight = data.get('weight')
        activity_level = data.get('activity_level')
        conn = get_db_connection()
        person = conn.execute("SELECT user_id FROM eating_histories WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        
        if person:
            conn = get_db_connection()
            conn.execute("""
            UPDATE users SET height = ?, weight = ?, activity_level = ?
            WHERE user_id = ?
            """, (height,weight,activity_level,user_id,))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Updated personal detail scuccessfully'}), 200 
        
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update personal detail'}), 404
        
# Show nutrition history within 3 days
def show_history():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    
    # Check if user exists
    user = conn.execute('SELECT user_id FROM eating_histories WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        conn = get_db_connection()
        nutrition_data = conn.execute(
            '''
            SELECT
                day,
                meal,
                GROUP_CONCAT(recipes.name, ',') AS recipes,
                SUM(carbs) AS carbs,
                SUM(protein) AS protein,
                SUM(fat) AS fat,
                SUM(calories) AS calories
            FROM eating_histories 
            JOIN recipes 
            ON eating_histories.recipe_id = recipes.recipe_id
            WHERE user_id = ? AND day >= date('now', '-3 days') AND eaten = 1
            GROUP BY day, meal
            ''', (user_id,)
        ).fetchall()
        conn.close()

        # Initialize result dictionary
        result = {}

        # Iterate over each row in the data
        for row in nutrition_data:
            day = row['day']
            # Assign recipes to specific meals (breakfast, lunch, dinner)
            result[day]["meals"][row['meal']] = row['recipes'].split(',')

            # Sum up nutrients for each day
            result[day]["nutrients"]["carbs"] += row['carbs']
            result[day]["nutrients"]["fat"] += row['fat']
            result[day]["nutrients"]["protein"] += row['protein']

        # Convert result to a list of dictionaries if needed
        final_result = [{day: data} for day, data in result.items()]
        return jsonify({'status': 'success', 'data': final_result}), 200, {'Content-Type': 'application/json'}
    
    return jsonify({'status': 'error', 'message': 'User not found'}), 404

             
#Show today's nutrition history 
def show_nutrition_today():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    
    user = conn.execute('SELECT user_id FROM eating_histories WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        conn = get_db_connection()
        nutrition_data = conn.execute(
            '''
            SELECT 
                meal, 
                SUM(carbs) AS "carbs",
                SUM(protein) AS "protein",
                SUM(fat) AS "fat",
                SUM(calories) AS "calories"
            FROM eating_histories 
            JOIN recipes 
            ON eating_histories.recipe_id = recipes.recipe_id
            WHERE user_id = ? AND day = date('now') AND eaten = 1
            GROUP BY meal
            ''', (user_id,)
        ).fetchall()  
        conn.close()
        
        conn =get_db_connection()
        total_nutrients =

    result = {}

    for row in nutrition_data:
        meal = row['meal']
        
        result[meal] = {
            "carbohydrates": row['carbs'],
            "protein": row['protein'],
            "fat": row['fat'],
            "calories": row['calories']
        }

    return jsonify({'status': 'success', 'data': result}), 200, {'Content-Type': 'application/json'}

    
       
    
   