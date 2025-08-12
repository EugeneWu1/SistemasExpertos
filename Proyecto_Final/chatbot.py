import flet as ft
import requests
import json

class TelegramNodeRedApp:
    def __init__(self):
        self.page = None
        self.node_red_url = "http://127.0.0.1:1880/telegram-message"  # Cambia el puerto si es diferente
        self.message_input = None
        self.phone_input = None
        self.status_text = None
        
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Enviar Mensaje Telegram"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 500
        page.window_height = 400
        page.window_resizable = False
        page.padding = 20
        
        # Campo para el número de teléfono
        self.phone_input = ft.TextField(
            label="Número de Teléfono",
            hint_text="Ejemplo: +1234567890 o @username",
            width=450,
            border_color=ft.Colors.BLUE_400
        )
        
        # Campo para el mensaje
        self.message_input = ft.TextField(
            label="Mensaje",
            hint_text="Escribe tu mensaje aquí...",
            multiline=True,
            min_lines=4,
            max_lines=6,
            width=450,
            border_color=ft.Colors.GREEN_400
        )
        
        # Botón de envío
        send_button = ft.ElevatedButton(
            text="Enviar Mensaje",
            on_click=self.send_message,
            width=200,
            height=50,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        
        # Texto de estado
        self.status_text = ft.Text(
            value="Listo para enviar mensajes",
            color=ft.Colors.GREEN_600,
            size=14,
            weight=ft.FontWeight.BOLD
        )
        
        # Layout de la aplicación
        page.add(
            ft.Column([
                ft.Container(
                    content=ft.Text(
                        "Enviar Mensaje a Telegram",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=30)
                ),
                
                self.phone_input,
                
                self.message_input,
                
                ft.Container(
                    content=send_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20, bottom=20)
                ),
                
                self.status_text
                
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
    def send_message(self, e):
        """Envía el mensaje a través de Node-RED"""
        try:
            # Validar campos
            if not self.message_input.value or not self.message_input.value.strip():
                self.show_error("Por favor, ingresa un mensaje")
                return
                
            if not self.phone_input.value or not self.phone_input.value.strip():
                self.show_error("Por favor, ingresa el número de teléfono")
                return
            
            # Actualizar estado
            self.status_text.value = "Enviando mensaje..."
            self.status_text.color = ft.Colors.ORANGE_600
            self.page.update()
            
            # Preparar datos para Node-RED
            payload = {
                "chat_id": self.phone_input.value.strip(),  # Cambié a chat_id para mantener consistencia
                "message": self.message_input.value.strip()
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Realizar petición HTTP
            response = requests.post(
                self.node_red_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Procesar respuesta
            if response.status_code == 200:
                self.show_success("Mensaje enviado correctamente")
                # Limpiar el campo de mensaje
                self.message_input.value = ""
                self.page.update()
            else:
                self.show_error(f"Error al enviar mensaje: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.show_error("Error de conexión. Verifica que Node-RED esté ejecutándose")
        except requests.exceptions.Timeout:
            self.show_error("Tiempo de espera agotado")
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
    
    def show_success(self, message):
        """Muestra mensaje de éxito"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.GREEN_600
        self.page.update()
        
    def show_error(self, message):
        """Muestra mensaje de error"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_600
        self.page.update()

# Función principal para ejecutar la aplicación
def run_app():
    app = TelegramNodeRedApp()
    ft.app(target=app.main)

if __name__ == "__main__":
    run_app()
