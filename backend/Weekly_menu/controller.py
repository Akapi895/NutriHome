from flask import Blueprint
from .services import generate_weekly_menu

weekly_menu = Blueprint("weekly_menu", __name__)

@weekly_menu.route("/api/weekly_menu", methods=['GET'])
def weekly_menu_api(user_id):
    return generate_weekly_menu(user_id=user_id)