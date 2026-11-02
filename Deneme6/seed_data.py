import sqlite3
from datetime import datetime, timedelta
import random

DB_NAME = "performance_data.db"

def seed_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Clear existing data to start fresh
    c.execute("DELETE FROM reports")
    c.execute("DELETE FROM department_goals")
    c.execute("DELETE FROM company_goals")

    # 2. Add Company Goals
    company_goals = [
        ("2024 Global Büyüme", "Şirketin global pazar payını %15 artırmak", 100, 45, "Büyüme"),
        ("Operasyonel Maliyet Azaltımı", "Lojistik ve üretim maliyetlerini %10 düşürmek", 50, 20, "Finansal"),
        ("Müşteri Memnuniyeti Artışı", "NPS skorunu 70'in üzerine çıkarmak", 100, 85, "Müşteri")
    ]
    
    for title, desc, target, current, cat in company_goals:
        c.execute('''
            INSERT INTO company_goals (title, description, target_value, current_value, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, desc, target, current, cat, datetime.now()))
    
    # Get the IDs of the goals we just created
    c.execute("SELECT id, title FROM company_goals")
    cg_rows = c.fetchall()
    cg_map = {row[1]: row[0] for row in cg_rows}

    # 3. Add Department Goals
    departments = ["IT", "HR", "Satış", "Pazarlama", "Üretim", "Finans"]
    
    dept_goals = [
        ("Satış", "2024 Global Büyüme", "Avrupa Pazarı Satış Artışı", 40, 500000, 250000, "2024-12-31"),
        ("Pazarlama", "2024 Global Büyüme", "Dijital Reklam Dönüşüm Oranı", 20, 5, 2.5, "2024-11-30"),
        ("Üretim", "Operasyonel Maliyet Azaltımı", "Atık Azaltma Projesi", 60, 100, 75, "2024-10-15"),
        ("IT", "Operasyonel Maliyet Azaltımı", "Bulut Altyapı Optimizasyonu", 40, 20000, 15000, "2024-09-20"),
    ]

    for dept, cg_title, title, weight, target, current, deadline in dept_goals:
        c.execute('''
            INSERT INTO department_goals (department, company_goal_id, title, weight_on_company_goal, target_value, current_value, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (dept, cg_map[cg_title], title, weight, target, current, deadline))

    # 4. Add Performance Reports
    periods = ["Ocak 2024", "Şubat 2024", "Mart 2024"]
    
    for dept in departments:
        for period in periods:
            kpi = float(random.uniform(70, 98))
            eff = float(random.uniform(65, 95))
            sat = float(random.uniform(3.5, 4.8))
            t_goals = int(random.randint(5, 12))
            met_goals = int(random.randint(3, t_goals))
            
            c.execute('''
                INSERT INTO reports (department, reporting_period, kpi_score, goals_met, total_goals, efficiency, employee_satisfaction, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dept, period, round(kpi, 2), met_goals, t_goals, 
                round(eff, 2), round(sat, 1), f"{dept} departmanı {period} ayı performans özeti.", 
                (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat()
            ))

    conn.commit()
    conn.close()
    print("Test verileri başarıyla yüklendi!")

if __name__ == "__main__":
    seed_data()
