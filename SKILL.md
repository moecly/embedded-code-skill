---
name: embedded-flash
description: 嵌入式烧录调试闭环 - 支持 J-Link/ST-Link/CMSIS-DAP 自动检测、烧录、串口监控和智能调试
---

# 规则

## 核心功能

1. **自动检测烧录器**：J-Link / ST-Link / CMSIS-DAP
2. **跨平台串口监控**：实时捕获串口输出
3. **调试闭环**：烧录 → 监控 → 分析 → 修改 → 循环（最多3次）
4. **日志记录**：每次循环保存详细日志

---

# Agent 使用指南

## 重要：必须先检测设备！

使用 skill 前，**必须**先执行检测脚本获取环境信息：

```
python "SKILL_DIR/workflows/detect.py" --json
```

SKILL_DIR = `C:\Users\m\.config\opencode\skills\embedd-code-skill`

## 检测脚本输出格式

```json
{
  "flashers": [
    {
      "type": "jlink",
      "available": true,
      "path": "JLink.exe",
      "status": "connected"
    },
    {
      "type": "stlink",
      "available": false,
      "reason": "STLink executable not found"
    },
    {
      "type": "cmsis_dap",
      "available": true,
      "path": "openocd.exe",
      "status": "connected"
    }
  ],
  "serial_ports": [
    {
      "port": "COM3",
      "description": "USB Serial Device"
    }
  ],
  "summary": {
    "total_flashers_found": 2,
    "total_serial_ports": 1
  }
}
```

---

## 完整调试流程

### 步骤 1：检测设备（必须）

```bash
python "C:\Users\m\.config\opencode\skills\embedd-code-skill\workflows\detect.py" --json
```

根据检测结果：
- 选择可用的烧录器类型（jlink/stlink/cmsis_dap）
- 选择对应的串口端口

### 步骤 2：配置项目

创建或修改 `configs/project.yaml`：

```yaml
project:
  name: "my_firmware"
  build_cmd: "make -j4"
  output: "build/firmware.elf"

flasher:
  type: "jlink"        # 根据检测结果选择：jlink / stlink / cmsis_dap
  device: "STM32F103RC"
  speed: 4000
  interface: "SWD"

serial:
  port: "COM3"         # 根据检测结果选择
  baudrate: 115200
  timeout: 5

debug:
  max_retries: 3
  log_dir: "logs"
```

### 步骤 3：启动调试闭环

```bash
python "C:\Users\m\.config\opencode\skills\embedd-code-skill\workflows\debug_loop.py" --config configs/project.yaml
```

### 步骤 4：分析输出

1. 观察串口输出
2. 根据用户提供的修改指令修改代码
3. 自动重新编译、烧录、监控
4. 循环最多 3 次
5. 3 次失败后生成报告，提示用户手动介入

---

## 脚本路径速查

| 功能 | 路径 |
|------|------|
| 设备检测 | `workflows/detect.py` |
| 调试闭环 | `workflows/debug_loop.py` |
| 配置模板 | `configs/project.yaml` |
| 日志目录 | `logs/` |

---

# 扩展烧录器

在 `tools/flashers/` 下新建文件，继承 `FlasherBase`：

```python
from .base import FlasherBase

class MyFlasher(FlasherBase):
    name = "my_flasher"
    
    def detect(self) -> bool:
        # 检测烧录器是否连接
        pass
    
    def flash(self, elf_path: str) -> bool:
        # 烧录固件
        pass
    
    def reset(self) -> bool:
        # 重置芯片
        pass
```

然后在 `tools/flashers/discover.py` 中注册即可。
