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

> **⚠️ Agent 行为约束**
>
> 1. **遇到问题 → 反馈用户**：脚本执行失败时，应将错误信息反馈给用户，而不是自行尝试其他方法
> 2. **不擅作主张**：不要绕过 skill 提供的脚本，自己去调用命令行工具（如 `JLink.exe`、`openocd` 等）
> 3. **执行前确认参数**：烧录前，应先显示检测到的参数（芯片型号、烧录器、串口、波特率、接口类型），询问用户是否需要调整，确认后再执行
> 4. **遇到不确定 → 询问**：无法确定的信息应向用户确认，而不是猜测

## 推荐：使用 agent_flash.py（最简单）

```bash
# 1. 检测环境
python "SKILL/workflows/agent_flash.py" --detect

# 2. 首次使用：初始化项目配置
python "SKILL/workflows/agent_flash.py" --project D:/project/firmware --init

# 3. 烧录并监控
python "SKILL/workflows/agent_flash.py" --project D:/project/firmware --flash MDK-ARM/project/project.hex --device STM32F407ZGTx --serial COM3

# 4. 编译+烧录+监控
python "SKILL/workflows/agent_flash.py" --project D:/project/firmware --build --flash MDK-ARM/project/project.hex --device STM32F407ZGTx --serial COM3
```

### agent_flash.py 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--project` / `-p` | 工程目录 | `D:/project/firmware` |
| `--flash` | 烧录文件（支持 .elf/.hex/.bin） | `MDK-ARM/project/project.hex` |
| `--addr` | 烧录地址（仅 .bin 需要） | `0x08000000` |
| `--flasher` / `-f` | 烧录器类型 | `jlink` / `stlink` / `cmsis_dap` |
| `--device` / `-d` | 芯片型号 | `STM32F407ZGTx` |
| `--serial` / `-s` | 串口端口 | `COM3` |
| `--baudrate` / `-b` | 波特率 | `115200` |
| `--speed` | 烧录速度(KHz) | `4000` |
| `--interface` / `-i` | 接口 | `SWD` / `JTAG` |
| `--monitor-timeout` / `-t` | 串口监控超时秒数 | `10` |
| `--build` | 编译后再烧录 | flag |
| `--skip-monitor` | 跳过串口监控 | flag |
| `--detect` | 仅检测环境 | flag |
| `--init` | 首次初始化项目配置 | flag |
| `--json` | 输出 JSON 格式结果 | flag |

### 烧录文件说明

| 文件类型 | 说明 | 示例 |
|----------|------|------|
| `.elf` | Keil/GCC 编译产物，包含调试信息 | `--flash firmware.elf` |
| `.hex` | Intel hex 格式，包含地址信息 | `--flash firmware.hex` |
| `.bin` | 纯二进制文件，需要指定烧录地址 | `--flash firmware.bin --addr 0x08000000` |

> **注意**：`.bin` 文件必须通过 `--addr` 指定烧录地址（如 STM32 通常是 `0x08000000`）

---

## 首次使用流程

### 1. 初始化项目配置

```bash
python "SKILL/workflows/agent_flash.py" --project "D:/project/firmware" --init
```

脚本会：

1. 检测项目文件（Keil/Makefile/CMake）
2. 检测烧录器（J-Link/ST-Link/CMSIS-DAP）
3. 检测串口
4. 显示检测结果供用户确认
5. 生成 `项目目录/configs/project.yaml`

### 2. 确认配置

```
检测结果：
  项目类型: Keil MDK
  项目路径: D:/project/firmware/MDK-ARM/project.uvprojx
  烧录器:   J-Link
  串口:     COM3

请输入芯片型号 (如 STM32F407ZGTx): STM32F407ZGTx
请输入接口类型 (SWD/JTAG, 默认 SWD): SWD

是否保存配置? (Y/n): Y
```

### 3. 后续使用

初始化后，直接使用：

```bash
python "SKILL/workflows/agent_flash.py" --project "D:/project/firmware" --flash "MDK-ARM/project/project.hex"
```

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

## 常见问题

**Q: 烧录失败？**
A: 请用户检查：

- 硬件连接：烧录器与芯片是否正常连接（SWD/JTAG 接口）
- 芯片型号：是否与实际芯片匹配（如 STM32F407ZGTx）
- 供电情况：芯片是否正常供电

**Q: 串口无输出？**
A: 请用户检查：

- 串口号：是否选择了正确的 COM 口
- 波特率：是否与固件配置一致（默认 115200）
- 串口被占用：是否有其他程序占用该串口

**Q: .bin 文件如何烧录？**
A: 需要指定烧录地址：

   ```bash
   python "SKILL/workflows/agent_flash.py" \
       --project "D:/project/firmware" \
       --flash "firmware.bin" \
       --addr 0x08000000
   ```

---

## 配置文件

初始化后会生成 `工程目录/configs/project.yaml`：

```yaml
project:
  name: "project"
  type: "keil"

flasher:
  type: "jlink"
  device: "STM32F407ZGTx"
  speed: 4000
  interface: "SWD"

serial:
  port: "COM3"
  baudrate: 115200

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

> **路径说明**
>
> - `SKILL`：技能工作区路径（Python 脚本所在目录）
> - `--project`：用户项目目录（由用户指定）
> - Python 脚本在 SKILL 工作区内执行，用户代码在 WORKSPACE 中
