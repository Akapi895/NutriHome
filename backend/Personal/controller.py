from flask import Blueprint
from .services import user_calculator

personal = Blueprint('personal', __name__)

@personal.route('/api/personal/update', methods=['PUT'])
def update_user_nutrition(user_id):
    return user_calculator(user_id)