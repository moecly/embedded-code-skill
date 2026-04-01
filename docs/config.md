# 配置文件说明

## 完整配置示例

```yaml
build:
  type: "cmake"          # keil / makefile / cmake
  search_root: ".."      # 相对于 configs 目录的工程根目录
  keil:
    path: null           # 留空自动检测，或指定路径
  makefile:
    cmd: "make -j4"
  cmake:
    build_dir: "build"

flasher:
  type: "jlink"          # jlink / stlink / cmsis_dap
  device: "<芯片型号>"
  speed: 4000            # KHz
  interface: "SWD"       # SWD / JTAG

serial:
  port: "<串口号>"
  baudrate: 115200
  timeout: 10

flash:
  elf: "../build/project.elf"
  hex: "../build/project.hex"

debug:
  max_retries: 3
  log_dir: "logs"
```

## 配置项说明

### build

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 项目类型：keil/makefile/cmake |
| `search_root` | string | 搜索项目的根目录（相对于 configs 目录） |
| `keil.path` | string | UV4.exe 路径，不在 PATH 时指定 |
| `makefile.cmd` | string | make 命令 |
| `cmake.build_dir` | string | 构建目录 |

### flasher

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 烧录器类型：jlink/stlink/cmsis_dap |
| `device` | string | 芯片型号，如 `<芯片型号>` |
| ... |
| `port` | string | 串口端口，如 `<串口号>` |
| `baudrate` | int | 波特率 |
| `timeout` | int | 超时时间（秒） |

### flash

| 字段 | 类型 | 说明 |
|------|------|------|
| `elf` | string | ELF 文件路径（相对于 configs 目录） |
| `hex` | string | HEX 文件路径 |

### debug

| 字段 | 类型 | 说明 |
|------|------|------|
| `max_retries` | int | 最大重试次数 |
| `log_dir` | string | 日志目录 |
