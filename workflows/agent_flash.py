#!/usr/bin/env python3
"""
Agent 专用烧录脚本 - 提供简单的命令行接口

用法:
    python agent_flash.py --project <工程目录> [--flasher <类型>] [--device <芯片>] [--serial <端口>]
    python agent_flash.py --detect              # 仅检测环境
    python agent_flash.py --help               # 显示帮助

示例:
    python agent_flash.py --project D:/workspacePrj/JL5104
    python agent_flash.py --project D:/workspacePrj/JL5104 --flasher jlink --device STM32F407ZGTx
"""
import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builder import detect_projects
from tools.flashers import (
    JLinkFlasher,
    STLinkFlasher,
    CMSISDAPFlasher,
    list_serial_ports,
)
from tools.monitor import SerialMonitor
from tools.builder import (
    KeilBuilder,
    MakefileBuilder,
    CMakeBuilder,
)


def normalize_path(path_str, base_dir=None):
    """
    规范化路径为正斜杠格式，跨平台兼容
    
    Args:
        path_str: 原始路径字符串
        base_dir: 基础目录（用于相对路径）
    
    Returns:
        规范化后的正斜杠路径字符串
    """
    if not path_str:
        return path_str
    
    # 如果包含反斜杠，先替换
    path_str = path_str.replace('\\', '/')
    
    # 如果是相对路径，结合 base_dir
    if base_dir and not path_str.startswith('/') and ':' not in path_str:
        base_dir = base_dir.replace('\\', '/')
        path_str = f"{base_dir}/{path_str}"
    
    # 使用 pathlib 处理并返回正斜杠格式
    try:
        p = Path(path_str)
        return p.as_posix()
    except Exception:
        return path_str


def validate_path(path_str, base_dir=None):
    """
    验证路径是否存在
    
    Args:
        path_str: 路径字符串
        base_dir: 基础目录
    
    Returns:
        (规范化路径, 错误信息) - 成功时错误信息为 None
    """
    if not path_str:
        return None, "路径为空"
    
    # 规范化路径
    normalized = normalize_path(path_str, base_dir)
    
    # 检查是否为绝对路径
    if normalized.startswith('/') or ':' in normalized:
        check_path = normalized
    elif base_dir:
        check_path = f"{base_dir}/{normalized}"
    else:
        check_path = normalized
    
    # 转换为 Path 对象检查
    p = Path(check_path)
    if p.exists():
        return normalize_path(str(p.absolute())), None
    else:
        return normalized, f"文件不存在: {check_path}"


def detect_environment():
    """检测环境并返回结果"""
    result = {
        "flashers": [],
        "serial_ports": [],
        "projects": []
    }
    
    print("检测烧录器...")
    jlink = JLinkFlasher()
    if jlink.detect():
        result["flashers"].append({
            "type": "jlink",
            "available": True,
            "devices": jlink.list_devices()
        })
    
    stlink = STLinkFlasher()
    if stlink.detect():
        result["flashers"].append({
            "type": "stlink",
            "available": True,
            "devices": stlink.list_devices()
        })
    
    cmsis = CMSISDAPFlasher()
    if cmsis.detect():
        result["flashers"].append({
            "type": "cmsis_dap",
            "available": True,
            "devices": cmsis.list_devices()
        })
    
    print("检测串口...")
    for port in list_serial_ports():
        result["serial_ports"].append(port)
    
    return result


def auto_detect_project(search_root):
    """自动检测项目"""
    print(f"搜索项目: {search_root}")
    projects = detect_projects(search_root)
    if projects:
        return projects[0]
    return None


def flash_with_jlink(elf_path, device="STM32F407ZG", speed=4000, interface="SWD"):
    """使用 JLink 烧录"""
    print(f"\n烧录: {elf_path}")
    print(f"设备: {device}, 接口: {interface}, 速度: {speed} KHz")
    
    flasher = JLinkFlasher(device=device, speed=speed, interface=interface)
    
    if flasher.flash(elf_path):
        print("烧录成功!")
        return True
    else:
        print("烧录失败!")
        return False


def build_project(project_path, project_type="keil"):
    """编译项目"""
    print(f"\n编译项目: {project_path}")
    
    if project_type == "keil":
        builder = KeilBuilder(project_path=project_path)
        if builder.detect_tool():
            success, output = builder.build()
            if success:
                print("编译成功!")
                return builder.get_output_path()
            else:
                print(f"编译失败: {output}")
                return None
        else:
            print("Keil MDK 不可用")
            return None
    
    return None


