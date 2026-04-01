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
    --project "D:/project/firmware" \
    --flash "MDK-ARM/project/firmware.hex" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

### 场景 3：编译 + 烧录 + 监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "D:/project/firmware" \
    --build \
    --flash "MDK-ARM/project/firmware.hex" \
    --device "STM32F407ZGTx" \
    --serial "COM3"
```

### 场景 4：跳过监控，只烧录

```bash
python "SKILL/workflows/agent_flash.py" \
    --project "D:/project/firmware" \
    --flash "MDK-ARM/project/firmware.hex" \
    --device "STM32F407ZGTx" \
    --skip-monitor
```

---

## 路径规范（重要！）

### 路径规则

| 规则 | 说明 | 示例 |
|------|------|------|
| **使用正斜杠** `/` | 跨平台兼容 | `D:/project/firmware.hex` |
| **相对路径** | 相对于 `--project` | `MDK-ARM/project/firmware.hex` |
| **始终使用引号** | 防止空格问题 | `"D:/My Project/firmware.hex"` |

### 正确 vs 错误

```bash
# ✅ 正确写法
--project "D:/project/firmware"
--flash "MDK-ARM/project/firmware.hex"
--flash "../output/firmware.hex"

# ❌ 错误写法
--flash "D:\My Projects\firmware\firmware.hex"
--flash D:/project/firmware.hex
```

### 路径解析说明

脚本会自动处理以下情况：
1. 反斜杠 `\` → 自动转换为正斜杠 `/`
2. 相对路径 → 自动基于 `--project` 解析
3. 路径不存在 → 报错并提示正确路径

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
| `--project` | 是 | 工程目录 | `D:/project/firmware` |
| `--flash` | 是 | 烧录文件（支持 .elf/.hex/.bin） | `MDK-ARM/project/firmware.hex` |
| `--addr` | 否 | 烧录地址（仅 .bin 需要） | `0x08000000` |
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

## 常见问题

**Q: 路径有空格怎么办？**
A: 用引号包裹路径：`"D:/My Project/firmware.hex"`

**Q: Windows 反斜杠可以用吗？**
A: 可以，脚本会自动转换，但不建议使用

**Q: 相对路径怎么写？**
A: 相对于 `--project` 参数指定的目录

**Q: 找不到文件怎么办？**
A: 检查路径是否正确，使用正斜杠 `/`

**Q: 工具运行出错？**
A: 询问用户是否执行自动化测试：
```bash
pip install -r requirements.txt
pytest tests/ -v
```
