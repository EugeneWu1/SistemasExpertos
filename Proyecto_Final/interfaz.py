import flet as ft
import json
import requests
import uuid
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import re

load_dotenv()

def main(page: ft.Page):
    page.title = "Sistema Experto: Hipertensión Arterial"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ALWAYS
    page.window_width = 1200
    page.window_height = 800
    page.bgcolor = "#F8F9FA"

    # Configuración de la base de datos
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_DATABASE'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'charset': 'utf8mb4',
        'autocommit': True,
        'time_zone': '+00:00'
    }

    # Base de datos simulada de pacientes
    pacientes_db = []
    diagnosticos_archivo = "diagnosticos.json"
    
    # Configuración del bot de Telegram
    TELEGRAM_BOT_URL = "http://localhost:1880/telegram-message"
    API_KEY = os.getenv('GEMINI_API_KEY')

    # Árbol de decisión mejorado
    arbol = {
        0: {"pregunta": "¿El paciente tiene presión arterial elevada (≥140/90 mmHg)?",
            "respuesta": "La hipertensión arterial es una enfermedad cardiovascular crónica que afecta a millones de personas.",
            "si": 1, "no": 2},
        1: {"pregunta": "¿Presenta factores de riesgo como obesidad, sedentarismo o consumo excesivo de sal?",
            "respuesta": "Los factores de riesgo modificables son clave en el desarrollo de hipertensión.",
            "si": 3, "no": 4},
        2: {"pregunta": "¿Tiene síntomas como dolor de cabeza frecuente o visión borrosa?",
            "respuesta": "Estos síntomas pueden indicar hipertensión en desarrollo o complicaciones.",
            "si": 5, "no": 6},
        3: {"pregunta": "¿El IMC del paciente indica obesidad (>30)?",
            "respuesta": "La obesidad aumenta significativamente el riesgo cardiovascular.",
            "si": 9, "no": 10},
        4: {"pregunta": "¿Tiene antecedentes familiares de hipertensión?",
            "respuesta": "La predisposición genética es un factor importante a considerar.",
            "si": 11, "no": 12},
        5: {"pregunta": "¿Los síntomas son frecuentes (más de 3 veces por semana)?",
            "respuesta": "La frecuencia de síntomas ayuda a determinar la severidad.",
            "si": 13, "no": 14},
        6: {"pregunta": "¿Realiza chequeos médicos regulares?",
            "respuesta": "El control preventivo es fundamental para detectar hipertensión temprana.",
            "si": 15, "no": 16},
        7: {"pregunta": "¿Consume alcohol regularmente?",
            "respuesta": "El alcohol en exceso eleva la presión arterial.",
            "si": 17, "no": 18},
        8: {"pregunta": "¿Fuma o ha fumado en los últimos 5 años?",
            "respuesta": "El tabaquismo daña los vasos sanguíneos y eleva la presión.",
            "si": 19, "no": 20},
        9: {"pregunta": "¿Está siguiendo algún tratamiento para bajar de peso?",
            "respuesta": "La pérdida de peso es crucial para controlar la hipertensión.",
            "si": 21, "no": 22},
        10: {"pregunta": "¿Realiza ejercicio cardiovascular regularmente?",
             "respuesta": "El ejercicio aeróbico ayuda a reducir la presión arterial.",
             "si": 23, "no": 24},
        11: {"pregunta": "¿Múltiples familiares directos tienen hipertensión?",
             "respuesta": "Múltiples antecedentes familiares aumentan significativamente el riesgo.",
             "si": 25, "no": 26},
        12: {"pregunta": "¿Mantiene una dieta baja en sodio?",
             "respuesta": "La restricción de sodio es fundamental en la prevención.",
             "si": 27, "no": 28},
        13: {"pregunta": "¿Ha consultado con un médico sobre estos síntomas?",
             "respuesta": "La evaluación médica es esencial ante síntomas frecuentes.",
             "si": 29, "no": 30},
        14: {"pregunta": "¿Los síntomas aparecen en situaciones de estrés?",
             "respuesta": "El estrés puede desencadenar episodios hipertensivos.",
             "si": 31, "no": 32},

        # Nodos finales (15-32)
        15: {"pregunta": "Diagnóstico: Control preventivo adecuado",
             "respuesta": "Mantener chequeos regulares y hábitos saludables.",
             "si": None, "no": None},
        16: {"pregunta": "Diagnóstico: Necesita evaluación médica",
             "respuesta": "Programar chequeo médico lo antes posible.",
             "si": None, "no": None},
        17: {"pregunta": "Diagnóstico: Reducir consumo de alcohol",
             "respuesta": "El alcohol puede estar contribuyendo a la hipertensión.",
             "si": None, "no": None},
        18: {"pregunta": "Diagnóstico: Mantener hábitos actuales",
             "respuesta": "Continuar con estilo de vida saludable.",
             "si": None, "no": None},
        19: {"pregunta": "Diagnóstico: Cesación de tabaquismo urgente",
             "respuesta": "Dejar de fumar es prioritario para la salud cardiovascular.",
             "si": None, "no": None},
        20: {"pregunta": "Diagnóstico: Excelente factor protector",
             "respuesta": "No fumar es un factor protector importante.",
             "si": None, "no": None},
        21: {"pregunta": "Diagnóstico: Continuar pérdida de peso",
             "respuesta": "Mantener el programa de pérdida de peso con supervisión médica.",
             "si": None, "no": None},
        22: {"pregunta": "Diagnóstico: Iniciar programa de pérdida de peso",
             "respuesta": "Consultar nutricionista y iniciar plan de pérdida de peso.",
             "si": None, "no": None},
        23: {"pregunta": "Diagnóstico: Excelente control con ejercicio",
             "respuesta": "Mantener rutina de ejercicio cardiovascular.",
             "si": None, "no": None},
        24: {"pregunta": "Diagnóstico: Iniciar programa de ejercicio",
             "respuesta": "Comenzar actividad física gradual con supervisión.",
             "si": None, "no": None},
        25: {"pregunta": "Diagnóstico: Alto riesgo genético",
             "respuesta": "Monitoreo frecuente y medidas preventivas intensivas.",
             "si": None, "no": None},
        26: {"pregunta": "Diagnóstico: Riesgo genético moderado",
             "respuesta": "Control regular y hábitos preventivos.",
             "si": None, "no": None},
        27: {"pregunta": "Diagnóstico: Dieta adecuada",
             "respuesta": "Mantener dieta baja en sodio y balanceada.",
             "si": None, "no": None},
        28: {"pregunta": "Diagnóstico: Mejorar dieta",
             "respuesta": "Reducir sodio y consultar nutricionista.",
             "si": None, "no": None},
        29: {"pregunta": "Diagnóstico: Seguimiento médico",
             "respuesta": "Continuar tratamiento y controles médicos.",
             "si": None, "no": None},
        30: {"pregunta": "Diagnóstico: Consulta médica urgente",
             "respuesta": "Buscar atención médica inmediata por síntomas frecuentes.",
             "si": None, "no": None},
        31: {"pregunta": "Diagnóstico: Manejo del estrés",
             "respuesta": "Implementar técnicas de relajación y manejo del estrés.",
             "si": None, "no": None},
        32: {"pregunta": "Diagnóstico: Síntomas ocasionales",
             "respuesta": "Monitorear síntomas y consultar si empeoran.",
             "si": None, "no": None},
    }

    estado = {"nodo": 0, "historial": [], "paciente_actual": None, "respuestas": []}

    def cargar_diagnosticos():
        """Carga los diagnósticos desde el archivo JSON"""
        try:
            with open(diagnosticos_archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def guardar_diagnosticos(diagnosticos):
        """Guarda los diagnósticos en el archivo JSON"""
        try:
            with open(diagnosticos_archivo, 'w', encoding='utf-8') as f:
                json.dump(diagnosticos, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando diagnósticos: {e}")
            return False

    def conectar_bd():
        """Establece conexión con la base de datos"""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                return connection
        except mysql.connector.Error as err:
            print(f"Error MySQL: {err}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        return None

    def mostrar_notificacion(mensaje, color="green"):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=color,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()

    # ================ TAB 1: REGISTRO DE PACIENTES ================
    def crear_tab_registro():
        # Campos del formulario mejorados
        nombre_field = ft.TextField(
            label="Nombre Completo *", 
            width=300, 
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        
        edad_field = ft.TextField(
            label="Edad *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.CAKE,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        
        sexo_dropdown = ft.Dropdown(
            label="Sexo *",
            width=150,
            options=[
                ft.dropdown.Option("M", "Masculino"),
                ft.dropdown.Option("F", "Femenino"),
            ],
            prefix_icon=ft.Icons.WC,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        
        telefono_field = ft.TextField(
            label="Teléfono *", 
            width=200, 
            prefix_icon=ft.Icons.PHONE,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        
        email_field = ft.TextField(
            label="Email", 
            width=300, 
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
            keyboard_type=ft.KeyboardType.EMAIL,
            bgcolor="#FFFFFF",
            border_color="#4CAF50",
            hint_text="Opcional para envío de reportes"
        )
        
        telegram_field = ft.TextField(
            label="Usuario Telegram", 
            width=250, 
            prefix_icon=ft.Icons.TELEGRAM,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#4CAF50",
            hint_text="@usuario o chat_id (opcional)"
        )
        
        peso_field = ft.TextField(
            label="Peso (kg) *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.MONITOR_WEIGHT,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        
        altura_field = ft.TextField(
            label="Altura (cm) *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.STRAIGHTEN,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )

        def crear_paciente(_):
            # Validar campos requeridos
            if not all([nombre_field.value, edad_field.value, sexo_dropdown.value, 
                       telefono_field.value, peso_field.value, altura_field.value]):
                mostrar_notificacion("Complete todos los campos obligatorios (*)", "#F44336")
                return
            
            try:
                paciente_id = str(uuid.uuid4())[:8]
                peso = float(peso_field.value)
                altura = float(altura_field.value) / 100  # Convertir cm a metros
                imc = round(peso / (altura ** 2), 2)
                
                paciente = {
                    "id": paciente_id,
                    "nombre": nombre_field.value.strip(),
                    "edad": int(edad_field.value),
                    "sexo": sexo_dropdown.value,
                    "telefono": telefono_field.value.strip(),
                    "email": email_field.value.strip() if email_field.value else "",
                    "telegram": telegram_field.value.strip() if telegram_field.value else "",
                    "peso": peso,
                    "altura": altura,
                    "imc": imc,
                    "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "respuestas": [],
                    "diagnostico": "",
                    "estado_evaluacion": "Pendiente"
                }
                
                pacientes_db.append(paciente)
                estado["paciente_actual"] = paciente
                
                # Limpiar formulario
                for field in [nombre_field, edad_field, telefono_field, email_field, 
                             telegram_field, peso_field, altura_field]:
                    field.value = ""
                sexo_dropdown.value = None
                
                mostrar_notificacion(f"Paciente registrado: {paciente['nombre']} (ID: {paciente_id})", "#4CAF50")
                actualizar_tabla_pacientes()
                page.update()
                
            except ValueError:
                mostrar_notificacion("Verifique que edad, peso y altura sean números válidos", "#F44336")
            except Exception as e:
                mostrar_notificacion(f"Error al registrar paciente: {str(e)}", "#F44336")

        def limpiar_formulario(_):
            for field in [nombre_field, edad_field, telefono_field, email_field, 
                         telegram_field, peso_field, altura_field]:
                field.value = ""
            sexo_dropdown.value = None
            page.update()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ADD, size=30, color="#2196F3"),
                        ft.Text("Registro de Pacientes", size=24, weight=ft.FontWeight.BOLD, color="#2196F3")
                    ]),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Información Personal", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                            ft.Row([nombre_field], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([edad_field, sexo_dropdown], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                            
                            ft.Divider(color="#E0E0E0"),
                            
                            ft.Text("Información de Contacto", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                            ft.Row([telefono_field], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([email_field], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([telegram_field], alignment=ft.MainAxisAlignment.CENTER),
                            
                            ft.Divider(color="#E0E0E0"),
                            
                            ft.Text("Información Física", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                            ft.Row([peso_field, altura_field], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                            
                            ft.Divider(color="#E0E0E0"),
                            
                            ft.Row([
                                ft.ElevatedButton(
                                    "Registrar Paciente",
                                    on_click=crear_paciente,
                                    bgcolor="#4CAF50",
                                    color="white",
                                    width=200,
                                    height=45,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10)
                                    )
                                ),
                                ft.OutlinedButton(
                                    "Limpiar Formulario",
                                    on_click=limpiar_formulario,
                                    width=150,
                                    height=45
                                )
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                        ], spacing=15),
                        padding=30
                    ),
                    elevation=5
                )
            ]),
            padding=20
        )

    # ================ TAB 2: EVALUACIÓN ================
    def crear_tab_evaluacion():
        question_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        respuesta_text = ft.Text("", size=14, color="#666")
        diagnostico_text = ft.Text("", size=16, color="#D32F2F", weight=ft.FontWeight.BOLD)
        
        progreso = ft.ProgressBar(width=400, value=0, bgcolor="#E0E0E0", color="#4CAF50")
        
        def actualizar_pregunta():
            if estado["paciente_actual"]:
                nodo_actual = estado["nodo"]
                question_text.value = f"Pregunta {nodo_actual + 1}: {arbol[nodo_actual]['pregunta']}"
                progreso.value = len(estado["historial"]) / 15  # Aproximadamente 15 preguntas
            else:
                question_text.value = "Por favor, registre un paciente primero"
            page.update()

        def siguiente_pregunta(respuesta):
            if not estado["paciente_actual"]:
                mostrar_notificacion("Debe registrar un paciente primero", "#F44336")
                return
                
            nodo_actual = estado["nodo"]
            estado["historial"].append(nodo_actual)
            estado["respuestas"].append(f"P{nodo_actual + 1}: {respuesta}")
            
            datos = arbol[nodo_actual]
            respuesta_text.value = f"📝 {datos['respuesta']}"

            siguiente = datos["si"] if respuesta == "Sí" else datos["no"]
            if siguiente is None:
                # Evaluación finalizada
                diagnostico_final = datos["respuesta"]
                diagnostico_text.value = f"🎯 Diagnóstico: {diagnostico_final}"
                
                # Actualizar paciente
                estado["paciente_actual"]["respuestas"] = estado["respuestas"].copy()
                estado["paciente_actual"]["diagnostico"] = diagnostico_final
                estado["paciente_actual"]["estado_evaluacion"] = "Completada"
                estado["paciente_actual"]["fecha_evaluacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardar en JSON
                diagnosticos = cargar_diagnosticos()
                diagnosticos.append(estado["paciente_actual"].copy())
                if guardar_diagnosticos(diagnosticos):
                    mostrar_notificacion("Diagnóstico guardado exitosamente", "#4CAF50")
                
                # Enviar reporte si tiene contacto
                enviar_reporte_completo(estado["paciente_actual"])
                
                actualizar_tabla_pacientes()
                botones_container.visible = False
                reiniciar_btn.visible = True
            else:
                estado["nodo"] = siguiente
                actualizar_pregunta()

            actualizar_arbol_visual()
            page.update()

        def reiniciar_evaluacion(_):
            estado["nodo"] = 0
            estado["historial"] = []
            estado["respuestas"] = []
            diagnostico_text.value = ""
            respuesta_text.value = ""
            progreso.value = 0
            botones_container.visible = True
            reiniciar_btn.visible = False
            actualizar_pregunta()
            actualizar_arbol_visual()

        botones_container = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "✅ Sí",
                    on_click=lambda _: siguiente_pregunta("Sí"),
                    bgcolor="#4CAF50",
                    color="white",
                    width=120,
                    height=50
                ),
                ft.ElevatedButton(
                    "❌ No",
                    on_click=lambda _: siguiente_pregunta("No"),
                    bgcolor="#F44336",
                    color="white",
                    width=120,
                    height=50
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=30)
        )
        
        reiniciar_btn = ft.ElevatedButton(
            "🔄 Nueva Evaluación",
            on_click=reiniciar_evaluacion,
            bgcolor="#FF9800",
            color="white",
            width=200,
            height=50,
            visible=False
        )

        # Árbol visual simplificado
        arbol_visual = ft.Container(
            height=200,
            bgcolor="#F5F5F5",
            border_radius=10,
            padding=10
        )

        def actualizar_arbol_visual():
            # Implementación simplificada del árbol visual
            nodos_visitados = len(estado["historial"])
            arbol_visual.content = ft.Column([
                ft.Text(f"Progreso de la Evaluación: {nodos_visitados} preguntas respondidas", 
                       size=14, weight=ft.FontWeight.BOLD),
                progreso,
                ft.Text("🟢 Pregunta actual | 🔵 Preguntas respondidas", size=12, color="#666")
            ])

        actualizar_pregunta()
        actualizar_arbol_visual()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.QUIZ, size=30, color="#FF9800"),
                        ft.Text("Evaluación de Hipertensión", size=24, weight=ft.FontWeight.BOLD, color="#FF9800")
                    ]),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            question_text,
                            ft.Divider(),
                            botones_container,
                            reiniciar_btn,
                            ft.Divider(),
                            respuesta_text,
                            diagnostico_text,
                        ], spacing=20),
                        padding=30
                    ),
                    elevation=5
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=arbol_visual,
                        padding=20
                    ),
                    elevation=3
                )
            ]),
            padding=20
        )

    # ================ TAB 3: CHATBOT IA ================
    def crear_tab_chatbot():
        chat_container = ft.Column(
            height=400,
            scroll=ft.ScrollMode.AUTO,
            spacing=10
        )
        
        prompt_input = ft.TextField(
            label="Pregunta sobre hipertensión...",
            multiline=True,
            max_lines=3,
            width=600,
            border_radius=10
        )

        def agregar_mensaje(contenido, es_usuario=True):
            color = "#E3F2FD" if es_usuario else "#E8F5E8"
            icono = "🤔" if es_usuario else "🤖"
            
            chat_container.controls.append(
                ft.Container(
                    content=ft.Text(f"{icono} {contenido}", selectable=True),
                    bgcolor=color,
                    padding=15,
                    border_radius=10,
                    margin=ft.margin.only(bottom=5)
                )
            )
            page.update()

        def enviar_pregunta(_):
            pregunta = prompt_input.value.strip()
            if not pregunta:
                return
            
            agregar_mensaje(pregunta, True)
            prompt_input.value = ""
            page.update()
            
            try:
                if not API_KEY:
                    agregar_mensaje("❌ Error: API Key de Gemini no configurada", False)
                    return
                
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                
                context = """Eres un asistente médico especializado en hipertensión arterial. 
                Proporciona información médica precisa pero recuerda siempre que no sustituyes 
                la consulta médica profesional."""
                
                full_prompt = f"{context}\n\nPregunta: {pregunta}"
                
                if estado["paciente_actual"]:
                    p = estado["paciente_actual"]
                    patient_context = f"\nPaciente actual: {p['nombre']}, {p['edad']} años, IMC: {p['imc']}"
                    full_prompt += patient_context
                
                response = model.generate_content(full_prompt)
                respuesta = response.text + "\n\n⚠️ Consulte siempre con un médico profesional."
                
                agregar_mensaje(respuesta, False)
                
            except Exception as e:
                agregar_mensaje(f"❌ Error: {str(e)}", False)

        def limpiar_chat(_):
            chat_container.controls.clear()
            agregar_mensaje("¡Hola! Soy tu asistente de hipertensión. ¿En qué puedo ayudarte?", False)

        # Inicializar chat
        limpiar_chat(None)

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, size=30, color="#4CAF50"),
                        ft.Text("Asistente IA - Hipertensión", size=24, weight=ft.FontWeight.BOLD, color="#4CAF50")
                    ]),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=chat_container,
                        padding=20
                    ),
                    elevation=5
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            prompt_input,
                            ft.ElevatedButton(
                                "Enviar",
                                on_click=enviar_pregunta,
                                bgcolor="#4CAF50",
                                color="white"
                            ),
                            ft.OutlinedButton(
                                "Limpiar",
                                on_click=limpiar_chat
                            )
                        ], spacing=10),
                        padding=20
                    ),
                    elevation=3
                )
            ]),
            padding=20
        )

    # ================ TAB 4: PACIENTES REGISTRADOS ================
    def crear_tab_pacientes():
        tabla_pacientes = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Nombre", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Edad", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("IMC", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha Registro", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )

        def actualizar_tabla_pacientes():
            tabla_pacientes.rows.clear()
            
            for paciente in pacientes_db:
                color_estado = "#4CAF50" if paciente["estado_evaluacion"] == "Completada" else "#FF9800"
                
                tabla_pacientes.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(paciente["id"])),
                            ft.DataCell(ft.Text(paciente["nombre"])),
                            ft.DataCell(ft.Text(str(paciente["edad"]))),
                            ft.DataCell(ft.Text(str(paciente["imc"]))),
                            ft.DataCell(ft.Text(paciente["estado_evaluacion"], color=color_estado)),
                            ft.DataCell(ft.Text(paciente["fecha_registro"][:10])),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        ft.Icons.VISIBILITY,
                                        tooltip="Ver detalles",
                                        on_click=lambda e, p=paciente: ver_detalle_paciente(p)
                                    ),
                                    ft.IconButton(
                                        ft.Icons.SEND,
                                        tooltip="Enviar reporte",
                                        on_click=lambda e, p=paciente: enviar_reporte_manual(p)
                                    )
                                ])
                            ),
                        ]
                    )
                )
            page.update()

        def ver_detalle_paciente(paciente):
            def cerrar_dialog(_):
                dialog.open = False
                page.update()

            detalle_content = ft.Column([
                ft.Text(f"Detalles del Paciente: {paciente['nombre']}", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"ID: {paciente['id']}"),
                ft.Text(f"Edad: {paciente['edad']} años"),
                ft.Text(f"Sexo: {'Masculino' if paciente['sexo'] == 'M' else 'Femenino'}"),
                ft.Text(f"Teléfono: {paciente['telefono']}"),
                ft.Text(f"Email: {paciente['email'] if paciente['email'] else 'No proporcionado'}"),
                ft.Text(f"Telegram: {paciente['telegram'] if paciente['telegram'] else 'No proporcionado'}"),
                ft.Text(f"Peso: {paciente['peso']} kg"),
                ft.Text(f"Altura: {paciente['altura']:.2f} m"),
                ft.Text(f"IMC: {paciente['imc']}"),
                ft.Text(f"Estado: {paciente['estado_evaluacion']}"),
                ft.Divider(),
                ft.Text("Respuestas de la Evaluación:", weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text(f"• {respuesta}", size=12) for respuesta in paciente.get('respuestas', [])
                ], scroll=ft.ScrollMode.AUTO, height=150),
                ft.Text(f"Diagnóstico: {paciente.get('diagnostico', 'No completado')}", 
                       weight=ft.FontWeight.BOLD, color="#D32F2F"),
            ], scroll=ft.ScrollMode.AUTO, height=400)

            dialog = ft.AlertDialog(
                title=ft.Text("Información del Paciente"),
                content=detalle_content,
                actions=[
                    ft.TextButton("Cerrar", on_click=cerrar_dialog)
                ]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()

        def enviar_reporte_manual(paciente):
            if paciente["estado_evaluacion"] != "Completada":
                mostrar_notificacion("El paciente no ha completado la evaluación", "#FF9800")
                return
            
            enviar_reporte_completo(paciente)

        def exportar_diagnosticos(_):
            try:
                diagnosticos = cargar_diagnosticos()
                export_data = {
                    "fecha_exportacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_pacientes": len(diagnosticos),
                    "pacientes": diagnosticos
                }
                
                filename = f"diagnosticos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                mostrar_notificacion(f"Diagnósticos exportados a {filename}", "#4CAF50")
            except Exception as e:
                mostrar_notificacion(f"Error al exportar: {str(e)}", "#F44336")

        actualizar_tabla_pacientes()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PEOPLE, size=30, color="#9C27B0"),
                        ft.Text("Pacientes Registrados", size=24, weight=ft.FontWeight.BOLD, color="#9C27B0")
                    ]),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"Total de pacientes: {len(pacientes_db)}", size=16, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "📊 Exportar Diagnósticos",
                            on_click=exportar_diagnosticos,
                            bgcolor="#9C27B0",
                            color="white"
                        ),
                        ft.ElevatedButton(
                            "🔄 Actualizar",
                            on_click=lambda _: actualizar_tabla_pacientes(),
                            bgcolor="#2196F3",
                            color="white"
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            tabla_pacientes
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=20
                    ),
                    elevation=5
                )
            ]),
            padding=20
        )

    # ================ FUNCIONES DE COMUNICACIÓN ================
    def enviar_reporte_completo(paciente):
        """Envía reporte por email y/o telegram según disponibilidad"""
        mensaje_enviado = False
        
        reporte = generar_reporte_texto(paciente)
        
        # Intentar enviar por Telegram si tiene usuario
        if paciente.get("telegram"):
            if enviar_telegram(paciente, reporte):
                mensaje_enviado = True
        
        # Intentar enviar por email si tiene email
        if paciente.get("email"):
            if enviar_email(paciente, reporte):
                mensaje_enviado = True
        
        if mensaje_enviado:
            mostrar_notificacion(f"Reporte enviado a {paciente['nombre']}", "#4CAF50")
        else:
            mostrar_notificacion("No se pudo enviar el reporte - verifique los datos de contacto", "#FF9800")

    def generar_reporte_texto(paciente):
        """Genera el texto del reporte médico"""
        categoria_imc = obtener_categoria_imc(paciente["imc"])
        
        reporte = f"""🏥 REPORTE MÉDICO - SISTEMA EXPERTO HIPERTENSIÓN

👤 INFORMACIÓN DEL PACIENTE:
• Nombre: {paciente['nombre']}
• ID: {paciente['id']}
• Edad: {paciente['edad']} años
• Sexo: {'Masculino' if paciente['sexo'] == 'M' else 'Femenino'}
• IMC: {paciente['imc']} kg/m² ({categoria_imc})
• Fecha de evaluación: {paciente.get('fecha_evaluacion', 'N/A')}

📋 EVALUACIÓN REALIZADA:
{chr(10).join(f"• {respuesta}" for respuesta in paciente.get('respuestas', []))}

🎯 DIAGNÓSTICO:
{paciente.get('diagnostico', 'Evaluación no completada')}

⚠️ RECOMENDACIONES GENERALES:
• Consulte con un médico especialista
• Monitoree su presión arterial regularmente
• Mantenga una dieta baja en sodio
• Realice ejercicio cardiovascular regular
• Evite el tabaco y limite el alcohol
• Mantenga un peso saludable

📞 IMPORTANTE:
Este reporte es generado por un sistema experto de apoyo diagnóstico.
NO sustituye la consulta médica profesional.
Consulte con su médico para un diagnóstico definitivo y tratamiento.

Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return reporte

    def obtener_categoria_imc(imc):
        """Devuelve la categoría del IMC"""
        if imc < 18.5:
            return "Bajo peso"
        elif 18.5 <= imc < 25:
            return "Peso normal"
        elif 25 <= imc < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"

    def enviar_telegram(paciente, mensaje):
        """Envía mensaje por Telegram"""
        try:
            payload = {
                "chat_id": paciente["telegram"],
                "message": mensaje
            }
            response = requests.post(TELEGRAM_BOT_URL, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando Telegram: {e}")
            return False

    def enviar_email(paciente, mensaje):
        """Simulación de envío por email (implementar según necesidades)"""
        try:
            # Aquí implementarías el envío real por email
            # Por ahora solo simulamos el envío
            print(f"Enviando email a {paciente['email']}: {mensaje[:100]}...")
            return True
        except Exception as e:
            print(f"Error enviando email: {e}")
            return False

    # ================ CONFIGURACIÓN DE TABS ================
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="👤 Registro",
                icon=ft.Icons.PERSON_ADD,
                content=crear_tab_registro()
            ),
            ft.Tab(
                text="🩺 Evaluación",
                icon=ft.Icons.QUIZ,
                content=crear_tab_evaluacion()
            ),
            ft.Tab(
                text="🤖 Asistente IA",
                icon=ft.Icons.SMART_TOY,
                content=crear_tab_chatbot()
            ),
            ft.Tab(
                text="📊 Pacientes",
                icon=ft.Icons.PEOPLE,
                content=crear_tab_pacientes()
            )
        ],
        expand=1
    )

    # Función para actualizar la tabla de pacientes desde otros tabs
    def actualizar_tabla_pacientes():
        if len(tabs.tabs) > 3:  # Verificar que el tab de pacientes existe
            # Recrear el contenido del tab de pacientes
            tabs.tabs[3].content = crear_tab_pacientes()
            page.update()

    # ================ LAYOUT PRINCIPAL ================
    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=40, color="#FFFFFF"),
            ft.Text(
                "Sistema Experto - Diagnóstico de Hipertensión Arterial",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF"
            ),
            ft.Icon(ft.Icons.FAVORITE, size=40, color="#FFFFFF")
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#2196F3",
        padding=20,
        border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=15, bottom_right=15)
    )

    footer = ft.Container(
        content=ft.Text(
            "© 2024 Sistema Experto Hipertensión - Desarrollado con Flet + IA + Node-RED",
            size=12,
            color="#666",
            text_align=ft.TextAlign.CENTER
        ),
        padding=10,
        bgcolor="#F5F5F5"
    )

    # Cargar diagnósticos existentes al inicio
    diagnosticos_existentes = cargar_diagnosticos()
    pacientes_db.extend(diagnosticos_existentes)

    page.add(
        ft.Column([
            header,
            ft.Container(
                content=tabs,
                expand=True,
                padding=0
            ),
            footer
        ], spacing=0, expand=True)
    )

    page.update()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8080)