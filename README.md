# Embedded Code Skill

嵌入式固件烧录工具集，简化嵌入式开发中的 **编译 → 烧录 → 监控 → 调试** 流程。

---

## 这是什么

这是一个帮助您烧录嵌入式固件的工具。可以：
- 自动检测连接的烧录器（J-Link / ST-Link / CMSIS-DAP）
- 自动识别您的项目类型（Keil / Makefile / CMake）
- 烧录.hex、.elf、.bin 文件
- 监控串口输出

---

## 快速开始

### 第一步：检测环境

先看看您的电脑能识别到哪些设备：

```bash
cd "技能目录"
python workflows/agent_flash.py --detect
```

会显示检测到的烧录器和串口。

### 第二步：初始化项目配置

首次使用时，获取项目信息：

```bash
python workflows/agent_flash.py --init
```

工具会输出 JSON 格式的检测信息（项目、烧录器、串口）。
Agent 解析后询问用户芯片型号等信息，然后生成配置文件。

### 第三步：烧录固件

```bash
python workflows/agent_flash.py --flash "firmware.hex"
```

---

## 支持的芯片

| 系列 | 型号示例 |
|------|----------|
| STM32F1 | STM32F103RC, STM32F103ZE |
| STM32F4 | STM32F407ZG, STM32F407ZGTx, STM32F429ZI |
| STM32H7 | STM32H743ZI, STM32H743ZIT6 |
| APM32 | APM32F407ZG, APM32F103RC |

---

## 支持的烧录器

| 烧录器 | 说明 |
|--------|------|
| J-Link | SEGGER 出品，速度快，兼容性好 |
| ST-Link | STM 官方工具，免费 |
| CMSIS-DAP | 开源标准，通过 OpenOCD 使用 |

---

## 支持的烧录文件

| 文件类型 | 说明 | 示例 |
|----------|------|------|
| `.hex` | Intel hex 格式，Keil 默认输出 | `--flash firmware.hex` |
| `.elf` | 包含调试信息 | `--flash firmware.elf` |
| `.bin` | 纯二进制，需要指定地址 | `--flash firmware.bin --addr 0x08000000` |

---

## 常见问题

### 烧录失败？

请检查：
- 烧录器是否正确连接
- 芯片型号是否正确
- 芯片是否正常供电

### 串口无输出？

请检查：
- 串口号是否正确（可以用 `--detect` 查看）
- 波特率是否匹配（默认 115200）
- 串口是否被其他程序占用

### 工具运行出错？

可以运行自动化测试来检验：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

测试会验证工具的基本功能是否正常。

---

## 目录结构

```
embedded-code-skill/
├── README.md              # 本文档
├── requirements.txt       # Python 依赖
├── workflows/            # 核心脚本
│   ├── agent_flash.py   # 主脚本（推荐使用）
│   ├── detect.py         # 环境检测
│   ├── build.py         # 编译检测
│   └── debug_loop.py    # 调试闭环
├── tests/               # 测试用例
│   ├── test_agent_flash.py
│   ├── test_detect.py
│   └── test_flashers/
├── tools/               # 工具模块
│   ├── builder/         # 编译器适配
│   ├── flashers/       # 烧录器适配
│   └── monitor/        # 串口监控
└── references/          # Agent 参考文档
    ├── README.md
    ├── agent-guide.md
    └── config.md
```

---

## 技术支持

- 使用 `--help` 查看脚本帮助
- 使用 `--detect` 检测环境
- 查看 `references/` 目录下的参考文档


