from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

class AIExpertSystem:
    """Sistema experto con IA para Pick and Place"""
    
    def __init__(self):
        self.model = None
        self.training_data = []
        self.is_trained = False
        self.decision_tree = DecisionTreeClassifier(random_state=42)
        self.random_forest = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Estados del sistema
        self.system_states = {
            'IDLE': 0,
            'DETECTING': 1,
            'PICKING': 2,
            'MOVING': 3,
            'PLACING': 4,
            'ERROR': 5
        }
        
        # Patrones de decisión predefinidos
        self.load_default_patterns()
        
    def load_default_patterns(self):
        """Cargar patrones por defecto para el sistema experto"""
        # Datos de entrenamiento sintéticos para Pick and Place
        # [item_at_entry, item_detected, moving_x, moving_z, item_at_exit] -> [action]
        self.training_data = [
            [1, 1, 0, 0, 0, 1],  # Pieza en entrada detectada -> Grab
            [1, 1, 1, 0, 0, 2],  # Pieza agarrada -> Move X
            [0, 1, 1, 0, 1, 3],  # Pieza en salida -> Release/Place
            [1, 0, 0, 0, 0, 4],  # Pieza en entrada sin detectar -> Start conveyors
            [0, 0, 0, 0, 0, 0],  # No hay actividad -> Idle
            [1, 1, 1, 1, 0, 0],  # Múltiples movimientos -> Wait/Idle
            [0, 1, 0, 1, 1, 5],  # Estado inconsistente -> Error
        ]
        
        self.train_model()
    
    def train_model(self):
        """Entrenar el modelo de IA"""
        if len(self.training_data) < 3:
            return False
        
        X = [row[:-1] for row in self.training_data]  # Features
        y = [row[-1] for row in self.training_data]   # Labels
        
        try:
            self.decision_tree.fit(X, y)
            self.random_forest.fit(X, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error entrenando modelo: {e}")
            return False
    
    def predict_action(self, sensor_data):
        """Predecir acción basada en datos de sensores"""
        if not self.is_trained:
            return 0
        
        try:
            # Usar Random Forest como modelo principal
            prediction = self.random_forest.predict([sensor_data])[0]
            confidence = max(self.random_forest.predict_proba([sensor_data])[0])
            
            return int(prediction), float(confidence)
        except Exception as e:
            print(f"Error en predicción: {e}")
            return 0, 0.0
    
    def add_training_sample(self, features, action):
        """Agregar nueva muestra de entrenamiento"""
        sample = features + [action]
        self.training_data.append(sample)
        
        # Re-entrenar si hay suficientes datos
        if len(self.training_data) % 5 == 0:
            self.train_model()
    
    def get_action_name(self, action_code):
        """Obtener nombre de acción"""
        actions = {
            0: "IDLE",
            1: "GRAB",
            2: "MOVE_X",
            3: "RELEASE",
            4: "START_CONVEYORS",
            5: "ERROR"
        }
        return actions.get(action_code, "UNKNOWN")
