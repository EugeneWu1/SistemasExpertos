import sys
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pickle
import os

from modbus_client import ModbusClient
from ai_expert_system import AIExpertSystem
from advanced_config_dialog import AdvancedConfigDialog


class PickPlaceGUI(QMainWindow):
    # Señales para comunicación entre hilos
    status_update = pyqtSignal(str)
    sensor_update = pyqtSignal(dict)
    ai_prediction = pyqtSignal(str, float)
    
    def __init__(self):
        super().__init__()
        self.modbus_client = ModbusClient()
        self.ai_system = AIExpertSystem()
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Configuración de FactoryIO - Actualizada según imagen
        self.factory_config = {
            'inputs': {
                'item_at_entry': 0,     # Input 0 - Item at entry
                'item_at_exit': 1,      # Input 1 - Item at exit
                'moving_x': 2,          # Input 2 - Moving X
                'moving_z': 3,          # Input 3 - Moving Z
                'item_detected': 4,     # Input 4 - Item detected
                'start_button': 5,      # Input 5 - Start
                'reset_button': 6,      # Input 6 - Reset
                'stop_button': 7,       # Input 7 - Stop
                'emergency_stop': 8,    # Input 8 - Emergency stop
                'auto_mode': 9,         # Input 9 - Auto
                'factory_running': 10   # Input 10 - FACTORY I/O (Running)
            },
            'outputs': {
                'entry_conveyor': 0,    # Coil 0 - Entry conveyor
                'exit_conveyor': 1,     # Coil 1 - Exit conveyor
                'move_x': 2,            # Coil 2 - Move X
                'move_z': 3,            # Coil 3 - Move Z
                'grab': 4,              # Coil 4 - Grab
                'start_light': 5,       # Coil 5 - Start light
                'reset_light': 6,       # Coil 6 - Reset light
                'stop_light': 7         # Coil 7 - Stop light
            }
        }
        
        self.initUI()
        self.setup_connections()
        
    def initUI(self):
        self.setWindowTitle('Sistema Experto Pick & Place - IA + FactoryIO')
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo - Conexión y control
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Panel central - Monitor de sistema
        center_panel = self.create_monitor_panel()
        main_layout.addWidget(center_panel, 2)
        
        # Panel derecho - IA y configuración
        right_panel = self.create_ai_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Barra de estado
        self.statusBar().showMessage('Desconectado de FactoryIO')
        
        # Aplicar estilos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #666;
                padding: 8px;
                border-radius: 4px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #555;
                color: #00ff00;
                font-family: 'Courier New';
            }
            QLabel {
                color: white;
            }
        """)
    
    def create_control_panel(self):
        """Crear panel de control y conexión"""
        group = QGroupBox("Control de Conexión")
        layout = QVBoxLayout(group)
        
        # Configuración de conexión
        conn_layout = QFormLayout()
        self.host_input = QLineEdit("192.168.56.1")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(502)
        
        conn_layout.addRow("Host:", self.host_input)
        conn_layout.addRow("Puerto:", self.port_input)
        layout.addLayout(conn_layout)
        
        # Botones de conexión
        self.connect_btn = QPushButton("Conectar FactoryIO")
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setEnabled(False)
        
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)
        
        # Estado de conexión
        self.connection_status = QLabel("❌ Desconectado")
        layout.addWidget(self.connection_status)
        
        layout.addWidget(QLabel(""))  # Espaciador
        
        # Control manual
        manual_group = QGroupBox("Control Manual")
        manual_layout = QVBoxLayout(manual_group)
        
        self.manual_entry_btn = QPushButton("Entry Conveyor")
        self.manual_exit_btn = QPushButton("Exit Conveyor")
        self.manual_grab_btn = QPushButton("Grab")
        self.manual_move_x_btn = QPushButton("Move X")
        self.manual_move_z_btn = QPushButton("Move Z")
        self.manual_stop_btn = QPushButton("PARAR TODO")
        self.manual_stop_btn.setStyleSheet("background-color: #cc0000;")
        
        manual_layout.addWidget(self.manual_entry_btn)
        manual_layout.addWidget(self.manual_exit_btn)
        manual_layout.addWidget(self.manual_grab_btn)
        manual_layout.addWidget(self.manual_move_x_btn)
        manual_layout.addWidget(self.manual_move_z_btn)
        manual_layout.addWidget(self.manual_stop_btn)
        
        layout.addWidget(manual_group)
        
        # Monitor automático
        self.auto_monitor_btn = QPushButton("Iniciar Monitoreo Auto")
        self.stop_monitor_btn = QPushButton("Detener Monitoreo")
        self.stop_monitor_btn.setEnabled(False)
        
        layout.addWidget(self.auto_monitor_btn)
        layout.addWidget(self.stop_monitor_btn)
        
        return group
    
    def create_monitor_panel(self):
        """Crear panel de monitoreo del sistema"""
        group = QGroupBox("Monitor del Sistema")
        layout = QVBoxLayout(group)
        
        # Estados de sensores
        sensor_group = QGroupBox("Estados de Sensores")
        sensor_layout = QGridLayout(sensor_group)
        
        self.sensor_labels = {}
        sensors = ['Item at Entry', 'Item at Exit', 'Moving X', 'Moving Z', 'Item Detected', 
                  'Start Button', 'Reset Button', 'Stop Button', 'Emergency Stop', 'Auto Mode']
        
        for i, sensor in enumerate(sensors):
            label = QLabel(sensor + ":")
            status = QLabel("❌")
            self.sensor_labels[sensor] = status
            sensor_layout.addWidget(label, i, 0)
            sensor_layout.addWidget(status, i, 1)
        
        layout.addWidget(sensor_group)
        
        # Estados de actuadores
        actuator_group = QGroupBox("Estados de Actuadores")
        actuator_layout = QGridLayout(actuator_group)
        
        self.actuator_labels = {}
        actuators = ['Entry Conveyor', 'Exit Conveyor', 'Move X', 'Move Z', 'Grab', 
                    'Start Light', 'Reset Light', 'Stop Light']
        
        for i, actuator in enumerate(actuators):
            label = QLabel(actuator + ":")
            status = QLabel("❌")
            self.actuator_labels[actuator] = status
            actuator_layout.addWidget(label, i, 0)
            actuator_layout.addWidget(status, i, 1)
        
        layout.addWidget(actuator_group)
        
        # Log del sistema
        log_group = QGroupBox("Log del Sistema")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        clear_log_btn = QPushButton("Limpiar Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        return group
    
    def create_ai_panel(self):
        """Crear panel de IA y configuración"""
        group = QGroupBox("Consulta con IA")
        layout = QVBoxLayout(group)
        
        # Estado de IA

        


        # Configuración de IA
        ai_config_group = QGroupBox("Configuración IA")
        ai_config_layout = QVBoxLayout(ai_config_group)

        retrain_btn = QPushButton("Re-entrenar Modelo")
        retrain_btn.clicked.connect(self.retrain_ai_model)
        
        save_model_btn = QPushButton("Guardar Modelo")
        save_model_btn.clicked.connect(self.save_ai_model)
        
        load_model_btn = QPushButton("Cargar Modelo")
        load_model_btn.clicked.connect(self.load_ai_model)
        
        ai_config_layout.addWidget(retrain_btn)
        ai_config_layout.addWidget(save_model_btn)
        ai_config_layout.addWidget(load_model_btn)
        
        layout.addWidget(ai_config_group)
        
        # Parámetros del sistema
        params_group = QGroupBox("Parámetros")
        params_layout = QFormLayout(params_group)
        
        self.cycle_time_input = QSpinBox()
        self.cycle_time_input.setRange(100, 5000)
        self.cycle_time_input.setValue(500)
        self.cycle_time_input.setSuffix(" ms")
        
        self.confidence_threshold = QDoubleSpinBox()
        self.confidence_threshold.setRange(0.1, 1.0)
        self.confidence_threshold.setValue(0.7)
        self.confidence_threshold.setDecimals(2)
        
        params_layout.addRow("Tiempo de Ciclo:", self.cycle_time_input)
        params_layout.addRow("Umbral Confianza:", self.confidence_threshold)
        
        layout.addWidget(params_group)
        
        # Estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QVBoxLayout(stats_group)
        
        self.cycles_label = QLabel("Ciclos: 0")
        self.errors_label = QLabel("Errores: 0")
        self.efficiency_label = QLabel("Eficiencia: 0%")
        
        stats_layout.addWidget(self.cycles_label)
        stats_layout.addWidget(self.errors_label)
        stats_layout.addWidget(self.efficiency_label)
        
        layout.addWidget(stats_group)
        
        return group
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones de conexión
        self.connect_btn.clicked.connect(self.connect_factory)
        self.disconnect_btn.clicked.connect(self.disconnect_factory)
        
        # Botones de control manual
        self.manual_entry_btn.clicked.connect(lambda: self.manual_control('entry_conveyor', True))
        self.manual_exit_btn.clicked.connect(lambda: self.manual_control('exit_conveyor', True))
        self.manual_grab_btn.clicked.connect(lambda: self.manual_control('grab', True))
        self.manual_move_x_btn.clicked.connect(lambda: self.manual_control('move_x', True))
        self.manual_move_z_btn.clicked.connect(lambda: self.manual_control('move_z', True))
        self.manual_stop_btn.clicked.connect(self.emergency_stop)
        
        # Monitoreo automático
        self.auto_monitor_btn.clicked.connect(self.start_monitoring)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        
        # Señales internas
        self.status_update.connect(self.update_status)
        self.sensor_update.connect(self.update_sensor_display)
        self.ai_prediction.connect(self.update_ai_display)
    
    def connect_factory(self):
        """Conectar a FactoryIO"""
        host = self.host_input.text()
        port = self.port_input.value()
        
        self.modbus_client.host = host
        self.modbus_client.port = port
        
        if self.modbus_client.connect():
            self.connection_status.setText("✅ Conectado")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.statusBar().showMessage(f'Conectado a FactoryIO - {host}:{port}')
            self.log_message("Conectado a FactoryIO exitosamente")
        else:
            self.connection_status.setText("❌ Error de conexión")
            self.log_message("Error: No se pudo conectar a FactoryIO")
    
    def disconnect_factory(self):
        """Desconectar de FactoryIO"""
        if self.is_monitoring:
            self.stop_monitoring()
        
        self.modbus_client.disconnect()
        self.connection_status.setText("❌ Desconectado")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.statusBar().showMessage('Desconectado de FactoryIO')
        self.log_message("Desconectado de FactoryIO")
    
    def manual_control(self, actuator, state):
        """Control manual de actuadores"""
        if not self.modbus_client.connected:
            self.log_message("Error: No conectado a FactoryIO")
            return
        
        address_map = {
            'entry_conveyor': self.factory_config['outputs']['entry_conveyor'],
            'exit_conveyor': self.factory_config['outputs']['exit_conveyor'],
            'move_x': self.factory_config['outputs']['move_x'],
            'move_z': self.factory_config['outputs']['move_z'],
            'grab': self.factory_config['outputs']['grab']
        }
        
        if actuator in address_map:
            address = address_map[actuator]
            if self.modbus_client.write_single_coil(address, state):
                self.log_message(f"Control manual: {actuator} = {state}")
            else:
                self.log_message(f"Error en control manual: {actuator}")
    
    def emergency_stop(self):
        """Parada de emergencia"""
        if not self.modbus_client.connected:
            return
        
        # Desactivar todos los actuadores
        for output in self.factory_config['outputs'].values():
            self.modbus_client.write_single_coil(output, False)
        
        self.log_message("PARADA DE EMERGENCIA ACTIVADA")
    
    def start_monitoring(self):
        """Iniciar monitoreo automático"""
        if not self.modbus_client.connected:
            self.log_message("Error: No conectado a FactoryIO")
            return
        
        self.is_monitoring = True
        self.auto_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
        
        # Iniciar hilo de monitoreo
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.log_message("Monitoreo automático iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo automático"""
        self.is_monitoring = False
        self.auto_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)
        self.log_message("Monitoreo automático detenido")
    
    def monitoring_loop(self):
        """Bucle principal de monitoreo"""
        cycle_count = 0
        error_count = 0
        
        while self.is_monitoring:
            try:
                # Leer sensores
                sensors = self.read_all_sensors()
                if sensors is None:
                    error_count += 1
                    time.sleep(0.1)
                    continue
                
                # Actualizar display
                self.sensor_update.emit(sensors)
                
                # Preparar datos para IA - Actualizados para Pick and Place
                sensor_data = [
                    int(sensors['item_at_entry']),
                    int(sensors['item_detected']),
                    int(sensors['moving_x']),
                    int(sensors['moving_z']),
                    int(sensors['item_at_exit'])
                ]
                
                # Obtener predicción de IA
                action, confidence = self.ai_system.predict_action(sensor_data)
                action_name = self.ai_system.get_action_name(action)
                
                # Actualizar display de IA
                self.ai_prediction.emit(action_name, confidence)
                
                # Ejecutar acción si la confianza es suficiente
                if confidence >= self.confidence_threshold.value():
                    self.execute_ai_action(action, sensors)
                
                cycle_count += 1
                
                # Actualizar estadísticas
                if cycle_count > 0:
                    efficiency = ((cycle_count - error_count) / cycle_count) * 100
                    self.cycles_label.setText(f"Ciclos: {cycle_count}")
                    self.errors_label.setText(f"Errores: {error_count}")
                    self.efficiency_label.setText(f"Eficiencia: {efficiency:.1f}%")
                
                # Esperar antes del siguiente ciclo
                time.sleep(self.cycle_time_input.value() / 1000.0)
                
            except Exception as e:
                error_count += 1
                self.log_message(f"Error en monitoreo: {e}")
                time.sleep(0.5)
    
    def read_all_sensors(self):
        """Leer todos los sensores"""
        try:
            # Leer primeras 11 bobinas (sensores)
            coils = self.modbus_client.read_coils(0, 11)
            if coils is None:
                return None
            
            sensors = {
                'item_at_entry': coils[0] if len(coils) > 0 else False,
                'item_at_exit': coils[1] if len(coils) > 1 else False,
                'moving_x': coils[2] if len(coils) > 2 else False,
                'moving_z': coils[3] if len(coils) > 3 else False,
                'item_detected': coils[4] if len(coils) > 4 else False,
                'start_button': coils[5] if len(coils) > 5 else False,
                'reset_button': coils[6] if len(coils) > 6 else False,
                'stop_button': coils[7] if len(coils) > 7 else False,
                'emergency_stop': coils[8] if len(coils) > 8 else False,
                'auto_mode': coils[9] if len(coils) > 9 else False,
                'factory_running': coils[10] if len(coils) > 10 else False
            }
            
            return sensors
        except Exception as e:
            self.log_message(f"Error leyendo sensores: {e}")
            return None
    
    def execute_ai_action(self, action, sensors):
        """Ejecutar acción recomendada por IA"""
        try:
            if action == 1:  # PICK/GRAB
                if sensors['item_detected'] and not sensors['moving_x']:
                    self.modbus_client.write_single_coil(
                        self.factory_config['outputs']['grab'], True)
                    self.log_message("IA: Ejecutando GRAB")
                    
            elif action == 2:  # MOVE_X
                if sensors['item_detected']:
                    self.modbus_client.write_single_coil(
                        self.factory_config['outputs']['move_x'], True)
                    self.log_message("IA: Ejecutando MOVE_X")
                    
            elif action == 3:  # PLACE/RELEASE
                if sensors['moving_x'] and sensors['item_at_exit']:
                    self.modbus_client.write_single_coil(
                        self.factory_config['outputs']['grab'], False)
                    self.log_message("IA: Ejecutando PLACE/RELEASE")
                    
            elif action == 4:  # START_CONVEYORS
                self.modbus_client.write_single_coil(
                    self.factory_config['outputs']['entry_conveyor'], True)
                self.modbus_client.write_single_coil(
                    self.factory_config['outputs']['exit_conveyor'], True)
                self.log_message("IA: Iniciando transportadores")
                    
            elif action == 0:  # IDLE
                # Mantener estado actual o desactivar movimientos no necesarios
                pass
                    
            elif action == 5:  # ERROR
                self.log_message("IA: Estado de ERROR detectado")
                self.emergency_stop()
                
        except Exception as e:
            self.log_message(f"Error ejecutando acción IA: {e}")
    
    def update_sensor_display(self, sensors):
        """Actualizar display de sensores"""
        status_map = {
            'Item at Entry': sensors.get('item_at_entry', False),
            'Item at Exit': sensors.get('item_at_exit', False),
            'Moving X': sensors.get('moving_x', False),
            'Moving Z': sensors.get('moving_z', False),
            'Item Detected': sensors.get('item_detected', False),
            'Start Button': sensors.get('start_button', False),
            'Reset Button': sensors.get('reset_button', False),
            'Stop Button': sensors.get('stop_button', False),
            'Emergency Stop': sensors.get('emergency_stop', False),
            'Auto Mode': sensors.get('auto_mode', False)
        }
        
        for sensor, status in status_map.items():
            if sensor in self.sensor_labels:
                self.sensor_labels[sensor].setText("✅" if status else "❌")
    
    def update_ai_display(self, prediction, confidence):
        """Actualizar display de IA"""
        self.ai_prediction_label.setText(f"Predicción: {prediction}")
        self.ai_confidence_label.setText(f"Confianza: {confidence*100:.1f}%")
    
    def update_status(self, message):
        """Actualizar barra de estado"""
        self.statusBar().showMessage(message)
    
    def log_message(self, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Mantener solo las últimas 100 líneas
        document = self.log_text.document()
        if document.blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def retrain_ai_model(self):
        """Re-entrenar modelo de IA"""
        if self.ai_system.train_model():
            self.log_message("Modelo de IA re-entrenado exitosamente")
            self.ai_status_label.setText("✅ Modelo Re-entrenado")
        else:
            self.log_message("Error re-entrenando modelo de IA")
            self.ai_status_label.setText("❌ Error en Entrenamiento")
    
    def save_ai_model(self):
        """Guardar modelo de IA"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Modelo IA", "ai_model.pkl", "Pickle Files (*.pkl)")
        
        if filename:
            try:
                model_data = {
                    'decision_tree': self.ai_system.decision_tree,
                    'random_forest': self.ai_system.random_forest,
                    'training_data': self.ai_system.training_data,
                    'is_trained': self.ai_system.is_trained
                }
                
                with open(filename, 'wb') as f:
                    pickle.dump(model_data, f)
                
                self.log_message(f"Modelo guardado: {filename}")
            except Exception as e:
                self.log_message(f"Error guardando modelo: {e}")
    
    def load_ai_model(self):
        """Cargar modelo de IA"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Cargar Modelo IA", "", "Pickle Files (*.pkl)")
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.ai_system.decision_tree = model_data['decision_tree']
                self.ai_system.random_forest = model_data['random_forest']
                self.ai_system.training_data = model_data['training_data']
                self.ai_system.is_trained = model_data['is_trained']
                
                self.ai_status_label.setText("✅ Modelo Cargado")
                self.log_message(f"Modelo cargado: {filename}")
            except Exception as e:
                self.log_message(f"Error cargando modelo: {e}")
                self.ai_status_label.setText("❌ Error Cargando")
    
    def closeEvent(self, event):
        """Manejar cierre de aplicación"""
        if self.is_monitoring:
            self.stop_monitoring()
        
        if self.modbus_client.connected:
            self.modbus_client.disconnect()
        
        event.accept()