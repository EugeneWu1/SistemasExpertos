import sys
import socket
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTextEdit, QFrame, QSplitter)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
import google.generativeai as genai
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusWorker(QThread):
    connection_status = pyqtSignal(bool)
    error_message = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.client = None
        self.running = False

    def run(self):
        try:
            self.client = ModbusTcpClient(self.host, port=self.port)
            connection = self.client.connect()
            if connection:
                self.connection_status.emit(True)
                self.running = True
                while self.running:
                    self.msleep(1000)
            else:
                self.connection_status.emit(False)
                self.error_message.emit("Conexión fallida")
        except Exception as e:
            self.connection_status.emit(False)
            self.error_message.emit(f"Error: {str(e)}")

    def stop(self):
        self.running = False
        if self.client:
            self.client.close()
        self.quit()
        self.wait()

class FactoryIOController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Factory I/O Controller")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #333333;
            }
        """)

        self.modbus_client = None
        self.worker_thread = None
        self.is_connected = False

        self.host = "127.0.0.1"
        self.port = 502
        self.motor_address = 0
        self.sensor_address = 1

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # HEADER - Estado de conexión centralizado
        header_widget = self.create_header_widget()
        main_layout.addWidget(header_widget)

        # Línea separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ecf0f1; max-height: 1px;")
        main_layout.addWidget(separator)

        # CONTENIDO PRINCIPAL - Dos módulos
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ecf0f1;
                width: 2px;
            }
        """)

        # MÓDULO IZQUIERDO - Factory I/O
        factory_module = self.create_factory_module()
        content_splitter.addWidget(factory_module)

        # MÓDULO DERECHO - IA
        ia_module = self.create_ia_module()
        content_splitter.addWidget(ia_module)

        # Establecer proporciones iguales
        content_splitter.setSizes([450, 450])
        
        main_layout.addWidget(content_splitter)

    def create_header_widget(self):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(10)

        # Título principal
        title = QLabel("Factory I/O Controller")
        title.setFont(QFont("Arial", 20, QFont.Light))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        header_layout.addWidget(title)

        # Estado de conexión
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_indicator.setStyleSheet("color: #e74c3c;")
        
        self.status_text = QLabel("Desconectado")
        self.status_text.setFont(QFont("Arial", 14, QFont.Medium))
        self.status_text.setStyleSheet("color: #7f8c8d; margin-left: 8px;")

        status_layout.addStretch()
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        header_layout.addWidget(status_widget)
        return header_widget

    def create_factory_module(self):
        factory_widget = QWidget()
        factory_layout = QVBoxLayout(factory_widget)
        factory_layout.setContentsMargins(15, 15, 15, 15)
        factory_layout.setSpacing(20)

        # Título del módulo
        module_title = QLabel("Factory I/O")
        module_title.setFont(QFont("Arial", 16, QFont.Medium))
        module_title.setStyleSheet("color: #34495e; margin-bottom: 10px;")
        factory_layout.addWidget(module_title)

        # Configuración de conexión
        connection_section = QWidget()
        connection_layout = QVBoxLayout(connection_section)
        connection_layout.setSpacing(12)

        conn_label = QLabel("Conexión")
        conn_label.setFont(QFont("Arial", 12, QFont.Medium))
        conn_label.setStyleSheet("color: #7f8c8d;")
        connection_layout.addWidget(conn_label)

        # Inputs de conexión
        connection_inputs = QHBoxLayout()
        
        self.ip_input = QLineEdit(self.host)
        self.ip_input.setPlaceholderText("IP Address")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)

        self.port_input = QLineEdit(str(self.port))
        self.port_input.setPlaceholderText("Puerto")
        self.port_input.setMaximumWidth(80)
        self.port_input.setStyleSheet(self.ip_input.styleSheet())

        connection_inputs.addWidget(self.ip_input)
        connection_inputs.addWidget(self.port_input)
        connection_layout.addLayout(connection_inputs)

        # Botón conectar
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.btn_connect.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.btn_connect)

        factory_layout.addWidget(connection_section)

        # Separador
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background-color: #ecf0f1; max-height: 1px;")
        factory_layout.addWidget(sep1)

        # Control del motor
        motor_section = QWidget()
        motor_layout = QVBoxLayout(motor_section)
        motor_layout.setSpacing(15)

        motor_label = QLabel("Control del Motor")
        motor_label.setFont(QFont("Arial", 12, QFont.Medium))
        motor_label.setStyleSheet("color: #7f8c8d;")
        motor_layout.addWidget(motor_label)

        # Botones de control
        motor_buttons = QHBoxLayout()
        
        self.btn_on = QPushButton("ON")
        self.btn_on.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 18px;
                font-size: 16px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_on.clicked.connect(self.turn_on_motor)
        self.btn_on.setEnabled(False)

        self.btn_off = QPushButton("OFF")
        self.btn_off.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 18px;
                font-size: 16px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_off.clicked.connect(self.turn_off_motor)
        self.btn_off.setEnabled(False)

        motor_buttons.addWidget(self.btn_on)
        motor_buttons.addWidget(self.btn_off)
        motor_layout.addLayout(motor_buttons)

        # Estado del motor
        self.motor_status = QLabel("Motor: OFF")
        self.motor_status.setFont(QFont("Arial", 13))
        self.motor_status.setAlignment(Qt.AlignCenter)
        self.motor_status.setStyleSheet("color: #7f8c8d; margin: 10px 0;")
        motor_layout.addWidget(self.motor_status)

        factory_layout.addWidget(motor_section)

        # Log de actividades
        log_label = QLabel("Log de Actividades")
        log_label.setFont(QFont("Arial", 12, QFont.Medium))
        log_label.setStyleSheet("color: #7f8c8d;")
        factory_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #f8f9fa;
                color: #7f8c8d;
            }
        """)
        factory_layout.addWidget(self.log_text)

        factory_layout.addStretch()
        return factory_widget

    def create_ia_module(self):
        ia_widget = QWidget()
        ia_layout = QVBoxLayout(ia_widget)
        ia_layout.setContentsMargins(15, 15, 15, 15)
        ia_layout.setSpacing(20)

        # Título del módulo
        module_title = QLabel("Consulta IA")
        module_title.setFont(QFont("Arial", 16, QFont.Medium))
        module_title.setStyleSheet("color: #34495e; margin-bottom: 10px;")
        ia_layout.addWidget(module_title)

        # Chat section
        chat_label = QLabel("Asistente Virtual")
        chat_label.setFont(QFont("Arial", 12, QFont.Medium))
        chat_label.setStyleSheet("color: #7f8c8d;")
        ia_layout.addWidget(chat_label)

        # Input para prompt
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Escribe tu pregunta aquí...")
        self.prompt_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #9b59b6;
                outline: none;
            }
        """)

        # Botón enviar
        self.btn_send_prompt = QPushButton("Enviar")
        self.btn_send_prompt.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.btn_send_prompt.clicked.connect(self.send_prompt_to_ai)

        ia_layout.addWidget(self.prompt_input)
        ia_layout.addWidget(self.btn_send_prompt)

        # Área de respuesta
        response_label = QLabel("Respuestas")
        response_label.setFont(QFont("Arial", 12, QFont.Medium))
        response_label.setStyleSheet("color: #7f8c8d; margin-top: 15px;")
        ia_layout.addWidget(response_label)

        self.ia_response_text = QTextEdit()
        self.ia_response_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                background-color: #f8f9fa;
                color: #2c3e50;
                line-height: 1.4;
            }
        """)
        ia_layout.addWidget(self.ia_response_text)

        # Botón limpiar chat
        clear_btn = QPushButton("Limpiar Chat")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #bdc3c7;
            }
        """)
        clear_btn.clicked.connect(lambda: self.ia_response_text.clear())
        ia_layout.addWidget(clear_btn)

        return ia_widget

    def setup_timer(self):
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(5000)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_factory_io()
        else:
            self.disconnect_from_factory_io()

    def connect_to_factory_io(self):
        try:
            self.host = self.ip_input.text()
            self.port = int(self.port_input.text())

            self.worker_thread = ModbusWorker(self.host, self.port)
            self.worker_thread.connection_status.connect(self.on_connection_status)
            self.worker_thread.error_message.connect(self.on_connection_error)
            self.worker_thread.start()

            self.btn_connect.setText("Conectando...")
            self.btn_connect.setEnabled(False)

        except ValueError:
            self.log_message("Puerto inválido")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")

    def on_connection_status(self, connected):
        self.is_connected = connected
        if connected:
            self.status_indicator.setStyleSheet("color: #27ae60;")
            self.status_text.setText("Conectado")
            self.status_text.setStyleSheet("color: #27ae60; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("Desconectar")
            self.btn_on.setEnabled(True)
            self.btn_off.setEnabled(True)
            self.log_message("Conectado exitosamente")
            self.modbus_client = self.worker_thread.client
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c;")
            self.status_text.setText("Desconectado")
            self.status_text.setStyleSheet("color: #e74c3c; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("Conectar")
            self.btn_on.setEnabled(False)
            self.btn_off.setEnabled(False)
            self.log_message("Desconectado")

        self.btn_connect.setEnabled(True)

    def on_connection_error(self, error_msg):
        self.log_message(f"Error: {error_msg}")
        self.btn_connect.setText("Conectar")
        self.btn_connect.setEnabled(True)

    def disconnect_from_factory_io(self):
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread = None
        self.is_connected = False
        self.modbus_client = None

    def turn_on_motor(self):
        if self.is_connected and self.modbus_client:
            try:
                result = self.modbus_client.write_coil(self.motor_address, True)
                if not result.isError():
                    self.motor_status.setText("Motor: ON")
                    self.motor_status.setStyleSheet("color: #27ae60; font-weight: 600;")
                    self.log_message("Motor encendido")
                else:
                    self.log_message("Error al encender motor")
            except Exception as e:
                self.log_message(f"Error: {str(e)}")

    def turn_off_motor(self):
        if self.is_connected and self.modbus_client:
            try:
                result = self.modbus_client.write_coil(self.motor_address, False)
                if not result.isError():
                    self.motor_status.setText("Motor: OFF")
                    self.motor_status.setStyleSheet("color: #e74c3c; font-weight: 600;")
                    self.log_message("Motor apagado")
                else:
                    self.log_message("Error al apagar motor")
            except Exception as e:
                self.log_message(f"Error: {str(e)}")

    def check_connection(self):
        if self.is_connected and self.modbus_client:
            try:
                result = self.modbus_client.read_coils(self.motor_address)
                if result.isError():
                    self.log_message("Conexión inestable")
            except:
                self.log_message("Problema de conexión")

    def send_prompt_to_ai(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            return
        
        self.prompt_input.clear()
        self.ia_response_text.append(f"🤔 {prompt}")
        
        try:
            API_KEY = "AIzaSyB4hptdAfmMwWHRgm6bNLTpu5uKAFyecV8"
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            response = model.generate_content(prompt)
            self.ia_response_text.append(f"🤖 {response.text}\n")
        except Exception as e:
            self.ia_response_text.append(f"❌ Error: {str(e)}\n")

    def log_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        if self.worker_thread:
            self.worker_thread.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = FactoryIOController()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
