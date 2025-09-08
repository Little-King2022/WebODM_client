import tkinter as tk
import os
import sys
import traceback

from webodm_ui import WebODMClientUI

def main():
    """主函数"""
    try:
        # 创建Tkinter根窗口
        root = tk.Tk()
        
        # 创建WebODM客户端UI
        app = WebODMClientUI(root)
        
        # 启动主循环
        root.mainloop()
    except Exception as e:
        # 显示错误信息
        error_message = f"发生错误: {str(e)}\n\n{traceback.format_exc()}"
        print(error_message)
        
        # 如果GUI已经初始化，则显示错误对话框
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", error_message)
        except:
            pass

if __name__ == "__main__":
    main()