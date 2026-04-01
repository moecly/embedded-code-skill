# 烧录器使用说明

## J-Link

### 检测连接

```bash
echo -e "connect\nq" > cmd.txt && JLink.exe -CommandFile cmd.txt
```

### 烧录命令

```bash
JLink.exe -Device 芯片型号 -If SWD -Speed 4000 -CommandFile script.txt
```

### 脚本内容

```
connect
loadfile firmware.elf
r
qc
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-Device` | 芯片型号，如 STM32F407ZGTx |
| `-If` | 接口：SWD / JTAG |
| `-Speed` | 速度 (KHz) |

---

## ST-Link

### 检测设备

```bash
ST-Link_CLI.exe -List
```

### 烧录命令

```bash
ST-Link_CLI.exe -c ID=0 -P firmware.hex 0x08000000 -V -Rst -Run
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-c ID=0` | 连接第一个设备 |
| `-P file addr` | 编程到地址 |
| `-V` | 验证 |
| `-Rst` | 复位 |
| `-Run` | 运行 |
| `-ME` | 擦除 |

---

> **注意**：ST-Link 只支持 .hex 和 .bin 文件，不支持 .elf。

## CMSIS-DAP (OpenOCD)

### 检测设备

```bash
openocd -f interface/cmsis-dap.cfg -c "adapter list"
```

### 烧录命令

```bash
openocd -f interface/cmsis-dap.cfg -f target/stm32f4x.cfg \
  -c "program firmware.elf verify reset exit"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-f` | 配置文件 |
| `program` | 编程文件 |
| `verify` | 验证 |
| `reset` | 复位 |
| `exit` | 完成后退出 |

---

## 设备检测

| 烧录器 | 检测方式 |
|--------|----------|
| J-Link | USB 连接检测 |
| ST-Link | USB VID 0x0483 |
| CMSIS-DAP | USB VID 0x0D28 |
