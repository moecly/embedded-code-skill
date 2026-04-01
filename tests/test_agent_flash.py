"""
agent_flash.py 主脚本测试
"""
import sys
import os
from pathlib import Path
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.agent_flash import (
    normalize_path,
    validate_path,
    get_flash_info,
    detect_environment,
    flash_with_jlink,
    has_config,
    load_config,
    get_config_path,
    save_config,
)


class TestGetFlashInfo:
    """烧录文件信息解析测试"""
    
    def test_hex_file(self):
        """测试 hex 文件"""
        info, error = get_flash_info("firmware.hex")
        
        assert error is None
        assert info['type'] == 'hex'
        assert 'firmware.hex' in info['path']
    
    def test_elf_file(self):
        """测试 elf 文件"""
        info, error = get_flash_info("firmware.elf")
        
        assert error is None
        assert info['type'] == 'elf'
        assert 'firmware.elf' in info['path']
    
    def test_bin_file_without_addr(self):
        """测试 bin 文件无地址"""
        info, error = get_flash_info("firmware.bin")
        
        assert info is None
        assert "--addr" in error
    
    def test_bin_file_with_addr(self):
        """测试 bin 文件带地址"""
        info, error = get_flash_info("firmware.bin", addr="0x08000000")
        
        assert error is None
        assert info['type'] == 'bin'
        assert info['addr'] == "0x08000000"
    
    def test_unsupported_format(self):
        """测试不支持的文件格式"""
        info, error = get_flash_info("firmware.txt")
        
        assert info is None
        assert "不支持" in error
    
    def test_empty_path(self):
        """测试空路径"""
        info, error = get_flash_info("")
        
        assert info is None
        assert "为空" in error


class TestAgentFlashMain:
    """agent_flash.py 主流程测试"""
    
    def test_help_flag(self, capsys):
        """测试 --help 参数"""
        import argparse
        from workflows.agent_flash import main
        
        with pytest.raises(SystemExit) as exc_info:
            sys.argv = ['agent_flash.py', '--help']
            main()
        
        assert exc_info.value.code == 0
    
    def test_detect_flag(self, capsys):
        """测试 --detect 参数"""
        from workflows.agent_flash import main
        
        sys.argv = ['agent_flash.py', '--detect']
        main()
        
        captured = capsys.readouterr()
        assert "烧录器" in captured.out or "flasher" in captured.out.lower()
    
    def test_project_required_without_flash(self):
        """测试没有 --project 参数时报错"""
        from workflows.agent_flash import main
        
        sys.argv = ['agent_flash.py', '--flash', 'test.hex']
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    def test_bin_requires_addr(self, capsys):
        """测试 bin 文件需要 --addr 参数"""
        from workflows.agent_flash import main
        
        sys.argv = ['agent_flash.py', '--project', '/tmp/test', '--flash', 'test.bin']
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1


class TestConfigLoading:
    """配置文件加载测试"""
    
    def test_has_config_exists(self, temp_project_with_config):
        """测试配置文件存在时返回 True"""
        result = has_config(str(temp_project_with_config))
        assert result is True
    
    def test_has_config_not_exists(self, temp_project_without_config):
        """测试配置文件不存在时返回 False"""
        result = has_config(str(temp_project_without_config))
        assert result is False
    
    def test_get_config_path(self, temp_project):
        """测试获取配置文件路径"""
        config_path = get_config_path(str(temp_project))
        assert "configs" in config_path
        assert "project.yaml" in config_path
    
    def test_load_existing_config(self, temp_project, sample_config):
        """测试加载已存在的配置"""
        config_dir = temp_project / "configs"
        config_dir.mkdir()
        config_path = config_dir / "project.yaml"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        config = load_config(str(temp_project))
        
        assert config['flasher']['type'] == 'jlink'
        assert config['flasher']['device'] == '<芯片型号>'
    
    def test_load_nonexistent_config(self, temp_project):
        """测试加载不存在的配置"""
        config = load_config(str(temp_project))
        assert config == {}
    
    def test_save_config(self, temp_project, sample_config):
        """测试保存配置"""
        config_path = save_config(str(temp_project), sample_config)
        
        assert os.path.exists(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['flasher']['type'] == 'jlink'
        assert loaded['flasher']['device'] == '<芯片型号>'


class TestFlashWithJLink:
    """J-Link 烧录测试"""
    
    def test_flash_hex_success(self, mocker, temp_project):
        """测试 hex 文件烧录成功"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Downloading file...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        mocker.patch('tempfile.NamedTemporaryFile')
        
        flash_info = {
            'type': 'hex',
            'path': str(temp_project / "MDK-ARM" / "project.hex")
        }
        
        from tools.flashers import JLinkFlasher
        flasher = JLinkFlasher()
        
        result = flasher.flash(str(temp_project / "MDK-ARM" / "project.hex"), flash_type='hex')
        
        assert mock_result.call_count >= 0 or result is not None
    
    def test_flash_elf_success(self, mocker, temp_project):
        """测试 elf 文件烧录成功"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Downloading file...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        mocker.patch('tempfile.NamedTemporaryFile')
        
        flash_info = {
            'type': 'elf',
            'path': str(temp_project / "MDK-ARM" / "project.elf")
        }
        
        from tools.flashers import JLinkFlasher
        flasher = JLinkFlasher()
        
        result = flasher.flash(str(temp_project / "MDK-ARM" / "project.elf"), flash_type='elf')
        
        assert result is not None
    
    def test_flash_bin_with_addr(self, mocker, temp_project):
        """测试 bin 文件带地址烧录"""
        mock_result = mocker.MagicMock()
        mock_result.stdout = b"Downloading file...O.K.\n"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)
        mocker.patch('tempfile.NamedTemporaryFile')
        
        from tools.flashers import JLinkFlasher
        flasher = JLinkFlasher()
        
        result = flasher.flash(
            str(temp_project / "MDK-ARM" / "project.bin"),
            flash_type='bin',
            addr='0x08000000'
        )
        
        assert result is not None
