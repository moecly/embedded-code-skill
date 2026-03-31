# 快速开始

## 最简使用（Agent 推荐）

```bash
# 1. 检测环境
python "SKILL/workflows/agent_flash.py" --detect

# 2. 烧录并监控串口
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

---

## 完整流程

### 步骤 1：检测环境

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

输出示例：
```
=== 烧录器 ===
  jlink: 可用

=== 串口 ===
  COM3: USB Serial Port (COM3)
```

### 步骤 2：烧录 + 监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "你的工程目录" \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "芯片型号" \
    --serial "COM3"
```

### 步骤 3：分析结果

观察串口输出，判断代码是否正常运行：
- 有预期输出 → 成功
- 无输出或错误 → 修改代码，重新烧录

---

## 目录结构

```
工程目录/
├── configs/               # 可选：配置文件
│   └── project.yaml
├── MDK-ARM/             # Keil 项目
│   ├── test0.uvprojx
│   └── test0/
│       └── test0.elf    # 烧录文件
├── Core/                 # 源代码
└── ...
```

---

## 常见问题

**Q: 不知道芯片型号？**
A: 查看 Keil 项目的 .uvprojx 文件中的 `<Device>` 标签

**Q: 串口是哪个？**
A: 运行 `--detect` 查看所有可用串口

**Q: 用什么烧录器？**
A: 运行 `--detect` 查看已连接的烧录器