def monitor_serial(port, baudrate=115200, timeout=10):
    """监控串口"""
    print(f"\n监控串口 {port} @ {baudrate} bps ({timeout}s)...")
    print("-" * 50)
    
    try:
        monitor = SerialMonitor(port, baudrate, timeout)
        if not monitor.open():
            print("无法打开串口")
            return None
        
        output_lines = monitor.read_lines(timeout)
        monitor.close()
        
        print("-" * 50)
        print(f"输出 {len(output_lines)} 行:")
        for line in output_lines:
            print(line)
        
        return '\n'.join(output_lines)
    except Exception as e:
        print(f"串口监控失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Agent 专用烧录脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  检测环境:
    python agent_flash.py --detect
  
  烧录并监控:
    python agent_flash.py --project D:/workspacePrj/JL5104 --elf MDK-ARM/test0/test0.elf
  
  指定设备:
    python agent_flash.py --project D:/workspacePrj/JL5104 --flasher jlink --device STM32F407ZGTx --serial COM3
        """
    )
    
    parser.add_argument('--project', '-p', help='工程目录路径')
    parser.add_argument('--elf', '-e', help='ELF/Hex 文件路径（相对于工程目录）')
    parser.add_argument('--flasher', '-f', default='jlink', 
                       choices=['jlink', 'stlink', 'cmsis_dap'],
                       help='烧录器类型 (默认: jlink)')
    parser.add_argument('--device', '-d', help='芯片型号 (如 STM32F407ZGTx)')
    parser.add_argument('--serial', '-s', help='串口端口 (如 COM3)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200,
                       help='串口波特率 (默认: 115200)')
    parser.add_argument('--speed', type=int, default=4000,
                       help='烧录速度 KHz (默认: 4000)')
    parser.add_argument('--interface', '-i', default='SWD',
                       choices=['SWD', 'JTAG'],
                       help='烧录接口 (默认: SWD)')
    parser.add_argument('--monitor-timeout', '-t', type=int, default=10,
                       help='串口监控超时秒数 (默认: 10)')
    parser.add_argument('--detect', action='store_true',
                       help='仅检测环境，不烧录')
    parser.add_argument('--build', action='store_true',
                       help='编译后再烧录')
    parser.add_argument('--skip-monitor', action='store_true',
                       help='跳过串口监控')
    parser.add_argument('--json', action='store_true',
                       help='输出 JSON 格式结果')
    
    args = parser.parse_args()
    
    if args.detect:
        result = detect_environment()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n=== 烧录器 ===")
            if result["flashers"]:
                for f in result["flashers"]:
                    print(f"  {f['type']}: 可用")
                    for d in f.get('devices', []):
                        print(f"    {d}")
            else:
                print("  无可用烧录器")
            
            print("\n=== 串口 ===")
            if result["serial_ports"]:
                for p in result["serial_ports"]:
                    print(f"  {p['port']}: {p['description']}")
            else:
                print("  无可用串口")
        return
    
    if not args.project:
        print("错误: 需要指定 --project 参数")
        parser.print_help()
        sys.exit(1)
    
    # 规范化工程目录路径
    project_dir = normalize_path(args.project)
    
    # 验证工程目录
    project_dir, error = validate_path(project_dir)
    if error:
        print(f"错误: {error}")
        sys.exit(1)
    
    print("=" * 50)
    print("Agent Flash Tool")
    print("=" * 50)
    
    print(f"\n工程目录: {project_dir}")
    
    if args.build:
        project = auto_detect_project(project_dir)
        if project:
            elf = build_project(project.path, project.type)
        else:
            print("未找到项目文件，跳过编译")
    
    if args.elf:
        # 规范化并验证 ELF 文件路径
        elf_path, error = validate_path(args.elf, project_dir)
        if error:
            print(f"错误: {error}")
            sys.exit(1)
    else:
        elf_path = None
    
    if elf_path:
        if args.flasher == 'jlink':
            flash_with_jlink(
                elf_path,
                device=args.device or "STM32F407ZG",
                speed=args.speed,
                interface=args.interface
            )
    else:
        print("未指定 --elf 参数或文件不存在")
    
    if not args.skip_monitor and args.serial:
        monitor_serial(args.serial, args.baudrate, args.monitor_timeout)


if __name__ == "__main__":
    main()
