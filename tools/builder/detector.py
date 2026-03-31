import os
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path


@dataclass
class ProjectInfo:
    type: str
    path: str
    name: str
    root_dir: str


class ProjectDetector:
    PROJECT_PATTERNS = {
        "keil": ["*.uvprojx", "*.uvproj"],
        "makefile": ["Makefile", "makefile"],
        "cmake": ["CMakeLists.txt"]
    }
    
    def __init__(self, search_root: str = "."):
        self.search_root = os.path.abspath(search_root)
    
    def find_all_projects(self) -> List[ProjectInfo]:
        """查找所有项目"""
        projects = []
        
        for dirpath, dirnames, filenames in os.walk(self.search_root):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                
                for ptype, patterns in self.PROJECT_PATTERNS.items():
                    for pattern in patterns:
                        if self._match_pattern(filename, pattern):
                            projects.append(ProjectInfo(
                                type=ptype,
                                path=filepath,
                                name=filename,
                                root_dir=dirpath
                            ))
                            break
        
        return projects
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """匹配文件名模式"""
        if pattern.startswith("*"):
            return filename.endswith(pattern[1:])
        return filename == pattern
    
    def find_by_type(self, project_type: str) -> List[ProjectInfo]:
        """查找指定类型的项目"""
        all_projects = self.find_all_projects()
        return [p for p in all_projects if p.type == project_type]
    
    def format_projects(self, projects: List[ProjectInfo]) -> str:
        """格式化项目列表为可读字符串"""
        if not projects:
            return "未找到项目"
        
        result = []
        for i, p in enumerate(projects, 1):
            result.append(f"  [{i}] {p.type.upper()}: {p.name}")
            result.append(f"      路径: {p.path}")
            result.append(f"      目录: {p.root_dir}")
            result.append("")
        
        return "\n".join(result)


def detect_projects(search_root: str = ".") -> List[ProjectInfo]:
    """快速检测项目"""
    detector = ProjectDetector(search_root)
    return detector.find_all_projects()
