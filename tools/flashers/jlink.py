from .base import FlasherBase
import subprocess
import os
import shutil
import tempfile


class JLinkFlasher(FlasherBase):
    name = "jlink"
    
    def __init__(self, device: str = None, speed: int = 4000, interface: str = "SWD"):
        super().__init__(device, speed, interface)
        self.jlink_path = self._find_jlink()
    
    def _find_jlink(self) -> str:
        paths = [
            "JLink.exe",
            "JLink",
            "C:/Program Files/SEGGER/JLink/JLink.exe",
            "C:/Program Files (x86)/SEGGER/JLink/JLink.exe",
        ]
        for path in paths:
            if shutil.which(path):
                return path
        return "JLink.exe"
    
    def detect(self) -> bool:
        if not self.device:
            return False
        try:
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", "-", "-ExitCode"],
                input=f"connect\nqc\n".encode(),
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def flash(self, elf_path: str) -> bool:
        script = f"""
connect
loadfile {elf_path}
r
qc
"""
        try:
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", "-"],
                input=script.encode(),
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"JLink flash error: {e}")
            return False
    
    def reset(self) -> bool:
        script = "connect\nr\nqc\n"
        try:
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", "-"],
                input=script.encode(),
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def erase(self) -> bool:
        script = f"connect\nerase\nqc\n"
        try:
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", "-"],
                input=script.encode(),
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False
