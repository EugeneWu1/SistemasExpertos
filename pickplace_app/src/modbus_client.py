import socket
import struct

class ModbusClient:
    """Cliente Modbus TCP para comunicación con FactoryIO"""
    def __init__(self, host='192.168.56.1', port=502):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False
    
    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.connected = False
    
    def read_coils(self, address, count):
        """Leer bobinas (salidas digitales)"""
        if not self.connected:
            return None
        
        try:
            # Construir mensaje Modbus TCP
            transaction_id = 1
            protocol_id = 0
            length = 6
            unit_id = 1
            function_code = 1
            
            message = struct.pack('>HHHBBHH', 
                                transaction_id, protocol_id, length, 
                                unit_id, function_code, address, count)
            
            self.socket.send(message)
            response = self.socket.recv(1024)
            
            if len(response) >= 9:
                byte_count = response[8]
                data = response[9:9+byte_count]
                
                # Convertir bytes a lista de booleanos
                coils = []
                for byte in data:
                    for i in range(8):
                        if len(coils) < count:
                            coils.append(bool(byte & (1 << i)))
                
                return coils[:count]
        except Exception as e:
            print(f"Error leyendo bobinas: {e}")
            return None
    
    def write_single_coil(self, address, value):
        """Escribir bobina individual"""
        if not self.connected:
            return False
        
        try:
            transaction_id = 1
            protocol_id = 0
            length = 6
            unit_id = 1
            function_code = 5
            coil_value = 0xFF00 if value else 0x0000
            
            message = struct.pack('>HHHBBHH', 
                                transaction_id, protocol_id, length,
                                unit_id, function_code, address, coil_value)
            
            self.socket.send(message)
            response = self.socket.recv(1024)
            return len(response) > 0
        except Exception as e:
            print(f"Error escribiendo bobina: {e}")
            return False