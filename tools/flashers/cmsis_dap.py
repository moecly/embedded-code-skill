from .base import FlasherBase
import subprocess
import shutil


class CMSISDAPFlasher(FlasherBase):
    name = "cmsis_dap"
    
    def __init__(self, device: str = None, speed: int = 4000, interface: str = "SWD"):
        super().__init__(device, speed, interface)
        self.openocd_path = self._find_openocd()
    
    def _find_openocd(self) -> str:
        paths = [
            "openocd",
            "C:/Program Files/OpenOCD/bin/openocd.exe",
            "C:/Program Files (x86)/OpenOCD/bin/openocd.exe",
        ]
        for path in paths:
            if shutil.which(path):
                return path
        return "openocd"
    
    def detect(self) -> bool:
        try:
            result = subprocess.run(
                [self.openocd_path, "-f", "interface/cmsis-dap.cfg", "-c", "init", "-c", "shutdown"],
                capture_output=True,
                timeout=5
            )
            output = (result.stdout + result.stderr).decode('utf-8', errors='ignore')
            return "unable to find" not in output.lower() and "error" not in output.lower()[:300]
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def list_devices(self) -> list:
        """列出所有连接的 CMSIS-DAP 设备"""
        try:
            result = subprocess.run(
                [self.openocd_path, "-f", "interface/cmsis-dap.cfg", "-c", "init", "-c", "shutdown"],
                capture_output=True,
                timeout=5
            )
            output = (result.stdout + result.stderr).decode('utf-8', errors='ignore')
            if "unable to find" in output.lower() or "error" in output.lower()[:300]:
                return []
            return ["CMSIS-DAP"]
        except:
            return []
    
    def flash(self, file_path: str, flash_type: str = "elf", addr: str = None) -> bool:
        if flash_type == 'bin' and addr:
            program_cmd = f"program {file_path} {addr} verify reset"
        else:
            program_cmd = f"program {file_path} verify reset"
        
        cfg = f"""
adapter speed {self.speed}
transport select {self.interface.lower()}
init
reset halt
{program_cmd}
shutdown
"""
        try:
            result = subprocess.run(
                [self.openocd_path, "-f", "interface/cmsis-dap.cfg", "-c", cfg],
                capture_output=True,
                timeout=60
            )
            output = result.stdout.decode('utf-8', errors='ignore') + result.stderr.decode('utf-8', errors='ignore')
            return "Programming and verifying target" in output or result.returncode == 0
        except Exception as e:
            print(f"CMSIS-DAP flash error: {e}")
            return False
    
    def reset(self) -> bool:
        cfg = f"""
adapter speed {self.speed}
transport select {self.interface.lower()}
init
reset run
shutdown
"""
        try:
            result = subprocess.run(
                [self.openocd_path, "-f", "interface/cmsis-dap.cfg", "-c", cfg],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def erase(self) -> bool:
        cfg = f"""
adapter speed {self.speed}
transport select {self.interface.lower()}
init
reset halt
stm32f1x mass_erase 0
shutdown
"""
        try:
            result = subprocess.run(
                [self.openocd_path, "-f", "interface/cmsis-dap.cfg", "-c", cfg],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False
