import flet as ft
import json
import requests
import uuid
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def main(page: ft.Page):
    page.title = "Sistema Experto: Hipertensión"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ALWAYS

    # Base de datos simulada de pacientes
    pacientes_db = []
    
    # Configuración del bot de Telegram
    TELEGRAM_BOT_URL = "http://localhost:1880/telegram"  # URL de tu endpoint de Node-RED


    API_KEY = os.getenv('GEMINI_API_KEY') 

    arbol = {
        0: {"pregunta": "¿El paciente tiene presión arterial elevada (≥140/90 mmHg)?",
            "respuesta": "Esto indica hipertensión arterial, una enfermedad cardiovascular crónica.",
            "si": 1, "no": 2},
        1: {"pregunta": "¿Presenta factores de riesgo como obesidad o sedentarismo?",
            "respuesta": "Edad, obesidad, sedentarismo y sal son factores de riesgo frecuentes.",
            "si": 3, "no": 4},
        2: {"pregunta": "¿Tiene síntomas como dolor de cabeza o visión borrosa?",
            "respuesta": "Dolor de cabeza, visión borrosa y fatiga son síntomas comunes.",
            "si": 5, "no": 6},
        3: {"pregunta": "¿La obesidad está presente?",
            "respuesta": "Sí, el sobrepeso eleva significativamente el riesgo.",
            "si": 9, "no": 10},
        4: {"pregunta": "¿El paciente consume mucha sal?",
            "respuesta": "El consumo excesivo de sal aumenta la presión arterial.",
            "si": 11, "no": 22},
        5: {"pregunta": "¿No presenta ningún síntoma?",
            "respuesta": "La hipertensión puede ser silenciosa en fases tempranas.",
            "si": 15, "no": 28},
        6: {"pregunta": "¿Síntomas severos como confusión o convulsiones?",
            "respuesta": "Síntomas severos pueden indicar una crisis hipertensiva.",
            "si": 30, "no": 23},
        7: {"pregunta": "¿Tiene antecedentes familiares de hipertensión?",
        "respuesta": "La herencia genética puede predisponer a la hipertensión.",
        "si": 15, "no": 16},

    8: {"pregunta": "¿Realiza actividad física al menos 3 veces por semana?",
        "respuesta": "La actividad física ayuda a controlar la presión arterial.",
        "si": 17, "no": 18},

    9: {"pregunta": "¿Consume alcohol de forma regular?",
        "respuesta": "El consumo excesivo de alcohol eleva la presión arterial.",
        "si": 19, "no": 20},

    10: {"pregunta": "¿Tiene una dieta equilibrada?",
         "respuesta": "Una dieta balanceada ayuda a prevenir hipertensión.",
         "si": 21, "no": 22},

    11: {"pregunta": "¿Ha tenido mediciones de presión normales en los últimos 6 meses?",
         "respuesta": "Un historial estable es buena señal.",
         "si": 23, "no": 24},

    12: {"pregunta": "¿Presenta mareos o fatiga frecuente?",
         "respuesta": "Puede indicar problemas circulatorios o cardíacos.",
         "si": 25, "no": 26},

    13: {"pregunta": "¿Está tomando medicación antihipertensiva actualmente?",
         "respuesta": "Seguir el tratamiento médico es crucial.",
         "si": 27, "no": 28},

    14: {"pregunta": "¿Se ha realizado un chequeo médico en el último año?",
         "respuesta": "Los chequeos anuales ayudan a la prevención.",
         "si": 29, "no": 30},

    # --- HOJAS DEL ÁRBOL ---
    15: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Requiere seguimiento médico especializado.",
         "si": None, "no": None},

    16: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Mantener hábitos saludables y control periódico.",
         "si": None, "no": None},

    17: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Muy buena práctica. Mantenerla en el tiempo.",
         "si": None, "no": None},

    18: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Aumentar actividad física para reducir riesgos.",
         "si": None, "no": None},

    19: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Reducir el consumo de alcohol urgentemente.",
         "si": None, "no": None},

    20: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Mantener control y dieta saludable.",
         "si": None, "no": None},

    21: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Excelente, continúe con su dieta balanceada.",
         "si": None, "no": None},

    22: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Mejorar la dieta y reducir sal y grasas.",
         "si": None, "no": None},

    23: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Mantener monitoreo regular.",
         "si": None, "no": None},

    24: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Realizar seguimiento más frecuente.",
         "si": None, "no": None},

    25: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Puede necesitar evaluación cardiológica.",
         "si": None, "no": None},

    26: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Mantener observación y control.",
         "si": None, "no": None},

    27: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Seguir medicación y controles médicos.",
         "si": None, "no": None},

    28: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Consultar con médico para iniciar tratamiento.",
         "si": None, "no": None},

    29: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Buen control preventivo.",
         "si": None, "no": None},

    30: {"pregunta": "Fin del diagnóstico",
         "respuesta": "Realizar un chequeo lo antes posible.",
         "si": None, "no": None},
    }

    estado = {"nodo": 0, "historial": [], "paciente_actual": None, "respuestas": []}
    diagnostico_text = ft.Text("", size=22, color="red", weight="bold")
    respuesta_texto = ft.Text("", size=18, color="black")

    # --- COMPONENTES DEL CHATBOT IA ---
    ia_response_text = ft.Column(
        controls=[
            ft.Text("🤖 Asistente IA - Hipertensión", size=18, weight="bold"),
            ft.Text("Hola! Puedes hacerme preguntas sobre hipertensión, síntomas, tratamientos, etc.", 
                    size=14, color="blue")
        ],
        height=300,
        scroll=ft.ScrollMode.AUTO,
        spacing=5
    )
    
    prompt_input = ft.TextField(
        label="Escribe tu pregunta sobre hipertensión...",
        multiline=True,
        max_lines=3,
        expand=True
    )

    def send_prompt_to_ai():
        prompt = prompt_input.value.strip()
        if not prompt:
            return
        
        # Agregar pregunta del usuario al chat
        ia_response_text.controls.append(
            ft.Container(
                content=ft.Text(f"🤔 {prompt}", selectable=True),
                bgcolor=ft.Colors.BLUE_100,
                padding=10,
                border_radius=5,
                margin=ft.margin.only(bottom=5)
            )
        )
        
        prompt_input.value = ""
        page.update()
        
        try:
            if not API_KEY:
                ia_response_text.controls.append(
                    ft.Container(
                        content=ft.Text("❌ Error: API Key no configurada. Agrega tu API key de Gemini.", 
                                       selectable=True, color="red"),
                        bgcolor=ft.Colors.RED_100,
                        padding=10,
                        border_radius=5,
                        margin=ft.margin.only(bottom=5)
                    )
                )
                page.update()
                return
            
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            # Contexto médico especializado
            context = """Eres un asistente médico especializado en hipertensión arterial. 
            Proporciona información médica precisa pero siempre recuerda que no sustituyes 
            la consulta médica profesional. Responde de forma clara y comprensible."""
            
            full_prompt = f"{context}\n\nPregunta del paciente: {prompt}"
            
            # Agregar contexto del paciente actual si existe
            if estado["paciente_actual"]:
                p = estado["paciente_actual"]
                patient_context = f"\nDatos del paciente actual: {p['nombre']}, {p['edad']} años, IMC: {p['imc']}"
                if p.get('respuestas'):
                    patient_context += f", Respuestas de evaluación: {', '.join(p['respuestas'])}"
                full_prompt += patient_context
            
            response = model.generate_content(full_prompt)
            
            # Agregar respuesta de la IA al chat
            ai_response = response.text + "\n\n⚠️ Esta información es orientativa. Consulta siempre con un médico profesional."
            
            ia_response_text.controls.append(
                ft.Container(
                    content=ft.Text(f"🤖 {ai_response}", selectable=True),
                    bgcolor=ft.Colors.GREEN_100,
                    padding=10,
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )
            )
            
        except Exception as e:
            ia_response_text.controls.append(
                ft.Container(
                    content=ft.Text(f"❌ Error: {str(e)}", selectable=True, color="red"),
                    bgcolor=ft.Colors.RED_100,
                    padding=10,
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )
            )
        
        page.update()

    def limpiar_chat(_):
        ia_response_text.controls = [
            ft.Text("🤖 Asistente IA - Hipertensión", size=18, weight="bold"),
            ft.Text("Chat limpiado. ¿En qué puedo ayudarte?", size=14, color="blue")
        ]
        page.update()

    # --- COMPONENTES PARA FORMULARIO DE PACIENTE ---
    nombre_field = ft.TextField(label="Nombre Completo", width=300)
    edad_field = ft.TextField(label="Edad", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    sexo_dropdown = ft.Dropdown(
        label="Sexo",
        width=150,
        options=[
            ft.dropdown.Option("M", "Masculino"),
            ft.dropdown.Option("F", "Femenino"),
        ],
    )
    telefono_field = ft.TextField(label="Número de Teléfono", width=200)
    email_field = ft.TextField(label="Email", width=300)
    peso_field = ft.TextField(label="Peso (kg)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    altura_field = ft.TextField(label="Altura (cm)", width=150, keyboard_type=ft.KeyboardType.NUMBER)

    def mostrar_notificacion(mensaje, color="green"):
        page.snack_bar = ft.SnackBar(content=ft.Text(mensaje), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def validar_formulario():
        if not all([nombre_field.value, edad_field.value, sexo_dropdown.value, 
                   telefono_field.value, peso_field.value, altura_field.value]):
            return False
        return True

    def crear_paciente(_):
        if not validar_formulario():
            mostrar_notificacion("Por favor complete todos los campos", "red")
            return
        
        paciente_id = str(uuid.uuid4())[:8]
        imc = round(float(peso_field.value) / ((float(altura_field.value)/100) ** 2), 2)
        
        paciente = {
            "id": paciente_id,
            "nombre": nombre_field.value,
            "edad": int(edad_field.value),
            "sexo": sexo_dropdown.value,
            "telefono": telefono_field.value,
            "email": email_field.value,
            "peso": float(peso_field.value),
            "altura": float(altura_field.value),
            "imc": imc,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "respuestas": [],
            "diagnostico": ""
        }
        
        pacientes_db.append(paciente)
        estado["paciente_actual"] = paciente
        
        # Limpiar formulario
        for field in [nombre_field, edad_field, telefono_field, email_field, peso_field, altura_field]:
            field.value = ""
        sexo_dropdown.value = None
        
        mostrar_notificacion(f"Paciente registrado con ID: {paciente_id}")
        
        # Notificar en el chat sobre el nuevo paciente
        ia_response_text.controls.append(
            ft.Container(
                content=ft.Text(f"📋 Nuevo paciente registrado: {paciente['nombre']}, {paciente['edad']} años, IMC: {paciente['imc']}", 
                               selectable=True, color="purple"),
                bgcolor=ft.Colors.PURPLE_100,
                padding=10,
                border_radius=5,
                margin=ft.margin.only(bottom=5)
            )
        )
        
        page.update()

    def enviar_telegram(paciente, diagnostico_completo):
        try:
            mensaje = f"""🏥 SISTEMA EXPERTO - HIPERTENSIÓN

Estimado/a {paciente['nombre']},

Su evaluación ha sido completada:
- ID: {paciente['id']}
- IMC: {paciente['imc']} kg/m²
- Fecha: {paciente['fecha']}

RESPUESTAS:
{chr(10).join(paciente['respuestas'])}

RECOMENDACIONES:
- Consulte con un médico especialista
- Monitoree su presión arterial regularmente
- Mantenga una dieta baja en sodio
- Realice ejercicio regularmente

Este es un sistema de apoyo, no sustituye la consulta médica."""
            
            payload = {"telefono": paciente['telefono'], "mensaje": mensaje}
            response = requests.post(TELEGRAM_BOT_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                mostrar_notificacion("Mensaje enviado por Telegram exitosamente")
            else:
                mostrar_notificacion("Error al enviar mensaje por Telegram", "red")
                
        except Exception as e:
            mostrar_notificacion(f"Error de conexión: {str(e)}", "red")

    def siguiente_pregunta(respuesta):
        if not estado["paciente_actual"]:
            mostrar_notificacion("Debe registrar un paciente primero", "red")
            return
            
        nodo_actual = estado["nodo"]
        estado["historial"].append(nodo_actual)
        estado["respuestas"].append(f"P{nodo_actual + 1}: {respuesta}")
        
        datos = arbol[nodo_actual]
        respuesta_texto.value = f"Respuesta: {datos['respuesta']}"

        siguiente = datos["si"] if respuesta == "Sí" else datos["no"]
        if siguiente is None:
            # Guardar respuestas en el paciente
            estado["paciente_actual"]["respuestas"] = estado["respuestas"].copy()
            estado["paciente_actual"]["diagnostico"] = "Completado"
            
            diagnostico_text.value = "Evaluación finalizada. Consulte a un profesional para diagnóstico completo."
            botones.controls.clear()
            
            # Notificar en el chat sobre evaluación completada
            ia_response_text.controls.append(
                ft.Container(
                    content=ft.Text(f"✅ Evaluación de {estado['paciente_actual']['nombre']} completada. ¿Necesitas más información sobre el caso?", 
                                   selectable=True, color="green"),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=10,
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )
            )
            
            # Enviar por Telegram
            enviar_telegram(estado["paciente_actual"], diagnostico_text.value)
        else:
            estado["nodo"] = siguiente
            question.value = arbol[siguiente]["pregunta"]

        update_arbol()
        page.update()

    def reiniciar(_):
        estado["nodo"] = 0
        estado["historial"] = []
        estado["respuestas"] = []
        question.value = arbol[0]["pregunta"]
        diagnostico_text.value = ""
        respuesta_texto.value = ""
        botones.controls.clear()
        botones.controls.extend([
            ft.ElevatedButton("Sí", on_click=lambda _: siguiente_pregunta("Sí")),
            ft.ElevatedButton("No", on_click=lambda _: siguiente_pregunta("No")),
        ])
        update_arbol()
        page.update()

    def nodo_arbol(numero, texto):
        color = "grey"
        if numero == estado["nodo"]:
            color = "green"
        elif numero in estado["historial"]:
            color = "blue"
        return ft.Column([
            ft.CircleAvatar(content=ft.Text(str(numero + 1), color="white"), bgcolor=color, radius=25),
            ft.Text(texto, size=12, text_align="center")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def update_arbol():
        arbol_vista.controls.clear()

        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(0, arbol[0]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 1 (nodos 1 y 2)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(1, arbol[1]["pregunta"]), padding=10),
                ft.Container(width=200),  # espacio entre los nodos
                ft.Container(nodo_arbol(2, arbol[2]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 2 (nodos 3,4,5,6,7)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(3, arbol[3]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(4, arbol[4]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(5, arbol[5]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(6, arbol[6]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(7, arbol[7]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 3 (nodos 8 a 14)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(8, arbol[8]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(9, arbol[9]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(10, arbol[10]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(11, arbol[11]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(12, arbol[12]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(13, arbol[13]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(14, arbol[14]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 4 (nodos 15 a 30) — hojas (finales)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(15, arbol[15]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(16, arbol[16]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(17, arbol[17]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(18, arbol[18]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(19, arbol[19]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(20, arbol[20]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(21, arbol[21]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(22, arbol[22]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(23, arbol[23]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(24, arbol[24]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(25, arbol[25]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(26, arbol[26]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(27, arbol[27]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(28, arbol[28]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(29, arbol[29]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(30, arbol[30]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER, scroll="auto")
        )   
        page.update()

    question = ft.Text(arbol[estado["nodo"]]["pregunta"], size=20, weight="bold", text_align=ft.TextAlign.CENTER)

    botones = ft.Row([
        ft.ElevatedButton("Sí", on_click=lambda _: siguiente_pregunta("Sí")),
        ft.ElevatedButton("No", on_click=lambda _: siguiente_pregunta("No")),
    ], alignment=ft.MainAxisAlignment.CENTER)

    arbol_vista = ft.Column()
    update_arbol()

    # --- FORMULARIO DE PACIENTE AGREGADO ---


    # --- SECCIÓN DEL CHATBOT IA ---
    chatbot_container = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ia_response_text,
                bgcolor=ft.Colors.GREY_100,
                border_radius=10,
                padding=10,
            ),
            ft.Row([
                prompt_input,
                ft.ElevatedButton("Enviar", on_click=lambda _: send_prompt_to_ai()),
                ft.ElevatedButton("Limpiar", on_click=limpiar_chat, color=ft.Colors.RED_400)
            ], spacing=10),
            ft.Text("💡 Pregunta sobre síntomas, tratamientos, dieta, ejercicios, etc.", 
                   size=12, italic=True, color=ft.Colors.GREY_600),
            ft.Divider(),
        ], spacing=10),
        padding=10,
        bgcolor=ft.Colors.LIGHT_GREEN_50,
        border_radius=10,
    )

    # --- INFORMACIÓN DEL PACIENTE ACTUAL ---


    

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Sistema Experto: Hipertensión con IA", size=24, weight="bold"),       # Info del paciente actual
                    chatbot_container,    # NUEVO: Sección del chatbot IA
                    arbol_vista,          # Árbol de decisión
                    ft.Divider(),
                    question,             # Pregunta actual
                    botones,              # Botones Sí/No
                    respuesta_texto,      # Respuesta del sistema experto
                    diagnostico_text,     # Diagnóstico final
                    ft.ElevatedButton("Reiniciar", on_click=reiniciar)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            expand=True,
            padding=20,
            bgcolor=ft.Colors.WHITE,
        )
    )

    # Actualizar info del paciente periódicamente
    #def actualizar_info(_):
        #info_paciente.content = get_info_paciente()
        #page.update()
    
    # Timer para actualizar la info del paciente
    import threading
    def timer_update():
        while True:
            try:
                #actualizar_info(None)
                threading.Event().wait(2)  # Actualizar cada 2 segundos
            except:
                break
    
    threading.Thread(target=timer_update, daemon=True).start()

    page.update()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8080)