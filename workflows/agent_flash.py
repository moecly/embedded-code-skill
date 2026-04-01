#!/usr/bin/env python3
"""
Agent 专用烧录脚本 - 提供简单的命令行接口

用法:
    python agent_flash.py --project <工程目录> [--flash <文件>] [--device <芯片>] [--serial <端口>]
    python agent_flash.py --detect              # 仅检测环境
    python agent_flash.py --init               # 首次初始化项目配置
    python agent_flash.py --help               # 显示帮助

示例:
    python agent_flash.py --project D:/project/firmware --init
    python agent_flash.py --project D:/project/firmware --flash MDK-ARM/project/project.hex
    python agent_flash.py --project D:/project/firmware --flash firmware.bin --addr 0x08000000
"""
import sys
import os
import json
import yaml
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builder import detect_projects, KeilBuilder, MakefileBuilder, CMakeBuilder
from tools.flashers import (
    JLinkFlasher,
    STLinkFlasher,
    CMSISDAPFlasher,
    list_serial_ports,
)
from tools.monitor import SerialMonitor


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


def get_flash_info(flash_path, addr=None):
    """分析烧录文件类型，返回文件信息和错误"""
    if not flash_path:
        return None, "烧录文件路径为空"
    
    ext = Path(flash_path).suffix.lower()
    
    if ext == '.bin':
        if not addr:
            return None, f"错误: .bin 文件需要指定 --addr 参数（如 --addr 0x08000000）"
        return {'type': 'bin', 'addr': addr, 'path': flash_path}, None
    
    elif ext in ['.hex', '.elf']:
        return {'type': ext.lstrip('.'), 'path': flash_path}, None
    
    else:
        return None, f"错误: 不支持的文件格式 {ext}，仅支持 .elf/.hex/.bin"


def flash_with_jlink(flash_info, device="STM32F407ZG", speed=4000, interface="SWD"):
    """使用 JLink 烧录"""
    flash_path = flash_info['path']
    print(f"\n烧录: {flash_path}")
    print(f"设备: {device}, 接口: {interface}, 速度: {speed} KHz")
    
    flasher = JLinkFlasher(device=device, speed=speed, interface=interface)
    
    if flasher.flash(flash_path, flash_type=flash_info['type'], addr=flash_info.get('addr')):
        print("烧录成功!")
        return True
    else:
        print("烧录失败!")
        return False


def flash_with_stlink(flash_info, device=None, speed=4000, interface="SWD"):
    """使用 ST-Link 烧录"""
    flash_path = flash_info['path']
    print(f"\n烧录: {flash_path}")
    print(f"设备: {device or 'auto'}, 接口: {interface}, 速度: {speed} KHz")
    
    flasher = STLinkFlasher(device=device, speed=speed, interface=interface)
    
    if flasher.flash(flash_path, flash_type=flash_info['type'], addr=flash_info.get('addr')):
        print("烧录成功!")
        return True
    else:
        print("烧录失败!")
        return False


def flash_with_cmsis_dap(flash_info, device=None, speed=4000, interface="SWD"):
    """使用 CMSIS-DAP 烧录"""
    flash_path = flash_info['path']
    print(f"\n烧录: {flash_path}")
    print(f"设备: {device or 'auto'}, 接口: {interface}, 速度: {speed} KHz")
    
    flasher = CMSISDAPFlasher(device=device, speed=speed, interface=interface)
    
    if flasher.flash(flash_path, flash_type=flash_info['type'], addr=flash_info.get('addr')):
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


