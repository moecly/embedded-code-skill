#!/usr/bin/env python3
"""
嵌入式调试闭环 - 编译 → 烧录 → 监控 → 分析 → 循环
"""
import os
import sys
import yaml
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builder import (
    KeilBuilder,
    MakefileBuilder,
    CMakeBuilder,
    detect_projects,
)
from tools.flashers import (
    JLinkFlasher,
    STLinkFlasher,
    CMSISDAPFlasher,
    list_serial_ports,
)
from tools.monitor import SerialMonitor, LoopLogger


def normalize_path(path_str, base_dir=None):
    """规范化路径为正斜杠格式，跨平台兼容"""
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


class DebugLoop:
    def __init__(self, config_path: str = "configs/project.yaml"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.config_dir = os.path.dirname(os.path.abspath(config_path))
        self.builder = None
        self.flasher = None
        self.monitor = None
        self.logger = LoopLogger(self.config.get('debug', {}).get('log_dir', 'logs'))
        self.project_path = None
        self.output_path = None
    
    def _load_config(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_config(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)
    
    def detect_environment(self):
        """检测构建和烧录环境"""
        print("\n" + "=" * 50)
        print("环境检测")
        print("=" * 50)
        
        search_root_config = self.config.get('build', {}).get('search_root', '..')
        search_root = os.path.normpath(os.path.join(self.config_dir, search_root_config))
        
        print(f"\n[1] 检测项目文件 (搜索: {search_root})...")
        projects = detect_projects(search_root)
        if projects:
            for p in projects:
                print(f"    {p.type.upper()}: {p.name}")
                print(f"      路径: {p.path}")
        else:
            print("    未找到项目文件")
        
        print("\n[2] 检测编译工具...")
        keil = KeilBuilder()
        print(f"    Keil MDK: [OK]" if keil.detect_tool() else f"    Keil MDK: [FAIL]")
        
        make = MakefileBuilder()
        print(f"    Make: [OK]" if make.detect_tool() else f"    Make: [FAIL]")
        
        cmake = CMakeBuilder()
        print(f"    CMake: [OK]" if cmake.detect_tool() else f"    CMake: [FAIL]")
        
        print("\n[3] 检测烧录器...")
        flashers = self._detect_flashers()
        
        print("\n[4] 可用串口:")
        ports = list_serial_ports()
        if ports:
            for p in ports:
                print(f"    {p['port']}: {p['description']}")
        else:
            print("    未发现串口")
        
        return projects, flashers, ports
    
    def _detect_flashers(self) -> list:
        """检测可用的烧录器"""
        flashers = []
        
        jlink = JLinkFlasher()
        if jlink.detect():
            flashers.append(("jlink", jlink))
            print("    JLink: [OK]")
        
        stlink = STLinkFlasher()
        if stlink.detect():
            flashers.append(("stlink", stlink))
            print("    STLink: [OK]")
        
        cmsis = CMSISDAPFlasher()
        if cmsis.detect():
            flashers.append(("cmsis_dap", cmsis))
            print("    CMSIS-DAP: [OK]")
        
        if not flashers:
            print("    未发现烧录器")
        
        return flashers
    
    def init_builder(self, project_path: str = None):
        """初始化构建器"""
        build_config = self.config.get('build', {})
        project_type = build_config.get('type', '').lower()
        
        if not project_path:
            projects = detect_projects(build_config.get('search_root', '.'))
            if not projects:
                raise FileNotFoundError("未找到项目文件")
            project_path = projects[0].path
            project_type = projects[0].type
        
        tool_path = None
        if project_type == 'keil':
            tool_path = build_config.get('keil', {}).get('path')
            self.builder = KeilBuilder(tool_path=tool_path, project_path=project_path)
        elif project_type == 'makefile':
            cmd = build_config.get('makefile', {}).get('cmd', 'make -j4')
            self.builder = MakefileBuilder(tool_path=tool_path, project_path=project_path, build_cmd=cmd)
        elif project_type == 'cmake':
            build_dir = build_config.get('cmake', {}).get('build_dir', 'build')
            self.builder = CMakeBuilder(tool_path=tool_path, project_path=project_path, build_dir=build_dir)
        else:
            raise ValueError(f"不支持的项目类型: {project_type}")
        
        self.project_path = project_path
        return self.builder
    
    def init_flasher(self, flasher_type: str = None, device: str = None):
        """初始化烧录器"""
        flasher_config = self.config.get('flasher', {})
        
        ftype = flasher_type or flasher_config.get('type', 'jlink').lower()
        dev = device or flasher_config.get('device')
        speed = flasher_config.get('speed', 4000)
        interface = flasher_config.get('interface', 'SWD')
        
        if ftype == 'jlink':
            self.flasher = JLinkFlasher(device=dev, speed=speed, interface=interface)
        elif ftype == 'stlink':
            self.flasher = STLinkFlasher(device=dev, speed=speed, interface=interface)
        elif ftype == 'cmsis_dap':
            self.flasher = CMSISDAPFlasher(device=dev, speed=speed, interface=interface)
        else:
            raise ValueError(f"不支持的烧录器: {ftype}")
        
        return self.flasher
    
    def init_serial(self, port: str = None, baudrate: int = None):
        """初始化串口"""
        serial_config = self.config.get('serial', {})
        
        p = port or serial_config.get('port')
        br = baudrate or serial_config.get('baudrate', 115200)
        timeout = serial_config.get('timeout', 10)
        
        if not p:
            ports = list_serial_ports()
            if ports:
                p = ports[0]['port']
        
        if p:
            self.monitor = SerialMonitor(p, br, timeout)
            if self.monitor.open():
                print(f"[串口] 已连接 {p}")
                return self.monitor
        
        print("[警告] 无法连接串口，将跳过监控")
        return None
    
    def build(self) -> tuple:
        """编译固件"""
        if not self.builder:
            raise RuntimeError("未初始化构建器")
        
        print(f"\n[编译] {self.project_path}")
        success, output = self.builder.build()
        
        if success:
            self.output_path = self.builder.get_output_path()
            print(f"[编译] 成功")
            if self.output_path:
                print(f"[输出] {self.output_path}")
        else:
            print(f"[编译] 失败")
        
        return success, output
    
    def flash(self) -> tuple:
        """烧录固件"""
        if not self.flasher:
            raise RuntimeError("未初始化烧录器")
        
        elf_path = self.output_path or self.config.get('flash', {}).get('elf')
        
        if not elf_path:
            print("[错误] 未配置烧录文件")
            return False, "未配置烧录文件"
        
        # 规范化路径
        elf_path = normalize_path(elf_path, self.config_dir)
        
        # 检查文件是否存在
        p = Path(elf_path)
        if not p.exists():
            # 如果是相对路径，尝试相对于工程目录
            if self.project_path:
                project_dir = str(Path(self.project_path).parent)
                elf_path2 = normalize_path(self.config.get('flash', {}).get('elf'), project_dir)
                p = Path(elf_path2)
            
        if not p.exists():
            print(f"[错误] 文件不存在: {elf_path}")
            return False, f"文件不存在: {elf_path}"
        
        # 获取绝对路径
        elf_path = str(p.absolute())
        
        print(f"\n[烧录] {elf_path}")
        success = self.flasher.flash(elf_path)
        result = "成功" if success else "失败"
        print(f"[烧录] {result}")
        
        return success, result
    
    def reset(self) -> bool:
        """重置芯片"""
        if not self.flasher:
            return False
        
        print("\n[重置] 复位芯片...")
        return self.flasher.reset()
    
    def monitor_serial(self, duration: float = 10.0) -> str:
        """监控串口输出"""
        if not self.monitor:
            return ""
        
        print(f"\n[监控] 监听串口 {duration} 秒...")
        print("-" * 50)
        
        self.monitor.clear_buffer()
        output = self.monitor.read_lines(duration)
        
        print("-" * 50)
        print(f"[输出] 共 {len(output)} 行")
        
        return '\n'.join(output)
    
    def run(self, max_retries: int = 3) -> bool:
        """运行调试闭环"""
        print("\n" + "=" * 50)
        print("嵌入式调试闭环")
        print("=" * 50)
        
        print("\n[初始化] 检测环境...")
        projects, flashers, ports = self.detect_environment()
        
        if not projects:
            print("\n[错误] 未找到项目文件")
            return False
        
        print("\n[初始化] 初始化构建器...")
        try:
            self.init_builder()
        except Exception as e:
            print(f"[错误] {e}")
            return False
        
        if self.builder and not self.builder.detect_tool():
            print(f"\n[错误] 构建工具不可用")
            return False
        
        print("\n[初始化] 初始化烧录器...")
        if flashers:
            self.init_flasher(flasher_type=flashers[0][0])
        else:
            default_type = self.config.get('flasher', {}).get('type', 'jlink')
            self.init_flasher(flasher_type=default_type)
        
        print("\n[初始化] 连接串口...")
        self.init_serial()
        
        print("\n" + "=" * 50)
        print(f"开始调试闭环 (最多 {max_retries} 次)")
        print("=" * 50)
        
        for loop in range(1, max_retries + 1):
            print(f"\n{'=' * 50}")
            print(f"循环 {loop}/{max_retries}")
            print(f"{'=' * 50}")
            
            self.logger.log_loop_start(loop, self.config)
            
            print("\n[步骤1] 编译...")
            success, output = self.build()
            self.logger.log_flash_result(success, output)
            
            if not success:
                print("[错误] 编译失败")
                self.logger.log_loop_end(False)
                continue
            
            print("\n[步骤2] 烧录...")
            success, output = self.flash()
            self.logger.log_flash_result(success, output)
            
            if not success:
                print("[错误] 烧录失败")
                self.logger.log_loop_end(False)
                continue
            
            print("\n[步骤3] 重置...")
            self.reset()
            time.sleep(1)
            
            if self.monitor:
                print("\n[步骤4] 监控串口...")
                serial_output = self.monitor_serial(duration=10.0)
                self.logger.log_serial_output(serial_output)
                
                if serial_output and len(serial_output) > 5:
                    print(f"\n[成功] 串口有输出")
                    self.logger.log_loop_end(True)
                    self.monitor.close()
                    print("\n" + "=" * 50)
                    print("调试完成!")
                    print("=" * 50)
                    self.logger.generate_report(True)
                    return True
                else:
                    print(f"\n[失败] 无串口输出或输出异常")
            else:
                print("\n[跳过] 串口未连接")
            
            self.logger.log_loop_end(False)
            
            if loop < max_retries:
                print("\n" + "-" * 50)
                print("请检查代码，描述需要修改的内容")
                print("-" * 50)
                print("\n[等待用户修改代码...]")
                return False
        
        if self.monitor:
            self.monitor.close()
        
        print("\n" + "=" * 50)
        print("调试失败，已达到最大重试次数")
        print("=" * 50)
        report_path = self.logger.generate_report(False)
        print(f"\n报告已保存: {report_path}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='嵌入式调试闭环')
    parser.add_argument('--config', '-c', default='configs/project.yaml', help='配置文件路径')
    parser.add_argument('--detect', action='store_true', help='仅检测环境')
    args = parser.parse_args()
    
    loop = DebugLoop(args.config)
    
    if args.detect:
        loop.detect_environment()
    else:
        max_retries = loop.config.get('debug', {}).get('max_retries', 3)
        success = loop.run(max_retries=max_retries)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
