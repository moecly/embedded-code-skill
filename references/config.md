# 配置参考

Agent 读取此文件了解 `configs/project.yaml` 的字段含义。

## 完整配置示例

```yaml
project:
  name: "firmware"           # 项目名称
  type: "cmake"              # keil / makefile / cmake

flasher:
  type: "jlink"              # jlink / stlink / cmsis_dap
  device: "<芯片型号>"        # 芯片型号
  speed: 4000                # 烧录速度 (KHz)
  interface: "SWD"           # SWD / JTAG

serial:
  port: "<串口号>"            # 串口号
  baudrate: 115200           # 波特率
  timeout: 10                # 超时时间（秒）

debug:
  max_retries: 3             # 最大重试次数
  log_dir: "logs"            # 日志目录
```

## 配置项说明

### project

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 项目名称 |
| `type` | string | 项目类型：`keil` / `makefile` / `cmake` |

### flasher

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 烧录器类型：`jlink` / `stlink` / `cmsis_dap` |
| `device` | string | 芯片型号 |
| `speed` | int | 烧录速度 (KHz)，默认 4000 |
| `interface` | string | 接口：`SWD` 或 `JTAG` |

### serial

| 字段 | 类型 | 说明 |
|------|------|------|
| `port` | string | 串口号 |
| `baudrate` | int | 波特率，默认 115200 |
| `timeout` | int | 超时时间（秒），默认 10 |

### debug

| 字段 | 类型 | 说明 |
|------|------|------|
| `max_retries` | int | 最大重试次数，默认 3 |
| `log_dir` | string | 日志目录 |
