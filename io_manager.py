"""
io_manager.py
Maneja toda la interacción con hardware GPIO y periféricos.
"""

import logging
import threading
import time
from typing import Dict, Optional, Callable
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available. Running in simulation mode.")

class IOManager:
    """Gestiona todas las operaciones de entrada/salida del sistema."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.gpio_initialized = False
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Mapeos
        self.gpio_to_module: Dict[int, dict] = {}  # {gpio_pin: module_info}
        self.module_to_gpio: Dict[int, int] = {}   # {module_id: gpio_pin}
        
        # Callbacks
        self.on_sensor_trigger: Optional[Callable] = None
        self.on_alarm_reset: Optional[Callable] = None
        
        # Configuración por defecto
        self.defaults = {
            'check_interval': 0.1,  # segundos
            'bounce_time': 300,     # milisegundos
            'simulation_mode': not GPIO_AVAILABLE
        }
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Configurar GPIO si está disponible."""
        if not GPIO_AVAILABLE or self.defaults['simulation_mode']:
            logging.info("Running in GPIO simulation mode")
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            self.gpio_initialized = True
            logging.info("GPIO initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize GPIO: {e}")
            self.gpio_initialized = False
    
    def register_sensor(self, module_id: int, gpio_pin: int, 
                       sensor_type: str = 'NO', pull_config: str = 'UP') -> bool:
        """
        Registrar un sensor en un pin GPIO específico.
        
        Args:
            module_id: ID único del módulo/sensor
            gpio_pin: Número de pin GPIO (BCM)
            sensor_type: 'NO' (Normalmente Abierto) o 'NC' (Normalmente Cerrado)
            pull_config: 'UP' o 'DOWN'
        
        Returns:
            True si se registró exitosamente
        """
        if not self.gpio_initialized and not self.defaults['simulation_mode']:
            logging.error("GPIO not initialized")
            return False
        
        # Validar parámetros
        if sensor_type not in ['NO', 'NC']:
            logging.error(f"Invalid sensor type: {sensor_type}")
            return False
        
        if pull_config not in ['UP', 'DOWN']:
            logging.error(f"Invalid pull config: {pull_config}")
            return False
        
        # Configurar el pin si estamos en modo real
        if self.gpio_initialized:
            try:
                pull = GPIO.PUD_UP if pull_config == 'UP' else GPIO.PUD_DOWN
                GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=pull)
                
                # Configurar debounce
                GPIO.add_event_detect(
                    gpio_pin, 
                    GPIO.BOTH,
                    callback=self._gpio_event_callback,
                    bouncetime=self.defaults['bounce_time']
                )
            except Exception as e:
                logging.error(f"Failed to setup GPIO pin {gpio_pin}: {e}")
                return False
        
        # Guardar mapeo
        self.gpio_to_module[gpio_pin] = {
            'module_id': module_id,
            'sensor_type': sensor_type,
            'pull_config': pull_config,
            'simulated_state': 'normal'  # Para modo simulación
        }
        self.module_to_gpio[module_id] = gpio_pin
        
        logging.info(f"Sensor registered: Module {module_id} -> GPIO {gpio_pin} ({sensor_type}, {pull_config})")
        return True
    
    def _gpio_event_callback(self, channel):
        """Callback para eventos de GPIO (interrupciones)."""
        if channel not in self.gpio_to_module:
            return
        
        module_info = self.gpio_to_module[channel]
        module_id = module_info['module_id']
        current_state = self.read_sensor_state(module_id)
        
        logging.debug(f"GPIO event on channel {channel}. Module {module_id} state: {current_state}")
        
        # Notificar al callback si está configurado
        if self.on_sensor_trigger:
            self.on_sensor_trigger(module_id, current_state)
    
    def read_sensor_state(self, module_id: int) -> str:
        """
        Leer el estado actual de un sensor.
        
        Returns:
            'normal', 'alarm', o 'unknown'
        """
        if module_id not in self.module_to_gpio:
            return 'unknown'
        
        gpio_pin = self.module_to_gpio[module_id]
        module_info = self.gpio_to_module[gpio_pin]
        
        # Modo simulación
        if not self.gpio_initialized or self.defaults['simulation_mode']:
            return module_info.get('simulated_state', 'normal')
        
        # Modo real - leer GPIO
        try:
            current_state = GPIO.input(gpio_pin)
            sensor_type = module_info['sensor_type']
            
            if sensor_type == 'NO':  # Normalmente Abierto
                return 'alarm' if current_state == GPIO.HIGH else 'normal'
            else:  # Normalmente Cerrado
                return 'alarm' if current_state == GPIO.LOW else 'normal'
                
        except Exception as e:
            logging.error(f"Error reading GPIO pin {gpio_pin}: {e}")
            return 'unknown'
    
    def set_sensor_state(self, module_id: int, state: str) -> bool:
        """
        Establecer estado de sensor (solo en modo simulación).
        
        Args:
            module_id: ID del módulo
            state: 'normal' o 'alarm'
        
        Returns:
            True si se estableció exitosamente
        """
        if module_id not in self.module_to_gpio:
            return False
        
        gpio_pin = self.module_to_gpio[module_id]
        if gpio_pin in self.gpio_to_module:
            self.gpio_to_module[gpio_pin]['simulated_state'] = state
            logging.info(f"Simulated sensor {module_id} set to {state}")
            return True
        
        return False
    
    def activate_output(self, output_type: str, duration: float = None) -> bool:
        """
        Activar una salida física (sirena, LED, etc.).
        
        Args:
            output_type: Tipo de salida ('siren', 'led', 'relay')
            duration: Duración en segundos (None = mantener activo)
        
        Returns:
            True si se activó exitosamente
        """
        # Mapeo de tipos de salida a pines GPIO (configurable)
        output_pins = {
            'siren': 17,   # Pin para sirena
            'status_led': 27,  # LED de estado
            'relay_1': 22,     # Relé 1
            'relay_2': 23,     # Relé 2
        }
        
        if output_type not in output_pins:
            logging.error(f"Unknown output type: {output_type}")
            return False
        
        pin = output_pins[output_type]
        
        if not self.gpio_initialized or self.defaults['simulation_mode']:
            logging.info(f"[SIM] Output {output_type} activated on pin {pin}")
            return True
        
        try:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            
            # Si hay duración, programar apagado
            if duration:
                threading.Timer(duration, self._deactivate_output, args=[pin]).start()
            
            logging.info(f"Output {output_type} activated on pin {pin}")
            return True
        except Exception as e:
            logging.error(f"Failed to activate output {output_type}: {e}")
            return False
    
    def _deactivate_output(self, pin: int):
        """Desactivar una salida GPIO."""
        try:
            GPIO.output(pin, GPIO.LOW)
        except:
            pass
    
    def start_monitoring(self):
        """Iniciar monitoreo continuo de sensores."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logging.info("I/O monitoring started")
    
    def stop_monitoring(self):
        """Detener monitoreo."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logging.info("I/O monitoring stopped")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.monitoring_active:
            try:
                # Chequear estado de todos los sensores registrados
                for gpio_pin, module_info in self.gpio_to_module.items():
                    module_id = module_info['module_id']
                    state = self.read_sensor_state(module_id)
                    
                    # Loggear cambios de estado
                    current_state = module_info.get('last_state')
                    if current_state != state:
                        module_info['last_state'] = state
                        logging.debug(f"Module {module_id} state changed: {current_state} -> {state}")
                
                time.sleep(self.defaults['check_interval'])
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
    def get_all_sensor_states(self) -> Dict[int, dict]:
        """Obtener estado de todos los sensores registrados."""
        states = {}
        for module_id, gpio_pin in self.module_to_gpio.items():
            states[module_id] = {
                'gpio_pin': gpio_pin,
                'state': self.read_sensor_state(module_id),
                **self.gpio_to_module[gpio_pin]
            }
        return states
    
    def cleanup(self):
        """Limpiar recursos GPIO."""
        self.stop_monitoring()
        
        if self.gpio_initialized:
            try:
                GPIO.cleanup()
                self.gpio_initialized = False
                logging.info("GPIO cleanup completed")
            except Exception as e:
                logging.error(f"Error during GPIO cleanup: {e}")
    
    def get_gpio_info(self) -> dict:
        """Obtener información sobre la configuración GPIO."""
        return {
            'initialized': self.gpio_initialized,
            'simulation_mode': self.defaults['simulation_mode'],
            'sensors_registered': len(self.gpio_to_module),
            'gpio_available': GPIO_AVAILABLE
        }