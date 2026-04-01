# 扩展指南

## 添加新的编译器

在 `tools/builder/` 下新建文件，继承 `BuilderBase`：

```python
from .base import BuilderBase

class MyBuilder(BuilderBase):
    name = "My Builder"
    type = "mybuilder"
    project_extensions = ["*.myproj"]
    
    def detect_tool(self) -> bool:
        """检测工具是否可用"""
        import shutil
        return shutil.which("mycompiler") is not None
    
    def build(self, project_path: str = None) -> tuple:
        """执行编译，返回 (success, output)"""
        # 实现编译逻辑
        pass
    
    def get_output_path(self, project_path: str = None) -> str:
        """获取输出文件路径"""
        pass
```

然后在 `tools/builder/__init__.py` 中导入。

---

## 添加新的烧录器

在 `tools/flashers/` 下新建文件，继承 `FlasherBase`：

```python
from .base import FlasherBase

class MyFlasher(FlasherBase):
    name = "my_flasher"
    
    def detect(self) -> bool:
        """检测烧录器是否连接"""
        import shutil
        return shutil.which("myprogrammer") is not None
    
    def list_devices(self) -> list:
        """列出所有连接的设备"""
        pass
    
    def flash(self, file_path: str, flash_type: str = "elf", addr: str = None) -> bool:
        """烧录固件
        
        Args:
            file_path: 烧录文件路径
            flash_type: 文件类型 (elf/hex/bin)
            addr: 烧录地址（仅 bin 文件需要）
        """
        pass
    
    def reset(self) -> bool:
        """重置芯片"""
        pass
    
    def erase(self) -> bool:
        """擦除芯片"""
        pass
```

然后在 `tools/flashers/discover.py` 中注册：

```python
from .my_flasher import MyFlasher

manager.register(MyFlasher())
```

---

## 添加新的串口工具

在 `tools/monitor/` 下修改 `serial.py`：

```python
class MySerialMonitor:
    """自定义串口监控实现"""
    pass
```

---

## 添加测试用例

新增烧录器或编译器后，建议添加对应的测试用例：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

测试文件位置：
- 烧录器测试：`tests/test_flashers/test_xxx.py`
- 编译器测试：`tests/test_builders/test_xxx.py`

参考现有测试文件的写法，确保基本功能有测试覆盖。
