# Agent 工作流指南

## 核心原则

1. **先检测环境** — 运行 `--detect --json` 了解可用烧录器和串口
2. **初始化配置** — 运行 `--init` 获取 JSON，解析后询问用户生成配置
3. **生成配置文件** — 根据用户回答写入 `configs/project.yaml`
4. **后续直接烧录** — 配置文件存在后，脚本无需交互

---

## 首次配置流程

```bash
# 1. 检测环境（查看烧录器、串口、芯片连接状态）
python "SKILL/workflows/agent_flash.py" --detect --json

# 2. 初始化配置（输出 JSON 供解析）
python "SKILL/workflows/agent_flash.py" --init
```

`--init` 输出示例：
```json
{
  "project": {"name": "firmware", "type": "keil", "path": "MDK-ARM/project.uvprojx"},
  "flashers": [
    {
      "type": "jlink",
      "name": "J-Link",
      "device_connected": true,
      "device_message": "芯片连接正常"
    }
  ],
  "available_flashers": ["jlink"],
  "serial_ports": [
    {"port": "COM3", "description": "USB Serial Port"}
  ]
}
```

**注意**：`device_connected` 为 `false` 时，`device_message` 会包含错误原因和排查建议。此时应告知用户检查硬件连接，不要继续烧录。

### Agent 询问用户

根据 `--init` 输出，向用户确认：

| 信息 | 来源 | 说明 |
|------|------|------|
| 烧录器 | `flashers` 列表 | 如有多个，让用户选择 |
| 芯片连接状态 | `device_connected` | 为 false 时提示用户检查硬件 |
| 芯片型号 | 需询问用户 | 脚本无法自动检测 |
| 串口 | `serial_ports` 列表 | 如有多个，让用户选择 |
| 波特率 | 需询问用户 | 默认 115200 |

### 生成配置文件

用户确认后，Agent 生成 `<项目目录>/configs/project.yaml`：

```yaml
project:
  name: "firmware"
  type: "keil"

flasher:
  type: "jlink"
  device: "<芯片型号>"
  speed: 4000
  interface: "SWD"

serial:
  port: "COM3"
  baudrate: 115200

debug:
  max_retries: 3
```

---

## 后续烧录流程

配置文件存在后，直接烧录：

```bash
python "SKILL/workflows/agent_flash.py" --flash "build/firmware.hex"
```

---

## 常用场景

### 检测环境

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

### 烧录 + 串口监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --flash "build/firmware.hex" \
    --device "<芯片型号>" \
    --serial "<串口号>"
```

### 编译 + 烧录 + 监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --build \
    --flash "build/firmware.hex"
```

### 仅烧录，跳过监控

```bash
python "SKILL/workflows/agent_flash.py" \
    --flash "build/firmware.hex" \
    --skip-monitor
```

---

## 路径规范

| 规则 | 说明 |
|------|------|
| 使用正斜杠 `/` | 跨平台兼容 |
| 相对路径 | 相对于 `--project` 或当前目录 |
| 使用引号 | 路径含空格时必须加引号 |

脚本自动处理：
1. 反斜杠 `\` → 正斜杠 `/`
2. 相对路径 → 基于当前目录或 `--project` 解析
3. 路径不存在 → 报错

---

## 检测输出格式

`--detect --json` 输出：
```json
{
  "flashers": [
    {
      "type": "jlink",
      "available": true,
      "devices": ["SEGGER J-Link Commander V8.10k..."],
      "device_connected": true,
      "device_message": "芯片连接正常"
    }
  ],
  "serial_ports": [
    {"port": "COM3", "description": "USB Serial Port"}
  ]
}
```

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
3. 分析结果：
   ├─ 烧录失败 → 反馈用户，让用户检查硬件连接（最多3次）
   └─ 烧录成功 → 分析串口输出
       ├─ 输出符合预期 → 结束
       └─ 输出不符合预期 → Agent 自动修复 bug → 回到步骤1
```

---

## 常见问题

**Q: 路径有空格怎么办？**
A: 用引号包裹路径：`"D:/My Project/firmware.hex"`

**Q: 工具运行出错？**
A: 询问用户是否执行自动化测试：
```bash
pip install -r requirements.txt
pytest tests/ -v
```
