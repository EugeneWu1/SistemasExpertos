import flet as ft
import mysql.connector
from mysql.connector import Error
import re
from datetime import datetime
#from main import main as main_estudio
import os
from dotenv import load_dotenv

load_dotenv()

def main(page: ft.Page):
    page.title = "Sistema de Registro de Pacientes"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#F5F5F5"
    page.window_width = 500
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

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

    def conectar_bd():
        """Establece conexión con la base de datos con manejo específico de errores"""
        try:
            print("🔄 Intentando conectar a la base de datos...")
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                print("✅ Conexión exitosa a la base de datos")
                return connection
        except mysql.connector.Error as err:
            print(f"❌ Error MySQL: {err}")
            mostrar_notificacion(f"Error MySQL: {err}", "#F44336")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            mostrar_notificacion(f"Error inesperado: {e}", "#F44336")
        return None

    def verificar_email_existe(email):
        """Verifica si el email ya existe en la base de datos"""
        print(f"🔍 Verificando email: {email}")
        connection = conectar_bd()
        if not connection:
            print("❌ No se pudo conectar para verificar email")
            return False
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT email FROM paciente WHERE email = %s", (email,))
            result = cursor.fetchone()
            existe = result is not None
            print(f"📧 Email {'existe' if existe else 'no existe'} en la BD")
            return existe
        except Error as e:
            print(f"❌ Error al verificar email: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def insertar_paciente(datos_paciente):
        """Inserta un nuevo paciente en la base de datos"""
        print(f"💾 Intentando insertar paciente: {datos_paciente[0]}")
        connection = conectar_bd()
        if not connection:
            print("❌ No se pudo conectar para insertar")
            return None
        
        try:
            cursor = connection.cursor()
            query = """INSERT INTO paciente 
                       (nombre_completo, edad, peso, genero, numero_telefono, email, altura, diagnostico) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            print(f"📝 Query: {query}")
            print(f"📋 Datos: {datos_paciente}")
            
            cursor.execute(query, datos_paciente)
            connection.commit()
            paciente_id = cursor.lastrowid
            print(f"✅ Paciente insertado con ID: {paciente_id}")
            return paciente_id
        except Error as e:
            print(f"❌ Error al insertar paciente: {e}")
            mostrar_notificacion(f"Error al insertar paciente: {str(e)}", "#F44336")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    # Campos del formulario
    nombre_field = ft.TextField(
        label="Nombre Completo", 
        width=350, 
        prefix_icon=ft.Icons.PERSON,
        border_radius=10,
        error_text="",
        max_length=100
    )
    
    edad_field = ft.TextField(
        label="Edad", 
        width=170, 
        keyboard_type=ft.KeyboardType.NUMBER, 
        prefix_icon=ft.Icons.CAKE,
        border_radius=10,
        error_text=""
    )
    
    genero_dropdown = ft.Dropdown(
        label="Género",
        width=170,
        options=[
            ft.dropdown.Option("M", "Masculino"),
            ft.dropdown.Option("F", "Femenino"),
            ft.dropdown.Option("Otro", "Otro"),
        ],
        prefix_icon=ft.Icons.WC,
        border_radius=10,
        error_text=""
    )
    
    telefono_field = ft.TextField(
        label="Número de Teléfono", 
        width=250, 
        prefix_icon=ft.Icons.PHONE,
        border_radius=10,
        error_text="",
        max_length=20
    )
    
    email_field = ft.TextField(
        label="Email", 
        width=350, 
        prefix_icon=ft.Icons.EMAIL,
        border_radius=10,
        keyboard_type=ft.KeyboardType.EMAIL,
        error_text="",
        max_length=100
    )
    
    peso_field = ft.TextField(
        label="Peso (kg)", 
        width=170, 
        keyboard_type=ft.KeyboardType.NUMBER, 
        prefix_icon=ft.Icons.MONITOR_WEIGHT,
        border_radius=10,
        error_text="",
        hint_text="Ej: 70.5"
    )
    
    altura_field = ft.TextField(
        label="Altura (m)", 
        width=170, 
        keyboard_type=ft.KeyboardType.NUMBER, 
        prefix_icon=ft.Icons.STRAIGHTEN,
        border_radius=10,
        error_text="",
        hint_text="Ej: 1.75"
    )
    
    # AGREGADO: Campo de diagnóstico que faltaba
    diagnostico_field = ft.TextField(
        label="Diagnóstico (Opcional)", 
        width=350,
        prefix_icon=ft.Icons.MEDICAL_SERVICES,
        border_radius=10,
        multiline=True,
        min_lines=2,
        max_lines=3,
        hint_text="Ingrese el diagnóstico médico si aplica..."
    )

    # Contenedor para mostrar información del paciente registrado
    info_paciente = ft.Container(
        visible=False,
        bgcolor="#E8F5E8",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20)
    )

    # Indicador de estado de conexión
    estado_conexion = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CIRCLE, size=12),
            ft.Text("Verificando conexión...", size=12)
        ], spacing=5),
        padding=5,
        bgcolor="#FFF3E0",
        border_radius=5,
        margin=ft.margin.only(bottom=10)
    )

    def verificar_conexion_inicial():
        """Verifica la conexión inicial a la base de datos"""
        print("🔄 Verificando conexión inicial...")
        connection = conectar_bd()
        if connection:
            estado_conexion.content = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=12, color="#4CAF50"),
                ft.Text("Conectado a la base de datos", size=12, color="#4CAF50")
            ], spacing=5)
            estado_conexion.bgcolor = "#E8F5E8"
            connection.close()
            print("✅ Conexión inicial exitosa")
        else:
            estado_conexion.content = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=12, color="#F44336"),
                ft.Text("Error de conexión a la base de datos", size=12, color="#F44336")
            ], spacing=5)
            estado_conexion.bgcolor = "#FFEBEE"
            print("❌ Error en conexión inicial")
        page.update()

    def mostrar_notificacion(mensaje, color="green"):
        print(f"📢 Notificación: {mensaje}")
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white"),
            bgcolor=color,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()

    def validar_email(email):
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None

    def validar_telefono(telefono):
        # Validar que tenga entre 8 y 20 caracteres
        patron = r'^[\d\s\-\+\(\)]{8,20}$'
        return re.match(patron, telefono) is not None

    def limpiar_errores():
        campos = [nombre_field, edad_field, genero_dropdown, telefono_field, 
                 email_field, peso_field, altura_field]
        for campo in campos:
            campo.error_text = ""
        page.update()

    def validar_formulario():
        print("🔍 Iniciando validación del formulario...")
        limpiar_errores()
        es_valido = True

        # Validar nombre
        if not nombre_field.value or len(nombre_field.value.strip()) < 2:
            nombre_field.error_text = "El nombre debe tener al menos 2 caracteres"
            es_valido = False
            print("❌ Nombre inválido")

        # Validar edad
        try:
            edad = int(edad_field.value)
            if edad < 1 or edad > 120:
                edad_field.error_text = "La edad debe estar entre 1 y 120 años"
                es_valido = False
                print("❌ Edad fuera de rango")
        except (ValueError, TypeError):
            edad_field.error_text = "Ingrese una edad válida"
            es_valido = False
            print("❌ Edad inválida")

        # Validar género
        if not genero_dropdown.value:
            genero_dropdown.error_text = "Seleccione un género"
            es_valido = False
            print("❌ Género no seleccionado")

        # Validar teléfono
        if not telefono_field.value or not validar_telefono(telefono_field.value):
            telefono_field.error_text = "Ingrese un número de teléfono válido (8-20 caracteres)"
            es_valido = False
            print("❌ Teléfono inválido")

        # Validar email
        if not email_field.value or not validar_email(email_field.value):
            email_field.error_text = "Ingrese un email válido"
            es_valido = False
            print("❌ Email inválido")

        # Validar peso
        try:
            peso = float(peso_field.value)
            if peso < 1 or peso > 999.99:
                peso_field.error_text = "El peso debe estar entre 1 y 999.99 kg"
                es_valido = False
                print("❌ Peso fuera de rango")
        except (ValueError, TypeError):
            peso_field.error_text = "Ingrese un peso válido (use punto para decimales)"
            es_valido = False
            print("❌ Peso inválido")

        # Validar altura
        try:
            altura = float(altura_field.value)
            if altura < 0.5 or altura > 3.0:
                altura_field.error_text = "La altura debe estar entre 0.5 y 3.0 metros"
                es_valido = False
                print("❌ Altura fuera de rango")
        except (ValueError, TypeError):
            altura_field.error_text = "Ingrese una altura válida en metros (ej: 1.75)"
            es_valido = False
            print("❌ Altura inválida")

        # Verificar si el email ya existe en la BD (solo si las validaciones básicas pasaron)
        if es_valido and email_field.value:
            if verificar_email_existe(email_field.value.strip().lower()):
                email_field.error_text = "Este email ya está registrado en la base de datos"
                es_valido = False
                print("❌ Email ya existe")

        page.update()
        print(f"📋 Validación completa. Resultado: {'✅ Válido' if es_valido else '❌ Inválido'}")
        return es_valido

    def calcular_imc(peso, altura):
        return round(peso / (altura ** 2), 2)

    def obtener_categoria_imc(imc):
        if imc < 18.5:
            return "Bajo peso", "#FF9800"
        elif 18.5 <= imc < 25:
            return "Peso normal", "#4CAF50"
        elif 25 <= imc < 30:
            return "Sobrepeso", "#FF9800"
        else:
            return "Obesidad", "#F44336"

    def registrar_paciente(_):
        print("🚀 Iniciando proceso de registro...")
        
        if not validar_formulario():
            mostrar_notificacion("Por favor corrija los errores en el formulario", "#F44336")
            return
        
        try:
            # Preparar datos del paciente
            peso = float(peso_field.value)
            altura = float(altura_field.value)
            imc = calcular_imc(peso, altura)
            categoria_imc, color_imc = obtener_categoria_imc(imc)

            # CORREGIDO: Usar el campo diagnóstico correctamente
            diagnostico = diagnostico_field.value.strip() if diagnostico_field.value else ""
            
            datos_paciente = (
                nombre_field.value.strip(),
                int(edad_field.value),
                peso,
                genero_dropdown.value,
                telefono_field.value.strip(),
                email_field.value.strip().lower(),
                altura,
                diagnostico
            )
            
            print(f"📋 Datos preparados para insertar: {datos_paciente}")
            
            # Insertar en la base de datos
            paciente_id = insertar_paciente(datos_paciente)
            
            if paciente_id:
                print(f"✅ Paciente registrado exitosamente con ID: {paciente_id}")
                
                mostrar_notificacion(f"¡Registro exitoso! ID: {paciente_id}", "#4CAF50")
                page.clean()
                #main_estudio(page)

            else:
                print("❌ No se pudo obtener ID del paciente insertado")
                mostrar_notificacion("Error: No se pudo completar el registro", "#F44336")
            
        except Exception as e:
            print(f"❌ Excepción durante el registro: {e}")
            mostrar_notificacion(f"Error al registrar paciente: {str(e)}", "#F44336")

    def limpiar_formulario():
        print("🧹 Limpiando formulario...")
        campos = [nombre_field, edad_field, telefono_field, email_field, 
                 peso_field, altura_field, diagnostico_field]
        for campo in campos:
            campo.value = ""
            campo.error_text = ""
        
        genero_dropdown.value = None
        genero_dropdown.error_text = ""
        
        info_paciente.visible = False
        card.visible = True
        page.update()

    def probar_conexion(_):
        print("🔄 Probando conexión manualmente...")
        verificar_conexion_inicial()

    # Botones del formulario
    botones = ft.Row([
        ft.ElevatedButton(
            "Registrar Paciente",
            on_click=registrar_paciente,
            bgcolor="#1976D2",
            color="white",
            width=180,
            height=40
        ),
        ft.TextButton(
            "Limpiar",
            on_click=lambda _: limpiar_formulario(),
            width=100
        ),
        ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Probar conexión",
            on_click=probar_conexion
        )
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    # Card principal del formulario
    card = ft.Container(
        content=ft.Column(
            [
                estado_conexion,
                ft.Icon(ft.Icons.LOCAL_HOSPITAL, size=40, color="#1976D2"),
                ft.Text("Registro de Pacientes", size=28, weight=ft.FontWeight.BOLD, color="#1976D2"),
                ft.Text("Sistema de Gestión Médica", size=14, color="#666", italic=True),
                ft.Divider(height=2, color="#E0E0E0"),
                
                # Información personal
                ft.Text("Información Personal", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                nombre_field,
                ft.Row([edad_field, genero_dropdown], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                # Contacto
                ft.Text("Información de Contacto", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                telefono_field,
                email_field,
                
                # Información física
                ft.Text("Información Física", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                ft.Row([peso_field, altura_field], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                # AGREGADO: Campo diagnóstico en el formulario
                ft.Text("Información Médica (Opcional)", size=16, weight=ft.FontWeight.BOLD, color="#424242"),
                diagnostico_field,
                
                ft.Divider(height=2, color="#E0E0E0"),
                botones,
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=30,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color="#BDBDBD", offset=ft.Offset(0, 4)),
        width=450,
        alignment=ft.alignment.center,
    )

    # Verificar conexión inicial
    verificar_conexion_inicial()

    # Agregar elementos a la página
    page.add(card, info_paciente)

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8080)