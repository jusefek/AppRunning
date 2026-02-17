import streamlit as st
import google.generativeai as genai
from groq import Groq
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

# Cargar variables de entorno si existen
load_dotenv()

# --- Configuración de Página ---
st.set_page_config(
    page_title="RunSmart AI",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado (Dark Mode Deportivo) ---
st.markdown("""
<style>
    .stApp {
        /* background-color: #0e1117; handled by theme */
        /* color: #fafafa; handled by theme */
    }
    .stButton>button {
        background-color: #2ecc71;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #27ae60;
        color: white;
    }
    h1, h2, h3 {
        color: #fafafa;
    }
    .highlight-card {
        background-color: #1e2329;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2ecc71;
        margin-bottom: 20px;
    }
    .warning-card {
        background-color: #1e2329;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #e67e22;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Gestión de Estado ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")
if 'workout_plan' not in st.session_state:
    st.session_state.workout_plan = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_data_summary' not in st.session_state:
    st.session_state.user_data_summary = ""

# --- Sidebar: Configuración ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    api_key_input = st.text_input(
        "API Key (Gemini o Groq)",
        value=st.session_state.api_key,
        type="password",
        help="Introduce tu clave API de Google Gemini o Groq (empieza por gsk_)."
    )
    
    provider = "Desconocido"
    if api_key_input:
        st.session_state.api_key = api_key_input
        if api_key_input.startswith("gsk_"):
             provider = "Groq 🚀"
        else:
             provider = "Gemini 🧠"
             genai.configure(api_key=api_key_input)
        
        st.success(f"Conectado con {provider}")
    else:
        st.warning("⚠️ Necesitas una API Key para continuar.")
        st.markdown("[Conseguir Gemini Key](https://aistudio.google.com/app/apikey) | [Conseguir Groq Key](https://console.groq.com/keys)")

    st.markdown("---")
    st.markdown("### Acerca de")
    st.markdown("RunSmart AI optimiza tu entrenamiento diario usando Inteligencia Artificial.")
    st.markdown("v1.1.0 Multi-Model Support")

# --- Funciones Auxiliares IA ---

def generate_ai_content(prompt):
    api_key = st.session_state.api_key
    if not api_key:
        raise ValueError("API Key no configurada")
    
    if api_key.startswith("gsk_"):
        # Usar Groq
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        st.toast("Generando con Groq (Llama 3.3)...", icon="🚀")
        return chat_completion.choices[0].message.content
    else:
        # Usar Gemini (Default)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text

def generate_workout(data_context):
    """Genera el entrenamiento del día usando la IA configurada"""
    try:
        prompt = f"""
        Actúa como un entrenador de running de élite. Analiza los siguientes datos de un corredor y genera una recomendación de entrenamiento para HOY.
        
        Datos del Corredor:
        {data_context}
        
        Tu respuesta debe ser estructurada y motivadora.
        Formato de respuesta (Markdown):
        ## 🏃 Entrenamiento Recomendado: [Nombre Sesión]
        
        **Objetivo:** [Breve descripción del objetivo fisiológico]
        
        **Detalles:**
        - **Calentamiento:** [Tiempo/Distancia]
        - **Núcleo:** [Series, Rodaje, etc. con ritmos específicos si se pueden deducir, sino por sensación]
        - **Vuelta a la calma:** [Tiempo/Distancia]
        
        **¿Por qué este entreno?**
        [Explicación breve basada en los datos]
        """
        
        with st.spinner('Analizando tus datos con IA...'):
            return generate_ai_content(prompt)
            
            
    except Exception as e:
        return f"Error al generar entrenamiento: {str(e)}"

def load_user_data():
    """Carga los datos CSV del directorio data/"""
    data_summary = ""
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return "No se encontró el directorio de datos."

        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        if not files:
            return ""
        
        for file in files:
            df = pd.read_csv(os.path.join(data_dir, file))
            data_summary += f"\n--- {file} ---\n"
            data_summary += df.to_string(index=False) + "\n"
            
        return data_summary
    except Exception as e:
        return ""

def generate_race_strategy(race_type, target_time, user_data_context):
    """Genera una estrategia de carrera con la IA"""
    try:
        prompt = f"""
        Actúa como un entrenador de running de élite especializado en {race_type}.
        
        Objetivo del Corredor:
        - Tipo de Carrera: {race_type}
        - Tiempo Objetivo (si aplica): {target_time}
        
        Datos Históricos y Actuales del Corredor (CSV Data):
        {user_data_context}
        
        GENERA DOS SALIDAS:
        
        1. PLAN DE CARRERA DETALLADO (en Markdown):
           - Desglosa la carrera por tramos (ej. Salida, Medio, Muro, Final).
           - Estrategia de Ritmos (Pacing).
           - Estrategia de Nutrición e Hidratación (DETALLADA: qué tomar y cuándo).
           - Consejos mentales.
        
        2. DATOS PARA GRÁFICA (al final, en bloque CSV):
           - Genera un bloque CSV con las columnas: Km, Ritmo_Objetivo, FC_Objetivo_Estimada, Nutricion_Alert (1 si comer, 0 si no)
           - Debe cubrir toda la distancia de la carrera.
           - Encierra este bloque CSV entre etiquetas <CHART_DATA> y </CHART_DATA>.
        """
        
        with st.spinner('Diseñando tu estrategia de carrera...'):
            return generate_ai_content(prompt)
            
    except Exception as e:
        return f"Error: {str(e)}"

# --- Interfaz Principal ---

st.title("🏃 RunSmart AI")
st.markdown("### Tu entrenador personal inteligente")

# Tabs principales
# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Datos & Conexión", "🎯 Plan de Hoy", "💬 Chat Assistant", "🏆 Plan de Carrera"])

with tab1:
    st.header("Actualiza tu Estado")
    
    input_method = st.radio("Método de entrada:", ["Manual", "Link de Actividad (Strava/Garmin)"], horizontal=True)
    
    current_data = ""
    
    if input_method == "Manual":
        col1, col2 = st.columns(2)
        with col1:
            km_week = st.number_input("Kilómetros esta semana", min_value=0.0, value=20.0, step=1.0)
            avg_pace = st.text_input("Ritmo medio últimos rodajes (min/km)", value="5:30")
        with col2:
            fatigue = st.slider("Nivel de Cansancio (1=Fresco, 10=Agotado)", 1, 10, 5)
            soreness = st.selectbox("¿Dolores musculares?", ["Ninguno", "Molestia ligera", "Dolor agudo"])
            
        current_data = f"Km Semanales: {km_week}, Ritmo Medio: {avg_pace}, Cansancio: {fatigue}/10, Dolor: {soreness}"
        
    else:
        st.info("Pega aquí el enlace a tu actividad o copia y pega el texto resumen de tu última sesión.")
        activity_link = st.text_area("Link o Texto de Actividad", height=100, placeholder="Ej: https://strava.com/activities/... o 'Ayer hice 10k a 4:30 con pulsaciones medias de 145'")
        if activity_link:
            current_data = f"Información de actividad externa: {activity_link}."
    
    if st.button("Guardar y Analizar"):
        st.session_state.user_data_summary = current_data
        st.toast("Datos actualizados correctamente", icon="✅")
        # Auto-generar plan si hay API Key
        if st.session_state.api_key:
            plan = generate_workout(current_data)
            st.session_state.workout_plan = plan
            st.success("¡Plan generado! Ve a la pestaña 'Plan de Hoy'.")
        else:
            st.error("Por favor configura tu API Key primero.")

with tab2:
    st.header("Tu Entrenamiento para Hoy")
    
    if st.session_state.workout_plan:
        st.markdown(st.session_state.workout_plan)
        
        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            if st.button("Regenerar"):
                 if st.session_state.user_data_summary and st.session_state.api_key:
                    plan = generate_workout(st.session_state.user_data_summary + " (Genera una opción alternativa)")
                    st.session_state.workout_plan = plan
                    st.rerun()
    else:
        st.info("👈 Ve a la pestaña 'Datos' e introduce tu información para generar el plan.")

with tab3:
    st.header("💬 Chat con tu Entrenador")
    st.markdown("Pregunta dudas sobre el plan, nutrición o estrategia.")
    
    # Mostrar historial
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # Input de chat
    if prompt := st.chat_input("Escribe tu pregunta..."):
        if not st.session_state.api_key:
            st.error("Configura tu API Key para chatear.")
        else:
            # Añadir mensaje usuario
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generar respuesta IA
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Contexto para el chat
                    context_prompt = f"""
                    Eres un asistente experto en running.
                    Datos del usuario: {st.session_state.user_data_summary}
                    Plan de hoy sugerido: {st.session_state.workout_plan}
                    
                    Historial de chat reciente:
                    {st.session_state.chat_history[-5:]}
                    
                    Usuario pregunta: {prompt}
                    
                    Responde de forma breve, útil y directa.
                    """
                    
                    full_response = generate_ai_content(context_prompt)
                    message_placeholder.markdown(full_response)
                    
                    # Guardar respuesta
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"Error: {e}")

with tab4:
    st.header("🏆 Generador de Estrategia de Carrera")
    st.markdown("Diseña tu plan perfecto para Maratón, Ultra o Distancia personalizada.")
    
    col_race1, col_race2 = st.columns(2)
    with col_race1:
        race_type = st.selectbox("Distancia", ["10K", "Media Maratón", "Maratón", "Ultra 50K", "Ultra 80K+", "Personalizada"])
        target_time = st.text_input("Tiempo Objetivo (opcional)", placeholder="Ej: 3:30:00")
    
    # Estado para datos manuales
    if 'manual_race_data' not in st.session_state:
        st.session_state.manual_race_data = {}

    # Cargar datos CSV al inicio
    csv_data = load_user_data()
    
    # Si no hay CSVs, mostramos el formulario manual SIEMPRE (fuera del botón)
    manual_context = ""
    if not csv_data:
        st.info("⚠️ No se detectaron archivos CSV. Por favor, introduce tus datos manualmente para que la IA pueda ayudarte.")
        with st.expander("📝 Datos del Corredor (Manual)", expanded=True):
            col_man1, col_man2 = st.columns(2)
            with col_man1:
                md_dist = st.text_input("Última carrera (Distancia)", placeholder="Ej: 10K")
                md_time = st.text_input("Tiempo última carrera", placeholder="Ej: 45:00")
            with col_man2:
                md_vol = st.text_input("Volumen Semanal Promedio", placeholder="Ej: 40 km")
                md_long = st.text_input("Tirada más larga reciente", placeholder="Ej: 18 km")
            
            # Guardamos en variable para usar al generar
            if md_dist and md_time:
                manual_context = f"Última Carrera: {md_dist} en {md_time}. Volumen Semanal: {md_vol}. Tirada Larga: {md_long}."

    if st.button("Generar Estrategia de Carrera"):
        if not st.session_state.api_key:
            st.error("Configura tu API Key primero en la barra lateral.")
        elif not csv_data and not manual_context:
             st.error("⚠️ Necesitamos datos para generar el plan. Sube archivos CSV a la carpeta 'data' o rellena los campos manuales arriba.")
        else:
             # Combinar datos
            full_context = f"{st.session_state.user_data_summary}\n\nHISTORIAL:\n{csv_data if csv_data else 'Datos Manuales: ' + manual_context}"
            
            response = generate_race_strategy(race_type, target_time, full_context)
            
            # Separar texto y datos de gráfica
            import re
            chart_match = re.search(r'<CHART_DATA>(.*?)</CHART_DATA>', response, re.DOTALL)
            
            plan_text = response
            if chart_match:
                csv_block = chart_match.group(1).strip()
                # Limpiar texto del plan para no mostrar el CSV raw
                plan_text = response.replace(chart_match.group(0), "")
                
                # Procesar Gráfica
                try:
                    from io import StringIO
                    df_chart = pd.read_csv(StringIO(csv_block))
                    
                    st.success("¡Estrategia Generada!")
                    
                    # Visualización
                    st.subheader("📈 Tu Ritmo de Carrera")
                    
                    # Crear gráfica con matplotlib para más control
                    fig, ax1 = plt.subplots(figsize=(10, 5))
                    
                    color = 'tab:blue'
                    ax1.set_xlabel('Kilómetros')
                    ax1.set_ylabel('Ritmo (min/km)', color=color)
                    # Convertir ritmo a float si es necesario o plotear tal cual si son números
                    # Asumimos que la IA da ritmo en min/km formato decimal o similar, o intentamos plotear
                    # Si es formato MM:SS, habría que convertirlo. Le pediremos float a la IA o lo intentamos parsear.
                    # Para simplificar, le pediremos ritmos decimales o nos arriesgamos.
                    # Mejor: Pedir ritmo en min/km (decimal) en el prompt o parsear.
                    # Intentaremos plotear directamente.
                    
                    ax1.plot(df_chart['Km'], df_chart['Ritmo_Objetivo'], color=color, label='Ritmo')
                    ax1.tick_params(axis='y', labelcolor=color)
                    ax1.invert_yaxis() # Ritmo más bajo es más rápido
                    
                    # Marcar nutrición
                    if 'Nutricion_Alert' in df_chart.columns:
                        nutrition_points = df_chart[df_chart['Nutricion_Alert'] == 1]
                        if not nutrition_points.empty:
                            ax1.scatter(nutrition_points['Km'], nutrition_points['Ritmo_Objetivo'], color='red', s=100, label='Comer/Beber', zorder=5)
                    
                    st.pyplot(fig)
                    
                    # Mostrar tabla de pasos si se quiere
                    with st.expander("Ver tabla de pasos detallada"):
                        st.dataframe(df_chart)
                        
                except Exception as e:
                    st.warning(f"No se pudo generar la gráfica: {e}")
            
            st.markdown("## 📝 Tu Plan Detallado")
            st.markdown(plan_text)
