# Alarm core engine 
import sqlite3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger("CORE")

class AlarmCore:
    def __init__(self, db_name='alarm_core.db'):
        self.db_name = db_name
        self.connection = None
        self._initialize_db()  # Cambié el nombre a inglés para consistencia
        
    def _initialize_db(self):
        """Initialize the database and create necessary tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_name)
            cursor = self.connection.cursor()
            
            # Tabla de módulos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de alarmas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_id INTEGER,
                    alarm_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT 0,
                    FOREIGN KEY(module_id) REFERENCES modules(id)
                )
            ''')
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logging.info("Database initialized successfully.")
            
            # Crear usuario admin por defecto si no existe
            self._create_default_admin()
            
        except sqlite3.Error as e:
            logging.error(f"Database initialization failed: {e}")
            raise
    
    def _create_default_admin(self):
        """Create default admin user if no users exist."""
        cursor = self.connection.cursor()
        
        # Verificar si ya hay usuarios
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Crear usuario admin por defecto
            # ¡EN PRODUCCIÓN DEBES USAR HASH PARA LAS CONTRASEÑAS!
            default_password = "admin123"  # Cambia esto
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', ('admin', default_password, 'administrator'))
            
            self.connection.commit()
            logging.info("Default admin user created.")
    
    # ===== MÉTODOS PARA USUARIOS =====
    
    def insert_user(self, username, password, role='operator'):
        """Insert a new user into the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', (username, password, role))
            
            self.connection.commit()
            logging.info(f"User '{username}' created with role '{role}'.")
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            logging.warning(f"Username '{username}' already exists.")
            return None
        except sqlite3.Error as e:
            logging.error(f"Failed to insert user: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate a user."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id, username, role FROM users 
                WHERE username = ? AND password = ?
            ''', (username, password))
            
            user = cursor.fetchone()
            if user:
                logging.info(f"User '{username}' authenticated successfully.")
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2]
                }
            else:
                logging.warning(f"Failed authentication attempt for user '{username}'.")
                return None
                
        except sqlite3.Error as e:
            logging.error(f"Authentication error: {e}")
            return None
    
    # ===== MÉTODOS PARA MÓDULOS =====
    
    def register_module(self, name, initial_status='inactive'):
        """Register a new module in the system."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO modules (name, status)
                VALUES (?, ?)
            ''', (name, initial_status))
            
            self.connection.commit()
            module_id = cursor.lastrowid
            logging.info(f"Module '{name}' registered with ID {module_id}.")
            return module_id
            
        except sqlite3.Error as e:
            logging.error(f"Failed to register module: {e}")
            return None
    
    def update_module_status(self, module_id, status):
        """Update the status of a module."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE modules 
                SET status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, module_id))
            
            self.connection.commit()
            if cursor.rowcount > 0:
                logging.info(f"Module {module_id} status updated to '{status}'.")
                return True
            return False
            
        except sqlite3.Error as e:
            logging.error(f"Failed to update module status: {e}")
            return False
    
    def unregister_module(self, module_id):
        """Remove a module from the system by its ID."""
        try:
            cursor = self.connection.cursor()
            
            # Primero verificamos si el módulo existe
            cursor.execute('''
                SELECT name FROM modules WHERE id = ?
            ''', (module_id,))
            
            module = cursor.fetchone()
            
            if not module:
                logging.warning(f"No module found with ID {module_id}.")
                return False
            
            # Eliminamos el módulo
            cursor.execute('''
                DELETE FROM modules WHERE id = ?
            ''', (module_id,))
            
            self.connection.commit()
            logging.info(f"Module '{module[0]}' (ID {module_id}) has been removed.")
            return True
            
        except sqlite3.Error as e:
            logging.error(f"Failed to unregister module: {e}")
            self.connection.rollback()
            return False

    def get_all_modules(self):
        """Get all registered modules as a dictionary."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM modules ORDER BY name')
            rows = cursor.fetchall()
            
            # Convertir a diccionario
            modules_dict = {}
            
            # Asumiendo que la tabla tiene: id, name, type, pin, state, description, etc.
            for row in rows:
                module_id = row[0]  # ID del módulo
                modules_dict[module_id] = {
                    "id": row[0],
                    "name": row[1],
                    "type": row[2] if len(row) > 2 else "unknown",
                    "pin": row[3] if len(row) > 3 else 0,
                    "state": row[4] if len(row) > 4 else "unknown",
                    "description": row[5] if len(row) > 5 else ""
                }
            
            return modules_dict
            
        except sqlite3.Error as e:
            logging.error(f"Failed to get modules: {e}")
            return {}
    
    # ===== MÉTODOS PARA ALARMAS =====
    
    def trigger_alarm(self, module_id, alarm_type, description=""):
        """Trigger a new alarm."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO alarms (module_id, alarm_type, description)
                VALUES (?, ?, ?)
            ''', (module_id, alarm_type, description))
            
            self.connection.commit()
            alarm_id = cursor.lastrowid
            
            # También actualizar el estado del módulo
            self.update_module_status(module_id, 'alarm')
            
            logging.warning(f"Alarm triggered: {alarm_type} on module {module_id}")
            return alarm_id
            
        except sqlite3.Error as e:
            logging.error(f"Failed to trigger alarm: {e}")
            return None
    
    def acknowledge_alarm(self, alarm_id):
        """Mark an alarm as acknowledged."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE alarms 
                SET acknowledged = 1 
                WHERE id = ?
            ''', (alarm_id,))
            
            self.connection.commit()
            if cursor.rowcount > 0:
                logging.info(f"Alarm {alarm_id} acknowledged.")
                return True
            return False
            
        except sqlite3.Error as e:
            logging.error(f"Failed to acknowledge alarm: {e}")
            return False
    
    def get_active_alarms(self):
        """Get all unacknowledged alarms."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT a.*, m.name as module_name 
                FROM alarms a
                JOIN modules m ON a.id = m.id
                WHERE a.acknowledged = 0
                ORDER BY a.timestamp DESC
            ''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Failed to get active alarms: {e}")
            return []
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")
    
    def __enter__(self):
        """Support for context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context."""
        self.close()

# ===== EJEMPLO DE USO =====
if __name__ == "__main__":
    # Crear instancia del sistema de alarmas
    alarm_system = AlarmCore()
    
    # Registrar algunos módulos
    module1_id = alarm_system.register_module("Temperature Sensor", "active")
    module2_id = alarm_system.register_module("Pressure Sensor", "active")
    module3_id = alarm_system.register_module("Camera System", "inactive")
    
    # Crear usuarios
    alarm_system.insert_user("admin", "admin123", "administrator")
    alarm_system.insert_user("operator1", "op123", "operator")
    
    # Simular alarmas
    alarm_system.trigger_alarm(module1_id, "HIGH_TEMP", "Temperature exceeded 100°C")
    alarm_system.trigger_alarm(module2_id, "LOW_PRESSURE", "Pressure below threshold")
    
    """# Obtener alarmas activas
    active_alarms = alarm_system.get_active_alarms()
    print("Active Alarms:")
    for alarm in active_alarms:
        print(f"  - {alarm[3]} on {alarm[7]} at {alarm[4]}")
    
    # Autenticar usuario
    user = alarm_system.authenticate_user("admin", "admin123")
    if user:
        print(f"\nAuthenticated: {user['username']} ({user['role']})")
    
    # Cerrar conexión"""
    alarm_system.close()