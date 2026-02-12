import streamlit as st
import google.generativeai as genai
from groq import Groq
import os
from dotenv import load_dotenv

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
        background-color: #0e1117;
        color: #fafafa;
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
            model="llama3-70b-8192",
            temperature=0.7,
        )
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

# --- Interfaz Principal ---

st.title("🏃 RunSmart AI")
st.markdown("### Tu entrenador personal inteligente")

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📊 Datos & Conexión", "🎯 Plan de Hoy", "💬 Chat Assistant"])

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
