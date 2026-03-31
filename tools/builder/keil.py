import os
import subprocess
import shutil
from .base import BuilderBase


class KeilBuilder(BuilderBase):
    name = "Keil MDK"
    type = "keil"
    project_extensions = [".uvprojx", ".uvproj"]
    
    def __init__(self, tool_path: str = None, project_path: str = None):
        super().__init__(tool_path, project_path)
        if not self.tool_path:
            self.tool_path = self._find_tool()
    
    def _find_tool(self) -> str:
        """从环境变量 PATH 中查找 UV4.exe"""
        tool = shutil.which("UV4.exe") or shutil.which("UV4")
        return tool if tool else "UV4.exe"
    
    def detect_tool(self) -> bool:
        """检测 Keil MDK 是否可用"""
        import shutil
        path = shutil.which("UV4.exe") or shutil.which("UV4")
        if path and os.path.exists(path):
            self.tool_path = path
            return True
        if os.path.exists(self.tool_path):
            return True
        return False
    
    def find_project(self, root: str = ".") -> str:
        """查找 Keil 项目文件"""
        projects = []
        for dirpath, _, filenames in os.walk(os.path.abspath(root)):
            for filename in filenames:
                if filename.endswith(('.uvprojx', '.uvproj')):
                    projects.append(os.path.join(dirpath, filename))
        
        if len(projects) == 1:
            return projects[0]
        elif len(projects) > 1:
            raise ValueError(f"找到多个 Keil 项目，请手动指定:\n" + 
                           "\n".join(f"  - {p}" for p in projects))
        else:
            raise FileNotFoundError("未找到 Keil 项目文件 (.uvprojx/.uvproj)")
    
    def build(self, project_path: str = None) -> tuple:
        """编译 Keil 项目"""
        project = project_path or self.project_path
        
        if not project:
            project = self.find_project()
        
        if not os.path.exists(project):
            return False, f"项目文件不存在: {project}"
        
        project = os.path.abspath(project)
        
        cmd = [
            self.tool_path,
            "-j0",
            "-b",
            project
        ]
        
        try:
            print(f"[Keil] 编译: {project}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + "\n" + result.stderr
            
            if result.returncode == 0:
                return True, "编译成功\n" + output
            else:
                return False, f"编译失败 (code {result.returncode})\n{output}"
        
        except subprocess.TimeoutExpired:
            return False, "编译超时（超过5分钟）"
        except FileNotFoundError:
            return False, f"未找到 UV4.exe，请确认 Keil MDK 已安装并在 PATH 中"
        except Exception as e:
            return False, f"编译异常: {str(e)}"
    
    def get_output_path(self, project_path: str = None) -> str:
        """获取输出文件路径"""
        project = project_path or self.project_path
        if not project:
            project = self.find_project()
        
        project_dir = os.path.dirname(os.path.abspath(project))
        
        extensions = [".hex", ".bin", ".axf"]
        for ext in extensions:
            for root, _, files in os.walk(project_dir):
                for f in files:
                    if f.endswith(ext):
                        return os.path.join(root, f)
        
        return None
