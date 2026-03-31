import os
import sys
import yaml
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.flashers import (
    discover_flashers,
    list_serial_ports,
    JLinkFlasher,
    STLinkFlasher,
    CMSISDAPFlasher,
)
from tools.monitor import SerialMonitor, LoopLogger


class DebugLoop:
    def __init__(self, config_path: str = "configs/project.yaml"):
        self.config = self._load_config(config_path)
        self.flasher = None
        self.monitor = None
        self.logger = LoopLogger(self.config.get('debug', {}).get('log_dir', 'logs'))
    
    def _load_config(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_config(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)
    
    def discover_devices(self):
        """发现并选择设备"""
        print("\n" + "="*50)
        print("设备检测")
        print("="*50)
        
        print("\n[1] 检测烧录器...")
        flashers = list_serial_ports()
        
        print("\n[2] 可用串口:")
        ports = list_serial_ports()
        if ports:
            for i, p in enumerate(ports, 1):
                print(f"    {i}. {p['port']} - {p['description']}")
        else:
            print("    未发现串口")
        
        return ports
    
    def select_flasher(self) -> Optional[Any]:
        """选择烧录器"""
        print("\n" + "="*50)
        print("选择烧录器")
        print("="*50)
        
        flasher_type = self.config.get('flasher', {}).get('type', 'jlink').lower()
        
        if flasher_type == 'jlink':
            return JLinkFlasher(
                device=self.config.get('flasher', {}).get('device'),
                speed=self.config.get('flasher', {}).get('speed', 4000),
                interface=self.config.get('flasher', {}).get('interface', 'SWD')
            )
        elif flasher_type == 'stlink':
            return STLinkFlasher(
                device=self.config.get('flasher', {}).get('device'),
                speed=self.config.get('flasher', {}).get('speed', 4000),
                interface=self.config.get('flasher', {}).get('interface', 'SWD')
            )
        elif flasher_type == 'cmsis_dap':
            return CMSISDAPFlasher(
                device=self.config.get('flasher', {}).get('device'),
                speed=self.config.get('flasher', {}).get('speed', 4000),
                interface=self.config.get('flasher', {}).get('interface', 'SWD')
            )
        return None
    
    def select_serial(self) -> Optional[SerialMonitor]:
        """选择串口"""
        port = self.config.get('serial', {}).get('port')
        baudrate = self.config.get('serial', {}).get('baudrate', 115200)
        timeout = self.config.get('serial', {}).get('timeout', 5)
        
        if port:
            monitor = SerialMonitor(port, baudrate, timeout)
            if monitor.open():
                return monitor
        return None
    
    def build(self) -> bool:
        """编译固件"""
        build_cmd = self.config.get('project', {}).get('build_cmd')
        if not build_cmd:
            print("[WARN] 未配置编译命令")
            return True
        
        print(f"\n[编译] 执行: {build_cmd}")
        try:
            result = subprocess.run(
                build_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("[错误] 编译超时")
            return False
        except Exception as e:
            print(f"[错误] 编译失败: {e}")
            return False
    
    def flash(self) -> tuple:
        """烧录固件"""
        if not self.flasher:
            print("[错误] 未选择烧录器")
            return False, ""
        
        elf_path = self.config.get('project', {}).get('output')
        if not elf_path:
            print("[错误] 未配置烧录文件")
            return False, ""
        
        if not os.path.exists(elf_path):
            print(f"[错误] 文件不存在: {elf_path}")
            return False, ""
        
        print(f"\n[烧录] {elf_path}")
        print(f"[设备] {self.flasher.device or '未知'}")
        
        success = self.flasher.flash(elf_path)
        output = f"Flash {'成功' if success else '失败'}"
        print(f"[结果] {output}")
        
        return success, output
    
    def reset(self) -> bool:
        """重置芯片"""
        if not self.flasher:
            return False
        
        print("\n[重置] 复位芯片...")
        return self.flasher.reset()
    
    def monitor_serial(self, duration: float = 10.0) -> str:
        """监控串口输出"""
        if not self.monitor:
            print("[WARN] 串口未连接")
            return ""
        
        print(f"\n[监控] 监听串口 {duration} 秒...")
        print("-" * 50)
        
        self.monitor.clear_buffer()
        output = self.monitor.read_lines(duration)
        
        print("-" * 50)
        print(f"[输出] 共 {len(output)} 行")
        
        return '\n'.join(output)
    
    def analyze_output(self, output: str) -> tuple:
        """
        分析串口输出
        返回: (is_normal, reason)
        """
        if not output or len(output) < 5:
            return False, "无串口输出或输出过少"
        
        return True, "输出正常"
    
    def run(self, max_retries: int = 3) -> bool:
        """运行调试闭环"""
        print("\n" + "="*50)
        print("嵌入式调试闭环")
        print("="*50)
        
        print("\n[初始化] 加载配置...")
        self.discover_devices()
        
        print("\n[初始化] 选择烧录器...")
        self.flasher = self.select_flasher()
        if not self.flasher:
            print("[错误] 无法初始化烧录器")
            return False
        
        print("\n[初始化] 连接串口...")
        self.monitor = self.select_serial()
        if not self.monitor:
            print("[WARN] 无法连接串口，将跳过监控")
        
        print("\n" + "="*50)
        print("开始调试闭环 (最多 {} 次)".format(max_retries))
        print("="*50)
        
        for loop in range(1, max_retries + 1):
            print(f"\n{'='*50}")
            print(f"循环 {loop}/{max_retries}")
            print(f"{'='*50}")
            
            self.logger.log_loop_start(loop, self.config)
            
            print("\n[步骤1] 编译...")
            if not self.build():
                print("[错误] 编译失败，跳过本次循环")
                self.logger.log_loop_end(False)
                continue
            
            print("\n[步骤2] 烧录...")
            success, flash_output = self.flash()
            self.logger.log_flash_result(success, flash_output)
            
            if not success:
                print("[错误] 烧录失败")
                self.logger.log_loop_end(False)
                continue
            
            print("\n[步骤3] 重置...")
            self.reset()
            time.sleep(1)
            
            if self.monitor:
                print("\n[步骤4] 监控串口...")
                serial_output = self.monitor_serial(duration=10.0)
                self.logger.log_serial_output(serial_output)
                
                is_normal, reason = self.analyze_output(serial_output)
                
                if is_normal:
                    print(f"\n✅ 验证成功: {reason}")
                    self.logger.log_loop_end(True)
                    self.monitor.close()
                    print("\n" + "="*50)
                    print("调试完成!")
                    print("="*50)
                    self.logger.generate_report(True)
                    return True
                else:
                    print(f"\n❌ 验证失败: {reason}")
            else:
                print("\n[步骤4] 跳过串口监控")
            
            self.logger.log_loop_end(False)
            
            if loop < max_retries:
                print("\n" + "-"*50)
                print("请提供修改指令（描述需要修改的代码和问题）")
                print("-"*50)
                print("\n[等待用户输入修改指令...]")
                return False
        
        if self.monitor:
            self.monitor.close()
        
        print("\n" + "="*50)
        print("调试失败，已达到最大重试次数")
        print("="*50)
        report_path = self.logger.generate_report(False)
        print(f"\n报告已保存: {report_path}")
        return False


def main():
    config_path = "configs/project.yaml"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("用法: python debug_loop.py [--config <path>]")
            return
        elif sys.argv[1] == "--config":
            config_path = sys.argv[2] if len(sys.argv) > 2 else config_path
    
    loop = DebugLoop(config_path)
    success = loop.run(max_retries=loop.config.get('debug', {}).get('max_retries', 3))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
