from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FlasherInfo:
    name: str
    type: str
    available: bool
    device: Optional[str] = None
    serial_number: Optional[str] = None


class FlasherBase(ABC):
    name: str = "base"
    
    def __init__(self, device: Optional[str] = None, speed: int = 4000, interface: str = "SWD"):
        self.device = device
        self.speed = speed
        self.interface = interface
    
    @abstractmethod
    def detect(self) -> bool:
        """检测烧录器是否连接"""
        pass
    
    @abstractmethod
    def flash(self, elf_path: str) -> bool:
        """烧录固件"""
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """重置芯片"""
        pass
    
    def erase(self) -> bool:
        """擦除芯片（可选实现）"""
        raise NotImplementedError
    
    def get_info(self) -> FlasherInfo:
        """获取烧录器信息"""
        return FlasherInfo(
            name=self.name,
            type=self.__class__.__name__,
            available=self.detect(),
            device=self.device
        )


class FlasherManager:
    def __init__(self):
        self.flashers: List[FlasherBase] = []
    
    def register(self, flasher: FlasherBase):
        self.flashers.append(flasher)
    
    def detect_all(self) -> List[FlasherInfo]:
        """检测所有注册的烧录器"""
        infos = []
        for flasher in self.flashers:
            info = flasher.get_info()
            if info.available:
                infos.append(info)
        return infos
    
    def get_flasher(self, flasher_type: str) -> Optional[FlasherBase]:
        """根据类型获取烧录器"""
        for flasher in self.flashers:
            if flasher.name == flasher_type.lower():
                return flasher
        return None
