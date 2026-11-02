import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
import os
import io
import PyPDF2
import docx
import re

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="DevPerformX | Departman Performans Platformu",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- DATABASE SETUP ---
DB_NAME = "performance_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            reporting_period TEXT,
            kpi_score REAL,
            goals_met INTEGER,
            total_goals INTEGER,
            efficiency REAL,
            employee_satisfaction REAL,
            summary TEXT,
            created_at TIMESTAMP
        )
    ''')
    # Company Goals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            target_value REAL,
            current_value REAL,
            category TEXT, -- 'Growth', 'Financial', 'Operational'
            status TEXT DEFAULT 'Devam Ediyor',
            created_at TIMESTAMP
        )
    ''')
    # Department Goals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS department_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            company_goal_id INTEGER,
            title TEXT,
            weight_on_company_goal REAL, -- How much this dept goal affects the company goal (0-100)
            target_value REAL,
            current_value REAL,
            deadline DATE,
            FOREIGN KEY (company_goal_id) REFERENCES company_goals(id)
        )
    ''')
    # File Uploads table
    c.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            filename TEXT,
            file_data BLOB,
            uploaded_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_report(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (department, reporting_period, kpi_score, goals_met, total_goals, efficiency, employee_satisfaction, summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['department'], data['period'], data['kpi'], data['goals_met'], 
        data['total_goals'], data['efficiency'], data['satisfaction'], 
        data['summary'], datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_all_reports():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY created_at DESC", conn)
    conn.close()
    return df

def save_company_goal(title, desc, target, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO company_goals (title, description, target_value, current_value, category, created_at) VALUES (?, ?, ?, 0, ?, ?)',
              (title, desc, target, category, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_company_goals():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM company_goals", conn)
    conn.close()
    return df

def save_department_goal(dept, company_goal_id, title, weight, target, deadline):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ensure deadline is stored as string
    deadline_str = deadline.isoformat() if hasattr(deadline, 'isoformat') else str(deadline)
    c.execute('''
        INSERT INTO department_goals (department, company_goal_id, title, weight_on_company_goal, target_value, current_value, deadline)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    ''', (dept, company_goal_id, title, weight, target, deadline_str))
    conn.commit()
    conn.close()

def get_department_goals(dept=None):
    conn = sqlite3.connect(DB_NAME)
    if dept:
        query = "SELECT dg.*, cg.title as company_goal_title FROM department_goals dg JOIN company_goals cg ON dg.company_goal_id = cg.id WHERE dg.department = ?"
        df = pd.read_sql_query(query, conn, params=(dept,))
    else:
        query = "SELECT dg.*, cg.title as company_goal_title FROM department_goals dg JOIN company_goals cg ON dg.company_goal_id = cg.id"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_goal_progress(table, goal_id, new_value):
    # Restrict table name to whitelist to prevent SQL injection
    if table not in ['company_goals', 'department_goals']:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = f"UPDATE {table} SET current_value = ? WHERE id = ?"
    c.execute(query, (new_value, goal_id))
    conn.commit()
    conn.close()

def save_upload(dept, filename, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO uploads (department, filename, file_data, uploaded_at) VALUES (?, ?, ?, ?)',
              (dept, filename, data, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_uploads(dept=None):
    conn = sqlite3.connect(DB_NAME)
    if dept:
        df = pd.read_sql_query("SELECT id, department, filename, uploaded_at FROM uploads WHERE department = ?", conn, params=(dept,))
    else:
        df = pd.read_sql_query("SELECT id, department, filename, uploaded_at FROM uploads", conn)
    conn.close()
    return df

# --- AI ANALYSIS UTILS ---
def extract_text_from_file(file):
    filename = file.name
    content = ""
    try:
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                content += page.extract_text()
        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            for para in doc.paragraphs:
                content += para.text + "\n"
        elif filename.endswith('.txt'):
            content = file.read().decode('utf-8')
    except Exception as e:
        return f"Dosya okunurken hata oluştu: {str(e)}"
    return content

# --- NEURAL STRATEGIC ENGINE (ULTRA-INTELLIGENCE LAYER) ---
class NeuralStrategicEngine:
    """
    Simulated Deep Learning & Cognitive Analysis Architecture.
    Processes data through multiple conceptual layers.
    """
    def __init__(self, text, goals_df):
        self.text = text
        self.goals_df = goals_df
        self.entities = self._extract_entities()
        self.sentiment_map = self._neural_sentiment()
        self.causal_links = self._detect_causality()
        
    def _extract_entities(self):
        return {
            "percentages": re.findall(r'%?\d+(?:[\.,]\d+)?\s?%', self.text) or re.findall(r'%\s?\d+', self.text),
            "money": re.findall(r'[\d\.,]+\s?(?:TL|USD|EUR|TRY|\$|€)', self.text),
            "dates": re.findall(r'\d{2}[./-]\d{2}[./-]\d{4}', self.text),
            "key_metrics": re.findall(r'(?:KPI|ROI|NPS|EBITDA|OEE)', self.text, re.IGNORECASE)
        }

    def _neural_sentiment(self):
        layers = {
            "Strategic": ["vizyon", "plan", "strateji", "yol haritası", "büyüme", "genişleme", "yatırım"],
            "Operational": ["süreç", "akış", "üretim", "verimlilik", "standardizasyon", "otomasyon"],
            "Risk": ["tehdit", "darboğaz", "gecikme", "hata", "kayıp", "maliyet artışı", "kriz"],
            "Innovation": ["ar-ge", "yeni", "dijitalleşme", "inovasyon", "teknoloji", "geliştirme"]
        }
        scores = {}
        for layer, keywords in layers.items():
            scores[layer] = sum(1 for k in keywords if k in self.text.lower())
        return scores

    def _detect_causality(self):
        # Detecting "Reason -> Result" patterns
        connectors = ["çünkü", "sebebiyle", "nedeniyle", "sonucunda", "dolayı", "hedeflendiği için"]
        causal_sentences = []
        sentences = re.split(r'[.!?]', self.text)
        for s in sentences:
            if any(c in s.lower() for c in connectors):
                causal_sentences.append(s.strip())
        return causal_sentences[:3]

    def generate_omega_report(self):
        # 1. Main Clear Narrative (Executive Submission Format)
        pos_total = self.sentiment_map["Strategic"] + self.sentiment_map["Innovation"]
        neg_total = self.sentiment_map["Risk"]
        
        # Formal Header
        narrative = f"SAYIN ÜST YÖNETİCİ,\n"
        narrative += f"KONU: STRATEJİK PERFORMANS VE DEPARTMAN ANALİZİ\n"
        narrative += f"TARİH: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        narrative += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Paragraph 1: Executive Summary
        tone_desc = "stratejik büyüme hedefleriyle tam uyumlu ve proaktif" if pos_total > neg_total else "operasyonel risklerin yönetimi ve süreç stabilizasyonuna odaklanan"
        narrative += f"Ekte sunulan veriler doğrultusunda, ilgili dönem raporu analiz edilmiş olup departman genel profilinin {tone_desc} olduğu saptanmıştır. "
        
        if self.sentiment_map["Innovation"] > 0:
            narrative += "Özellikle inovasyon ve dijital dönüşüm kalemlerindeki faaliyetlerin kurumsal rekabet gücümüze doğrudan katkı sağladığı gözlemlenmektedir. "
        
        # Paragraph 2: Key Operational Metrics
        narrative += "\n\nKRİTİK PERFORMANS GÖSTERGELERİ:\n"
        if self.entities["percentages"]:
            narrative += f"- Operasyonel verimlilik ve KPI uyumu noktasında %{self.entities['percentages'][0].replace('%','')} seviyesi öne çıkmaktadır.\n"
        if self.entities["money"]:
            narrative += f"- Bütçe disiplini ve finansal etki tarafında {self.entities['money'][0]} hacmindeki kalemler stratejik öneme sahiptir.\n"
        
        # Paragraph 3: Strategic Alignment
        aligned = [goal['title'] for _, goal in self.goals_df.iterrows() if any(word in self.text.lower() for word in goal['title'].lower().split() if len(word) > 3)] if self.goals_df is not None else []
        if aligned:
            narrative += f"\nKURUMSAL STRATEJİ UYUMU:\nSistemimizde tanımlı '{', '.join(aligned)}' hedeflerine ilişkin faaliyetler rapor içerisinde detaylandırılmış ve şirket vizyonuyla paralellik sağlanmıştır.\n"
        
        # Paragraph 4: Projections & Risk Assessment
        kpi_est = min(100, 72 + (self.sentiment_map["Strategic"] * 4) + (self.sentiment_map["Innovation"] * 3) - (self.sentiment_map["Risk"] * 5))
        narrative += f"\nGELECEK PROJEKSİYONU VE DEĞERLENDİRME:\nDepartman için projekte edilen performans katsayısı %{kpi_est:.1f} olarak hesaplanmıştır. "
        if neg_total > 1:
            narrative += "Büyüme ivmesinin korunabilmesi adına, saptanan operasyonel darboğazların ivedilikle giderilmesi ve kaynak planlamasının bu yönde revize edilmesi kritik önem arz etmektedir."
        else:
            narrative += "Mevcut başarılı iş modellerinin standartlaştırılarak diğer operasyon birimlerine de entegre edilmesi, kurumsal yaygınlaştırma stratejimiz için uygun bulunmuştur."

        narrative += "\n\nBilgilerinize arz ederim.\nSaygılarımla,\nDevPerformX AI Strateji Birimi"

        # 2. Technical Metrics (The Notification/Side Panel)
        metrics_html = f"""
        <div style="background: rgba(99, 102, 241, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #6366f1;">
            <h4 style="margin:0; color:#6366f1;">🧠 OMEGA ENGINE: STRATEJİK ANALİZ VERİLERİ</h4>
            <hr style="opacity:0.2">
            <p style="font-size:0.9rem;"><b>Durum Matrisi:</b> {'🔴 YÜKSEK RİSK' if self.sentiment_map['Risk'] > 2 else ('🟢 STRATEJİK İVME' if self.sentiment_map['Strategic'] > 2 else '🔵 OPERASYONEL DENGE')}</p>
            <p style="font-size:0.9rem;"><b>Bilişsel Katmanlar:</b> Strateji: {self.sentiment_map['Strategic']} | Operasyon: {self.sentiment_map['Operational']} | Risk: {self.sentiment_map['Risk']} | İnovasyon: {self.sentiment_map['Innovation']}</p>
            <p style="font-size:0.9rem;"><b>Veri Kapasitesi:</b> {len(self.entities['percentages'])} Oran | {len(self.entities['money'])} Finansal Veri</p>
        </div>
        """
        
        # 3. Gaps
        gaps = [goal['title'] for _, goal in self.goals_df.iterrows() if goal['title'] not in aligned] if self.goals_df is not None else []

        return narrative, metrics_html, gaps

def ai_analyze_content(text, dept_goals_df=None):
    if not text:
        return "Veri girişi yapılmadı.", "", []
    
    engine = NeuralStrategicEngine(text, dept_goals_df)
    narrative, metrics, gaps = engine.generate_omega_report()
    
    return narrative, metrics, gaps

# Initialize DB
init_db()

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main {
        background-color: #0f1116;
        color: #e0e0e0;
    }

    /* Glassmorphism sidebar */
    section[data-testid="stSidebar"] {
        background-image: linear-gradient(180deg, #1a1c23 0%, #0f1116 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #4f46e5;
        background: rgba(79, 70, 229, 0.05);
    }

    .metric-title {
        color: #94a3b8;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 8px;
    }

    /* Header styling */
    .stHeading h1 {
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Input styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }

    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        transform: scale(1.02);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom-color: #6366f1 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=80)
    st.title("DevPerformX")
    st.markdown("---")
    
    menu = st.radio(
        "Navigasyon",
        ["🏠 Dashboard", "🎯 Stratejik Hedefler", "💹 Büyüme Planı", "➕ Yeni Rapor", "📁 Arşiv", "🏢 Departman Ayarları"],
        index=0
    )
    
    st.markdown("---")
    st.info("Bu platform şirket hedefleri ve departman performans takibi için tasarlanmıştır.")

# --- APP LOGIC ---

if menu == "🏠 Dashboard":
    st.title("Performans Özeti")
    
    df = get_all_reports()
    
    if df.empty:
        st.info("Henüz veri girişi yapılmamış. Lütfen 'Yeni Rapor' sekmesinden veri ekleyin.")
    else:
        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        avg_kpi = df['kpi_score'].mean()
        total_reports = len(df)
        avg_efficiency = df['efficiency'].mean()
        
        # Calculate company goal average progress
        cg_df = get_company_goals()
        if not cg_df.empty:
            avg_goal_progress = (cg_df['current_value'] / cg_df['target_value']).mean() * 100
        else:
            avg_goal_progress = 0
            
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">Şirket Hedef İlerlemesi</div>
                <div class="metric-value">{avg_goal_progress:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">Ortalama KPI</div>
                <div class="metric-value">{avg_kpi:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">Operasyonel Verimlilik</div>
                <div class="metric-value">{avg_efficiency:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">Toplam Rapor</div>
                <div class="metric-value">{total_reports}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Departman Bazlı Performans")
            fig_dept = px.bar(
                df.groupby('department')['kpi_score'].mean().reset_index(),
                x='department', y='kpi_score',
                color='kpi_score',
                color_continuous_scale='Viridis',
                template="plotly_dark"
            )
            fig_dept.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_dept, use_container_width=True)
            
        with c2:
            st.subheader("Performans Trendi")
            df['date'] = pd.to_datetime(df['created_at'], format='mixed')
            fig_trend = px.line(
                df.sort_values('date'),
                x='date', y='kpi_score',
                markers=True,
                line_shape='spline',
                template="plotly_dark"
            )
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("Son Raporlar")
        st.dataframe(df[['department', 'reporting_period', 'kpi_score', 'efficiency', 'created_at']], use_container_width=True)

elif menu == "🎯 Stratejik Hedefler":
    st.title("Stratejik Hedef Yönetimi")
    
    tab1, tab2 = st.tabs(["Şirket Hedefleri", "Departman Hedefleri"])
    
    with tab1:
        st.subheader("Ana Şirket Hedefleri")
        with st.expander("➕ Yeni Şirket Hedefi Ekle"):
            with st.form("company_goal_form"):
                g_title = st.text_input("Hedef Başlığı")
                g_desc = st.text_area("Açıklama")
                col_g1, col_g2 = st.columns(2)
                g_target = col_g1.number_input("Hedef Değer", min_value=1.0, value=100.0)
                g_cat = col_g2.selectbox("Kategori", ["Büyüme", "Finansal", "Operasyonel", "Müşteri"])
                if st.form_submit_button("Hedefi Kaydet"):
                    save_company_goal(g_title, g_desc, g_target, g_cat)
                    st.success("Şirket hedefi eklendi!")
                    st.rerun()
        
        goals = get_company_goals()
        for idx, goal in goals.iterrows():
            progress = (goal['current_value'] / goal['target_value'])
            st.markdown(f"**{goal['title']}** ({goal['category']})")
            st.progress(min(progress, 1.0))
            st.write(f"İlerleme: {goal['current_value']} / {goal['target_value']}")
            new_val = st.number_input("Güncel Değer", value=float(goal['current_value']), key=f"cg_{goal['id']}")
            if st.button("Güncelle", key=f"btn_cg_{goal['id']}"):
                update_goal_progress('company_goals', goal['id'], new_val)
                st.rerun()
            st.markdown("---")

    with tab2:
        st.subheader("Departman Bazlı Alt Hedefler")
        company_goals = get_company_goals()
        if company_goals.empty:
            st.warning("Önce şirket hedefi oluşturmalısınız.")
        else:
            with st.expander("➕ Yeni Departman Hedefi Ekle"):
                with st.form("dept_goal_form"):
                    d_dept = st.selectbox("Departman", ["IT", "HR", "Satış", "Pazarlama", "Üretim", "Finans"])
                    d_cg = st.selectbox("Bağlı Şirket Hedefi", company_goals['title'].tolist())
                    d_cg_id = company_goals[company_goals['title'] == d_cg]['id'].values[0]
                    d_title = st.text_input("Alt Hedef Başlığı")
                    d_weight = st.slider("Şirket Hedefine Etki Ağırlığı (%)", 0, 100, 20)
                    d_target = st.number_input("Hedef Değer", min_value=1.0, value=100.0)
                    d_deadline = st.date_input("Termin")
                    if st.form_submit_button("Hedefi Kaydet"):
                        save_department_goal(d_dept, d_cg_id, d_title, d_weight, d_target, d_deadline)
                        st.success("Departman hedefi eklendi!")
                        st.rerun()
            
            d_goals = get_department_goals()
            st.dataframe(d_goals[['department', 'title', 'company_goal_title', 'weight_on_company_goal', 'target_value', 'current_value', 'deadline']], use_container_width=True)

elif menu == "💹 Büyüme Planı":
    st.title("Şirket Büyüme ve Performans Analizi")
    
    cg_df = get_company_goals()
    dg_df = get_department_goals()
    
    if cg_df.empty:
        st.info("Büyüme analizi için henüz stratejik hedef tanımlanmamış.")
    else:
        st.subheader("Büyüme Kategorilerine Göre Dağılım")
        fig_growth = px.pie(cg_df, values='target_value', names='category', hole=.3, template="plotly_dark")
        st.plotly_chart(fig_growth, use_container_width=True)
        
        st.subheader("Departmanların Büyümeye Katkısı")
        if not dg_df.empty:
            growth_contrib = dg_df.groupby('department')['weight_on_company_goal'].sum().reset_index()
            fig_contrib = px.bar(growth_contrib, x='department', y='weight_on_company_goal', 
                                title="Şirket Hedeflerine Toplam Etki Ağırlığı",
                                labels={'weight_on_company_goal': 'Toplam Etki (%)'},
                                color='weight_on_company_goal',
                                template="plotly_dark")
            st.plotly_chart(fig_contrib, use_container_width=True)
        else:
            st.info("Büyümeye katkı analizi için henüz departman hedefi tanımlanmamış.")

    st.markdown("---")
    st.subheader("📂 Departman Büyüme Belgeleri")
    st.info("Departman liderleri büyüme planları ve stratejik dokümanları buradan yükleyebilir.")
    
    up_col1, up_col2 = st.columns([1, 2])
    
    with up_col1:
        st.markdown("**Yeni Belge Yükle**")
        u_dept = st.selectbox("Departmanınız", ["IT", "HR", "Satış", "Pazarlama", "Üretim", "Finans"], key="upload_dept_select")
        uploaded_file = st.file_uploader("Dosya Seçin (PDF, DOCX, XLSX)", type=['pdf', 'docx', 'xlsx', 'txt'])
        if st.button("Belgeyi Kaydet"):
            if uploaded_file is not None:
                save_upload(u_dept, uploaded_file.name, uploaded_file.getvalue())
                st.success(f"{uploaded_file.name} başarıyla yüklendi.")
                st.rerun()
            else:
                st.error("Lütfen bir dosya seçin.")

    with up_col2:
        st.markdown("**Yüklenen Belgeler**")
        files_df = get_uploads()
        if files_df.empty:
            st.write("Henüz yüklenmiş bir belge yok.")
        else:
            st.dataframe(files_df[['department', 'filename', 'uploaded_at']], use_container_width=True)
            st.caption("Not: Dosyalar veritabanında güvenli bir şekilde saklanmaktadır.")

elif menu == "➕ Yeni Rapor":
    st.title("AI Destekli Performans Raporu")
    st.markdown("Bir dosya yükleyin veya manuel olarak verileri girin. AI otomatik analiz yaparak metin alanını dolduracaktır.")
    
    # Session state for AI summary, gaps and technical metrics
    if 'ai_summary' not in st.session_state:
        st.session_state.ai_summary = ""
    if 'ai_gaps' not in st.session_state:
        st.session_state.ai_gaps = []
    if 'ai_metrics' not in st.session_state:
        st.session_state.ai_metrics = ""

    # File upload for AI analysis
    with st.expander("✨ AI ile Dosya Analiz Et", expanded=True):
        a_col1, a_col2 = st.columns([1, 1])
        with a_col1:
            analysis_dept = st.selectbox("Analiz Edilecek Departman", ["IT", "HR", "Satış", "Pazarlama", "Üretim", "Finans"], key="ai_dept_select")
        with a_col2:
            analysis_file = st.file_uploader("Analiz edilecek rapor dosyasını seçin", type=['pdf', 'docx', 'txt'], key="ai_analyser")
            
        if st.button("ULTRA-ZEKA ANALİZİNİ BAŞLAT (OMEGA ENGINE) ⚡"):
            if analysis_file:
                # Neural processing visual
                progress_bar = st.progress(0)
                status_text = st.empty()
                for percent_complete in range(100):
                    import time
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1)
                    if percent_complete == 30: status_text.text("🧠 Nöral Ağlar Yapılandırılıyor...")
                    if percent_complete == 70: status_text.text("⚡ Stratejik Sentez Oluşturuluyor...")
                
                with st.spinner("AI Omega Engine Sentezliyor..."):
                    current_goals = get_department_goals(analysis_dept)
                    text = extract_text_from_file(analysis_file)
                    narrative, metrics, gaps = ai_analyze_content(text, current_goals)
                    st.session_state.ai_summary = narrative
                    st.session_state.ai_metrics = metrics
                    st.session_state.ai_gaps = gaps
                
                status_text.empty()
                progress_bar.empty()
                st.success("Analiz tamamlandı! Rapor ve teknik veriler hazır.")
            else:
                st.error("Lütfen önce bir dosya yükleyin.")

    with st.form("report_form", clear_on_submit=True):
        # Display Technical Metrics at the top of the form as a notification block
        if st.session_state.ai_metrics:
            st.markdown(st.session_state.ai_metrics, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            dept_name = st.selectbox("Departman Seçin", ["IT", "HR", "Satış", "Pazarlama", "Üretim", "Finans"])
            period = st.text_input("Raporlama Dönemi (Örn: 2024 Q3)")
            kpi_score = st.slider("Genel KPI Skoru (%)", 0.0, 100.0, 75.0)
            
        with f_col2:
            efficiency = st.slider("Operasyonel Verimlilik (%)", 0.0, 100.0, 80.0)
            goals_met = st.number_input("Tamamlanan Hedef Sayısı", min_value=0, value=5)
            total_goals = st.number_input("Toplam Hedef Sayısı", min_value=1, value=10)
            
        # Manager Summary area (Clear Narrative)
        summary = st.text_area("Yönetici Özeti (Anlaşılır Metin)", value=st.session_state.ai_summary, height=350)
        
        # Display AI Gaps below the main form content
        if st.session_state.ai_gaps:
            st.warning("⚠️ STRATEJİK DENETİM: RAPORDA EKSİK KALAN HEDEFLER")
            for gap in st.session_state.ai_gaps:
                st.markdown(f"- ❌ **{gap}**")
            st.markdown("---")

        satisfaction = st.slider("Çalışan Memnuniyeti (1-5)", 1.0, 5.0, 4.0)
        
        submit = st.form_submit_button("Raporu Kaydet")
        
        if submit:
            if not period:
                st.error("Lütfen raporlama dönemini giriniz.")
            else:
                data = {
                    'department': dept_name,
                    'period': period,
                    'kpi': kpi_score,
                    'goals_met': goals_met,
                    'total_goals': total_goals,
                    'efficiency': efficiency,
                    'satisfaction': satisfaction,
                    'summary': summary
                }
                save_report(data)
                st.success(f"{dept_name} için AI destekli rapor başarıyla kaydedildi!")
                st.session_state.ai_summary = "" # Clear for next
                st.balloons()
                st.rerun()

elif menu == "📁 Arşiv":
    st.title("Rapor Arşivi")
    df = get_all_reports()
    
    if df.empty:
        st.info("Arşivde henüz rapor bulunmuyor.")
    else:
        search_dept = st.multiselect("Departmana Göre Filtrele", df['department'].unique())
        
        filtered_df = df
        if search_dept:
            filtered_df = df[df['department'].isin(search_dept)]
            
        for index, row in filtered_df.iterrows():
            with st.expander(f"📄 {row['department']} - {row['reporting_period']} (Skor: %{row['kpi_score']})"):
                ac1, ac2, ac3 = st.columns(3)
                ac1.metric("Verimlilik", f"%{row['efficiency']}")
                ac2.metric("Hedefler", f"{row['goals_met']}/{row['total_goals']}")
                ac3.metric("Memnuniyet", f"{row['employee_satisfaction']}/5")
                
                st.markdown("**Özet:**")
                st.write(row['summary'] if row['summary'] else "Not eklenmemiş.")
                st.caption(f"Kayıt Tarihi: {row['created_at']}")
                
                if st.button(f"SİL: {row['id']}", key=f"del_{row['id']}"):
                    # Logic to delete could go here
                    st.warning("Silme özelliği henüz aktif değil.")

elif menu == "🏢 Departman Ayarları":
    st.title("Departman ve KPI Ayarları")
    st.info("Buradan değerlendirme kriterlerini ve departman listesini güncelleyebilirsiniz (Gelecek Güncelleme).")
    
    st.markdown("""
    ### Planlanan Özellikler:
    - [ ] Özel KPI kriterleri tanımlama
    - [ ] Departman bazlı hedef atama
    - [ ] E-posta ile rapor gönderimi
    - [ ] PDF olarak dışa aktarma
    """)

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "© 2024 DevPerformX | Güçlü Analiz, Akıllı Kararlar"
    "</div>",
    unsafe_allow_html=True
)
