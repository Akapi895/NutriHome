from AI_services import get_simple_family_meal, connect_db

def AI_generate_family_meal(family_id):
    conn = connect_db("../nutrihome.db")
    get_simple_family_meal(family_id, conn)
    conn.close()

if __name__ == "__main__":
    AI_generate_family_meal(1)
