#!/usr/bin/env python3
"""
Agent 专用烧录脚本 - 提供简单的命令行接口

用法:
    python agent_flash.py --init                    # 初始化配置 (输出 JSON)
    python agent_flash.py --project <目录> --flash <文件>
    python agent_flash.py --flash <文件>            # 使用当前工作目录
    python agent_flash.py --detect                  # 仅检测环境
    python agent_flash.py --help                    # 显示帮助

示例:
    python agent_flash.py --init
    python agent_flash.py --flash firmware.hex
    python agent_flash.py --flash firmware.bin --addr 0x08000000
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


def get_config_path(project_dir):
    """获取配置文件路径"""
    return os.path.join(project_dir, 'configs', 'project.yaml')


def has_config(project_dir):
    """检查配置文件是否存在"""
    return os.path.exists(get_config_path(project_dir))


def load_config(project_dir):
    """加载配置文件"""
    config_path = get_config_path(project_dir)
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(project_dir, config):
    """保存配置文件"""
    config_dir = os.path.join(project_dir, 'configs')
    os.makedirs(config_dir, exist_ok=True)
    config_path = get_config_path(project_dir)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    return config_path


def detect_project_info(project_dir):
    """检测项目信息"""
    projects = detect_projects(project_dir)
    if projects:
        project = projects[0]
        return {
            'name': project.name,
            'type': project.type,
            'path': str(project.path)
        }
    return None


def detect_flasher_info():
    """检测烧录器信息"""
    flashers = []
    available_types = []
    
    jlink = JLinkFlasher()
    if jlink.detect():
        flashers.append({'type': 'jlink', 'name': 'J-Link'})
        available_types.append('jlink')
    
    stlink = STLinkFlasher()
    if stlink.detect():
        flashers.append({'type': 'stlink', 'name': 'ST-Link'})
        available_types.append('stlink')
    
    cmsis = CMSISDAPFlasher()
    if cmsis.detect():
        flashers.append({'type': 'cmsis_dap', 'name': 'CMSIS-DAP'})
        available_types.append('cmsis_dap')
    
    return flashers, available_types


def detect_serial_info():
    """检测串口信息"""
    ports = list_serial_ports()
    serial_info = []
    
    for p in ports:
        serial_info.append({
            'port': p['port'],
            'description': p.get('description', 'N/A')
        })
    
    return serial_info


def init_config(project_dir):
    """
    初始化配置 - 输出 JSON 格式，供 Agent 解析
    Agent 根据此输出询问用户，然后生成配置文件
    """
    result = {
        'project': detect_project_info(project_dir),
        'flashers': [],
        'available_flashers': [],
        'serial_ports': []
    }
    
    # 检测烧录器并检查芯片连接状态
    jlink = JLinkFlasher()
    if jlink.detect():
        device_connected, device_msg = jlink.check_device()
        result['flashers'].append({
            'type': 'jlink',
            'name': 'J-Link',
            'device_connected': device_connected,
            'device_message': device_msg
        })
        result['available_flashers'].append('jlink')
    
    stlink = STLinkFlasher()
    if stlink.detect():
        result['flashers'].append({
            'type': 'stlink',
            'name': 'ST-Link'
        })
        result['available_flashers'].append('stlink')
    
    cmsis = CMSISDAPFlasher()
    if cmsis.detect():
        result['flashers'].append({
            'type': 'cmsis_dap',
            'name': 'CMSIS-DAP'
        })
        result['available_flashers'].append('cmsis_dap')
    
    result['serial_ports'] = detect_serial_info()
    
    return result


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
        device_connected, device_msg = jlink.check_device()
        result["flashers"].append({
            "type": "jlink",
            "available": True,
            "devices": jlink.list_devices(),
            "device_connected": device_connected,
            "device_message": device_msg
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


def flash_with_jlink(flash_info, device="<芯片型号>", speed=4000, interface="SWD"):
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


def main():
    parser = argparse.ArgumentParser(
        description="Agent 专用烧录脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  初始化配置:
    python agent_flash.py --init
  
  检测环境:
    python agent_flash.py --detect
  
  烧录并监控 (使用当前目录):
    python agent_flash.py --flash firmware.hex
  
  烧录 bin 文件:
    python agent_flash.py --flash firmware.bin --addr 0x08000000
        """
    )
    
    parser.add_argument('--project', '-p', default='.', help='工程目录路径 (默认: 当前工作目录)')
    parser.add_argument('--flash', help='烧录文件（支持 .elf/.hex/.bin）')
    parser.add_argument('--addr', help='烧录地址（仅 .bin 需要，如 0x08000000）')
    parser.add_argument('--flasher', '-f', default='jlink', 
                       choices=['jlink', 'stlink', 'cmsis_dap'],
                       help='烧录器类型 (默认: jlink)')
    parser.add_argument('--device', '-d', help='芯片型号 (如 <芯片型号>)')
    parser.add_argument('--serial', '-s', help='串口端口 (如 <串口号>)')
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
                       help='初始化配置，输出 JSON 供 Agent 解析')
    parser.add_argument('--build', action='store_true',
                       help='编译后再烧录')
    parser.add_argument('--skip-monitor', action='store_true',
                       help='跳过串口监控')
    parser.add_argument('--json', action='store_true',
                       help='输出 JSON 格式结果')
    parser.add_argument('--force-config', action='store_true',
                       help='强制重新配置（忽略已有配置）')
    
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
                    if f.get('device_connected') is False:
                        print(f"  [!] 芯片未连接: {f.get('device_message', '')}")
                    elif f.get('device_connected') is True:
                        print(f"  [OK] 芯片连接正常")
            else:
                print("  无可用烧录器")
            
            print("\n=== 串口 ===")
            if result["serial_ports"]:
                for p in result["serial_ports"]:
                    print(f"  {p['port']}: {p['description']}")
            else:
                print("  无可用串口")
        return
    
    if args.init:
        if not args.project or args.project == '.':
            project_dir = os.getcwd()
        else:
            project_dir = normalize_path(args.project)
        
        project_dir, error = validate_path(project_dir)
        if error:
            print(f"错误: {error}")
            sys.exit(1)
        
        result = init_config(project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if not args.project or args.project == '.':
        project_dir = os.getcwd()
    else:
        project_dir = normalize_path(args.project)
    
    project_dir, error = validate_path(project_dir)
    if error:
        print(f"错误: {error}")
        sys.exit(1)
    
    print("=" * 50)
    print("Agent Flash Tool")
    print("=" * 50)
    print(f"\n工程目录: {project_dir}")
    
    config = {}
    
    if has_config(project_dir) and not args.force_config:
        print("\n检测到已有配置，加载配置...")
        config = load_config(project_dir)
    else:
        print("\n未检测到配置文件，请先运行 --init 初始化配置")
        print("命令: python agent_flash.py --project <目录> --init")
        sys.exit(1)
    
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
        
        device = args.device or config.get('flasher', {}).get('device', '<芯片型号>')
        flasher_type = args.flasher or config.get('flasher', {}).get('type', 'jlink')
        
        if flasher_type == 'jlink':
            flash_with_jlink(flash_info, device=device, speed=args.speed, interface=args.interface)
        elif flasher_type == 'stlink':
            flash_with_stlink(flash_info, device=device, speed=args.speed, interface=args.interface)
        elif flasher_type == 'cmsis_dap':
            flash_with_cmsis_dap(flash_info, device=device, speed=args.speed, interface=args.interface)
    else:
        print("\n未指定 --flash 参数，等待下一步指令...")
        print("可用指令:")
        print("  --build           编译项目")
        print("  --flash <文件>    烧录固件")
        print("  --detect          检测环境")
        print("  --force-config    重新配置")
        return
    
    serial_port = args.serial or config.get('serial', {}).get('port')
    if not args.skip_monitor and serial_port:
        monitor_serial(serial_port, args.baudrate, args.monitor_timeout)


if __name__ == "__main__":
    main()
