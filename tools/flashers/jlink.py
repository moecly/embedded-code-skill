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
        """检测 J-Link 烧录器是否可用"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("connect\nq\n")
                cmd_file = f.name
            
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", cmd_file],
                capture_output=True,
                timeout=10
            )
            os.unlink(cmd_file)
            
            output = (result.stdout + result.stderr).decode('utf-8', errors='ignore')
            return "O.K." in output or "Connecting to J-Link" in output
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def check_device(self) -> tuple:
        """
        检测目标芯片是否连接
        
        Returns:
            (connected: bool, message: str)
        """
        device = self.device or "STM32F407ZG"
        try:
            # 使用 stdin 管道而非 CommandFile，以确保真正尝试连接目标芯片
            result = subprocess.run(
                [self.jlink_path, "-Device", device, "-If", self.interface],
                input="connect\nh\nq\n",
                capture_output=True,
                text=True,
                timeout=15
            )
            
            output = result.stdout + result.stderr
            
            # 检测连接失败的关键词
            if "Could not connect" in output:
                return False, f"无法连接到芯片 (Device: {device}, Interface: {self.interface})\n请检查：\n  1. 芯片是否正常供电\n  2. SWD/JTAG 连线是否正确\n  3. 芯片型号是否与实际匹配"
            
            if "Connect failed" in output:
                return False, f"芯片连接失败 (Device: {device})\n请检查硬件连接"
            
            if "Can not attach to CPU" in output:
                return False, f"无法连接到 CPU (Device: {device})\n请检查 SWD/JTAG 连接"
            
            if "Error occurred" in output:
                return False, f"连接芯片时发生错误\n输出:\n{output}"
            
            # 检测连接成功
            if "Connected to target" in output or "Core found" in output:
                return True, "芯片连接正常"
            
            return False, f"芯片连接状态未知\n输出:\n{output}"
        except FileNotFoundError:
            return False, "JLink.exe 未找到"
        except Exception as e:
            return False, f"检测芯片时出错: {e}"
    
    def list_devices(self) -> list:
        """列出所有连接的 J-Link 设备"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("connect\nq\n")
                cmd_file = f.name
            
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", cmd_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            os.unlink(cmd_file)
            
            output = result.stdout + result.stderr
            devices = []
            for line in output.split('\n'):
                if 'J-Link' in line or 'Firmware' in line or 'S/N' in line or 'O.K.' in line:
                    devices.append(line.strip())
            return devices
        except:
            return []
    
    def flash(self, file_path: str, flash_type: str = "elf", addr: str = None) -> bool:
        file_path = file_path.replace('\\', '/')
        
        if flash_type == 'bin' and addr:
            load_cmd = f"loadfile {file_path} {addr}"
        else:
            load_cmd = f"loadfile {file_path}"
        
        script = f"""connect
{load_cmd}
go
exit
"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(script)
                cmd_file = f.name
            
            cmd = [
                self.jlink_path,
                "-Device", self.device or "STM32F407ZG",
                "-If", self.interface,
                "-Speed", str(self.speed),
                "-CommandFile", cmd_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )
            os.unlink(cmd_file)
            
            output = (result.stdout + result.stderr).decode('utf-8', errors='ignore')
            return "O.K." in output and "Downloading file" in output
        except Exception as e:
            print(f"JLink flash error: {e}")
            return False
    
    def reset(self) -> bool:
        script = "connect\nr\nqc\n"
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(script)
                cmd_file = f.name
            
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", cmd_file],
                capture_output=True,
                timeout=10
            )
            os.unlink(cmd_file)
            return result.returncode == 0
        except:
            return False
    
    def erase(self) -> bool:
        script = "connect\nerase\nqc\n"
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(script)
                cmd_file = f.name
            
            result = subprocess.run(
                [self.jlink_path, "-CommandFile", cmd_file],
                capture_output=True,
                timeout=30
            )
            os.unlink(cmd_file)
            return result.returncode == 0
        except:
            return False
