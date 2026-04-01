# 快速开始

## 最简使用

```bash
# 1. 检测环境
python "SKILL/workflows/agent_flash.py" --detect

# 2. 初始化项目配置
python "SKILL/workflows/agent_flash.py" --project "你的工程目录" --init

# 3. 烧录固件
python "SKILL/workflows/agent_flash.py" --project "你的工程目录" --flash "firmware.hex"
```

---

## 完整流程

### 步骤 1：检测环境

```bash
python "SKILL/workflows/agent_flash.py" --detect
```

会显示检测到的烧录器和串口。

### 步骤 2：初始化项目

```bash
python "SKILL/workflows/agent_flash.py" --project "你的工程目录" --init
```

脚本输出 JSON 格式，包含检测到的项目、烧录器、串口信息。
Agent 解析后询问用户芯片型号等信息，然后生成配置文件。

### 步骤 3：烧录固件

```bash
python "SKILL/workflows/agent_flash.py" --project "你的工程目录" --flash "firmware.hex"
```

### 步骤 4：分析结果

观察串口输出，判断代码是否正常运行：
- 有预期输出 → 成功
- 无输出或错误 → 修改代码，重新烧录

---

## 常见问题

**Q: 不知道芯片型号？**
A: 查看 Keil 项目的 .uvprojx 文件中的 `<Device>` 标签

**Q: 串口是哪个？**
A: 运行 `--detect` 查看所有可用串口

**Q: 用什么烧录器？**
A: 运行 `--detect` 查看已连接的烧录器

**Q: 工具运行出错？**
A: 可以运行自动化测试来检验：
```bash
pip install -r requirements.txt
pytest tests/ -v
```
