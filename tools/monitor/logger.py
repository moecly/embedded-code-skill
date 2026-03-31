import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class LoopLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.log_dir / f"session_{self.current_session}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.loops: List[Dict] = []
    
    def log_loop_start(self, loop_num: int, config: dict):
        """记录循环开始"""
        self.current_loop = {
            "loop_num": loop_num,
            "start_time": datetime.now().isoformat(),
            "config": config,
            "flash_output": "",
            "serial_output": "",
            "modifications": [],
            "success": False
        }
    
    def log_flash_result(self, success: bool, output: str):
        """记录烧录结果"""
        self.current_loop["flash_success"] = success
        self.current_loop["flash_output"] = output
    
    def log_serial_output(self, output: str):
        """记录串口输出"""
        self.current_loop["serial_output"] = output
    
    def log_modification(self, file_path: str, old_content: str, new_content: str, reason: str):
        """记录代码修改"""
        self.current_loop["modifications"].append({
            "file": file_path,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_loop_end(self, success: bool):
        """记录循环结束"""
        self.current_loop["end_time"] = datetime.now().isoformat()
        self.current_loop["success"] = success
        self.loops.append(self.current_loop)
        self._save_loop(loop_num=self.current_loop["loop_num"])
    
    def _save_loop(self, loop_num: int):
        """保存单次循环日志"""
        loop_file = self.session_dir / f"loop_{loop_num:02d}.json"
        with open(loop_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_loop, f, ensure_ascii=False, indent=2)
    
    def generate_report(self, final_success: bool = False) -> str:
        """生成最终报告"""
        report_path = self.session_dir / "report.md"
        
        report = f"""# 调试闭环报告

**会话时间**: {self.current_session}
**总循环次数**: {len(self.loops)}
**最终结果**: {'✅ 成功' if final_success else '❌ 失败'}

---

## 循环详情

"""
        for loop in self.loops:
            status = '✅' if loop['success'] else '❌'
            report += f"""### 循环 {loop['loop_num']} {status}

**时间**: {loop['start_time']} ~ {loop.get('end_time', 'N/A')}

**烧录**: {'成功' if loop.get('flash_success') else '失败'}

**串口输出**:
```
{loop.get('serial_output', 'N/A')[:500]}
```

"""
            if loop.get('modifications'):
                report += "**修改**:\n"
                for mod in loop['modifications']:
                    report += f"- {mod['file']}: {mod['reason']}\n"
                report += "\n"
        
        report += """---

## 失败原因分析

"""
        failed_loops = [l for l in self.loops if not l['success']]
        if failed_loops:
            report += "请检查上述循环的串口输出，确定代码问题后手动介入。\n"
        else:
            report += "所有循环均成功完成。\n"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(report_path)
    
    def get_summary(self) -> str:
        """获取简要摘要"""
        success_count = sum(1 for l in self.loops if l['success'])
        return f"循环: {len(self.loops)} 次, 成功: {success_count} 次"
