import flet as ft
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai
import time
try:
    # Intentar importar reportlab como alternativa más simple
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

# Cargar variables de entorno
load_dotenv()

class HypertensionApp:
    def __init__(self):
        self.node_red_url = os.getenv('NODE_RED_URL', 'http://localhost:1880')
        self.current_patient_id = None
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.current_decision_node = 0
        self.patient_responses = {}
        self.final_diagnosis = None  # Variable para almacenar el diagnóstico final
        
        # Configurar Gemini AI
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # Árbol de decisión para diagnóstico de hipertensión
        self.arbol_decision = {
            # Nodo inicial - Medición de presión arterial
            0: {"pregunta": "¿Ha medido su presión arterial recientemente y fue ≥140/90 mmHg?",
                "respuesta": "La hipertensión se define como presión arterial ≥140/90 mmHg en múltiples mediciones.",
                "si": 1, "no": 2},
            
            # Rama hipertensión confirmada
            1: {"pregunta": "¿Su presión arterial está por encima de 160/100 mmHg?",
                "respuesta": "Presiones >160/100 mmHg indican hipertensión moderada a severa.",
                "si": 3, "no": 4},
            
            # Rama sin hipertensión confirmada
            2: {"pregunta": "¿Tiene síntomas como dolor de cabeza matutino, mareos o palpitaciones?",
                "respuesta": "Estos síntomas pueden indicar hipertensión no diagnosticada.",
                "si": 5, "no": 6},
            
            # Hipertensión severa
            3: {"pregunta": "¿Presenta síntomas como dolor de pecho, dificultad para respirar o visión borrosa?",
                "respuesta": "Estos síntomas con PA alta pueden indicar crisis hipertensiva.",
                "si": 50, "no": 7},  # 50 = crisis hipertensiva
            
            # Hipertensión leve-moderada
            4: {"pregunta": "¿Está tomando medicamentos para la presión arterial?",
                "respuesta": "El tratamiento farmacológico es crucial en hipertensión establecida.",
                "si": 8, "no": 9},
            
            # Síntomas sin PA confirmada
            5: {"pregunta": "¿Los síntomas ocurren más de 3 veces por semana?",
                "respuesta": "La frecuencia de síntomas ayuda a evaluar la urgencia del diagnóstico.",
                "si": 51, "no": 10},  # 51 = evaluación urgente
            
            # Sin síntomas ni PA elevada
            6: {"pregunta": "¿Tiene factores de riesgo como obesidad, tabaquismo o diabetes?",
                "respuesta": "Los factores de riesgo aumentan la probabilidad de desarrollar hipertensión.",
                "si": 11, "no": 12},
            
            # Evaluación de tratamiento actual
            7: {"pregunta": "¿Está tomando al menos 2 medicamentos antihipertensivos?",
                "respuesta": "La mayoría de pacientes hipertensos requieren terapia combinada.",
                "si": 13, "no": 14},
            
            # Medicación actual
            8: {"pregunta": "¿Su presión está controlada (<140/90) con la medicación actual?",
                "respuesta": "El objetivo es mantener PA <140/90 (o <130/80 en alto riesgo).",
                "si": 15, "no": 16},
            
            # Sin medicación
            9: {"pregunta": "¿Ha intentado cambios de estilo de vida (dieta, ejercicio) durante al menos 3 meses?",
                "respuesta": "Los cambios de estilo de vida son la primera línea de tratamiento.",
                "si": 17, "no": 18},
            
            # Síntomas ocasionales
            10: {"pregunta": "¿Tiene antecedentes familiares de hipertensión o enfermedad cardiovascular?",
                 "respuesta": "Los antecedentes familiares aumentan el riesgo cardiovascular.",
                 "si": 19, "no": 20},
            
            # Factores de riesgo presentes
            11: {"pregunta": "¿Su IMC es mayor a 30 kg/m²?",
                 "respuesta": "La obesidad es un factor de riesgo modificable importante.",
                 "si": 21, "no": 22},
            
            # Sin factores de riesgo evidentes
            12: {"pregunta": "¿Realiza ejercicio cardiovascular al menos 150 minutos por semana?",
                 "respuesta": "El ejercicio regular es preventivo para hipertensión.",
                 "si": 23, "no": 24},
            
            # Politerapia antihipertensiva
            13: {"pregunta": "¿Incluye su tratamiento un diurético?",
                 "respuesta": "Los diuréticos son esenciales en muchos casos de hipertensión resistente.",
                 "si": 25, "no": 26},
            
            # Monoterapia
            14: {"pregunta": "¿Sigue una dieta baja en sodio (<2300mg/día)?",
                 "respuesta": "La restricción de sodio potencia el efecto antihipertensivo.",
                 "si": 27, "no": 28},
            
            # PA controlada con medicación
            15: {"pregunta": "¿Mantiene un peso saludable (IMC 18.5-24.9)?",
                 "respuesta": "El control de peso es fundamental para mantener la PA controlada.",
                 "si": 29, "no": 30},
            
            # PA no controlada
            16: {"pregunta": "¿Toma sus medicamentos correctamente todos los días?",
                 "respuesta": "La adherencia al tratamiento es crucial para el control.",
                 "si": 31, "no": 32},
            
            # Cambios de estilo intentados
            17: {"pregunta": "¿Ha logrado una reducción de peso de al menos 5% de su peso corporal?",
                 "respuesta": "Una pérdida del 5-10% del peso puede reducir significativamente la PA.",
                 "si": 33, "no": 34},
            
            # Sin cambios de estilo de vida
            18: {"pregunta": "¿Consume más de 2 bebidas alcohólicas al día?",
                 "respuesta": "El consumo excesivo de alcohol eleva la presión arterial.",
                 "si": 35, "no": 36},
            
            # Antecedentes familiares positivos
            19: {"pregunta": "¿Es mayor de 45 años (hombres) o 55 años (mujeres)?",
                 "respuesta": "La edad es un factor de riesgo no modificable importante.",
                 "si": 37, "no": 38},
            
            # Sin antecedentes familiares
            20: {"pregunta": "¿Se mide la presión arterial al menos una vez al año?",
                 "respuesta": "El tamizaje regular es importante para detección temprana.",
                 "si": 39, "no": 40},
            
            # Obesidad presente
            21: {"pregunta": "¿Tiene diagnóstico de diabetes o prediabetes?",
                 "respuesta": "La diabetes duplica el riesgo cardiovascular.",
                 "si": 41, "no": 42},
            
            # Sobrepeso sin obesidad
            22: {"pregunta": "¿Fuma o ha fumado en los últimos 10 años?",
                 "respuesta": "El tabaquismo acelera el daño vascular.",
                 "si": 43, "no": 44},
            
            # Ejercicio adecuado
            23: {"pregunta": "¿Sigue una dieta mediterránea o DASH?",
                 "respuesta": "Estos patrones dietéticos son cardioprotectores.",
                 "si": 45, "no": 46},
            
            # Sedentarismo
            24: {"pregunta": "¿Pasa más de 8 horas al día sentado?",
                 "respuesta": "El sedentarismo extremo aumenta el riesgo cardiovascular.",
                 "si": 47, "no": 48},
            
            # NODOS FINALES (25-60)
            
            # Control farmacológico óptimo
            25: {"pregunta": "Diagnóstico: Tratamiento farmacológico óptimo",
                 "respuesta": "✅ Continuar con el régimen actual. Monitoreo cada 3-6 meses.",
                 "si": None, "no": None},
            
            # Necesita optimización de tratamiento
            26: {"pregunta": "Diagnóstico: Optimizar tratamiento antihipertensivo",
                 "respuesta": "⚠️ Considerar agregar diurético tiazídico. Consulta cardiológica recomendada.",
                 "si": None, "no": None},
            
            # Dieta adecuada, monoterapia
            27: {"pregunta": "Diagnóstico: Intensificar tratamiento farmacológico",
                 "respuesta": "⚠️ Considerar terapia combinada. Mantener restricción de sodio.",
                 "si": None, "no": None},
            
            # Dieta inadecuada
            28: {"pregunta": "Diagnóstico: Mejorar adherencia dietética",
                 "respuesta": "🧂 Implementar dieta baja en sodio. Considerar consulta nutricional.",
                 "si": None, "no": None},
            
            # Peso saludable, PA controlada
            29: {"pregunta": "Diagnóstico: Control cardiovascular excelente",
                 "respuesta": "✅ Mantener estilo de vida y medicación actual. Control anual.",
                 "si": None, "no": None},
            
            # Sobrepeso con PA controlada
            30: {"pregunta": "Diagnóstico: Optimizar peso corporal",
                 "respuesta": "⚖️ Programa de pérdida de peso para mejorar control a largo plazo.",
                 "si": None, "no": None},
            
            # Buena adherencia, PA no controlada
            31: {"pregunta": "Diagnóstico: Hipertensión resistente",
                 "respuesta": "🚨 Referir a especialista. Evaluar hipertensión secundaria.",
                 "si": None, "no": None},
            
            # Mala adherencia
            32: {"pregunta": "Diagnóstico: Mejorar adherencia al tratamiento",
                 "respuesta": "💊 Educación sobre importancia del tratamiento. Simplificar régimen.",
                 "si": None, "no": None},
            
            # Pérdida de peso exitosa
            33: {"pregunta": "Diagnóstico: Continuar manejo no farmacológico",
                 "respuesta": "✅ Excelente progreso. Monitorear PA mensualmente. Considerar medicación si PA sigue elevada.",
                 "si": None, "no": None},
            
            # Pérdida de peso insuficiente
            34: {"pregunta": "Diagnóstico: Intensificar cambios de estilo de vida",
                 "respuesta": "⚡ Programa estructurado de pérdida de peso. Considerar inicio de medicación.",
                 "si": None, "no": None},
            
            # Consumo excesivo de alcohol
            35: {"pregunta": "Diagnóstico: Reducir consumo de alcohol",
                 "respuesta": "🍷 Limitar a 1-2 copas/día. Considerar programa de reducción de alcohol.",
                 "si": None, "no": None},
            
            # Sin exceso de alcohol
            36: {"pregunta": "Diagnóstico: Iniciar cambios de estilo de vida",
                 "respuesta": "🥗 Implementar dieta DASH, ejercicio regular y control de peso.",
                 "si": None, "no": None},
            
            # Edad avanzada + antecedentes
            37: {"pregunta": "Diagnóstico: Alto riesgo cardiovascular",
                 "respuesta": "🚨 Monitoreo intensivo. Medición domiciliaria de PA. Control cada 3 meses.",
                 "si": None, "no": None},
            
            # Joven con antecedentes
            38: {"pregunta": "Diagnóstico: Riesgo cardiovascular intermedio",
                 "respuesta": "⚠️ Prevención intensiva. Medición PA semestral. Cambios de estilo de vida.",
                 "si": None, "no": None},
            
            # Tamizaje regular
            39: {"pregunta": "Diagnóstico: Continuar tamizaje preventivo",
                 "respuesta": "✅ Mantener controles anuales. Estilo de vida cardiosaludable.",
                 "si": None, "no": None},
            
            # Sin tamizaje regular
            40: {"pregunta": "Diagnóstico: Mejorar tamizaje cardiovascular",
                 "respuesta": "📅 Establecer controles anuales de PA. Evaluación de riesgo cardiovascular.",
                 "si": None, "no": None},
            
            # Obesidad + diabetes
            41: {"pregunta": "Diagnóstico: Riesgo cardiovascular muy alto",
                 "respuesta": "🚨 Manejo multidisciplinario urgente. Control metabólico y cardiovascular intensivo.",
                 "si": None, "no": None},
            
            # Obesidad sin diabetes
            42: {"pregunta": "Diagnóstico: Programa intensivo de pérdida de peso",
                 "respuesta": "⚖️ Objetivo: reducir 10% peso corporal. Consulta endocrinología y nutrición.",
                 "si": None, "no": None},
            
            # Fumador
            43: {"pregunta": "Diagnóstico: Cesación tabáquica prioritaria",
                 "respuesta": "🚭 Programa de cesación de tabaco. Riesgo cardiovascular elevado.",
                 "si": None, "no": None},
            
            # No fumador, sobrepeso
            44: {"pregunta": "Diagnóstico: Control de peso preventivo",
                 "respuesta": "⚖️ Mantener peso estable. Prevenir progresión a obesidad.",
                 "si": None, "no": None},
            
            # Dieta + ejercicio óptimo
            45: {"pregunta": "Diagnóstico: Estilo de vida cardiovascular óptimo",
                 "respuesta": "✅ Excelente patrón de vida. Mantener hábitos actuales. Riesgo muy bajo.",
                 "si": None, "no": None},
            
            # Ejercicio sin dieta óptima
            46: {"pregunta": "Diagnóstico: Optimizar patrón dietético",
                 "respuesta": "🥗 Implementar dieta mediterránea o DASH para complementar ejercicio.",
                 "si": None, "no": None},
            
            # Sedentarismo extremo
            47: {"pregunta": "Diagnóstico: Combatir sedentarismo urgente",
                 "respuesta": "🏃‍♀️ Iniciar actividad física gradual. Objetivo: 30 min/día de actividad.",
                 "si": None, "no": None},
            
            # Sedentarismo moderado
            48: {"pregunta": "Diagnóstico: Incrementar actividad física",
                 "respuesta": "🚶‍♀️ Aumentar actividad a 150 min/semana. Incluir ejercicio de resistencia.",
                 "si": None, "no": None},
            
            # NODOS DE EMERGENCIA
            50: {"pregunta": "Diagnóstico: CRISIS HIPERTENSIVA - EMERGENCIA",
                 "respuesta": "🚨 BUSCAR ATENCIÓN MÉDICA INMEDIATA. Posible daño de órganos diana.",
                 "si": None, "no": None},
            
            51: {"pregunta": "Diagnóstico: Evaluación médica urgente",
                 "respuesta": "⚠️ Medir PA inmediatamente. Consulta médica dentro de 48 horas.",
                 "si": None, "no": None}
        }
        
    def main(self, page: ft.Page):
        page.title = "Sistema Experto: Hipertensión Arterial"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.scroll = ft.ScrollMode.AUTO
        page.window.width = 1200
        page.window.height = 800
        page.bgcolor = "#F8F9FA"
        page.padding = 20
        
        # Variables para el formulario
        self.nombre_field = ft.TextField(label="Nombre Completo *", 
            width=300, 
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3")
        self.edad_field = ft.TextField(label="Edad *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.CAKE,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3")
        self.peso_field = ft.TextField(label="Peso (kg) *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.MONITOR_WEIGHT,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3")
        self.altura_field = ft.TextField(label="Altura (cm) *", 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.STRAIGHTEN,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3")
        self.genero_dropdown = ft.Dropdown(
            label="Género",
            width=200,
            options=[
                ft.dropdown.Option("M", "Masculino"),
                ft.dropdown.Option("F", "Femenino"),
                ft.dropdown.Option("Otro", "Otro")
            ],
                        prefix_icon=ft.Icons.WC,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3"
        )
        self.telefono_field = ft.TextField(label="Teléfono *", 
            width=200, 
            prefix_icon=ft.Icons.PHONE,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#2196F3")
        self.email_field = ft.TextField(label="Email", 
            width=300, 
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
            keyboard_type=ft.KeyboardType.EMAIL,
            bgcolor="#FFFFFF",
            border_color="#4CAF50",
            hint_text="Opcional para envío de reportes")
        self.telegram_field = ft.TextField(label="Usuario Telegram", 
            width=250, 
            prefix_icon=ft.Icons.TELEGRAM,
            border_radius=10,
            bgcolor="#FFFFFF",
            border_color="#4CAF50",
            hint_text="@usuario o chat_id (opcional)")
        
        # Mensaje de confirmación
        self.success_message = ft.Text(
            "¡Paciente guardado exitosamente en la base de datos!",
            color=ft.Colors.GREEN,
            visible=False,
            size=16,
            weight=ft.FontWeight.BOLD
        )
        
        # Botón para ir al diagnóstico
        self.diagnostico_btn = ft.ElevatedButton(
            "Realizar Diagnóstico",
            on_click=lambda _: self.switch_to_tab(1),
            visible=False,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE
        )
        
        # Variables para el diagnóstico
        self.chat_messages = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            height=400,
            spacing=10
        )
        self.chat_input = ft.TextField(
            label="Describe tus síntomas...",
            multiline=True,
            max_lines=3,
            width=500
        )
        
        # Botón para guardar diagnóstico
        self.save_diagnosis_btn = ft.ElevatedButton(
            "Guardar Diagnóstico",
            on_click=self.save_diagnosis,
            bgcolor=ft.Colors.ORANGE,
            color=ft.Colors.WHITE,
            visible=False
        )
        
        # Botones para el árbol de decisión
        self.decision_buttons = ft.Row([
            ft.ElevatedButton(
                "Sí",
                on_click=lambda _: self.handle_decision("si"),
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                visible=False
            ),
            ft.ElevatedButton(
                "No",
                on_click=lambda _: self.handle_decision("no"),
                bgcolor=ft.Colors.RED,
                color=ft.Colors.WHITE,
                visible=False
            ),
            ft.ElevatedButton(
                "Reiniciar Diagnóstico",
                on_click=self.restart_diagnosis,
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                visible=False
            )
        ], spacing=10)
        
        # Toggle para modo de diagnóstico
        self.diagnosis_mode = ft.Dropdown(
            label="Modo de Diagnóstico",
            width=200,
            value="tree",
            options=[
                ft.dropdown.Option("tree", "Árbol de Decisión"),
                ft.dropdown.Option("chat", "Chat IA Libre")
            ],
            on_change=self.change_diagnosis_mode
        )
        
        # Variables para gestión de usuarios
        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Edad")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Acciones"))
            ],
            rows=[]
        )
        
        # Card para mostrar detalles del paciente (inicialmente oculto)
        self.patient_details_card = ft.Container(
            visible=False,
            content=ft.Column(),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            margin=ft.margin.only(top=20)
        )
        
        # Mensaje de estado general
        self.status_message = ft.Text("", size=14)
        
        # Guardar referencia a la página
        self.page = page
        
        # Crear tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="👤 Registro",
                    icon=ft.Icons.PERSON_ADD,
                    content=self.create_registro_tab()
                ),
                ft.Tab(
                    text="🩺 Evaluación",
                    icon=ft.Icons.QUIZ,
                    content=self.create_diagnostico_tab()
                ),
                ft.Tab(
                    text="📊 Pacientes",
                    icon=ft.Icons.PEOPLE,
                    content=self.create_usuarios_tab()
                )
            ],
            on_change=self.tab_changed
        )

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
            border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=0, bottom_right=0)
        )
        
        page.add(
            ft.Column([
                header,
                self.tabs
            ])
        )
        page.update()
    
    def create_registro_tab(self):
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
                ft.Divider(),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                self.nombre_field,
                                self.edad_field,
                                self.genero_dropdown
                            ]),
                            ft.Row([
                                self.peso_field,
                                self.altura_field,
                                self.telefono_field
                            ]),
                            ft.Row([
                                self.email_field,
                                self.telegram_field
                            ]),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Guardar Paciente",
                                on_click=self.save_patient,
                                bgcolor=ft.Colors.GREEN,
                                color=ft.Colors.WHITE,
                                width=200,
                                height=40
                            ),
                            ft.Container(height=10),
                            self.success_message,
                            self.diagnostico_btn
                        ], spacing=15),
                        padding=30
                    ),
                    elevation=5
                )
            ]),
            padding=20
        )
    
    def create_diagnostico_tab(self):
        # Crear row del chat libre (inicialmente oculto)
        self.chat_row = ft.Row([
            self.chat_input,
            ft.ElevatedButton(
                "Enviar",
                on_click=self.send_message,
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE
            )
        ], visible=False)
        
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
                ft.Divider(),
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, size=30, color=ft.Colors.GREEN),
                    self.diagnosis_mode
                ], spacing=10),
                ft.Text(
                    "Seleccione el modo de diagnóstico: Árbol de Decisión (guiado) o Chat IA (libre)",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=10),
                ft.Container(
                    content=self.chat_messages,
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=10
                ),
                ft.Container(height=10),
                # Controles para chat libre
                self.chat_row,
                # Controles para árbol de decisión
                self.decision_buttons,
                ft.Container(height=10),
                self.save_diagnosis_btn
            ]),
            padding=20
        )
    
    def create_usuarios_tab(self):
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
                ft.Divider(),
                ft.Row([
                    ft.ElevatedButton(
                        "Actualizar Lista",
                        on_click=self.load_users,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Cerrar Detalles",
                        on_click=self.close_details_card,
                        bgcolor=ft.Colors.GREY,
                        color=ft.Colors.WHITE,
                        visible=False
                    )
                ]),
                ft.Container(height=20),
                ft.Card(
                    ft.Container(
                        content=ft.Column([
                            self.users_table
                        ], scroll=ft.ScrollMode.AUTO),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        padding=10,
                        height=400,
                    ),
                    elevation=5
                ),
                # Card de detalles del paciente
                self.patient_details_card,
                ft.Container(height=10),
                self.status_message
            ]),
            padding=20
        )
    
    def save_patient(self, e):
        # Validar campos
        if not all([
            self.nombre_field.value,
            self.edad_field.value,
            self.peso_field.value,
            self.altura_field.value,
            self.genero_dropdown.value,
            self.telefono_field.value,
            self.email_field.value
        ]):
            self.show_error("Por favor, complete todos los campos obligatorios.")
            return
        
        try:
            # Preparar datos del paciente
            patient_data = {
                "nombre_completo": self.nombre_field.value,
                "edad": int(self.edad_field.value),
                "peso": float(self.peso_field.value),
                "altura": float(self.altura_field.value),
                "genero": self.genero_dropdown.value,
                "numero_telefono": self.telefono_field.value,
                "email": self.email_field.value,
                "telegram": self.telegram_field.value or None
            }
            
            # Enviar datos a Node-RED
            response = requests.post(
                f"{self.node_red_url}/save-patient",
                json=patient_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.current_patient_id = result.get('patient_id')
                
                # Mostrar mensaje de éxito
                self.success_message.visible = True
                self.page.update()
                time.sleep(3) 

                self.diagnostico_btn.visible = True
                
                # Limpiar formulario
                self.clear_form()
                self.success_message.visible = False
                self.page.update()
            else:
                self.show_error("Error al guardar el paciente. Intente nuevamente.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión: {str(ex)}")
        except ValueError as ex:
            self.show_error("Por favor, verifique que los valores numéricos sean correctos.")
        except Exception as ex:
            self.show_error(f"Error inesperado: {str(ex)}")
    
    def change_diagnosis_mode(self, e):
        mode = e.control.value
        
        if mode == "chat":
            self.chat_row.visible = True
            self.decision_buttons.visible = False
            self.start_free_chat()
        else:
            self.chat_row.visible = False
            self.decision_buttons.visible = True
            self.start_decision_tree()
        
        self.page.update()
    
    def start_free_chat(self):
        """Iniciar modo de chat libre con IA"""
        self.final_diagnosis = None  # Reiniciar diagnóstico final
        self.chat_messages.controls.clear()
        welcome_message = "🤖 ¡Hola! Soy tu asistente especializado en hipertensión arterial.\n\n"
        welcome_message += "Puedes hacerme cualquier pregunta sobre:\n"
        welcome_message += "• Síntomas de hipertensión\n"
        welcome_message += "• Factores de riesgo\n"
        welcome_message += "• Tratamientos y medicamentos\n"
        welcome_message += "• Prevención y estilo de vida\n"
        welcome_message += "• Complicaciones\n\n"
        welcome_message += "⚠️ Recuerda: Siempre consulta con un médico profesional para un diagnóstico definitivo."
        
        self.add_ai_message(welcome_message)
        self.page.update()
    
    def start_decision_tree(self):
        """Iniciar diagnóstico con árbol de decisión"""
        self.current_decision_node = 0
        self.patient_responses = {}
        self.final_diagnosis = None  # Reiniciar diagnóstico final
        self.chat_messages.controls.clear()
        
        intro_message = "🔍 **Diagnóstico Guiado de Hipertensión Arterial**\n\n"
        intro_message += "Te haré una serie de preguntas específicas para evaluar tu riesgo cardiovascular.\n"
        intro_message += "Responde con 'Sí' o 'No' a cada pregunta.\n\n"
        intro_message += "⚠️ Este es un diagnóstico preliminar automatizado. Siempre consulta con un médico profesional.\n"
        intro_message += "\n" + "─" * 50 + "\n"
        
        self.add_ai_message(intro_message)
        self.ask_current_question()
        
        # Mostrar botones de decisión
        for control in self.decision_buttons.controls:
            control.visible = True
        self.decision_buttons.visible = True
        self.page.update()
    
    def ask_current_question(self):
        """Hacer la pregunta actual del árbol de decisión"""
        if self.current_decision_node in self.arbol_decision:
            node = self.arbol_decision[self.current_decision_node]
            question_message = f"**Pregunta {len(self.patient_responses) + 1}:**\n\n"
            question_message += f"❓ {node['pregunta']}\n\n"
            question_message += f"💡 {node['respuesta']}"
            
            self.add_ai_message(question_message)
    
    def handle_decision(self, answer):
        """Manejar respuesta del árbol de decisión"""
        if self.current_decision_node not in self.arbol_decision:
            return
            
        current_node = self.arbol_decision[self.current_decision_node]
        self.patient_responses[self.current_decision_node] = answer
        
        # Agregar respuesta del usuario
        response_text = "✅ Sí" if answer == "si" else "❌ No"
        self.add_user_message(response_text)
        
        # Determinar siguiente nodo
        next_node = current_node.get(answer)
        
        if next_node is None:
            # Es un nodo terminal, dar diagnóstico final
            self.give_final_diagnosis()
        else:
            # Continuar con la siguiente pregunta
            self.current_decision_node = next_node
            self.ask_current_question()
        
        self.page.update()
    
    def give_final_diagnosis(self):
        """Dar diagnóstico final basado en el árbol de decisión"""
        current_node = self.arbol_decision[self.current_decision_node]
        
        final_message = "\n" + "🎯" * 20 + "\n"
        final_message += "**DIAGNÓSTICO PRELIMINAR COMPLETADO**\n\n"
        final_message += f"📋 {current_node['pregunta']}\n\n"
        final_message += f"📝 **Recomendación:** {current_node['respuesta']}\n\n"
        
        # Agregar recomendaciones generales según el diagnóstico
        final_message += self.get_general_recommendations()
        
        final_message += "\n⚠️ **IMPORTANTE**: Este es un diagnóstico preliminar automatizado. "
        final_message += "Para un diagnóstico definitivo y tratamiento adecuado, siempre consulte con un médico profesional.\n"
        final_message += "🎯" * 20
        
        # Guardar el diagnóstico final
        self.final_diagnosis = final_message

        self.add_ai_message(final_message)
        
        # Mostrar botón para guardar diagnóstico
        self.save_diagnosis_btn.visible = True
        
        # Ocultar botones Sí/No y mostrar reiniciar
        for control in self.decision_buttons.controls[:2]:
            control.visible = False
        self.decision_buttons.controls[2].visible = True  # Botón reiniciar
        
        self.page.update()
    
    def get_general_recommendations(self):
        """Obtener recomendaciones generales basadas en las respuestas"""
        recommendations = "\n📋 **RECOMENDACIONES ADICIONALES:**\n\n"
        
        # Analizar respuestas para dar recomendaciones personalizadas
        risk_factors = []
        
        if 1 in self.patient_responses and self.patient_responses[1] == "si":
            risk_factors.append("factores_riesgo_modificables")
        if 3 in self.patient_responses and self.patient_responses[3] == "si":
            risk_factors.append("obesidad")
        if 4 in self.patient_responses and self.patient_responses[4] == "si":
            risk_factors.append("antecedentes_familiares")
        
        if "factores_riesgo_modificables" in risk_factors:
            recommendations += "• 🏃‍♀️ Implementar programa de ejercicio cardiovascular (30 min, 5 días/semana)\n"
            recommendations += "• 🥗 Reducir consumo de sodio (<2300mg/día)\n"
            recommendations += "• ⚖️ Mantener peso saludable (IMC 18.5-24.9)\n"
        
        if "obesidad" in risk_factors:
            recommendations += "• 📉 Programa de pérdida de peso supervisado\n"
            recommendations += "• 👩‍⚕️ Consulta con nutricionista\n"
        
        if "antecedentes_familiares" in risk_factors:
            recommendations += "• 🩺 Monitoreo más frecuente de presión arterial\n"
            recommendations += "• 📅 Chequeos médicos regulares cada 6 meses\n"
        
        recommendations += "\n🏥 **CUÁNDO BUSCAR ATENCIÓN MÉDICA INMEDIATA:**\n"
        recommendations += "• Presión arterial >180/110 mmHg\n"
        recommendations += "• Dolor de cabeza severo con náuseas\n"
        recommendations += "• Dificultad para respirar\n"
        recommendations += "• Dolor en el pecho\n"
        recommendations += "• Cambios en la visión\n"
        
        return recommendations
    
    def restart_diagnosis(self, e):
        """Reiniciar el diagnóstico"""
        self.start_decision_tree()
    
    def add_user_message(self, message):
        """Agregar mensaje del usuario al chat"""
        self.chat_messages.controls.append(
            ft.Container(
                content=ft.Text(f"👤 Usuario: {message}", size=14),
                bgcolor=ft.Colors.BLUE_100,
                padding=10,
                border_radius=10,
                margin=ft.margin.only(right=50)
            )
        )
    
    def add_ai_message(self, message):
        """Agregar mensaje de la IA al chat"""
        self.chat_messages.controls.append(
            ft.Container(
                content=ft.Text(f"🤖 IA Médica: {message}", size=14, selectable=True),
                bgcolor=ft.Colors.GREEN_100,
                padding=10,
                border_radius=10,
                margin=ft.margin.only(left=50)
            )
        )
    
    def send_message(self, e):
        """Manejar mensajes en modo chat libre"""
        if not self.chat_input.value or not self.chat_input.value.strip():
            return
            
        user_message = self.chat_input.value.strip()
        
        # Agregar mensaje del usuario
        self.add_user_message(user_message)
        self.chat_input.value = ""
        self.page.update()
        
        try:
            # Usar Gemini AI si está disponible, sino usar sistema básico
            if self.gemini_api_key and self.model:
                self.process_with_gemini_ai(user_message)
            else:
                self.process_with_basic_ai(user_message)
                
        except Exception as ex:
            error_message = f"❌ Error al procesar mensaje: {str(ex)}\n\n"
            error_message += "💡 Sugerencia: Verifica tu conexión a internet y la configuración de la API."
            self.add_ai_message(error_message)
            self.page.update()
    
    def process_with_gemini_ai(self, user_message):
        """Procesar mensaje con Gemini AI"""
        try:
            # Contexto especializado en hipertensión
            context = """Eres un asistente médico especializado en hipertensión arterial con amplio conocimiento en:
            - Diagnóstico y síntomas de hipertensión
            - Factores de riesgo cardiovascular
            - Tratamientos farmacológicos y no farmacológicos
            - Complicaciones de la hipertensión
            - Prevención y cambios de estilo de vida
            - Monitoreo de presión arterial
            
            Proporciona información médica precisa, actualizada y basada en evidencia.
            Siempre recuerda al usuario que la información no sustituye la consulta médica profesional.
            Usa un lenguaje claro y profesional pero accesible."""
            
            full_prompt = f"{context}\n\nPregunta del paciente: {user_message}"
            
            # Agregar contexto del paciente actual si existe
            if self.current_patient_id:
                patient_context = f"\nNota: El paciente está registrado en el sistema (ID: {self.current_patient_id})"
                full_prompt += patient_context
            
            response = self.model.generate_content(full_prompt)
            ai_response = response.text
            
            # Agregar disclaimer médico
            ai_response += "\n\n⚠️ **Importante**: Esta información es solo para fines educativos. Siempre consulte con un médico profesional para diagnóstico y tratamiento específicos."
            self.final_diagnosis = ai_response
            
            self.add_ai_message(ai_response)
            
        except Exception as e:
            error_message = f"Error con Gemini AI: {str(e)}\nUsando sistema básico como respaldo..."
            self.add_ai_message(error_message)
            self.process_with_basic_ai(user_message)
        
        # Mostrar botón de guardar después de la primera respuesta
        self.save_diagnosis_btn.visible = True
        self.page.update()
    
    def process_with_basic_ai(self, user_message):
        """Sistema básico de respuestas para hipertensión"""
        user_message_lower = user_message.lower()
        
        # Respuestas especializadas en hipertensión
        if any(word in user_message_lower for word in ['dolor de cabeza', 'cefalea', 'cabeza']):
            response = """🔍 **Dolor de cabeza e Hipertensión**
            
El dolor de cabeza puede estar relacionado con hipertensión arterial, especialmente cuando:
• La presión arterial está muy elevada (>180/110 mmHg)
• Es un dolor pulsátil en la parte posterior de la cabeza
• Se presenta al despertar en la mañana
• Se acompaña de otros síntomas como mareos o visión borrosa

**¿Qué hacer?**
✅ Medir la presión arterial inmediatamente
✅ Si PA >180/110: buscar atención médica urgente
✅ Mantener registro de episodios de dolor
✅ Evitar automedicación excesiva"""

        elif any(word in user_message_lower for word in ['mareo', 'mareado', 'vértigo']):
            response = """🌀 **Mareos e Hipertensión**
            
Los mareos pueden indicar:
• Hipertensión arterial no controlada
• Hipotensión ortostática (efecto de medicamentos)
• Problemas de circulación cerebral

**Evaluación importante:**
📊 Medir presión arterial en posición acostada y de pie
⏰ Anotar momento del día cuando ocurren
💊 Revisar medicamentos antihipertensivos
🚨 Si se acompaña de confusión o desmayo: atención inmediata"""

        elif any(word in user_message_lower for word in ['presión', 'tensión', 'hipertensión']):
            response = """🩺 **Información sobre Presión Arterial**
            
**Valores de referencia:**
• Normal: <120/80 mmHg
• Prehipertensión: 120-139/80-89 mmHg
• Hipertensión Grado 1: 140-159/90-99 mmHg
• Hipertensión Grado 2: ≥160/100 mmHg
• Crisis hipertensiva: >180/110 mmHg

**Factores que afectan la medición:**
☕ Cafeína (aumenta temporalmente)
🚬 Tabaco (aumenta)
🏃‍♀️ Ejercicio reciente (aumenta)
😰 Estrés y ansiedad (aumenta)
💤 Sueño inadecuado (aumenta)"""

        elif any(word in user_message_lower for word in ['tratamiento', 'medicamento', 'medicina']):
            response = """💊 **Tratamiento de la Hipertensión**
            
**Cambios de estilo de vida (siempre primero):**
🥗 Dieta DASH (rica en frutas, vegetales, granos integrales)
🧂 Reducir sodio (<2300mg/día, ideal <1500mg/día)
🏃‍♀️ Ejercicio aeróbico (150 min/semana)
⚖️ Mantener peso saludable
🚭 No fumar
🍷 Limitar alcohol (max 2 copas/día hombres, 1 mujer)

**Tipos de medicamentos antihipertensivos:**
• IECA (enalapril, lisinopril)
• ARA II (losartán, valsartán)
• Diuréticos tiazídicos (hidroclorotiazida)
• Bloqueadores de canales de calcio (amlodipino)
• Betabloqueadores (metoprolol)

⚠️ Nunca suspender medicamentos sin supervisión médica"""

        else:
            response = """🤖 **Asistente de Hipertensión Arterial**
            
Puedo ayudarte con información sobre:

📊 **Medición y valores de presión arterial**
⚠️ **Síntomas y signos de alarma**
💊 **Tratamientos y medicamentos**
🥗 **Dieta y nutrición (Plan DASH)**
🏃‍♀️ **Ejercicio y actividad física**
⚖️ **Factores de riesgo**
🚨 **Complicaciones**
🏥 **Cuándo buscar atención médica**

**¿Sobre qué tema específico te gustaría saber más?**
"""
        self.final_diagnosis = response

        self.add_ai_message(response)
        self.save_diagnosis_btn.visible = True
        self.page.update()
    
    def save_diagnosis(self, e):
        if not self.current_patient_id:
            self.show_error("No hay paciente seleccionado.")
            return
            
        try:
            # Recopilar todo el chat como diagnóstico
            messages = []
            for control in self.chat_messages.controls:
                if hasattr(control, 'content') and hasattr(control.content, 'value'):
                    messages.append(control.content.value)
            
            diagnosis_data = {
                "patient_id": self.current_patient_id,
                "diagnosis": {
                    "timestamp": datetime.now().isoformat(),
                    "messages": messages,
                    "diagnostico": self.final_diagnosis if self.final_diagnosis else "No se completó el diagnóstico",
                    "session_id": f"session_{self.current_patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            }
            
            response = requests.post(
                f"{self.node_red_url}/save-diagnosis",
                json=diagnosis_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.show_success("Diagnóstico guardado exitosamente.")
            else:
                self.show_error("Error al guardar el diagnóstico.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión: {str(ex)}")
    
    def load_users(self, e):
        try:
            response = requests.get(
                f"{self.node_red_url}/get-patients",
                timeout=10
            )
            
            if response.status_code == 200:
                patients = response.json()
                
                # Limpiar tabla
                self.users_table.rows.clear()
                
                # Agregar filas
                for patient in patients:
                    # Crear funciones lambda con captura de ID
                    view_func = lambda _, pid=patient['id']: self.view_patient(pid)
                    delete_func = lambda _, pid=patient['id']: self.delete_patient(pid)
                    send_func = lambda _, pid=patient['id']: self.send_report(pid)
                    generate_report_func = lambda _, pid=patient['id']: self.generate_report(pid)

                    self.users_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(str(patient.get('id', '')))),
                                ft.DataCell(ft.Text(patient.get('nombre_completo', ''))),
                                ft.DataCell(ft.Text(str(patient.get('edad', '')))),
                                ft.DataCell(ft.Text(patient.get('email', ''))),
                                ft.DataCell(
                                    ft.Row([
                                        ft.IconButton(
                                            ft.Icons.VISIBILITY,
                                            on_click=view_func,
                                            tooltip="Ver detalles"
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE,
                                            on_click=delete_func,
                                            tooltip="Eliminar",
                                            icon_color=ft.Colors.RED
                                        )
                                    ])
                                )
                            ]
                        )
                    )
                
                self.show_success(f"Se cargaron {len(patients)} pacientes.")
                self.page.update()
            else:
                self.show_error("Error al cargar los usuarios.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión: {str(ex)}")
    
    def view_patient(self, patient_id):
        """Mostrar detalles del paciente en el card debajo de la tabla"""
        try:
            # Obtener datos del paciente específico
            response = requests.get(
                f"{self.node_red_url}/get-patient/{patient_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                patient = response.json()
                self.show_patient_details_in_card(patient)
            else:
                self.show_error("Error al cargar los detalles del paciente.")

        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error al obtener datos del paciente: {str(ex)}")

    def show_patient_details_in_card(self, patient):
        """Mostrar los detalles del paciente en el card"""
        
        # Calcular IMC
        try:
            peso = float(patient.get('peso', 0))
            altura = float(patient.get('altura', 1)) / 100  # Convertir cm a m
            imc = peso / (altura * altura) if altura > 0 else 0
            imc_categoria = self.get_imc_category(imc)
        except (ValueError, TypeError):
            imc = 0
            imc_categoria = "No calculable"
        
        # Procesar diagnóstico JSON
        diagnostico_info = self.process_diagnosis_data(patient.get('diagnostico'))
        
        # Crear contenido del card
        card_content = ft.Column([
            # Encabezado del card
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=35, color="#FFFFFF"),
                    ft.Column([
                        ft.Text(
                            f"Paciente #{patient.get('id', 'N/A')}",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color="#FFFFFF"
                        ),
                        ft.Text(
                            patient.get('nombre_completo', 'Nombre no disponible'),
                            size=16,
                            color="#FFFFFF"
                        )
                    ], spacing=5),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color="#FFFFFF",
                        on_click=self.close_details_card,
                        tooltip="Cerrar detalles"
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#2196F3",
                padding=15,
                border_radius=ft.border_radius.only(top_left=10, top_right=10)
            ),
            
            # Contenido en tabs
            ft.Tabs(
                selected_index=0,
                animation_duration=300,
                height=400,
                tabs=[
                    ft.Tab(
                        text="Información Personal",
                        icon=ft.Icons.PERSON_OUTLINE,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Column([
                                            self.create_info_row("👤 Nombre", patient.get('nombre_completo', 'N/A')),
                                            self.create_info_row("🎂 Edad", f"{patient.get('edad', 'N/A')} años"),
                                            self.create_info_row("⚧️ Género", self.get_gender_display(patient.get('genero', 'N/A'))),
                                        ], spacing=10),
                                        expand=1
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            self.create_info_row("📧 Email", patient.get('email', 'N/A')),
                                            self.create_info_row("📞 Teléfono", patient.get('numero_telefono', 'N/A')),
                                            self.create_info_row("💬 Telegram", patient.get('telegram', 'No especificado')),
                                        ], spacing=10),
                                        expand=1
                                    )
                                ]),
                                ft.Divider(height=20),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Column([
                                            self.create_info_row("⚖️ Peso", f"{patient.get('peso', 'N/A')} kg"),
                                            self.create_info_row("📏 Altura", f"{patient.get('altura', 'N/A')} cm"),
                                            self.create_info_row("📊 IMC", f"{imc:.1f} kg/m² ({imc_categoria})"),
                                        ], spacing=10),
                                        expand=1
                                    ),
                                    ft.Container(
                                        content=ft.Column([
                                            self.create_info_row("🗓️ Registro", self.format_date(patient.get('created_at'))),
                                            self.create_info_row("🔄 Actualizado", self.format_date(patient.get('updated_at'))),
                                        ], spacing=10),
                                        expand=1
                                    )
                                ])
                            ], spacing=10),
                            padding=20
                        )
                    ),
                    ft.Tab(
                        text="Diagnósticos",
                        icon=ft.Icons.MEDICAL_SERVICES,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("📋 Historial de Diagnósticos", size=16, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                ft.Container(
                                    content=diagnostico_info,
                                    expand=True,
                                    bgcolor=ft.Colors.GREY_50,
                                    padding=10,
                                    border_radius=8,
                                )
                            ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE),
                            padding=20
                        )
                    ),
                    ft.Tab(
                        text="Evaluación de Riesgo",
                        icon=ft.Icons.WARNING_AMBER,
                        content=ft.Container(
                            content=self.create_risk_assessment(patient, imc),
                            padding=20
                        )
                    )
                ]
            ),
            
            # Botones de acción
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "Generar PDF",
                        icon=ft.Icons.PICTURE_AS_PDF,
                        on_click=lambda _: self.generate_report(patient.get('id')),
                        bgcolor=ft.Colors.ORANGE,
                        color=ft.Colors.WHITE
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                padding=15,
                bgcolor=ft.Colors.GREY_100,
                border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
            )
        ], spacing=0)
        
        # Actualizar el contenido del card y mostrarlo
        self.patient_details_card.content = card_content
        self.patient_details_card.visible = True
        
        # Mostrar botón de cerrar detalles
        for control in self.tabs.tabs[2].content.content.controls[2].controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "Cerrar Detalles":
                control.visible = True
        
        self.page.update()
    
    def close_details_card(self, e=None):
        """Cerrar el card de detalles del paciente"""
        self.patient_details_card.visible = False
        
        # Ocultar botón de cerrar detalles
        for control in self.tabs.tabs[2].content.content.controls[2].controls:
            if isinstance(control, ft.ElevatedButton) and control.text == "Cerrar Detalles":
                control.visible = False
        
        self.page.update()
    
    def confirm_delete_patient(self, patient_id):
        """Confirmar eliminación del paciente"""
        def handle_delete(e):
            self.delete_patient(patient_id)
            self.close_details_card()
            dlg.open = False
            self.page.update()
        
        def handle_cancel(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text("¿Está seguro de que desea eliminar este paciente? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=handle_cancel),
                ft.TextButton("Eliminar", on_click=handle_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def send_report(self, patient_id):
        """Enviar reporte del paciente"""
        try:
            response = requests.post(
                f"{self.node_red_url}/send-report/{patient_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.show_success("Reporte enviado exitosamente.")
            else:
                self.show_error("Error al enviar el reporte.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión: {str(ex)}")
    
    def generate_report(self, patient_id):
        try:
            # Primero obtener los datos completos del paciente
            response = requests.get(
                f"{self.node_red_url}/get-patient/{patient_id}",
                timeout=10
            )
            
            if response.status_code != 200:
                self.show_error("Error al obtener datos del paciente.")
                return
                
            patient = response.json()
            
            # Mostrar mensaje de progreso
            self.show_success(f"📄 Generando reporte PDF para {patient.get('nombre_completo', 'paciente')}...")
            
            # Enviar solicitud a Node-RED para generar el PDF
            response = requests.post(
                f"{self.node_red_url}/export-diagnosis-pdf",
                json={"patient_id": patient_id},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    # El HTML está disponible, ahora convertir a PDF
                    self.convert_html_to_pdf(result, patient)
                else:
                    self.show_error(f"Error: {result.get('message', 'Error desconocido')}")
            else:
                self.show_error("Error al generar el reporte en el servidor.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión al generar reporte: {str(ex)}")
        except Exception as ex:
            self.show_error(f"Error inesperado: {str(ex)}")

    def convert_html_to_pdf(self, html_data, patient):
        """Convertir HTML a PDF y manejarlo según las capacidades disponibles"""
        try:
            html_content = html_data.get('html', '')
            filename = html_data.get('filename', f"reporte_{patient.get('id', 'paciente')}.pdf")
            
            # Opción 1: Usar reportlab (más compatible con Windows)
            if REPORTLAB_AVAILABLE:
                try:
                    self.generate_pdf_with_reportlab(html_data, patient, filename)
                    return
                except Exception as e:
                    self.show_error(f"Error al generar PDF con reportlab: {str(e)}")
            
            # Opción 2: Usar weasyprint si está disponible
            if WEASYPRINT_AVAILABLE:
                try:
                    from io import BytesIO
                    
                    # Generar PDF con weasyprint
                    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
                    
                    # Guardar archivo
                    self.save_pdf_file(pdf_bytes, filename, patient)
                    return
                    
                except Exception as e:
                    self.show_error(f"Error al generar PDF con weasyprint: {str(e)}")
            
            # Opción 3: Fallback - guardar como HTML
            self.show_error("No hay librerías PDF disponibles. Guardando como HTML...")
            self.save_as_html_report(html_content, filename.replace('.pdf', '.html'), patient)
                
        except Exception as e:
            self.show_error(f"Error al procesar el reporte: {str(e)}")

    def generate_pdf_with_reportlab(self, html_data, patient, filename):
        """Generar PDF usando reportlab (más simple, compatible con Windows)"""
        try:
            from io import BytesIO
            import re
            
            # Crear directorio de reportes si no existe
            reports_dir = "reportes_medicos"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            file_path = os.path.join(reports_dir, filename)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_style = styles['Title']
            story.append(Paragraph("Reporte Médico - Sistema Experto Hipertensión", title_style))
            story.append(Spacer(1, 20))
            
            # Información del paciente
            patient_info = f"""
            <b>Información del Paciente:</b><br/>
            Nombre: {patient.get('nombre_completo', 'N/A')}<br/>
            Edad: {patient.get('edad', 'N/A')} años<br/>
            Género: {self.get_gender_display(patient.get('genero', 'N/A'))}<br/>
            Email: {patient.get('email', 'N/A')}<br/>
            Teléfono: {patient.get('numero_telefono', 'N/A')}<br/>
            Peso: {patient.get('peso', 'N/A')} kg<br/>
            Altura: {patient.get('altura', 'N/A')} cm<br/>
            """
            
            story.append(Paragraph(patient_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Evaluación de riesgo (simulada)
            peso = float(patient.get('peso', 0))
            altura = float(patient.get('altura', 1)) / 100
            imc = peso / (altura * altura) if altura > 0 else 0
            imc_categoria = self.get_imc_category(imc)
            
            risk_info = f"""
            <b>Evaluación de Riesgo Cardiovascular:</b><br/>
            IMC: {imc:.1f} kg/m² ({imc_categoria})<br/>
            """
            
            story.append(Paragraph(risk_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Diagnóstico si existe
            diagnostico = patient.get('diagnostico')
            if diagnostico:
                story.append(Paragraph("<b>Diagnóstico:</b>", styles['Heading2']))
                if isinstance(diagnostico, str):
                    # Limpiar HTML básico para reportlab
                    clean_text = re.sub('<[^<]+?>', '', diagnostico)
                    story.append(Paragraph(clean_text, styles['Normal']))
                elif isinstance(diagnostico, dict):
                    diag_text = str(diagnostico)
                    clean_text = re.sub('<[^<]+?>', '', diag_text)
                    story.append(Paragraph(clean_text, styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Fecha de generación
            fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
            story.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_actual}", styles['Normal']))
            
            # Generar PDF
            doc.build(story)
            
            self.show_success(f"✅ Reporte PDF generado: {file_path}")
            print(f"PDF con reportlab guardado en: {file_path}")
            
            # Mostrar diálogo
            self.show_pdf_generated_dialog(file_path, patient)
            
        except Exception as e:
            self.show_error(f"Error al generar PDF con reportlab: {str(e)}")
            raise e

    def save_pdf_file(self, pdf_bytes, filename, patient):
        """Guardar archivo PDF"""
        try:
            # Por ahora, guardamos en el directorio actual
            import os
            
            # Crear directorio de reportes si no existe
            reports_dir = "reportes_medicos"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # Guardar archivo
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            
            self.show_success(f"✅ Reporte PDF generado: {file_path}")
            print(f"PDF guardado en: {file_path}")
            
            # Mostrar diálogo con información del archivo generado
            self.show_pdf_generated_dialog(file_path, patient)
            
        except Exception as e:
            self.show_error(f"Error al guardar PDF: {str(e)}")

    def save_as_html_report(self, html_content, filename, patient):
        """Guardar reporte como archivo HTML"""
        try:
            # Crear directorio de reportes si no existe
            reports_dir = "reportes_medicos"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # Guardar archivo HTML
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.show_success(f"✅ Reporte HTML generado: {file_path}")
            print(f"HTML guardado en: {file_path}")
            
            # Mostrar diálogo con información del archivo generado
            self.show_html_generated_dialog(file_path, patient)
            
        except Exception as e:
            self.show_error(f"Error al guardar HTML: {str(e)}")

    def show_pdf_generated_dialog(self, file_path, patient):
        """Mostrar diálogo cuando se genera el PDF"""
        def close_dialog(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("📄 PDF Generado Exitosamente"),
            content=ft.Column([
                ft.Text(f"Reporte generado para: {patient.get('nombre_completo', 'Paciente')}"),
                ft.Text(f"Archivo guardado en: {file_path}"),
                ft.Text("El archivo se ha guardado en la carpeta 'reportes_medicos'")
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_html_generated_dialog(self, file_path, patient):
        """Mostrar diálogo cuando se genera el HTML"""
        def close_dialog(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("📄 Reporte HTML Generado"),
            content=ft.Column([
                ft.Text(f"Reporte generado para: {patient.get('nombre_completo', 'Paciente')}"),
                ft.Text(f"Archivo guardado en: {file_path}"),
                ft.Text("Nota: Se guardó como HTML porque PDF no está disponible"),
                ft.Text("Puede abrir el archivo en cualquier navegador web")
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def create_info_row(self, label, value):
        """Crear fila de información con etiqueta y valor"""
        return ft.Row([
            ft.Container(
                content=ft.Text(label, weight=ft.FontWeight.BOLD, size=14),
                width=120
            ),
            ft.Text(str(value), size=14, color=ft.Colors.GREY_800)
        ], spacing=10)
    
    def get_gender_display(self, gender):
        """Convertir código de género a texto legible"""
        gender_map = {
            'M': 'Masculino',
            'F': 'Femenino',
            'Otro': 'Otro'
        }
        return gender_map.get(gender, gender)
    
    def get_imc_category(self, imc):
        """Determinar categoría del IMC"""
        if imc < 18.5:
            return "Bajo peso"
        elif imc < 25:
            return "Normal"
        elif imc < 30:
            return "Sobrepeso"
        elif imc < 35:
            return "Obesidad I"
        elif imc < 40:
            return "Obesidad II"
        else:
            return "Obesidad III"
    
    def format_date(self, date_str):
        """Formatear fecha para mostrar"""
        if not date_str:
            return "No disponible"
        try:
            from datetime import datetime
            # Intentar varios formatos de fecha
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str.split('.')[0], fmt)
                    return date_obj.strftime('%d/%m/%Y %H:%M')
                except ValueError:
                    continue
            return date_str
        except:
            return "Formato inválido"
        
    def process_diagnosis_data(self, diagnostico):
        """Procesar datos de diagnóstico JSON"""
        if not diagnostico:
            return ft.Text("No hay diagnósticos registrados", 
                          style=ft.TextThemeStyle.BODY_MEDIUM, 
                          color=ft.Colors.GREY_600)
        
        try:
            # Si es string JSON, parsearlo
            if isinstance(diagnostico, str):
                import json
                diagnostico = json.loads(diagnostico)
            
            # Crear lista de diagnósticos
            diagnosis_widgets = []
            
            if isinstance(diagnostico, dict):
                # Diagnóstico único
                diagnosis_widgets.append(self.create_diagnosis_item(diagnostico))
            elif isinstance(diagnostico, list):
                # Múltiples diagnósticos
                for i, diag in enumerate(diagnostico, 1):
                    diagnosis_widgets.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"Sesión {i}", weight=ft.FontWeight.BOLD),
                                self.create_diagnosis_item(diag)
                            ]),
                            margin=ft.margin.only(bottom=10)
                        )
                    )
            
            return ft.Column(diagnosis_widgets, spacing=10)
            
        except Exception as e:
            return ft.Text(f"Error al procesar diagnóstico: {str(e)}", 
                          color=ft.Colors.RED)
    
    def create_diagnosis_item(self, diagnosis):
        """Crear widget para un item de diagnóstico"""
        try:
            timestamp = diagnosis.get('timestamp', 'Fecha no disponible')
            messages = diagnosis.get('messages', [])
            session_id = diagnosis.get('session_id', 'N/A')
            
            if not messages:
                return ft.Text("No hay mensajes en este diagnóstico")
            
            # Mostrar todos los mensajes completos
            content = "\n".join([msg.replace("👤 Usuario: ", "• ").replace("🤖 IA Médica: ", "→ ") 
                               for msg in messages])
            
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"📅 {timestamp}", size=12, color=ft.Colors.GREY_600),
                    ft.Text(f"🆔 Sesión: {session_id}", size=12, color=ft.Colors.GREY_600),
                    ft.Text(content, size=13, selectable=True),
                ], spacing=5),
                bgcolor=ft.Colors.WHITE,
                padding=10,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300)
            )
            
        except Exception as e:
            return ft.Text(f"Error al mostrar diagnóstico: {str(e)}", color=ft.Colors.RED)
    
    def create_risk_assessment(self, patient, imc):
        """Crear evaluación de riesgo cardiovascular"""
        risk_factors = []
        risk_score = 0
        
        # Evaluar factores de riesgo
        try:
            edad = int(patient.get('edad', 0))
            genero = patient.get('genero', '')
            
            # Edad
            if (genero == 'M' and edad >= 45) or (genero == 'F' and edad >= 55):
                risk_factors.append("Edad avanzada")
                risk_score += 2
            
            # IMC
            if imc >= 30:
                risk_factors.append("Obesidad")
                risk_score += 2
            elif imc >= 25:
                risk_factors.append("Sobrepeso")
                risk_score += 1
            
            # Determinar nivel de riesgo
            if risk_score >= 4:
                risk_level = "Alto"
                risk_color = ft.Colors.RED
                risk_icon = "🚨"
            elif risk_score >= 2:
                risk_level = "Moderado"
                risk_color = ft.Colors.ORANGE
                risk_icon = "⚠️"
            else:
                risk_level = "Bajo"
                risk_color = ft.Colors.GREEN
                risk_icon = "✅"
            
        except:
            risk_level = "No evaluable"
            risk_color = ft.Colors.GREY
            risk_icon = "❓"
            risk_factors = ["Datos insuficientes"]
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "⚡ Evaluación de Riesgo Cardiovascular",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_600
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(risk_icon, size=24),
                            ft.Text(f"Riesgo {risk_level}", 
                                   size=16, 
                                   weight=ft.FontWeight.BOLD, 
                                   color=risk_color)
                        ], spacing=10),
                        ft.Text("Factores identificados:", 
                               size=14, 
                               weight=ft.FontWeight.BOLD),
                        ft.Text("• " + "\n• ".join(risk_factors) if risk_factors else "Ninguno", 
                               size=13),
                    ], spacing=8),
                    bgcolor=ft.Colors.PURPLE_50,
                    padding=15,
                    border_radius=10
                )
            ], spacing=10)
        )
    
    def delete_patient(self, patient_id):
        """Eliminar paciente"""
        try:
            response = requests.delete(
                f"{self.node_red_url}/delete-patient/{patient_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.show_success("Paciente eliminado exitosamente.")
                # Recargar lista automáticamente
                self.load_users(None)
            else:
                self.show_error("Error al eliminar el paciente.")
                
        except requests.exceptions.RequestException as ex:
            self.show_error(f"Error de conexión: {str(ex)}")
    
    def switch_to_tab(self, index):
        self.tabs.selected_index = index
        self.diagnostico_btn.visible = False
        self.page.update()
    
    def tab_changed(self, e):
        if e.control.selected_index == 1:  # Tab de diagnóstico
            # Inicializar el modo por defecto (árbol de decisión)
            if not hasattr(self, 'diagnosis_initialized'):
                self.start_decision_tree()
                self.diagnosis_initialized = True
        elif e.control.selected_index == 2:  # Tab de usuarios
            self.load_users(e)
    
    def clear_form(self):
        self.nombre_field.value = ""
        self.edad_field.value = ""
        self.peso_field.value = ""
        self.altura_field.value = ""
        self.genero_dropdown.value = None
        self.telefono_field.value = ""
        self.email_field.value = ""
        self.telegram_field.value = ""
        self.page.update()
    
    def show_error(self, message):
        self.status_message.value = f"❌ {message}"
        self.status_message.color = ft.Colors.RED
        self.page.update()
        print(f"Error: {message}")
    
    def show_success(self, message):
        print(f"Éxito: {message}")
        self.status_message.value = f"✅ {message}"
        self.status_message.color = ft.Colors.GREEN
        self.page.update()
        

def main(page: ft.Page):
    app = HypertensionApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main, port=8080, view=ft.WEB_BROWSER)