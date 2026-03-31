# Agent 使用指南

## 核心原则

作为 Agent，使用这个 skill 时应该：
1. **先检测环境** - 了解可用的烧录器和串口
2. **使用最简单的命令** - `agent_flash.py`
3. **按需选择** - 如果需要更精细控制再用其他脚本

---

## 推荐的 Agent 工作流

### 场景 1：快速检测环境

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

### 场景 2：烧录 + 串口监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

### 场景 3：编译 + 烧录 + 监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --build \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

### 场景 4：跳过监控，只烧录

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "D:/workspacePrj/JL5104" \
    --elf "MDK-ARM/test0/test0.elf" \
    --device "STM32F407ZGTx" \
    --skip-monitor
```

---

## 检测输出格式

```json
{
  "flashers": [
    {"type": "jlink", "available": true, "devices": ["SEGGER J-Link..."]}
  ],
  "serial_ports": [
    {"port": "COM3", "description": "USB Serial Port"}
  ]
}
```

---

## 常见参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--project` | 是 | 工程目录 | `D:/workspacePrj/JL5104` |
| `--elf` | 是 | 烧录文件 | `MDK-ARM/test0/test0.elf` |
| `--device` | 是 | 芯片型号 | `STM32F407ZGTx` |
| `--serial` | 否 | 串口端口 | `COM3` |
| `--flasher` | 否 | 烧录器类型 | `jlink` (默认) |

---

## 芯片型号参考

| 系列 | 型号示例 |
|------|----------|
| STM32F1 | `STM32F103RC`, `STM32F103ZE` |
| STM32F4 | `STM32F407ZG`, `STM32F407ZGTx`, `STM32F429ZI` |
| STM32H7 | `STM32H743ZI`, `STM32H743ZIT6` |
| APM32 | `APM32F407ZG`, `APM32F103RC` |

---

## 调试闭环流程

```
1. 用户修改代码
2. 执行烧录+监控
3. 分析串口输出
4. 判断代码是否正常运行
5. 是 → 结束
6. 否 → 用户修改代码 → 回到步骤1 (最多3次)
```

---

## 注意事项

1. **路径使用正斜杠** - Windows 下也用 `/` 而非 `\`
2. **芯片型号要准确** - 与 Keil 项目中一致
3. **串口端口正确** - 从检测结果中选择
