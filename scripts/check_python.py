"""
ATF Lab - Python 版本检查辅助脚本

用途：供 start.bat 在 for 块内调用。
     把版本判断放在独立脚本里，避免在批处理的 for (...) do ( ... ) 块中
     出现括号导致 "此时不应有 )" 语法错误。

退出码：
    0  Python 版本满足要求（>= 3.9）
    1  版本过低
"""
import sys

if sys.version_info < (3, 9):
    sys.exit(1)
sys.exit(0)
