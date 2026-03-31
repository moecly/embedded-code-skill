import os
import subprocess
import shutil
from .base import BuilderBase


class CMakeBuilder(BuilderBase):
    name = "CMake"
    type = "cmake"
    project_extensions = ["CMakeLists.txt"]
    
    def __init__(self, tool_path: str = None, project_path: str = None, build_dir: str = "build"):
        super().__init__(tool_path, project_path)
        self.build_dir = build_dir
        if not self.tool_path:
            self.tool_path = self._find_tool()
    
    def _find_tool(self) -> str:
        """查找 cmake 工具"""
        return shutil.which("cmake") or "cmake"
    
    def detect_tool(self) -> bool:
        """检测 cmake 是否可用"""
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
        """查找 CMakeLists.txt"""
        root_path = os.path.abspath(root)
        
        cmake_path = os.path.join(root_path, "CMakeLists.txt")
        if os.path.exists(cmake_path):
            return cmake_path
        
        for dirpath, _, filenames in os.walk(root_path):
            if "CMakeLists.txt" in filenames:
                return os.path.join(dirpath, "CMakeLists.txt")
        
        raise FileNotFoundError("未找到 CMakeLists.txt")
    
    def _configure(self, source_dir: str, build_dir: str, generator: str = None) -> tuple:
        """CMake 配置"""
        cmd = [self.tool_path, "-S", source_dir, "-B", build_dir]
        
        if generator:
            cmd.extend(["-G", generator])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, "CMake 配置成功"
            else:
                return False, f"CMake 配置失败:\n{result.stderr}"
        
        except Exception as e:
            return False, f"CMake 配置异常: {str(e)}"
    
    def build(self, project_path: str = None, build_dir: str = None, clean: bool = False) -> tuple:
        """编译 CMake 项目"""
        cmake_file = project_path or self.project_path
        
        if not cmake_file:
            cmake_file = self.find_project()
        
        if not os.path.exists(cmake_file):
            return False, f"CMakeLists.txt 不存在: {cmake_file}"
        
        source_dir = os.path.dirname(os.path.abspath(cmake_file))
        build = build_dir or self.build_dir
        build_dir_abs = os.path.join(source_dir, build)
        
        if clean and os.path.exists(build_dir_abs):
            import shutil as sh
            sh.rmtree(build_dir_abs)
        
        os.makedirs(build_dir_abs, exist_ok=True)
        
        print(f"[CMake] 配置 (源码: {source_dir}, 构建: {build_dir_abs})")
        success, msg = self._configure(source_dir, build_dir_abs)
        if not success:
            return False, msg
        
        print(f"[CMake] 编译...")
        try:
            result = subprocess.run(
                [self.tool_path, "--build", build_dir_abs, "--", "-j4"],
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
        except Exception as e:
            return False, f"编译异常: {str(e)}"
    
    def get_output_path(self, build_dir: str = None) -> str:
        """获取输出文件路径"""
        cmake_file = self.project_path or self.find_project()
        source_dir = os.path.dirname(os.path.abspath(cmake_file))
        search_dir = os.path.join(source_dir, build_dir or self.build_dir)
        
        if not os.path.exists(search_dir):
            return None
        
        extensions = [".elf", ".bin", ".hex"]
        for ext in extensions:
            for root, _, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(ext):
                        return os.path.join(root, f)
        
        return None
