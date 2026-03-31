#!/usr/bin/env python3
"""
构建脚本 - 支持多种编译器的统一入口
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builder import (
    KeilBuilder,
    MakefileBuilder,
    CMakeBuilder,
    ProjectDetector,
    detect_projects,
)


def normalize_path(path_str, base_dir=None):
    """
    规范化路径为正斜杠格式，跨平台兼容
    """
    if not path_str:
        return path_str
    
    path_str = path_str.replace('\\', '/')
    
    if base_dir and not path_str.startswith('/') and ':' not in path_str:
        base_dir = base_dir.replace('\\', '/')
        path_str = f"{base_dir}/{path_str}"
    
    try:
        p = Path(path_str)
        return p.as_posix()
    except Exception:
        return path_str


class BuildManager:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.builder = None
        self.project_path = None
    
    def detect_projects(self, search_root: str = ".") -> list:
        """检测项目"""
        normalized = normalize_path(search_root)
        return detect_projects(normalized)
    
    def select_project(self, projects: list, index: int = None) -> str:
        """选择项目"""
        if not projects:
            raise FileNotFoundError("未找到任何项目")
        
        if len(projects) == 1:
            return projects[0].path
        
        if index is not None and 0 <= index < len(projects):
            return projects[index].path
        
        print("\n找到多个项目，请选择:")
        for i, p in enumerate(projects, 1):
            print(f"  [{i}] {p.type.upper()}: {p.name}")
            print(f"      {p.path}")
        
        while True:
            try:
                choice = input("\n请输入序号: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    return projects[idx].path
            except ValueError:
                pass
            print("无效输入，请重新输入")
    
    def create_builder(self, project_type: str = None, project_path: str = None, tool_path: str = None):
        """创建构建器"""
        ptype = project_type or self.config.get('type', '').lower()
        
        if ptype == 'keil':
            self.builder = KeilBuilder(tool_path=tool_path, project_path=project_path)
        elif ptype == 'makefile':
            build_cmd = self.config.get('makefile', {}).get('cmd', 'make -j4')
            self.builder = MakefileBuilder(tool_path=tool_path, project_path=project_path, build_cmd=build_cmd)
        elif ptype == 'cmake':
            build_dir = self.config.get('cmake', {}).get('build_dir', 'build')
            self.builder = CMakeBuilder(tool_path=tool_path, project_path=project_path, build_dir=build_dir)
        else:
            raise ValueError(f"不支持的项目类型: {ptype}")
        
        return self.builder
    
    def build(self, project_path: str = None) -> tuple:
        """执行构建"""
        if not self.builder:
            raise RuntimeError("未创建构建器，请先调用 create_builder")
        
        return self.builder.build(project_path)
    
    def get_output(self) -> str:
        """获取输出文件路径"""
        if not self.builder:
            return None
        return self.builder.get_output_path()


def detect_build_environment(search_root: str = ".") -> dict:
    """检测构建环境"""
    result = {
        "projects": [],
        "available_tools": [],
        "summary": {
            "total_projects": 0,
            "available_builders": 0
        }
    }
    
    normalized_root = normalize_path(search_root)
    
    print("检测项目文件...", file=sys.stderr)
    projects = detect_projects(normalized_root)
    result["projects"] = [
        {
            "type": p.type,
            "path": normalize_path(p.path),
            "name": p.name,
            "root_dir": normalize_path(p.root_dir)
        }
        for p in projects
    ]
    result["summary"]["total_projects"] = len(projects)
    
    print("检测编译工具...", file=sys.stderr)
    tools_status = []
    
    keil = KeilBuilder()
    tools_status.append({
        "type": "keil",
        "name": "Keil MDK",
        "available": keil.detect_tool(),
        "tool_path": normalize_path(keil.tool_path)
    })
    
    makefile = MakefileBuilder()
    tools_status.append({
        "type": "makefile",
        "name": "Make",
        "available": makefile.detect_tool(),
        "tool_path": normalize_path(makefile.tool_path)
    })
    
    cmake = CMakeBuilder()
    tools_status.append({
        "type": "cmake",
        "name": "CMake",
        "available": cmake.detect_tool(),
        "tool_path": normalize_path(cmake.tool_path)
    })
    
    result["available_tools"] = tools_status
    result["summary"]["available_builders"] = sum(1 for t in tools_status if t["available"])
    
    return result


def print_human_readable(result: dict):
    """打印人类可读格式"""
    print("\n" + "=" * 50)
    print("构建环境检测结果")
    print("=" * 50)
    
    print("\n【项目文件】")
    if result["projects"]:
        for p in result["projects"]:
            print(f"  {p['type'].upper()}: {p['name']}")
            print(f"    路径: {p['path']}")
    else:
        print("  未找到项目文件")
    
    print("\n【编译工具】")
    for tool in result["available_tools"]:
        status = "✓ 可用" if tool["available"] else "✗ 不可用"
        print(f"  {tool['name']}: {status}")
        if tool["available"]:
            print(f"    路径: {tool['tool_path']}")
    
    print("\n" + "-" * 50)
    print(f"项目: {result['summary']['total_projects']} 个")
    print(f"可用工具: {result['summary']['available_builders']} 个")
    print("=" * 50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='嵌入式固件构建工具')
    parser.add_argument('--detect', action='store_true', help='检测构建环境')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('--human', action='store_true', help='输出人类可读格式')
    parser.add_argument('--search', '-s', default='.', help='搜索目录')
    parser.add_argument('--build', '-b', metavar='PROJECT', help='编译指定项目文件路径')
    parser.add_argument('--clean', action='store_true', help='清理后编译')
    args = parser.parse_args()
    
    if args.build:
        project_path = normalize_path(args.build)
        print(f"编译项目: {project_path}")
        
        from tools.builder.detector import ProjectDetector
        detector = ProjectDetector()
        
        from pathlib import Path
        p = Path(project_path)
        ptype = None
        if p.suffix in ['.uvprojx', '.uvproj']:
            ptype = 'keil'
        elif p.name in ['Makefile', 'makefile']:
            ptype = 'makefile'
        elif p.name == 'CMakeLists.txt':
            ptype = 'cmake'
        
        if not ptype:
            print(f"错误: 无法识别的项目类型: {project_path}")
            sys.exit(1)
        
        print(f"项目类型: {ptype}")
        
        if ptype == 'keil':
            builder = KeilBuilder(project_path=project_path)
        elif ptype == 'makefile':
            builder = MakefileBuilder(project_path=project_path)
        elif ptype == 'cmake':
            builder = CMakeBuilder(project_path=project_path)
        else:
            print(f"错误: 不支持的项目类型: {ptype}")
            sys.exit(1)
        
        if not builder.detect_tool():
            print(f"错误: 未找到编译工具")
            sys.exit(1)
        
        print(f"编译工具: {builder.tool_path}")
        success, output = builder.build()
        
        if args.json:
            result = {
                "success": success,
                "output": output,
                "output_path": builder.get_output_path() if success else None
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if success:
                print(f"\n编译成功!")
                output_path = builder.get_output_path()
                if output_path:
                    print(f"输出文件: {output_path}")
            else:
                print(f"\n编译失败!")
                print(output)
        
        sys.exit(0 if success else 1)
    
    if args.detect:
        result = detect_build_environment(args.search)
        if args.json or not args.human:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_human_readable(result)
    else:
        result = detect_build_environment(args.search)
        print_human_readable(result)
        
        if result["summary"]["total_projects"] == 0:
            print("\n错误: 未找到项目文件")
            sys.exit(1)
        
        print("\n输入 --detect 查看详细信息")
        print("输入 --json 查看 JSON 格式")


if __name__ == "__main__":
    main()
