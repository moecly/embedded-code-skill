"""
CMSIS-DAP 烧录器测试
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.flashers.cmsis_dap import CMSISDAPFlasher


class TestCMSISDAPFlasher:
    """CMSIS-DAP 烧录器测试"""
    
    def test_init(self):
        """测试初始化"""
        flasher = CMSISDAPFlasher(device="STM32F407ZG")
        
        assert flasher.device == "STM32F407ZG"
        assert flasher.speed == 4000
        assert flasher.interface == "SWD"
        assert flasher.name == "cmsis_dap"
    
    def test_init_custom_params(self):
        """测试自定义参数"""
        flasher = CMSISDAPFlasher(
            device="STM32F103RC",
            speed=2000,
            interface="JTAG"
        )
        
        assert flasher.device == "STM32F103RC"
        assert flasher.speed == 2000
        assert flasher.interface == "JTAG"
    
    def test_detect_returns_bool(self):
        """测试检测返回布尔值"""
        flasher = CMSISDAPFlasher()
        result = flasher.detect()
        
        assert isinstance(result, bool)
    
    def test_list_devices_returns_list(self):
        """测试设备列表返回列表"""
        flasher = CMSISDAPFlasher()
        devices = flasher.list_devices()
        
        assert isinstance(devices, list)
    
    def test_flash_hex_success(self, mocker):
        """测试 hex 文件烧录成功"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Programming and verifying target...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        
        flasher = CMSISDAPFlasher()
        result = flasher.flash("test.hex", flash_type="hex")
        
        assert result is not None
    
    def test_flash_elf_success(self, mocker):
        """测试 elf 文件烧录成功"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Programming and verifying target...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        
        flasher = CMSISDAPFlasher()
        result = flasher.flash("test.elf", flash_type="elf")
        
        assert result is not None
    
    def test_flash_bin_with_addr(self, mocker):
        """测试 bin 文件带地址烧录"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Programming and verifying target...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        
        flasher = CMSISDAPFlasher()
        result = flasher.flash("test.bin", flash_type="bin", addr="0x08000000")
        
        assert result is not None
    
    def test_reset(self, mocker):
        """测试重置"""
        mock_result = mocker.MagicMock()
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        
        flasher = CMSISDAPFlasher()
        result = flasher.reset()
        
        assert isinstance(result, bool)


class TestCMSISDAPFlasherHardware:
    """CMSIS-DAP 硬件测试（需要实际连接设备）"""
    
    def test_cmsis_dap_flash_hex_hardware(self):
        """测试 CMSIS-DAP 烧录 hex 文件（需要硬件）"""
        import tempfile
        
        flasher = CMSISDAPFlasher()
        
        if not flasher.detect():
            pytest.skip("CMSIS-DAP not connected, skipping hardware test")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hex', delete=False) as f:
            f.write(":020000040800F2\n:1000000012345678ABCDEF00ABCDEF00ABCDEF0090\n:00000001FF\n")
            hex_path = f.name
        
        try:
            result = flasher.flash(hex_path, flash_type="hex")
            assert result is True
        finally:
            import os
            os.unlink(hex_path)
    
    def test_cmsis_dap_flash_bin_hardware(self):
        """测试 CMSIS-DAP 烧录 bin 文件（需要硬件）"""
        import tempfile
        
        flasher = CMSISDAPFlasher()
        
        if not flasher.detect():
            pytest.skip("CMSIS-DAP not connected, skipping hardware test")
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            bin_path = f.name
        
        try:
            result = flasher.flash(bin_path, flash_type="bin", addr="0x08000000")
            assert result is True
        finally:
            import os
            os.unlink(bin_path)
    
    def test_cmsis_dap_reset_hardware(self):
        """测试 CMSIS-DAP 重置（需要硬件）"""
        flasher = CMSISDAPFlasher()
        
        if not flasher.detect():
            pytest.skip("CMSIS-DAP not connected, skipping hardware test")
        
        result = flasher.reset()
        assert result is True
