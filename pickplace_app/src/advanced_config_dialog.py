from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QFormLayout, QSpinBox, QHBoxLayout, QPushButton

class AdvancedConfigDialog(QDialog):
    """Diálogo de configuración avanzada"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Avanzada")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Configuración Modbus
        modbus_group = QGroupBox("Configuración Modbus")
        modbus_layout = QFormLayout(modbus_group)
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 30)
        self.timeout_input.setValue(5)
        self.timeout_input.setSuffix(" seg")
        
        self.retry_input = QSpinBox()
        self.retry_input.setRange(1, 10)
        self.retry_input.setValue(3)
        
        modbus_layout.addRow("Timeout:", self.timeout_input)
        modbus_layout.addRow("Reintentos:", self.retry_input)
        
        layout.addWidget(modbus_group)
        
        # Configuración IA
        ai_group = QGroupBox("Configuración IA")
        ai_layout = QFormLayout(ai_group)
        
        self.n_estimators_input = QSpinBox()
        self.n_estimators_input.setRange(10, 500)
        self.n_estimators_input.setValue(100)
        
        self.max_depth_input = QSpinBox()
        self.max_depth_input.setRange(1, 20)
        self.max_depth_input.setValue(10)
        
        ai_layout.addRow("N° Estimadores:", self.n_estimators_input)
        ai_layout.addRow("Profundidad Máx:", self.max_depth_input)
        
        layout.addWidget(ai_group)
        
        # Botones
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Aceptar")
        cancel_btn = QPushButton("Cancelar")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)