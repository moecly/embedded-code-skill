from .base import FlasherBase
import subprocess
import shutil


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
        if not self.device:
            return False
        try:
            result = subprocess.run(
                [self.stlink_path, "-List"],
                capture_output=True,
                timeout=5
            )
            return self.device in result.stdout.decode('utf-8', errors='ignore')
        except:
            return False
    
    def flash(self, elf_path: str) -> bool:
        if not os.path.exists(elf_path):
            print(f"File not found: {elf_path}")
            return False
        
        try:
            cmd = [
                self.stlink_path,
                "-c", f"ID={self.device}",
                "-P", elf_path, "0x08000000",
                "-V", "15",
                "-Rst",
                "-Run"
            ]
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
