#!/usr/bin/env python3
"""
设备检测脚本 - 检测可用的烧录器和串口设备
供 agent 调用，返回 JSON 格式结果
"""
import sys
import json
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import serial.tools.list_ports


def detect_jlink():
    """检测 JLink"""
    jlink_paths = [
        "JLink.exe",
        "JLink",
        "C:/Program Files/SEGGER/JLink/JLink.exe",
        "C:/Program Files (x86)/SEGGER/JLink/JLink.exe",
    ]
    
    jlink_path = None
    for path in jlink_paths:
        if shutil.which(path) or Path(path).exists():
            jlink_path = path
            break
    
    if not jlink_path:
        return {"type": "jlink", "available": False, "reason": "JLink executable not found"}
    
    try:
        result = subprocess.run(
            [jlink_path, "-CommandFile", "-", "-ExitCode"],
            input=b"connect\nqc\n",
            capture_output=True,
            timeout=5
        )
        available = result.returncode == 0
        return {
            "type": "jlink",
            "available": available,
            "path": jlink_path,
            "status": "connected" if available else "not connected"
        }
    except Exception as e:
        return {"type": "jlink", "available": False, "reason": str(e)}


def detect_stlink():
    """检测 ST-Link"""
    stlink_paths = [
        "stlink_cli",
        "ST-Link_CLI",
        "ST-LINK_CLI",
        "C:/Program Files/STMicroelectronics/ST-Link CLI/ST-Link_CLI.exe",
    ]
    
    stlink_path = None
    for path in stlink_paths:
        if shutil.which(path) or Path(path).exists():
            stlink_path = path
            break
    
    if not stlink_path:
        return {"type": "stlink", "available": False, "reason": "STLink executable not found"}
    
    try:
        result = subprocess.run(
            [stlink_path, "-List"],
            capture_output=True,
            timeout=5
        )
        output = result.stdout.decode('utf-8', errors='ignore')
        available = "STM32" in output or result.returncode == 0
        devices = []
        for line in output.split('\n'):
            if 'STM32' in line or 'ST-LINK' in line:
                devices.append(line.strip())
        return {
            "type": "stlink",
            "available": available,
            "path": stlink_path,
            "devices": devices,
            "status": "connected" if available else "not connected"
        }
    except Exception as e:
        return {"type": "stlink", "available": False, "reason": str(e)}


def detect_cmsis_dap():
    """检测 CMSIS-DAP (通过 openocd)"""
    openocd_paths = [
        "openocd",
        "openocd.exe",
        "C:/Program Files/OpenOCD/bin/openocd.exe",
        "C:/Program Files (x86)/OpenOCD/bin/openocd.exe",
    ]
    
    openocd_path = None
    for path in openocd_paths:
        if shutil.which(path) or Path(path).exists():
            openocd_path = path
            break
    
    if not openocd_path:
        return {"type": "cmsis_dap", "available": False, "reason": "OpenOCD not found"}
    
    try:
        result = subprocess.run(
            [openocd_path, "-c", "adapter list", "-c", "shutdown"],
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode('utf-8', errors='ignore') + result.stderr.decode('utf-8', errors='ignore')
        available = "CMSIS-DAP" in output or "dap" in output.lower()
        return {
            "type": "cmsis_dap",
            "available": available,
            "path": openocd_path,
            "status": "connected" if available else "not found",
            "raw_output": output[:500] if available else ""
        }
    except Exception as e:
        return {"type": "cmsis_dap", "available": False, "reason": str(e)}


def list_serial_ports():
    """列出所有可用串口"""
    ports = serial.tools.list_ports.comports()
    return [
        {
            "port": p.device,
            "name": p.name,
            "description": p.description,
            "hwid": p.hwid
        }
        for p in ports
    ]


def detect_all():
    """检测所有设备"""
    result = {
        "flashers": [],
        "serial_ports": list_serial_ports(),
        "summary": {
            "total_flashers_found": 0,
            "total_serial_ports": 0
        }
    }
    
    print("检测 JLink...", file=sys.stderr)
    jlink = detect_jlink()
    result["flashers"].append(jlink)
    if jlink.get("available"):
        result["summary"]["total_flashers_found"] += 1
    
    print("检测 STLink...", file=sys.stderr)
    stlink = detect_stlink()
    result["flashers"].append(stlink)
    if stlink.get("available"):
        result["summary"]["total_flashers_found"] += 1
    
    print("检测 CMSIS-DAP...", file=sys.stderr)
    cmsis_dap = detect_cmsis_dap()
    result["flashers"].append(cmsis_dap)
    if cmsis_dap.get("available"):
        result["summary"]["total_flashers_found"] += 1
    
    result["summary"]["total_serial_ports"] = len(result["serial_ports"])
    
    return result


def print_human_readable(result):
    """打印人类可读的格式"""
    print("\n" + "=" * 50)
    print("设备检测结果")
    print("=" * 50)
    
    print("\n【烧录器】")
    for flasher in result["flashers"]:
        status = "✓ 可用" if flasher.get("available") else "✗ 不可用"
        print(f"  {flasher['type'].upper()}: {status}")
        if flasher.get("available"):
            print(f"    路径: {flasher.get('path', 'N/A')}")
            if flasher.get("devices"):
                print(f"    设备: {', '.join(flasher['devices'])}")
        else:
            print(f"    原因: {flasher.get('reason', 'unknown')}")
    
    print("\n【串口】")
    if result["serial_ports"]:
        for port in result["serial_ports"]:
            print(f"  {port['port']}: {port['description']}")
    else:
        print("  未发现串口设备")
    
    print("\n" + "-" * 50)
    print(f"烧录器: {result['summary']['total_flashers_found']} 个可用")
    print(f"串口: {result['summary']['total_serial_ports']} 个可用")
    print("=" * 50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='检测嵌入式烧录设备和串口')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('--human', action='store_true', help='输出人类可读格式')
    args = parser.parse_args()
    
    result = detect_all()
    
    if args.json or not args.human:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)


if __name__ == "__main__":
    main()
