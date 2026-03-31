from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import shutil
import os


@dataclass
class BuilderInfo:
    name: str
    type: str
    available: bool
    tool_path: Optional[str] = None
    project_path: Optional[str] = None
    reason: Optional[str] = None


class BuilderBase(ABC):
    name: str = "base"
    type: str = "base"
    project_extensions: List[str] = []
    
    def __init__(self, tool_path: Optional[str] = None, project_path: Optional[str] = None):
        self.tool_path = tool_path
        self.project_path = project_path
    
    @abstractmethod
    def detect_tool(self) -> bool:
        """检测编译工具是否可用"""
        pass
    
    @abstractmethod
    def build(self, project_path: Optional[str] = None) -> tuple:
        """
        执行编译
        返回: (success: bool, output: str)
        """
        pass
    
    def get_info(self) -> BuilderInfo:
        """获取构建器信息"""
        available = self.detect_tool()
        return BuilderInfo(
            name=self.name,
            type=self.type,
            available=available,
            tool_path=self.tool_path,
            project_path=self.project_path,
            reason=None if available else f"{self.name} tool not found"
        )
    
    def find_project(self, root: str = ".") -> Optional[str]:
        """在指定目录查找项目文件"""
        for ext in self.project_extensions:
            for path in self._search_files(root, ext):
                return path
        return None
    
    def _search_files(self, root: str, extension: str) -> List[str]:
        """递归搜索文件"""
        results = []
        root_path = os.path.abspath(root)
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                if filename.endswith(extension):
                    results.append(os.path.join(dirpath, filename))
        
        return results


class BuilderManager:
    def __init__(self):
        self.builders = {}
    
    def register(self, builder: BuilderBase):
        self.builders[builder.type] = builder
    
    def get(self, build_type: str) -> Optional[BuilderBase]:
        return self.builders.get(build_type.lower())
    
    def detect_all(self) -> List[BuilderInfo]:
        """检测所有构建器"""
        infos = []
        for builder in self.builders.values():
            infos.append(builder.get_info())
        return infos
    
    def get_available(self) -> List[BuilderInfo]:
        """获取可用的构建器"""
        return [info for info in self.detect_all() if info.available]
