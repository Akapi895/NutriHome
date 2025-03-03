# 🍽️ **NutriHome: Family Menu Suggestion Application**

---

## 📖 **Table of Contents**  
1. [Introduction](#introduction)  
2. [Installation and Usage](#installation-and-usage)  
3. [Features](#features)  
4. [Team Members](#team-members)

---
<a id="introduction"></a>
## 🌟 **Introduction**
**NutriHome** is a web application that suggests family menus based on meal history, individual nutritional needs, and shopping receipts. The application helps users build a diet suitable for the health and lifestyle of the family.

The application helps you track and organize book information easily and conveniently with a user-friendly interface.

🎯 **Benefits of NutriHome**

  🥗 Personalized menu suggestions based on nutritional needs.
  
  📊 Track nutritional intake through meal history.
  
  🏡 Build menus for the whole family.
  
  📷 Save meal history by processing receipt images.
  
  🍽️ Recipe sharing forum.

---
<a id="installation-and-usage"></a>
## 🚀 **Installation and Usage**  
### 💻 **System Requirements**  
- Python 3.x
- Flask
- Streamlit
- SQLite
- Gemini API

### 🔧 **Installation Instructions**
**Clone the application to your machine**
```cmd
git clone https://github.com/Akapi895/NutriHome.git
cd NutriHome
```
**Set up a virtual environment and install dependencies**
```cmd
python -m venv venv
source venv/bin/activate  # Trên macOS/Linux
venv\Scripts\activate  # Trên Windows
pip install -r requirements.txt
```
**Run the application**
```cmd
cd frontend
streamlit run app.py
```
```cmd
cd backend
python app.py
```
```cmd
cd menu_service
python app.py
```

---
<a id="features"></a>
## ⚙️ **Features**  

### 🥗 **1. Personalized Menu Suggestions**  
- Users input **weight, height, activity level** to calculate nutritional needs.
- The system suggests suitable dishes for each family member.

### 🏡 **2. Group (Family) Menu Planning**  
- Create a family group to plan weekly menus.
- Ensure members have appropriate diets.

### 🧾 **3. Meal History Logging**  
- Save meal information from receipts using image processing.
- Record external meal history to track nutrient intake.

### 🍳 **4. Cooking Instructions**  
- Suggest recipes suitable for the menu.
- Detailed instructions for preparing each dish.

### 📚 **5. Recipe Sharing Forum**  
- Users can share cooking recipes.
- Save favorite recipes and calculate nutritional values.

---
<a id="team-members"></a>
## 👥 **Team Members**
- Nguyễn Phước Ngưỡng Long: Frontend Developer, Tester
- Hoàng Khánh Chi: Backend Developer, AI Enginner
- Vũ Mạnh Cường: Backend Developer, Database Designer
- Phạm Anh Tuấn: AI Engineer

---

Thank you for using **NutriHome**! 🚀