def init_project_config(project_dir):
    """首次初始化项目配置"""
    project_dir = normalize_path(project_dir)
    
    print("=" * 50)
    print("项目配置初始化")
    print("=" * 50)
    print(f"\n工程目录: {project_dir}")
    
    config = {
        'project': {},
        'flasher': {},
        'serial': {},
        'flash': {},
        'debug': {}
    }
    
    print("\n[1/5] 检测项目文件...")
    projects = detect_projects(project_dir)
    if projects:
        project = projects[0]
        print(f"  发现项目: {project.type.upper()} - {project.name}")
        print(f"  路径: {project.path}")
        config['project']['name'] = project.name
        config['project']['type'] = project.type
        config['project']['path'] = project.path
    else:
        print("  未发现项目文件")
    
    print("\n[2/5] 检测烧录器...")
    env = detect_environment()
    flasher_type = None
    for f in env.get('flashers', []):
        if f.get('available'):
            print(f"  发现烧录器: {f['type']}")
            if not flasher_type:
                flasher_type = f['type']
    
    if not flasher_type:
        print("  未发现可用烧录器")
    
    print("\n[3/5] 检测串口...")
    serial_port = None
    for p in env.get('serial_ports', []):
        print(f"  发现串口: {p['port']} - {p.get('description', 'N/A')}")
        if not serial_port:
            serial_port = p['port']
    
    if not serial_port:
        print("  未发现串口")
    
    print("\n" + "=" * 50)
    print("配置确认")
    print("=" * 50)
    
    print(f"""
检测结果：
  项目类型: {config['project'].get('type', 'N/A')}
  项目路径: {config['project'].get('path', 'N/A')}
  烧录器:   {flasher_type or 'N/A'}
  串口:     {serial_port or 'N/A'}
  波特率:   115200

  芯片型号: {input('请输入芯片型号 (如 STM32F407ZGTx): ') or 'STM32F407ZG'}
  接口类型: {input('请输入接口类型 (SWD/JTAG, 默认 SWD): ') or 'SWD'}
  烧录速度: {input('请输入烧录速度 KHz (默认 4000): ') or '4000'}
""")
    
    print("\n是否保存配置? (Y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['', 'y', 'yes']:
        config['flasher']['type'] = flasher_type or 'jlink'
        config['flasher']['device'] = input('芯片型号: ') or 'STM32F407ZG'
        config['flasher']['interface'] = input('接口 (SWD/JTAG): ') or 'SWD'
        config['flasher']['speed'] = int(input('速度 (KHz): ') or '4000')
        config['serial']['port'] = input('串口: ') or serial_port or 'COM3'
        config['serial']['baudrate'] = 115200
        config['debug']['max_retries'] = 3
        
        config_dir = os.path.join(project_dir, 'configs')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'project.yaml')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"\n配置已保存: {config_path}")
    else:
        print("已取消")


def main():
    parser = argparse.ArgumentParser(
        description="Agent 专用烧录脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  检测环境:
    python agent_flash.py --detect
  
  首次初始化:
    python agent_flash.py --project D:/project/firmware --init
  
  烧录并监控:
    python agent_flash.py --project D:/project/firmware --flash MDK-ARM/project/project.hex
  
  烧录 bin 文件:
    python agent_flash.py --project D:/project/firmware --flash firmware.bin --addr 0x08000000
        """
    )
    
    parser.add_argument('--project', '-p', help='工程目录路径')
    parser.add_argument('--flash', help='烧录文件（支持 .elf/.hex/.bin）')
    parser.add_argument('--addr', help='烧录地址（仅 .bin 需要，如 0x08000000）')
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
    parser.add_argument('--init', action='store_true',
                       help='首次初始化项目配置')
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
    
    if args.init:
        init_project_config(args.project)
        return
    
    project_dir = normalize_path(args.project)
    project_dir, error = validate_path(project_dir)
    if error:
        print(f"错误: {error}")
        sys.exit(1)
    
    config_path = os.path.join(project_dir, 'configs', 'project.yaml')
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    
    print("=" * 50)
    print("Agent Flash Tool")
    print("=" * 50)
    print(f"\n工程目录: {project_dir}")
    
    if args.build:
        project = auto_detect_project(project_dir)
        if project:
            build_result = build_project(project.path, project.type)
        else:
            print("未找到项目文件，跳过编译")
    
    if args.flash:
        ext = Path(args.flash).suffix.lower()
        if ext == '.bin' and not args.addr:
            print("错误: .bin 文件需要指定 --addr 参数（如 --addr 0x08000000）")
            sys.exit(1)
        
        flash_path, error = validate_path(args.flash, project_dir)
        if error:
            print(f"错误: {error}")
            sys.exit(1)
        
        flash_info, error = get_flash_info(flash_path, args.addr)
        if error:
            print(f"错误: {error}")
            sys.exit(1)
        
        device = args.device or config.get('flasher', {}).get('device', 'STM32F407ZG')
        flasher_type = args.flasher or config.get('flasher', {}).get('type', 'jlink')
        
        if flasher_type == 'jlink':
            flash_with_jlink(flash_info, device=device, speed=args.speed, interface=args.interface)
        elif flasher_type == 'stlink':
            flash_with_stlink(flash_info, device=device, speed=args.speed, interface=args.interface)
        elif flasher_type == 'cmsis_dap':
            flash_with_cmsis_dap(flash_info, device=device, speed=args.speed, interface=args.interface)
    else:
        print("未指定 --flash 参数")
    
    serial_port = args.serial or config.get('serial', {}).get('port')
    if not args.skip_monitor and serial_port:
        monitor_serial(serial_port, args.baudrate, args.monitor_timeout)


if __name__ == "__main__":
    main()
