# Embedded Flash Skill

嵌入式开发调试闭环工具集，支持 **编译 → 烧录 → 监控 → 分析** 全流程自动化。

## 特性

- **项目自动检测**：自动识别 Keil MDK、Makefile、CMake 项目类型
- **烧录器自动检测**：支持 J-Link、ST-Link、CMSIS-DAP
- **串口监控**：实时显示串口输出，便于调试分析
- **调试闭环**：烧录失败自动重试（最多3次）
- **跨平台路径**：自动处理 Windows/macOS/Linux 路径差异

## 目录结构

```
embedd-code-skill/
├── SKILL.md              # Skill 入口定义
├── README.md             # 本文档
├── docs/                 # 详细文档
│   ├── quickstart.md     # 快速开始
│   ├── agent-guide.md    # Agent 使用指南
│   ├── config.md         # 配置说明
│   ├── compilers.md       # 编译器说明
│   ├── flashers.md       # 烧录器说明
│   └── extending.md      # 扩展指南
├── configs/              # 配置模板
│   └── project.yaml      # 项目配置示例
├── workflows/            # 核心工作流脚本
│   ├── agent_flash.py    # ★ 推荐：一体化烧录脚本
│   ├── detect.py         # 环境检测
│   ├── build.py          # 项目构建检测
│   └── debug_loop.py     # 调试闭环
├── tools/                # 工具模块
│   ├── builder/          # 编译器适配
│   ├── flashers/         # 烧录器适配
│   └── monitor/          # 串口监控
├── jlink_cmd.txt         # J-Link 命令模板
└── logs/                 # 日志目录
```

---

## 快速开始

### 方式一：一条命令完成所有操作（推荐）

```bash
# 1. 检测环境（查看可用的烧录器和串口）
python "SKILL/workflows/agent_flash.py" --detect

# 2. 烧录 + 监控（最常用）
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --serial "COM3"

# 3. 编译 + 烧录 + 监控（完整流程）
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --build \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

### 方式二：分步执行

```bash
# 步骤 1：检测环境
python "SKILL/workflows/detect.py" --json
python "SKILL/workflows/build.py" --detect --json --search "工程目录"

# 步骤 2：创建配置文件
# 编辑 工程目录/configs/project.yaml

# 步骤 3：启动调试闭环
python "SKILL/workflows/debug_loop.py" --config "工程目录/configs/project.yaml"
```

---

## 参数说明

### agent_flash.py 参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--project` | 是 | 工程目录（绝对路径） | `D:/workspacePrj/JL5104` |
| `--elf` | 是 | 烧录文件（相对工程目录） | `MDK-ARM/test0/test0.elf` |
| `--device` | 是 | 芯片型号 | `STM32F407ZGTx` |
| `--flasher` | 否 | 烧录器类型 | `jlink` / `stlink` / `cmsis_dap` |
| `--serial` | 否 | 串口端口 | `COM3` |
| `--baudrate` | 否 | 波特率 | `115200`（默认） |
| `--speed` | 否 | 烧录速度(KHz) | `4000`（默认） |
| `--interface` | 否 | 调试接口 | `SWD`（默认）/ `JTAG` |
| `--build` | 否 | 编译后再烧录 | flag |
| `--skip-monitor` | 否 | 跳过串口监控 | flag |
| `--detect` | 否 | 仅检测环境 | flag |

### 常用芯片型号

| 系列 | 型号示例 |
|------|----------|
| STM32F1 | `STM32F103RC`, `STM32F103ZE` |
| STM32F4 | `STM32F407ZG`, `STM32F407ZGTx`, `STM32F429ZI` |
| STM32H7 | `STM32H743ZI`, `STM32H743ZIT6` |
| APM32 | `APM32F407ZG`, `APM32F103RC` |

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                      调试闭环流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户触发 skill                                            │
│        ↓                                                    │
│   检测环境 (agent_flash.py --detect)                        │
│        ↓                                                    │
│   分析检测结果，确定:                                        │
│   • 烧录器类型 (jlink / stlink / cmsis_dap)                 │
│   • 芯片型号 (STM32F407ZGTx)                                │
│   • 串口端口 (COM3)                                          │
│        ↓                                                    │
│   编译 + 烧录 + 重置                                         │
│        ↓                                                    │
│   串口监控 + 输出分析                                        │
│        ↓                                                    │
│   ┌─────────────────────┐                                   │
│   │ 代码正常运行？        │                                   │
│   └─────────┬───────────┘                                   │
│        是 ↙       ↘ 否                                      │
│      完成    用户修改代码                                    │
│                  ↓                                          │
│            重新烧录 (最多3次重试)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 配置文件（可选）

