import os
import subprocess
import shutil
from .base import BuilderBase


class MakefileBuilder(BuilderBase):
    name = "Makefile"
    type = "makefile"
    project_extensions = ["Makefile", "makefile"]
    
    def __init__(self, tool_path: str = None, project_path: str = None, build_cmd: str = "make -j4"):
        super().__init__(tool_path, project_path)
        self.build_cmd = build_cmd
        if not self.tool_path:
            self.tool_path = self._find_tool()
    
    def _find_tool(self) -> str:
        """查找 make 工具"""
        for tool in ["make", "mingw32-make", "make.exe", "mingw32-make.exe"]:
            found = shutil.which(tool)
            if found:
                return found
        return "make"
    
    def detect_tool(self) -> bool:
        """检测 make 是否可用"""
        try:
            result = subprocess.run(
                [self.tool_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def find_project(self, root: str = ".") -> str:
        """查找 Makefile"""
        root_path = os.path.abspath(root)
        
        makefile_path = os.path.join(root_path, "Makefile")
        if os.path.exists(makefile_path):
            return makefile_path
        
        makefile_path = os.path.join(root_path, "makefile")
        if os.path.exists(makefile_path):
            return makefile_path
        
        for dirpath, _, filenames in os.walk(root_path):
            if "Makefile" in filenames:
                return os.path.join(dirpath, "Makefile")
            if "makefile" in filenames:
                return os.path.join(dirpath, "makefile")
        
        raise FileNotFoundError("未找到 Makefile")
    
    def build(self, project_path: str = None, build_dir: str = None) -> tuple:
        """编译 Makefile 项目"""
        makefile = project_path or self.project_path
        
        if not makefile:
            makefile = self.find_project()
        
        if not os.path.exists(makefile):
            return False, f"Makefile 不存在: {makefile}"
        
        makefile_dir = os.path.dirname(os.path.abspath(makefile))
        if build_dir:
            work_dir = build_dir
        else:
            work_dir = makefile_dir
        
        try:
            print(f"[Makefile] 编译 (目录: {work_dir})")
            result = subprocess.run(
                self.build_cmd,
                shell=True,
                cwd=work_dir,
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
            return False, "未找到 make 命令，请确认已安装 MinGW/MSYS2/GCC ARM Embedded"
        except Exception as e:
            return False, f"编译异常: {str(e)}"
    
    def get_output_path(self, build_dir: str = None) -> str:
        """获取输出文件路径"""
        makefile = self.project_path or self.find_project()
        makefile_dir = os.path.dirname(os.path.abspath(makefile))
        
        search_dir = build_dir or makefile_dir
        
        extensions = [".elf", ".bin", ".hex"]
        for ext in extensions:
            for root, _, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(ext):
                        return os.path.join(root, f)
        
        return None
