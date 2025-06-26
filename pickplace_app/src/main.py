import sys
from PyQt5.QtWidgets import QApplication, QAction, QMessageBox

from advanced_config_dialog import AdvancedConfigDialog
from pickplace_gui import PickPlaceGUI

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de aplicación
    app.setStyle('Fusion')
    
    # Crear ventana principal
    window = PickPlaceGUI()
    window.show()
    
    # Agregar menú
    menubar = window.menuBar()
    
    # Menú Archivo
    file_menu = menubar.addMenu('Archivo')
    
    save_config_action = QAction('Guardar Configuración', window)
    load_config_action = QAction('Cargar Configuración', window)
    exit_action = QAction('Salir', window)
    exit_action.triggered.connect(window.close)
    
    file_menu.addAction(save_config_action)
    file_menu.addAction(load_config_action)
    file_menu.addSeparator()
    file_menu.addAction(exit_action)
    
    # Menú Herramientas
    tools_menu = menubar.addMenu('Herramientas')
    
    advanced_config_action = QAction('Configuración Avanzada', window)
    advanced_config_action.triggered.connect(
        lambda: AdvancedConfigDialog(window).exec_())
    
    calibrate_action = QAction('Calibrar Sistema', window)
    test_connection_action = QAction('Probar Conexión', window)
    
    tools_menu.addAction(advanced_config_action)
    tools_menu.addAction(calibrate_action)
    tools_menu.addAction(test_connection_action)
    
    # Menú Ayuda
    help_menu = menubar.addMenu('Ayuda')
    
    about_action = QAction('Acerca de', window)
    help_action = QAction('Ayuda', window)
    
    def show_about():
        QMessageBox.about(window, "Acerca de", 
            "Sistema Experto Pick & Place\n"
            "Integración IA + FactoryIO\n"
            "Versión 1.0\n\n"
            "Desarrollado con PyQt5, scikit-learn\n"
            "y comunicación Modbus TCP")
    
    about_action.triggered.connect(show_about)
    
    help_menu.addAction(help_action)
    help_menu.addAction(about_action)
    
    # Ejecutar aplicación
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()