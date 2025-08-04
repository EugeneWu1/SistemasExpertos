import flet as ft
import json
import requests
import uuid
from datetime import datetime

def main(page: ft.Page):
    page.title = "Sistema Experto: Hipertensión"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ALWAYS

    # Base de datos simulada de pacientes
    pacientes_db = []
    
    # Configuración del bot de Telegram
    TELEGRAM_BOT_URL = "http://localhost:1880/telegram"  # URL de tu endpoint de Node-RED

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
            "si": None, "no": None},
        4: {"pregunta": "¿El paciente consume mucha sal?",
            "respuesta": "El consumo excesivo de sal aumenta la presión arterial.",
            "si": None, "no": None},
        5: {"pregunta": "¿No presenta ningún síntoma?",
            "respuesta": "La hipertensión puede ser silenciosa en fases tempranas.",
            "si": None, "no": None},
        6: {"pregunta": "¿Síntomas severos como confusión o convulsiones?",
            "respuesta": "Síntomas severos pueden indicar una crisis hipertensiva.",
            "si": None, "no": None},
    }

    estado = {"nodo": 0, "historial": [], "paciente_actual": None, "respuestas": []}
    diagnostico_text = ft.Text("", size=22, color="red", weight="bold")
    respuesta_texto = ft.Text("", size=18, color="black")

    # --- NUEVOS COMPONENTES PARA FORMULARIO DE PACIENTE ---
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

        # Nivel 0
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(0, arbol[0]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 1 (nodos 1 y 2)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(1, arbol[1]["pregunta"]), padding=10),
                ft.Container(width=100),
                ft.Container(nodo_arbol(2, arbol[2]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # Nivel 2 (nodos 3, 4, 5, 6)
        arbol_vista.controls.append(
            ft.Row([
                ft.Container(nodo_arbol(3, arbol[3]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(4, arbol[4]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(5, arbol[5]["pregunta"]), padding=10),
                ft.Container(nodo_arbol(6, arbol[6]["pregunta"]), padding=10),
            ], alignment=ft.MainAxisAlignment.CENTER)
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
    formulario_paciente = ft.Container(
        content=ft.Column([
            ft.Text("📋 Datos del Paciente", size=20, weight="bold"),
            ft.Row([nombre_field, edad_field, sexo_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([telefono_field, email_field], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([peso_field, altura_field], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("Registrar Paciente", on_click=crear_paciente),
            ft.Divider(),
        ], spacing=10),
        padding=10,
        bgcolor=ft.Colors.BLUE_GREY_50,
        border_radius=10,
    )

    # --- INFORMACIÓN DEL PACIENTE ACTUAL ---
    def get_info_paciente():
        if estado["paciente_actual"]:
            p = estado["paciente_actual"]
            return ft.Text(f"👤 Paciente: {p['nombre']} | ID: {p['id']} | IMC: {p['imc']}", 
                          size=16, weight="bold", color="blue")
        return ft.Text("⚠️ No hay paciente registrado", size=16, color="red")

    info_paciente = ft.Container(content=get_info_paciente(), padding=10)

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Sistema Experto: Hipertensión", size=24, weight="bold"),
                    formulario_paciente,  # NUEVO: Formulario agregado
                    info_paciente,        # NUEVO: Info del paciente actual
                    arbol_vista,
                    ft.Divider(),
                    question,
                    botones,
                    respuesta_texto,
                    diagnostico_text,
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
    def actualizar_info(_):
        info_paciente.content = get_info_paciente()
        page.update()
    
    # Timer para actualizar la info del paciente
    import threading
    def timer_update():
        while True:
            try:
                actualizar_info(None)
                threading.Event().wait(2)  # Actualizar cada 2 segundos
            except:
                break
    
    threading.Thread(target=timer_update, daemon=True).start()

    page.update()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8080)