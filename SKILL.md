---
name: embedded-code
license: MIT
github: https://github.com/moecly/embedded-code-skill
description: 嵌入式固件烧录工具集，支持 Keil/Makefile/CMake 项目自动检测，J-Link/ST-Link/CMSIS-DAP 烧录，串口监控。
metadata:
  author: moecly
  version: "1.0.0"
---

# Embedded Code Skill

嵌入式固件烧录工具集，简化 **编译 → 烧录 → 监控 → 调试** 流程。

## 前置检查

首次使用前，先检测环境：

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

输出会显示检测到的烧录器和串口。如果没有检测到烧录器，请确保：
- 烧录器已通过 USB 连接
- 驱动已正确安装

烧录器（J-Link/ST-Link/CMSIS-DAP）是**可选工具**，根据用户实际拥有的硬件决定。

---

## 执行哲学

**遇到问题 → 反馈用户，而非自行尝试修复。**

### 决策树

```
脚本执行失败？
├── 错误信息明确 → 将错误反馈给用户，等待指示
├── 错误信息模糊 → 尝试诊断（如检查连接、重试），仍失败则反馈用户
└── 用户明确要求烧录但无烧录器 → 告知用户无可用烧录器，建议检查连接
```

### 约束

1. **不擅用命令行**：不要绕过 skill 脚本，直接调用 `JLink.exe`、`openocd` 等工具
2. **执行前确认**：烧录前显示检测到的参数，询问用户确认后再执行
3. **不确定就问**：无法判断的信息向用户确认，不猜测

---

## 工具选择

### 主脚本：agent_flash.py

所有操作优先使用 `agent_flash.py`，它会自动处理项目检测、配置管理、烧录、监控。

### 使用场景

| 场景 | 命令 | 说明 |
|------|------|------|
| 检测环境 | `--detect` | 查看可用烧录器和串口 |
| 首次配置 | `--project <目录>` | 自动检测项目、烧录器、串口，引导用户配置 |
| 烧录固件 | `--flash <文件>` | 烧录 .elf/.hex/.bin |
| 编译+烧录 | `--build --flash <文件>` | 编译后烧录 |
| 跳过监控 | `--skip-monitor` | 仅烧录，不监控串口 |

### 烧录文件类型

| 类型 | 说明 | 参数 |
|------|------|------|
| `.elf` | Keil/GCC 编译产物，包含调试信息 | `--flash firmware.elf` |
| `.hex` | Intel hex 格式 | `--flash firmware.hex` |
| `.bin` | 纯二进制，需指定地址 | `--flash firmware.bin --addr 0x08000000` |

> **注意**：ST-Link 不支持 .elf 文件

---

## 快速开始

### 1. 检测环境

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

### 2. 首次使用：配置项目

```bash
# 使用当前工作目录
python "SKILL/workflows/agent_flash.py"

# 或指定项目目录
python "SKILL/workflows/agent_flash.py" --project "<项目目录>"
```

脚本会自动：
1. 检测项目类型（Keil/Makefile/CMake）
2. 检测烧录器（J-Link/ST-Link/CMSIS-DAP）
3. 检测串口
4. 引导用户确认配置

### 3. 后续使用

```bash
# 使用当前目录
python "SKILL/workflows/agent_flash.py" --flash "<固件文件>"

# 或指定项目目录
python "SKILL/workflows/agent_flash.py" --project "<项目目录>" --flash "<固件文件>"
```

配置文件保存在 `<项目目录>/configs/project.yaml`，后续运行自动加载。

---

## 常用命令示例

### 检测并查看环境

```bash
python "SKILL/workflows/agent_flash.py" --detect --json
```

输出示例：
```json
{
  "flashers": [{"type": "jlink", "available": true}],
  "serial_ports": [{"port": "<串口号>", "description": "USB Serial Port"}]
}
```

### 烧录 + 串口监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --flash "<固件文件>" \
    --device "<芯片型号>" \
    --serial "<串口号>"
```

### 编译 + 烧录 + 监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --build \
    --flash "<固件文件>"
```

### 仅烧录，跳过监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --flash "<固件文件>" \
    --skip-monitor
```

---

## 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--project` / `-p` | 否 | 工程目录（默认当前目录） | `<项目目录>` |
| `--flash` | 否 | 烧录文件 | `<固件文件>` |
| `--addr` | 否 | 烧录地址（仅 .bin 需要） | `0x08000000` |
| `--device` / `-d` | 否 | 芯片型号 | `<芯片型号>` |
| `--serial` / `-s` | 否 | 串口端口 | `<串口号>` |
| `--baudrate` / `-b` | 否 | 波特率 | `115200` |
| `--flasher` / `-f` | 否 | 烧录器类型 | `jlink` |
| `--speed` | 否 | 烧录速度 (KHz) | `4000` |
| `--interface` / `-i` | 否 | 接口 | `SWD` / `JTAG` |
| `--monitor-timeout` / `-t` | 否 | 监控超时 (秒) | `10` |
| `--build` | 否 | 编译后再烧录 | flag |
| `--skip-monitor` | 否 | 跳过串口监控 | flag |
| `--detect` | 否 | 仅检测环境 | flag |
| `--force-config` | 否 | 强制重新配置 | flag |

---

## 配置文件

初始化后生成 `<项目目录>/configs/project.yaml`：

```yaml
project:
  name: "<项目名称>"
  type: "cmake"

flasher:
  type: "jlink"
  device: "<芯片型号>"
  speed: 4000
  interface: "SWD"

serial:
  port: "<串口号>"
  baudrate: 115200

debug:
  max_retries: 3
```

| 字段 | 说明 |
|------|------|
| `project.type` | 项目类型：`keil` / `makefile` / `cmake` |
| `flasher.type` | 烧录器：`jlink` / `stlink` / `cmsis_dap` |
| `flasher.device` | 芯片型号，如 `STM32F103RC` |
| `flasher.interface` | 接口：`SWD` 或 `JTAG` |
| `serial.port` | 串口号，如 `COM3` |
| `serial.baudrate` | 波特率 |

---

## 常见问题

**Q: 烧录失败？**
A: 请用户检查：
- 烧录器与芯片是否正常连接（SWD/JTAG 接口）
- 芯片型号是否与实际匹配
- 芯片是否正常供电

**Q: 串口无输出？**
A: 请用户检查：
- 串口号是否正确（用 `--detect` 查看）
- 波特率是否与固件配置一致
- 串口是否被其他程序占用

**Q: .bin 文件如何烧录？**
A: 必须指定烧录地址：
```bash
python "SKILL/workflows/agent_flash.py" --project "<目录>" --flash firmware.bin --addr 0x08000000
```

**Q: ST-Link 不支持 elf？**
A: 是的，ST-Link 只支持 .hex 和 .bin。使用 J-Link 或 CMSIS-DAP 可烧录 .elf。

**Q: 工具运行出错？**
A: 运行测试验证：
```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## References 索引

| 文件 | 何时加载 |
|------|---------|
| `docs/quickstart.md` | 新用户快速上手 |
| `docs/config.md` | 配置文件详解 |
| `docs/flashers.md` | 烧录器详细说明 |
| `docs/extending.md` | 添加新工具支持 |
| `docs/compilers.md` | Keil/Makefile/CMake 编译 |

---

## 脚本路径速查

| 功能 | 脚本 |
|------|------|
| **推荐** | `workflows/agent_flash.py` |
| 环境检测 | `workflows/detect.py` |
| 构建检测 | `workflows/build.py` |
| 调试闭环 | `workflows/debug_loop.py` |

> - `SKILL`：技能工作区路径
> - `--project`：用户项目目录
