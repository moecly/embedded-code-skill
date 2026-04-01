"""
pytest 配置和公共 fixtures
"""
import sys
import os
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_project(tmp_path):
    """创建临时项目目录"""
    project = tmp_path / "test_project"
    project.mkdir()
    
    mdk_arm = project / "MDK-ARM"
    mdk_arm.mkdir()
    
    project_dir = mdk_arm / "project"
    project_dir.mkdir()
    
    (mdk_arm / "project.hex").write_bytes(b":020000040800F2\n:1000000012345678ABCDEF00ABCDEF00ABCDEF0090\n:00000001FF\n")
    (mdk_arm / "project.elf").write_bytes(b"\x7fELF")
    (mdk_arm / "project.bin").write_bytes(b"\x00\x01\x02\x03")
    (project_dir / "firmware.hex").write_bytes(b":020000040800F2\n:1000000012345678ABCDEF00ABCDEF00ABCDEF0090\n:00000001FF\n")
    
    return project


@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config():
    """示例配置内容"""
    return {
        'project': {
            'name': 'test_project',
            'type': 'keil',
            'path': 'MDK-ARM/project.uvprojx'
        },
        'flasher': {
            'type': 'jlink',
            'device': 'STM32F407ZG',
            'speed': 4000,
            'interface': 'SWD'
        },
        'serial': {
            'port': 'COM3',
            'baudrate': 115200
        },
        'debug': {
            'max_retries': 3
        }
    }


@pytest.fixture
def mock_jlink_success(mocker):
    """模拟 J-Link 成功连接"""
    mock_result = mocker.MagicMock()
    mock_result.stdout = b"Connecting to J-Link...O.K.\nFirmware: J-Link V12\n"
    mock_result.stderr = b""
    mock_result.returncode = 0
    mocker.patch('subprocess.run', return_value=mock_result)
    return mock_result


@pytest.fixture
def mock_jlink_flash_success(mocker):
    """模拟 J-Link 烧录成功"""
    mock_result = mocker.MagicMock()
    mock_result.stdout = b"Downloading file...O.K.\n"
    mock_result.stderr = b""
    mock_result.returncode = 0
    mocker.patch('subprocess.run', return_value=mock_result)
    return mock_result


@pytest.fixture
def mock_jlink_flash_fail(mocker):
    """模拟 J-Link 烧录失败"""
    mock_result = mocker.MagicMock()
    mock_result.stdout = b"Error: Failed to connect\n"
    mock_result.stderr = b""
    mock_result.returncode = 1
    mocker.patch('subprocess.run', return_value=mock_result)
    return mock_result


@pytest.fixture
def mock_serial_ports(mocker):
    """模拟串口列表"""
    mock_ports = [
        {'port': 'COM3', 'name': 'COM3', 'description': 'USB Serial Port', 'hwid': 'USB VID:PID=1234:5678'}
    ]
    return mock_ports
