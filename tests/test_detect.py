"""
环境检测功能测试
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDetectEnvironment:
    """环境检测测试"""
    
    def test_detect_returns_dict(self):
        """测试检测返回字典"""
        from workflows.agent_flash import detect_environment
        
        result = detect_environment()
        
        assert isinstance(result, dict)
        assert "flashers" in result
        assert "serial_ports" in result
    
    def test_flashers_list(self):
        """测试烧录器列表结构"""
        from workflows.agent_flash import detect_environment
        
        result = detect_environment()
        
        assert isinstance(result["flashers"], list)
    
    def test_serial_ports_list(self):
        """测试串口列表结构"""
        from workflows.agent_flash import detect_environment
        
        result = detect_environment()
        
        assert isinstance(result["serial_ports"], list)
        for port in result["serial_ports"]:
            assert "port" in port
            assert "description" in port


class TestJLinkFlasherDetect:
    """J-Link 检测测试"""
    
    def test_jlink_detect_returns_bool(self):
        """测试 J-Link 检测返回布尔值"""
        from tools.flashers import JLinkFlasher
        
        flasher = JLinkFlasher()
        result = flasher.detect()
        
        assert isinstance(result, bool)


class TestSTLinkFlasherDetect:
    """ST-Link 检测测试"""
    
    def test_stlink_detect_returns_bool(self):
        """测试 ST-Link 检测返回布尔值"""
        from tools.flashers import STLinkFlasher
        
        flasher = STLinkFlasher()
        result = flasher.detect()
        
        assert isinstance(result, bool)


class TestCMSISDAPFlasherDetect:
    """CMSIS-DAP 检测测试"""
    
    def test_cmsis_dap_detect_returns_bool(self):
        """测试 CMSIS-DAP 检测返回布尔值"""
        from tools.flashers import CMSISDAPFlasher
        
        flasher = CMSISDAPFlasher()
        result = flasher.detect()
        
        assert isinstance(result, bool)


class TestSerialPorts:
    """串口检测测试"""
    
    def test_list_serial_ports_returns_list(self):
        """测试串口列表返回列表"""
        from tools.flashers import list_serial_ports
        
        ports = list_serial_ports()
        
        assert isinstance(ports, list)
    
    def test_serial_port_structure(self):
        """测试串口信息结构"""
        from tools.flashers import list_serial_ports
        
        ports = list_serial_ports()
        
        for port in ports:
            assert "port" in port
            assert "description" in port
