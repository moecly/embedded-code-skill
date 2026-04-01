# 编译器使用说明

## Keil MDK

### 编译命令

```bash
UV4.exe -j0 -b "项目文件.uvprojx" [-o log.txt]
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-j0` | 使用所有 CPU 核心 |
| `-b` | 只编译不打开 IDE |
| `-o log.txt` | 输出日志到文件 |

### 示例

```bash
"UV4.exe" -j0 -b "D:/project/MDK-ARM/project.uvprojx"
```

### 检测工具

```bash
UV4.exe --version
```

---

## Makefile

### 编译命令

```bash
make [-j4] [-C 目录] [-f 文件]
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-j4` | 4 个并行任务 |
| `-C dir` | 进入目录执行 |
| `-f file` | 指定 Makefile |

### 示例

```bash
make -j4
make -j4 -C "D:/project"
```

---

## CMake

### 编译命令

```bash
# 配置
cmake -S 源码目录 -B 构建目录

# 编译
cmake --build 构建目录 [-- -j4]

# 清理
cmake --build 构建目录 -- clean
```

### 示例

```bash
cmake -S . -B build
cmake --build build -- -j4
cmake --build build -- clean
```

---

## 项目检测

| 类型 | 检测文件 |
|------|----------|
| Keil MDK | `*.uvprojx`, `*.uvproj` |
| Makefile | `Makefile`, `makefile` |
| CMake | `CMakeLists.txt` |
