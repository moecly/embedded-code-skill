from .base import FlasherBase
import subprocess
import shutil
import os


class STLinkFlasher(FlasherBase):
    name = "stlink"
    
    def __init__(self, device: str = None, speed: int = 4000, interface: str = "SWD"):
        super().__init__(device, speed, interface)
        self.stlink_path = self._find_stlink()
    
    def _find_stlink(self) -> str:
        paths = [
            "stlink_cli",
            "ST-Link_CLI",
            "st-link",
            "C:/Program Files/STMicroelectronics/ST-Link CLI/ST-Link_CLI.exe",
        ]
        for path in paths:
            if shutil.which(path):
                return path
        return "ST-Link_CLI"
    
    def detect(self) -> bool:
        try:
            result = subprocess.run(
                [self.stlink_path, "-List"],
                capture_output=True,
                timeout=5
            )
            output = result.stdout.decode('utf-8', errors='ignore')
            return "ST-LINK" in output or "STM32" in output
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def list_devices(self) -> list:
        """列出所有连接的 ST-Link 设备"""
        try:
            result = subprocess.run(
                [self.stlink_path, "-List"],
                capture_output=True,
                text=True,
                timeout=5
            )
            devices = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'ST-LINK' in line or 'STM32' in line:
                    devices.append(line)
            return devices
        except:
            return []
    
    def flash(self, file_path: str, flash_type: str = "elf", addr: str = None) -> bool:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        if flash_type not in ['hex', 'bin']:
            print(f"STLink only supports .hex and .bin files, not .{flash_type}")
            return False
        
        flash_addr = addr or "0x08000000"
        
        try:
            cmd = [
                self.stlink_path,
                "-c", f"ID={self.device}" if self.device else "",
                "-P", file_path, flash_addr,
                "-V", "15",
                "-Rst",
                "-Run"
            ]
            cmd = [c for c in cmd if c]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            output = result.stdout.decode('utf-8', errors='ignore')
            return "Programming" in output and "Verification" in output
        except Exception as e:
            print(f"STLink flash error: {e}")
            return False
    
    def reset(self) -> bool:
        try:
            result = subprocess.run(
                [self.stlink_path, "-Rst", "-Run"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def erase(self) -> bool:
        try:
            result = subprocess.run(
                [self.stlink_path, "-c", f"ID={self.device}", "-ME"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False
