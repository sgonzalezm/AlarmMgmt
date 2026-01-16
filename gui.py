import logging
import tkinter as tk 
from tkinter import ttk
from datetime import datetime
import json
import os
from tkinter import messagebox
from tkinter import simpledialog
from core import AlarmCore  # Importa el módulo core.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("GUI")

class AlarmSystemGUI(tk.Tk):
    # Initialization
    def __init__(self):
        super().__init__() # Inicializa la clase padre

        self.title("Alarm System GUI")
        self.geometry("800x600")

        self.nucleo_alarma = AlarmCore()  # Instancia del núcleo de la alarma

        # Alarm states
        self.active_alarm = False
        self.quiet_mode = False
        self.active_conn = True
        
        # Sensor states
        self.sensor_states = self.nucleo_alarma.get_all_modules()
        

        # Config file path
        self.config_file = "alarm_config.json"
        self.system_config = {}  # Cambia el nombre para evitar conflicto
        self.load_config()

        # GUI Elements
        self.setup_interface()

        # Safe close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        config_default = {
            "telegram_token": "",
            "telegram_chat_id": "",
            "alarm_duration": 60,
            "deactivation_code": "1234",
            "night_mode": False,
            "email_notifications": False,
            "email_address": "",
            "apn_settings": {
                "apn": "",
                "username": "",
                "password": ""
            }
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.system_config = json.load(f)  # Cambiado a system_config
            else:
                self.system_config = config_default
                self.save_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.system_config = config_default
        
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.system_config, f, indent=4)  # Cambiado a system_config
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def setup_interface(self):
        # Create GUI elements here tabs !!!
        # menu bar
        self.create_menu_bar()

        # frames and notebook
        self.notebook = ttk.Notebook(self)  # Usa ttk.Notebook
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Control Panel Frame
        self.frame_control = tk.Frame(self.notebook)
        self.notebook.add(self.frame_control, text="Control Panel")
        self.create_control_frame()

        # Config Frame
        self.frame_config = tk.Frame(self.notebook)
        self.notebook.add(self.frame_config, text="Configuration")
        self.create_configuration_frame()
        
        # Registry Frame
        self.frame_registry = tk.Frame(self.notebook)
        self.notebook.add(self.frame_registry, text="Registry")
        self.create_registry_frame()

        # status bar
        self.create_status_bar()

    def create_menu_bar(self):
        system_menu = tk.Menu(self)
        # CORRECCIÓN: Usar super().config() o self.configure()
        self.configure(menu=system_menu)  # Cambiado a self.configure()

        # System Menu Items
        system_menu.add_command(label="Settings", command=self.open_settings_window)
        system_menu.add_command(label="Restart", command=self.restart_system)
        system_menu.add_command(label="Shutdown", command=self.shutdown_system)
        system_menu.add_command(label="About", command=self.show_about_info)
        system_menu.add_separator()
        system_menu.add_command(label="Exit", command=self.on_close)

    def create_control_frame(self):
        # Create control panel elements here
        frame_status = tk.LabelFrame(self.frame_control, text="Sensor Status", padx=10, pady=10)
        frame_status.pack(fill=tk.X, padx=10, pady=10)

        # Visual state indicators for sensors
        self.canvas_state = tk.Canvas(frame_status, width=50, height=50, bg='white')
        self.canvas_state.pack(side=tk.LEFT, padx=10)
        self.state_indicator = self.canvas_state.create_oval(10, 10, 40, 40, fill='green')

        # status information
        frame_info = tk.Frame(frame_status)
        frame_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.label_status = tk.Label(frame_info, text="All sensors normal", font=("Arial", 14))
        self.label_status.pack(anchor=tk.W)

        self.label_time = tk.Label(frame_info, text="Last Update: N/A", font=("Arial", 10))
        self.label_time.pack(anchor=tk.W)

        # Control Buttons
        frame_buttons = tk.Frame(self.frame_control)
        frame_buttons.pack(side=tk.RIGHT, padx=10)

        self.btn_activate = tk.Button(frame_buttons, text="Activate Alarm", command=self.activate_alarm, width=15)
        self.btn_activate.pack(pady=2)

        self.btn_deactivate = tk.Button(frame_buttons, text="Deactivate Alarm", command=self.deactivate_alarm, width=15)
        self.btn_deactivate.pack(pady=2)

        self.btn_panic = tk.Button(frame_buttons, text="Panic", command=self.trigger_panic, width=15, bg='red', fg='white')
        self.btn_panic.pack(pady=2)

        # Sensor Status List
        frame_summary = tk.LabelFrame(self.frame_control, text="Sensor Summary", padx=10, pady=10)
        frame_summary.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Sensor Listbox grid
        self.create_sensor_grid(frame_summary)

        frame_actions = tk.LabelFrame(self.frame_control, text="Actions", padx=10, pady=10)
        frame_actions.pack(fill=tk.X, padx=10, pady=10)

        btn_frame = tk.Frame(frame_actions)
        btn_frame.pack()

        tk.Button(btn_frame, text="Temporal silence", command=self.temporal_silence, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Last events", command=self.show_last_events, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Maintenance mode", command=self.toggle_maintenance_mode, width=20).pack(side=tk.LEFT, padx=5)

    def create_configuration_frame(self):
        # Frame principal para configuración
        main_frame = tk.Frame(self.frame_config)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sección de usuarios
        user_frame = tk.LabelFrame(main_frame, text="User Management", padx=15, pady=15)
        user_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botón para agregar usuario
        btn_add_user = tk.Button(
            user_frame, 
            text="+ Add New User", 
            command=self.add_user, 
            width=20,
            height=2
        )
        btn_add_user.pack(pady=10)
        
        # Sección de configuración del sistema
        system_frame = tk.LabelFrame(main_frame, text="System Configuration", padx=15, pady=15)
        system_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botones de configuración del sistema
        tk.Button(system_frame, text="General Settings", command=self.open_settings_window, width=20).pack(pady=5)
        tk.Button(system_frame, text="Sensor Configuration", command=self.configure_sensors, width=20).pack(pady=5)
        tk.Button(system_frame, text="Alarm Settings", command=self.configure_alarm, width=20).pack(pady=5)
        
        # Sección de mantenimiento
        maintenance_frame = tk.LabelFrame(main_frame, text="Maintenance", padx=15, pady=15)
        maintenance_frame.pack(fill=tk.X)
        
        tk.Button(maintenance_frame, text="Test System", command=self.test_system, width=20).pack(pady=5)
        tk.Button(maintenance_frame, text="Backup Configuration", command=self.backup_config, width=20).pack(pady=5)
        tk.Button(maintenance_frame, text="Restore Defaults", command=self.restore_defaults, width=20).pack(pady=5)

    def create_sensor_grid(self, parent):
        # Crea un frame para contener la cuadrícula
        grid_frame = tk.Frame(parent)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        self.sensor_widgets = {}

        for i, (sensor_id, info) in enumerate(self.sensor_states.items()):
            frame_sensor = tk.LabelFrame(grid_frame, text=info["name"], padx=5, pady=5)

            row = i // 2
            col = i % 2
            frame_sensor.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Expand grid cells
            grid_frame.columnconfigure(col, weight=1)
            grid_frame.rowconfigure(row, weight=1)

            # Visual indicator
            canvas = tk.Canvas(frame_sensor, width=40, height=40, bg='white')
            canvas.pack(padx=5)
            indicator = canvas.create_oval(5, 5, 35, 35, fill='green')

            # Status labels
            status_label = tk.Label(frame_sensor, text=f"Status: Normal", font=("Arial", 9))
            status_label.pack()

            # Last updated
            updates_label = tk.Label(frame_sensor, text="Last Update: N/A", font=("Arial", 8), fg='gray')  
            updates_label.pack()

            # Frame para botones de control del sensor
            frame_controls = tk.Frame(frame_sensor)
            frame_controls.pack(pady=5)
            
            tk.Button(frame_controls, text="Test", command=lambda sid=sensor_id: self.test_sensor(sid)).pack(side=tk.LEFT, padx=2)
            tk.Button(frame_controls, text="Configure", command=lambda sid=sensor_id: self.configure_sensor(sid)).pack(side=tk.LEFT, padx=2)
            tk.Button(frame_controls, text="History", command=lambda sid=sensor_id: self.show_sensor_history(sid)).pack(side=tk.LEFT, padx=2)

            self.sensor_widgets[sensor_id] = {
                "canvas": canvas,
                "indicator": indicator,
                "status_label": status_label,
                "updates_label": updates_label
            }
        
        # Botón para añadir nuevo sensor
        tk.Button(grid_frame, text="+ Add New Sensor", command=self.add_new_sensor).grid(
            row=len(self.sensor_states) // 2 + 1, 
            column=0, 
            columnspan=2, 
            pady=10
        )

        tk.Button(grid_frame, text=" - Delete Sensor", command=self.remove_sensor).grid(
            row=len(self.sensor_states) // 2 + 1, 
            column=1, 
            columnspan=2, 
            pady=10
        )

    # ========== Implementaciones de métodos faltantes ==========
    
    def create_registry_frame(self):
        """Crea el frame del registro de eventos"""
        # Título
        label_title = tk.Label(self.frame_registry, text="Event Registry", font=("Arial", 16))
        label_title.pack(pady=10)
        
        # Frame para controles
        frame_controls = tk.Frame(self.frame_registry)
        frame_controls.pack(fill=tk.X, padx=10, pady=5)
        
        # Botones de filtrado
        tk.Button(frame_controls, text="Today", width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_controls, text="Last 7 days", width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_controls, text="All", width=10).pack(side=tk.LEFT, padx=2)
        
        # Campo de búsqueda
        search_frame = tk.Frame(frame_controls)
        search_frame.pack(side=tk.RIGHT)
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        tk.Entry(search_frame, width=20).pack(side=tk.LEFT, padx=5)
        
        # AJUSTAR COLUMNAS según estructura de la BD
        # Tu consulta SQL devuelve: a.* (todos campos de alarms) + m.name (como module_name)
        # Campos típicos: id, module_id, description, priority, timestamp, acknowledged
        columns = ("ID", "Fecha", "Hora", "Módulo", "Descripción", "Prioridad")
        self.tree_events = ttk.Treeview(self.frame_registry, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        col_widths = {"ID": 50, "Fecha": 100, "Hora": 80, "Módulo": 120, "Descripción": 200, "Prioridad": 80}
        for col in columns:
            self.tree_events.heading(col, text=col)
            self.tree_events.column(col, width=col_widths.get(col, 120))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame_registry, orient="vertical", command=self.tree_events.yview)
        self.tree_events.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.tree_events.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # OBTENER Y MOSTRAR DATOS REALES
        try:
            real_alarm_data = self.nucleo_alarma.get_active_alarms()
            
            # Limpiar datos existentes en el Treeview
            self.tree_events.delete(*self.tree_events.get_children())
            
            # Insertar datos reales formateados
            if real_alarm_data:
                for item in real_alarm_data:
                    # Formatear los datos según la estructura de tu BD
                    # item[0] = id, item[5] = timestamp, item[6] = module_name, etc.
                    # Ajusta los índices según tu estructura real
                    
                    # Separar fecha y hora del timestamp
                    timestamp_str = str(item[5]) if item[5] else ""
                    fecha = timestamp_str.split()[0] if timestamp_str else ""
                    hora = timestamp_str.split()[1] if len(timestamp_str.split()) > 1 else ""
                    
                    # Crear tupla con los datos para el Treeview
                    tree_item = (
                        item[0],        # ID
                        fecha,          # Fecha
                        hora,           # Hora
                        item[6],        # module_name (índice 6 según tu consulta)
                        item[2],        # description (ajusta según tu BD)
                        item[3] if len(item) > 3 else ""  # priority o status
                    )
                    self.tree_events.insert("", tk.END, values=tree_item)
                
                # Mostrar mensaje informativo
                messagebox.showinfo(
                    "Registro de alarmas", 
                    f"Se cargaron {len(real_alarm_data)} alarmas activas"
                )
            else:
                messagebox.showinfo("Registro de alarmas", "No hay alarmas activas")
                
        except Exception as e:
            logging.error(f"Error al cargar alarmas: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar las alarmas: {e}")
    
    def create_status_bar(self):
        """Crea la barra de estado en la parte inferior de la ventana"""
        self.status_bar = tk.Frame(self, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Estado del sistema
        self.status_label = tk.Label(self.status_bar, text="System: Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Estado de conexión
        self.conn_label = tk.Label(self.status_bar, text="Connection: Active", anchor=tk.W)
        self.conn_label.pack(side=tk.LEFT, padx=5)
        
        # Fecha y hora
        self.datetime_label = tk.Label(self.status_bar, text="", anchor=tk.W)
        self.datetime_label.pack(side=tk.LEFT, padx=5)
        
        # Actualizar fecha y hora
        self.update_datetime()
        
        # Separador
        tk.Frame(self.status_bar, width=20).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Versión
        version_label = tk.Label(self.status_bar, text="v1.0.0", anchor=tk.E)
        version_label.pack(side=tk.RIGHT, padx=5)
    
    def update_datetime(self):
        """Actualiza la fecha y hora en la barra de estado"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.datetime_label.config(text=f"Date: {now}")
        # Programar próxima actualización en 1 segundo
        self.after(1000, self.update_datetime)
    
    def open_settings_window(self):
        """Abre la ventana de configuración"""
        messagebox.showinfo("Settings", "Settings window will be implemented here.")
    
    def restart_system(self):
        """Reinicia el sistema"""
        response = messagebox.askyesno("Restart System", "Are you sure you want to restart the system?")
        if response:
            logging.info("System restart requested.")
            messagebox.showinfo("Restart", "System restarting...")
    
    def shutdown_system(self):
        """Apaga el sistema"""
        response = messagebox.askyesno("Shutdown System", "Are you sure you want to shutdown the system?")
        if response:
            logging.info("System shutdown requested.")
            messagebox.showinfo("Shutdown", "System shutting down...")
            self.after(1000, self.quit)
    
    def show_about_info(self):
        """Muestra información acerca del sistema"""
        about_text = """Alarm System GUI v1.0.0
        
A complete alarm system management interface.
        
Features:
- Sensor monitoring
- Alarm control
- Event logging
- Module management

© 2026 Integral Electrica"""
        messagebox.showinfo("About", about_text)
    
    def test_alarm(self):
        """Prueba la alarma"""
        logging.info("Alarm test initiated.")
        messagebox.showwarning("Alarm Test", "Testing alarm system...")
    
    def sensor_simulation(self):
        """Simula eventos de sensores"""
        logging.info("Sensor simulation started.")
        messagebox.showinfo("Simulation", "Sensor simulation mode activated.")
    
    def test_connection(self):
        """Prueba la conexión"""
        logging.info("Connection test initiated.")
        messagebox.showinfo("Connection Test", "Testing system connections...")
    
    def open_documentation(self):
        """Abre la documentación"""
        logging.info("Opening documentation.")
        messagebox.showinfo("Documentation", "System documentation will open here.")
    
    def open_support(self):
        """Abre soporte técnico"""
        logging.info("Opening support.")
        messagebox.showinfo("Support", "Contact support: support@alarmsystem.com")
    
    def temporal_silence(self):
        """Silencia temporalmente las alarmas"""
        logging.info("Temporal silence activated.")
        self.quiet_mode = True
        messagebox.showinfo("Silence", "Alarms silenced for 30 minutes.")
        self.after(1800000, self.disable_silence)  # 30 minutos
    
    def disable_silence(self):
        """Desactiva el modo silencio"""
        self.quiet_mode = False
        logging.info("Temporal silence deactivated.")
    
    def show_last_events(self):
        """Muestra los últimos eventos"""
        logging.info("Showing last events.")
        # Redirige a la pestaña de registro
        self.notebook.select(self.frame_registry)
    
    def toggle_maintenance_mode(self):
        """Activa/desactiva el modo mantenimiento"""
        self.active_conn = not self.active_conn
        status = "ON" if not self.active_conn else "OFF"
        logging.info(f"Maintenance mode toggled: {status}")
        messagebox.showinfo("Maintenance", f"Maintenance mode: {status}")
    
    def test_sensor(self, sensor_id):
        """Prueba un sensor específico"""
        sensor_name = self.sensor_states[sensor_id]["name"]
        logging.info(f"Testing sensor: {sensor_name}")
        messagebox.showinfo("Test Sensor", f"Testing {sensor_name}...")
    
    def configure_sensor(self, sensor_id):
        """Configura un sensor específico"""
        sensor_name = self.sensor_states[sensor_id]["name"]
        logging.info(f"Configuring sensor: {sensor_name}")
        messagebox.showinfo("Configure Sensor", f"Configuration options for {sensor_name}")
    
    def show_sensor_history(self, sensor_id):
        """Muestra el historial de un sensor"""
        sensor_name = self.sensor_states[sensor_id]["name"]
        logging.info(f"Showing history for sensor: {sensor_name}")
        messagebox.showinfo("Sensor History", f"History for {sensor_name}")
    
    def add_new_sensor(self):
        top_sensor = tk.Toplevel(self)
        top_sensor.title("Add New Sensor")
        top_sensor.geometry("350x350")
        top_sensor.resizable(False, False)
        top_sensor.transient(self)  # Mantenerla sobre la ventana principal
        top_sensor.grab_set()  # Modal

        top_sensor.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (top_sensor.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (top_sensor.winfo_height() // 2)
        top_sensor.geometry(f"+{x}+{y}")

        # Frame principal con padding
        main_frame = tk.Frame(top_sensor, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
         # Título
        tk.Label(main_frame, text="Add New sensor", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        # Campos de entrada
        fields_frame1 = tk.Frame(main_frame)
        fields_frame1.pack(fill=tk.X, pady=10)

        # Sensor name
        tk.Label(fields_frame1, text="Sensor name:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        entry_sensor_name = tk.Entry(fields_frame1, width=25)
        entry_sensor_name.grid(row=0, column=1, padx=10, pady=5)

        # Role (usando Combobox en lugar de Entry)
        tk.Label(fields_frame1, text="Role:", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(fields_frame1, textvariable=type_var, width=23, state="readonly")
        type_combo['values'] = ("Motion", "Switch", "Smoke")
        type_combo.current(1)  # Por defecto "Switch"
        type_combo.grid(row=2, column=1, padx=10, pady=5)

        # Frame para botones
        button_frame1 = tk.Frame(main_frame)
        button_frame1.pack(fill=tk.X, pady=20)

        # Función para guardar sensor
        def save_sensor():
            sensor_name = entry_sensor_name.get().strip()
            sensor_type = type_var.get()
            
            if not sensor_name:
                messagebox.showerror("Error", "Sensor name is required!")
                return
            
            try:
                # Llamar al método del núcleo para insertar sensor
                self.nucleo_alarma.register_module(sensor_name, initial_status='inactive')
                logging.info(f"Sensor '{sensor_name}' added successfully.")
                messagebox.showinfo("Success", f"Sensor '{sensor_name}' added successfully!")
                top_sensor.destroy()
            except Exception as e:
                logging.error(f"Error adding sensor: {e}")
                messagebox.showerror("Error", f"Failed to add sensor: {str(e)}")
                messagebox.showerror("Error", "Username and password are required!")
                return
        
        # Botón de guardar
        btn_save1 = tk.Button(
            button_frame1, 
            text="Save sensor", 
            command=save_sensor,
            bg="#4CAF50",  # Verde
            fg="white",
            width=15,
            height=2
        )
        btn_save1.pack(side=tk.RIGHT, padx=5)
        
        # Botón de cancelar
        btn_cancel1 = tk.Button(
            button_frame1, 
            text="Cancel", 
            command=top_sensor.destroy,
            bg="#f44336",  # Rojo
            fg="white",
            width=15,
            height=2
        )
        btn_cancel1.pack(side=tk.RIGHT, padx=5)
        
        # Configurar grid
        fields_frame1.columnconfigure(1, weight=1)
        
        # Poner foco en el primer campo
        entry_sensor_name.focus_set()
        
        # Bind Enter para guardar
        top_sensor.bind('<Return>', lambda e: save_sensor())
        
        # Bind Escape para cancelar
        top_sensor.bind('<Escape>', lambda e: top_sensor.destroy())

    def remove_sensor(self):
        """Open a dialog to remove a sensor from the system."""
        top_remove = tk.Toplevel(self)
        top_remove.title("Remove Sensor")
        top_remove.geometry("400x400")
        top_remove.resizable(False, False)
        top_remove.transient(self)  # Mantenerla sobre la ventana principal
        top_remove.grab_set()  # Modal

        top_remove.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (top_remove.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (top_remove.winfo_height() // 2)
        top_remove.geometry(f"+{x}+{y}")

        # Frame principal con padding
        main_frame = tk.Frame(top_remove, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(main_frame, text="Remove Sensor", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Frame para selección de sensor
        selection_frame = tk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=10)
        
        # Label y Combobox para seleccionar sensor
        tk.Label(selection_frame, text="Select Sensor:", anchor="w").grid(row=0, column=0, sticky="w", pady=10)
        
        # Obtener lista de sensores activos de la base de datos
        try:
            cursor = self.nucleo_alarma.connection.cursor()
            cursor.execute("SELECT id, name, status FROM modules WHERE status != 'deleted' ORDER BY name")
            sensors = cursor.fetchall()
            
            if not sensors:
                tk.Label(selection_frame, text="No sensors available", fg="red").grid(row=1, column=0, columnspan=2, pady=10)
                btn_remove = tk.Button(
                    main_frame, 
                    text="Close", 
                    command=top_remove.destroy,
                    bg="#2196F3",
                    fg="white",
                    width=15,
                    height=2
                )
                btn_remove.pack(pady=20)
                return
        except Exception as e:
            logging.error(f"Error fetching sensors: {e}")
            messagebox.showerror("Error", f"Failed to load sensors: {str(e)}")
            top_remove.destroy()
            return
        
        # Diccionario para mapear IDs a nombres
        sensor_dict = {f"{sensor[1]} (ID: {sensor[0]})": sensor[0] for sensor in sensors}
        
        # Variable para el sensor seleccionado
        selected_sensor = tk.StringVar()
        sensor_combo = ttk.Combobox(selection_frame, textvariable=selected_sensor, width=30, state="readonly")
        sensor_combo['values'] = list(sensor_dict.keys())
        sensor_combo.grid(row=0, column=1, padx=10, pady=10)
        sensor_combo.current(0)  # Seleccionar el primero por defecto
        
        # Frame para información del sensor
        info_frame = tk.LabelFrame(main_frame, text="Sensor Information", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=15)
        
        # Labels para mostrar información
        info_labels = {}
        info_fields = ["ID:", "Name:", "Status:"]
        
        for i, field in enumerate(info_fields):
            tk.Label(info_frame, text=field, font=("Arial", 9, "bold"), anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            info_labels[field] = tk.Label(info_frame, text="", anchor="w")
            info_labels[field].grid(row=i, column=1, sticky="w", padx=10, pady=3)
        
        # Función para actualizar información cuando se selecciona un sensor
        def update_sensor_info(event=None):
            selected_text = selected_sensor.get()
            if selected_text and selected_text in sensor_dict:
                sensor_id = sensor_dict[selected_text]
                try:
                    cursor = self.nucleo_alarma.connection.cursor()
                    cursor.execute("SELECT id, name, status FROM modules WHERE id = ?", (sensor_id,))
                    sensor = cursor.fetchone()
                    
                    if sensor:
                        info_labels["ID:"].config(text=sensor[0])
                        info_labels["Name:"].config(text=sensor[1])
                        
                        # Mostrar estado con color
                        status = sensor[2]
                        color = "green" if status == "active" else "orange" if status == "inactive" else "red"
                        info_labels["Status:"].config(text=status, fg=color)
                except Exception as e:
                    logging.error(f"Error fetching sensor info: {e}")
        
        # Llamar inicialmente para mostrar información del primer sensor
        update_sensor_info()
        
        # Bind el cambio de selección
        sensor_combo.bind("<<ComboboxSelected>>", update_sensor_info)
        
        # Frame para botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Función para eliminar el sensor
        def delete_sensor():
            selected_text = selected_sensor.get()
            if not selected_text:
                messagebox.showwarning("Warning", "Please select a sensor to remove!")
                return
            
            # Confirmación de eliminación
            confirm = messagebox.askyesno(
                "Confirm Removal",
                f"Are you sure you want to remove sensor:\n'{selected_text}'?\n\nThis action cannot be undone!",
                icon='warning'
            )
            
            if not confirm:
                return
            
            try:
                sensor_id = sensor_dict[selected_text]
                
                # Llamar al método del núcleo para eliminar el sensor
                success = self.nucleo_alarma.unregister_module(sensor_id)
                
                if success:
                    logging.info(f"Sensor '{selected_text}' removed successfully.")
                    messagebox.showinfo("Success", f"Sensor '{selected_text}' has been removed successfully!")
                    
                    # Actualizar la lista de sensores
                    cursor = self.nucleo_alarma.connection.cursor()
                    cursor.execute("SELECT id, name, status FROM modules WHERE status != 'deleted' ORDER BY name")
                    sensors = cursor.fetchall()
                    
                    if sensors:
                        sensor_dict.clear()
                        sensor_dict.update({f"{sensor[1]} (ID: {sensor[0]})": sensor[0] for sensor in sensors})
                        sensor_combo['values'] = list(sensor_dict.keys())
                        sensor_combo.current(0)
                        update_sensor_info()
                    else:
                        # Si no hay más sensores, cerrar la ventana
                        messagebox.showinfo("Info", "All sensors have been removed.")
                        top_remove.destroy()
                else:
                    messagebox.showerror("Error", f"Failed to remove sensor '{selected_text}'.")
                    
            except Exception as e:
                logging.error(f"Error removing sensor: {e}")
                messagebox.showerror("Error", f"Failed to remove sensor: {str(e)}")
        
        # Botón de eliminar
        btn_remove = tk.Button(
            button_frame, 
            text="Remove Sensor", 
            command=delete_sensor,
            bg="#f44336",  # Rojo
            fg="white",
            width=15,
            height=2
        )
        btn_remove.pack(side=tk.RIGHT, padx=5)
        
        # Botón de cancelar
        btn_cancel = tk.Button(
            button_frame, 
            text="Cancel", 
            command=top_remove.destroy,
            bg="#757575",  # Gris
            fg="white",
            width=15,
            height=2
        )
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        # Configurar grid
        selection_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(1, weight=1)
        
        # Bind Enter para eliminar
        top_remove.bind('<Return>', lambda e: delete_sensor())
        
        # Bind Escape para cancelar
        top_remove.bind('<Escape>', lambda e: top_remove.destroy())
        
        # Poner foco en la ventana
        top_remove.focus_set()

    def add_user(self):
        # 1. Crear la ventana emergente
        top_user = tk.Toplevel(self)
        top_user.title("Add New User")
        top_user.geometry("350x350")
        top_user.resizable(False, False)
        top_user.transient(self)  # Mantenerla sobre la ventana principal
        top_user.grab_set()  # Modal
        
        # Centrar la ventana
        top_user.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (top_user.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (top_user.winfo_height() // 2)
        top_user.geometry(f"+{x}+{y}")
        
        # Frame principal con padding
        main_frame = tk.Frame(top_user, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(main_frame, text="Add New User", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Campos de entrada
        fields_frame = tk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=10)
        
        # Username
        tk.Label(fields_frame, text="Username:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        entry_username = tk.Entry(fields_frame, width=25)
        entry_username.grid(row=0, column=1, padx=10, pady=5)
        
        # Password
        tk.Label(fields_frame, text="Password:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        entry_password = tk.Entry(fields_frame, width=25, show="*")
        entry_password.grid(row=1, column=1, padx=10, pady=5)
        
        # Role (usando Combobox en lugar de Entry)
        tk.Label(fields_frame, text="Role:", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        role_var = tk.StringVar()
        role_combo = ttk.Combobox(fields_frame, textvariable=role_var, width=23, state="readonly")
        role_combo['values'] = ("admin", "user", "viewer")
        role_combo.current(1)  # Por defecto "user"
        role_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Checkbox para notificaciones
        notify_var = tk.BooleanVar(value=True)
        tk.Checkbutton(fields_frame, text="Enable notifications", variable=notify_var).grid(
            row=3, column=0, columnspan=2, pady=10, sticky="w"
        )
        
        # Frame para botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Función para guardar usuario
        def save_user():
            username = entry_username.get().strip()
            password = entry_password.get().strip()
            role = role_var.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Username and password are required!")
                return
            
            try:
                # Llamar al método del núcleo para insertar usuario
                self.nucleo_alarma.insert_user(username, password, role)
                logging.info(f"User '{username}' added successfully.")
                messagebox.showinfo("Success", f"User '{username}' added successfully!")
                top_user.destroy()
            except Exception as e:
                logging.error(f"Error adding user: {e}")
                messagebox.showerror("Error", f"Failed to add user: {str(e)}")
        
        # Botón de guardar
        btn_save = tk.Button(
            button_frame, 
            text="Save User", 
            command=save_user,
            bg="#4CAF50",  # Verde
            fg="white",
            width=15,
            height=2
        )
        btn_save.pack(side=tk.RIGHT, padx=5)
        
        # Botón de cancelar
        btn_cancel = tk.Button(
            button_frame, 
            text="Cancel", 
            command=top_user.destroy,
            bg="#f44336",  # Rojo
            fg="white",
            width=15,
            height=2
        )
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        # Configurar grid
        fields_frame.columnconfigure(1, weight=1)
        
        # Poner foco en el primer campo
        entry_username.focus_set()
        
        # Bind Enter para guardar
        top_user.bind('<Return>', lambda e: save_user())
        
        # Bind Escape para cancelar
        top_user.bind('<Escape>', lambda e: top_user.destroy())
    
    # Métodos adicionales para la configuración
    def configure_sensors(self):
        """Configuración de sensores"""
        messagebox.showinfo("Sensor Configuration", "Sensor configuration window will open here.")
    
    def configure_alarm(self):
        """Configuración de la alarma"""
        messagebox.showinfo("Alarm Configuration", "Alarm configuration window will open here.")
    
    def test_system(self):
        """Prueba del sistema"""
        messagebox.showinfo("System Test", "System test will be performed.")
    
    def backup_config(self):
        """Backup de configuración"""
        messagebox.showinfo("Backup", "Configuration backup will be created.")
    
    def restore_defaults(self):
        """Restaurar valores por defecto"""
        response = messagebox.askyesno("Restore Defaults", 
                                      "Are you sure you want to restore all settings to default values?")
        if response:
            messagebox.showinfo("Defaults Restored", "All settings have been restored to defaults.")

    def on_close(self):
        """Maneja el cierre de la aplicación"""
        response = messagebox.askyesno("Exit", "Are you sure you want to exit?")
        if response:
            logging.info("Application closing.")
            self.quit()
    
    def update_system_state(self):
        """Actualiza el estado del sistema en la interfaz"""
        status_text = "ACTIVE" if self.active_alarm else "READY"
        color = "red" if self.active_alarm else "green"
        
        self.status_label.config(text=f"System: {status_text}")
        self.canvas_state.itemconfig(self.state_indicator, fill=color)
        
        # Actualizar etiqueta de estado principal
        if self.active_alarm:
            self.label_status.config(text="ALARM ACTIVE", fg="red")
        else:
            self.label_status.config(text="All sensors normal", fg="black")

    # ========== Alarm Control Methods ==========

    def activate_alarm(self):
        response = messagebox.askyesno("Activate Alarm", "Are you sure you want to activate the alarm?")
        if response:
            self.active_alarm = True
            logging.info("Alarm activated by user.")
            self.update_system_state()
            messagebox.showinfo("Alarm Activated", "The alarm system is now active.")
    
    def deactivate_alarm(self):
        # CORRECCIÓN: Usar system_config en lugar de config
        code = simpledialog.askstring("Deactivate Alarm", "Enter deactivation code:", show="*")
        if code == self.system_config.get("deactivation_code", "1234"):  # Cambiado a system_config
            self.active_alarm = False
            logging.info("Alarm deactivated by user.")
            self.update_system_state()
            messagebox.showinfo("Alarm Deactivated", "The alarm system is now deactivated.")
        else:
            logging.warning("Incorrect deactivation code entered.")
            messagebox.showerror("Error", "Incorrect deactivation code.")
    
    def trigger_panic(self):
        response = messagebox.askyesno("Panic Alarm", "Are you sure you want to trigger the panic alarm?")
        if response:
            logging.warning("Panic alarm triggered by user.")
            self.active_alarm = True
            self.update_system_state()
            messagebox.showwarning("Panic Alarm", "Panic alarm has been triggered!")

# Para ejecutar la aplicación
if __name__ == "__main__":
    app = AlarmSystemGUI()
    app.mainloop()