在工程目录下创建 `configs/project.yaml` 可简化命令：

```yaml
# 工程目录/configs/project.yaml

flasher:
  type: "jlink"           # 烧录器类型: jlink / stlink / cmsis_dap
  device: "STM32F407ZGTx" # 芯片型号
  speed: 4000             # 烧录速度 (KHz)
  interface: "SWD"         # 调试接口: SWD / JTAG

serial:
  port: "COM3"             # 串口端口
  baudrate: 115200         # 波特率

flash:
  elf: "MDK-ARM/test0/test0.elf"  # 烧录文件（相对于工程目录）

debug:
  max_retries: 3           # 最大重试次数
  skip_monitor: false      # 是否跳过串口监控
```

使用配置文件后，只需：

```bash
python "SKILL/workflows/debug_loop.py" --config "工程目录/configs/project.yaml"
```

---

## 烧录器支持

### J-Link

- **检测命令**: `JLink.exe --version`
- **推荐速度**: 4000 KHz
- **接口**: SWD / JTAG
- **特点**: 兼容性好，速度快

### ST-Link

- **检测命令**: `ST-Link_CLI.exe -List`
- **特点**: STM 官方工具，免费

### CMSIS-DAP / OpenOCD

- **检测命令**: `openocd -f interface/cmsis-dap.cfg -c "adapter list"`
- **特点**: 开源标准，通用性强

---

## 项目类型检测

| 项目类型 | 检测文件 | 编译命令 |
|----------|----------|----------|
| Keil MDK | `*.uvprojx`, `*.uvproj` | `UV4.exe -j0 -b project.uvprojx` |
| Makefile | `Makefile`, `makefile` | `make -j4` |
| CMake | `CMakeLists.txt` | `cmake --build build -- -j4` |

---

## 路径规范

| 规则 | 说明 | 示例 |
|------|------|------|
| 使用正斜杠 `/` | 跨平台兼容 | `D:/project/test.elf` |
| 相对路径 | 相对于 `--project` | `MDK-ARM/test0/test0.elf` |
| 始终使用引号 | 防止空格问题 | `"D:/My Project/test.elf"` |

```bash
# ✓ 正确写法
--project "D:/workspacePrj/JL5104"
--elf "MDK-ARM/test0/test0.elf"
--elf "../output/firmware.hex"

# ✗ 错误写法
--elf "D:\workspacePrj\JL5104\MDK-ARM\test0\test0.elf"
--elf D:/project/test.elf
```

---

## 常见问题

**Q: 不知道芯片型号？**
A: 查看 Keil 项目的 `.uvprojx` 文件中的 `<Device>` 标签

**Q: 串口是哪个？**
A: 运行 `--detect` 查看所有可用串口

**Q: 用什么烧录器？**
A: 运行 `--detect` 查看已连接的烧录器

**Q: 路径有空格怎么办？**
A: 用引号包裹路径：`"D:/My Project/test.elf"`

**Q: Windows 反斜杠可以用吗？**
A: 可以，脚本会自动转换为正斜杠，但不建议使用

---

## 脚本速查

| 功能 | 脚本路径 |
|------|----------|
| **一体化烧录（推荐）** | `workflows/agent_flash.py` |
| 环境检测 | `workflows/detect.py` |
| 项目构建检测 | `workflows/build.py` |
| 调试闭环 | `workflows/debug_loop.py` |

---

## 文档导航

- [快速开始](docs/quickstart.md) - 最简使用流程
- [Agent 使用指南](docs/agent-guide.md) - Agent 工作流详解
- [配置说明](docs/config.md) - 配置文件详解
- [编译器说明](docs/compilers.md) - Keil/Makefile/CMake
- [烧录器说明](docs/flashers.md) - J-Link/ST-Link/OpenOCD
- [扩展指南](docs/extending.md) - 添加新工具支持

---

**SKILL 路径**: `C:\Users\m\.config\opencode\skills\embedd-code-skill`
