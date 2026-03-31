import serial
import serial.tools.list_ports
import time
import threading
from typing import Optional, Callable, List


class SerialMonitor:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 5.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.output_buffer: List[str] = []
        self._thread: Optional[threading.Thread] = None
    
    def open(self) -> bool:
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.serial.reset_input_buffer()
            return True
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            return False
    
    def close(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def read_line(self, timeout: Optional[float] = None) -> Optional[str]:
        if not self.serial or not self.serial.is_open:
            return None
        
        try:
            if timeout:
                self.serial.timeout = timeout
            line = self.serial.readline()
            if line:
                decoded = line.decode('utf-8', errors='replace').strip()
                self.output_buffer.append(decoded)
                return decoded
        except Exception as e:
            print(f"Serial read error: {e}")
        return None
    
    def read_lines(self, duration: float = 5.0) -> List[str]:
        """读取指定时长的数据"""
        self.output_buffer.clear()
        self.running = True
        start = time.time()
        
        while self.running and (time.time() - start) < duration:
            line = self.read_line(timeout=0.5)
            if line:
                print(line)
        
        return self.output_buffer
    
    def monitor_async(self, callback: Optional[Callable[[str], None]] = None):
        """异步监控串口"""
        self.running = True
        
        def _monitor():
            while self.running:
                line = self.read_line(timeout=0.1)
                if line and callback:
                    callback(line)
        
        self._thread = threading.Thread(target=_monitor, daemon=True)
        self._thread.start()
    
    def stop(self):
        self.running = False
    
    def get_output(self) -> str:
        return '\n'.join(self.output_buffer)
    
    def clear_buffer(self):
        self.output_buffer.clear()
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()


def list_ports() -> List[dict]:
    """列出所有可用串口"""
    ports = serial.tools.list_ports.comports()
    return [
        {
            "port": p.device,
            "name": p.name,
            "description": p.description,
            "hwid": p.hwid
        }
        for p in ports
    ]


def open_port(port: str, baudrate: int = 115200) -> Optional[SerialMonitor]:
    """打开串口"""
    monitor = SerialMonitor(port, baudrate)
    if monitor.open():
        return monitor
    return None
