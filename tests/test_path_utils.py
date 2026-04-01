"""
路径工具函数测试
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.agent_flash import normalize_path, validate_path


class TestNormalizePath:
    """normalize_path 函数测试"""
    
    def test_backslash_to_forward(self):
        """测试反斜杠转正斜杠"""
        assert normalize_path("D:\\project\\file") == "D:/project/file"
    
    def test_mixed_slashes(self):
        """测试混合斜杠"""
        assert normalize_path("D:\\project/file") == "D:/project/file"
    
    def test_relative_path(self):
        """测试相对路径"""
        result = normalize_path("MDK-ARM/firmware.hex")
        assert "/" in result or "\\" in result
    
    def test_empty_path(self):
        """测试空路径"""
        assert normalize_path("") == ""
        assert normalize_path(None) is None
    
    def test_posix_path_unchanged(self):
        """测试已经是正斜杠的路径不变"""
        result = normalize_path("D:/project/firmware")
        assert result == "D:/project/firmware"


class TestValidatePath:
    """validate_path 函数测试"""
    
    def test_validate_existing_file(self, temp_project):
        """测试存在的文件"""
        hex_file = temp_project / "MDK-ARM" / "project.hex"
        normalized, error = validate_path(str(hex_file))
        assert error is None
        assert normalized is not None
    
    def test_validate_nonexistent_file(self):
        """测试不存在的文件"""
        normalized, error = validate_path("nonexistent/file.txt")
        assert normalized is not None
        assert error is not None
        assert "不存在" in error
    
    def test_validate_empty_path(self):
        """测试空路径"""
        normalized, error = validate_path("")
        assert normalized is None
        assert "为空" in error
    
    def test_validate_relative_path_with_base(self, temp_project):
        """测试带 base_dir 的相对路径"""
        hex_file = "project.hex"
        base_dir = str(temp_project / "MDK-ARM")
        normalized, error = validate_path(hex_file, base_dir)
        assert error is None
        assert "project.hex" in normalized
    
    def test_validate_path_with_backslash(self, temp_project):
        """测试反斜杠路径"""
        hex_file = str(temp_project / "MDK-ARM" / "project.hex")
        normalized, error = validate_path(hex_file)
        assert error is None
        assert "/" in normalized
