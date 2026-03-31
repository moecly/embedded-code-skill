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

## 执行流程

### 步骤 1：环境检测

执行检测脚本，发现可用的：
- 烧录器（JLink/STLink/CMSIS-DAP）
- 串口设备

### 步骤 2：用户选择设备

展示检测到的设备列表，用户选择：
- 烧录器类型
- 烧录文件路径
- 串口端口

### 步骤 3：加载配置

从 `configs/project.yaml` 加载项目配置（若无则创建模板）。

### 步骤 4：进入调试闭环

```
┌─────────────────────────────────────────────┐
│  循环 (最多3次)                              │
│                                             │
│  1. 编译固件                                 │
│  2. 烧录到芯片                               │
│  3. 重置芯片                                 │
│  4. 监控串口输出                             │
│  5. 分析输出是否正常                          │
│                                             │
│  ├─ 正常 → 成功退出                          │
│  └─ 异常 → 询问用户修改指令                   │
│              ↓                              │
│         用户提供修改要求 → 修改代码            │
│              ↓                              │
│         继续下一轮循环                        │
└─────────────────────────────────────────────┘
```

### 步骤 5：处理失败

3次失败后：
1. 生成详细报告 (`logs/report_N.md`)
2. 列出失败原因
3. 提示用户手动介入

---

# 命令

## 启动调试

```
/flash
```

## 快速烧录（跳过监控）

```
/flash --no-monitor
```

## 指定配置

```
/flash --config path/to/project.yaml
```

---

# 配置文件格式

`configs/project.yaml`:

```yaml
project:
  name: "my_firmware"
  build_cmd: "make -j4"
  output: "build/firmware.elf"

flasher:
  type: "jlink"        # jlink / stlink / cmsis_dap
  device: "STM32F103RC"
  speed: 4000
  interface: "SWD"

serial:
  port: "COM3"
  baudrate: 115200
  timeout: 5

debug:
  max_retries: 3
  log_dir: "logs"
```

---

# 扩展烧录器

在 `tools/flashers/` 下新建文件，继承 `FlasherBase`：

```python
from .base import FlasherBase

class MyFlasher(FlasherBase):
    name = "my_flasher"
    
    def detect(self) -> bool:
        # 检测逻辑
        pass
    
    def flash(self, elf_path: str) -> bool:
        # 烧录逻辑
        pass
    
    def reset(self) -> bool:
        # 重置逻辑
        pass
```

然后在 `discover.py` 中注册即可。
