---
name: embedded-code
description: 嵌入式代码工具集 - 支持 Keil/Makefile/CMake 项目自动检测，J-Link/ST-Link/CMSIS-DAP 烧录，串口监控
---

# 功能

**编译 → 烧录 → 重置 → 监控 → 分析 → 修改 → 循环**

1. 自动检测项目类型（Keil/Makefile/CMake）
2. 自动检测烧录器（J-Link/ST-Link/CMSIS-DAP）
3. 串口监控与输出分析
4. 调试闭环（最多3次重试）

---

# Agent 使用指南

## 推荐：使用 agent_flash.py（最简单）

```bash
# 1. 检测环境
python "SKILL/workflows/agent_flash.py" --detect

# 2. 烧录并监控（常用）
python "SKILL/workflows/agent_flash.py" --project D:/workspacePrj/JL5104 --elf MDK-ARM/test0/test0.elf --device STM32F407ZGTx --serial COM3

# 3. 编译+烧录+监控
python "SKILL/workflows/agent_flash.py" --project D:/workspacePrj/JL5104 --build --elf MDK-ARM/test0/test0.elf --device STM32F407ZGTx --serial COM3
```

### agent_flash.py 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--project` | 工程目录 | `D:/workspacePrj/JL5104` |
| `--elf` | 烧录文件（相对工程目录） | `MDK-ARM/test0/test0.elf` |
| `--flasher` | 烧录器类型 | `jlink` / `stlink` / `cmsis_dap` |
| `--device` | 芯片型号 | `STM32F407ZGTx` |
| `--serial` | 串口端口 | `COM3` |
| `--baudrate` | 波特率 | `115200` |
| `--speed` | 烧录速度(KHz) | `4000` |
| `--interface` | 接口 | `SWD` / `JTAG` |
| `--build` | 编译后再烧录 | flag |
| `--skip-monitor` | 跳过串口监控 | flag |
| `--detect` | 仅检测环境 | flag |

---

## 备选：使用 detect.py 和 debug_loop.py

### 1. 检测环境

```bash
# 检测烧录器和串口
python "SKILL/workflows/detect.py" --json

# 检测项目和编译器
python "SKILL/workflows/build.py" --detect --json --search "工程目录"
```

### 2. 启动调试闭环

```bash
python "SKILL/workflows/debug_loop.py" --config "工程目录/configs/project.yaml"
```

### 3. 仅检测不烧录

```bash
python "SKILL/workflows/debug_loop.py" --detect --config "工程目录/configs/project.yaml"
```

---

## 工作流程

```
用户触发 skill
       ↓
检测环境 (agent_flash.py --detect)
       ↓
分析检测结果，确定:
- 烧录器类型 (jlink/stlink/cmsis_dap)
- 芯片型号 (STM32F407ZGTx)
- 串口端口 (COM3)
       ↓
执行烧录+监控
python agent_flash.py --project ... --elf ... --device ... --serial ...
       ↓
分析串口输出
       ↓
用户判断代码是否正常
       ↓
异常? → 修改代码 → 重新烧录 (最多3次)
       ↓
正常? → 完成
```

---

# 配置文件（可选）

如需持久化配置，创建 `工程目录/configs/project.yaml`：

```yaml
flasher:
  type: "jlink"
  device: "STM32F407ZGTx"

serial:
  port: "COM3"
  baudrate: 115200

flash:
  elf: "MDK-ARM/test0/test0.elf"

debug:
  max_retries: 3
```

---

# 文档目录

| 文档 | 说明 |
|------|------|
| [快速开始](docs/quickstart.md) | 最简使用流程 |
| [配置说明](docs/config.md) | 配置文件详解 |
| [编译器](docs/compilers.md) | Keil/Makefile/CMake |
| [烧录器](docs/flashers.md) | J-Link/ST-Link/OpenOCD |
| [扩展指南](docs/extending.md) | 添加新工具 |

---

# 脚本路径速查

| 功能 | 脚本 |
|------|------|
| **Agent 推荐** | `workflows/agent_flash.py` |
| 环境检测 | `workflows/detect.py` |
| 构建检测 | `workflows/build.py` |
| 调试闭环 | `workflows/debug_loop.py` |

SKILL = `C:\Users\m\.config\opencode\skills\embedd-core-skill`
