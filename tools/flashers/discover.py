import serial.tools.list_ports
from .base import FlasherManager, FlasherInfo
from .jlink import JLinkFlasher
from .stlink import STLinkFlasher
from .cmsis_dap import CMSISDAPFlasher


def discover_flashers() -> FlasherManager:
    """自动发现并注册所有烧录器"""
    manager = FlasherManager()
    
    manager.register(JLinkFlasher())
    manager.register(STLinkFlasher())
    manager.register(CMSISDAPFlasher())
    
    return manager


def list_available_flashers() -> list:
    """列出所有可用的烧录器"""
    manager = discover_flashers()
    return manager.detect_all()


def list_serial_ports() -> list:
    """列出所有可用的串口"""
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


def print_discovered_devices():
    """打印发现的设备"""
    print("\n=== 发现的烧录器 ===")
    flashers = list_available_flashers()
    if flashers:
        for i, f in enumerate(flashers, 1):
            print(f"  [{i}] {f.type}: {f.name} ({f.device or '未知设备'})")
    else:
        print("  未发现烧录器")
    
    print("\n=== 可用串口 ===")
    ports = list_serial_ports()
    if ports:
        for i, p in enumerate(ports, 1):
            print(f"  [{i}] {p['port']} - {p['description']}")
    else:
        print("  未发现串口设备")
