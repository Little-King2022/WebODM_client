import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import json
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from PIL import Image, ImageTk
import re

from webodm_api import WebODMAPI
from datetime import datetime
import pytz

status_map = {
    10: "队列中",
    20: "运行中",
    30: "失败",
    40: "已完成",
    50: "已取消"
}

VERSION = "1.0.0"

class WebODMClientUI:
    """WebODM客户端UI类，使用Tkinter实现用户界面"""
    
    def __init__(self, root: tk.Tk):
        """初始化UI界面
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title(f"WebODM 客户端 {VERSION}")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 创建API客户端
        self.api = WebODMAPI()
        
        # 创建配置文件夹
        self.config_dir = os.path.join(os.path.expanduser("~"), ".webodm_client")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
        
        # 创建UI组件
        self.create_menu()
        self.create_main_frame()
        
        # 如果有保存的服务器地址，则设置
        if 'server_url' in self.config:
            self.server_url_var.set(self.config['server_url'])
        
        # 如果有保存的认证信息，则自动登录
        if 'token' in self.config and 'server_url' in self.config:
            self.api.server_url = self.config['server_url']
            self.api.token = self.config['token']
            self.api.headers = {'Authorization': f'JWT {self.config["token"]}'}
            self.update_login_status(True)
            self.load_projects()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        config_path = os.path.join(self.config_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件错误: {str(e)}")
        return {}
    
    def save_config(self):
        """保存配置文件"""
        config_path = os.path.join(self.config_dir, "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"保存配置文件错误: {str(e)}")
    
    def create_menu(self):
        """创建菜单栏"""
        self.menu_bar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="退出", command=self.root.quit)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        
        # 设置菜单
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label="服务器设置", command=self.show_server_settings)
        self.menu_bar.add_cascade(label="设置", menu=settings_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        self.menu_bar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def create_main_frame(self):
        """创建主框架"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部连接框架
        self.create_connection_frame()
        
        # 创建项目和任务框架
        self.create_projects_tasks_frame()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_connection_frame(self):
        """创建连接框架"""
        connection_frame = ttk.LabelFrame(self.main_frame, text="服务器连接", padding="10")
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 服务器地址
        server_frame = ttk.Frame(connection_frame)
        server_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(server_frame, text="服务器地址:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.server_url_var = tk.StringVar(value="http://localhost:8000")
        server_entry = ttk.Entry(server_frame, textvariable=self.server_url_var, width=40)
        server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 登录按钮
        self.login_button = ttk.Button(server_frame, text="登录", command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        self.logout_button = ttk.Button(server_frame, text="注销", command=self.logout, state=tk.DISABLED)
        self.logout_button.pack(side=tk.LEFT)
        
        # 登录状态
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.login_status_var = tk.StringVar(value="未连接")
        ttk.Label(status_frame, textvariable=self.login_status_var).pack(side=tk.LEFT)
    
    def create_projects_tasks_frame(self):
        """创建项目和任务框架"""
        # 创建分隔窗格
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建项目框架
        self.create_projects_frame()
        
        # 创建任务框架
        self.create_tasks_frame()
    
    def create_projects_frame(self):
        """创建项目框架"""
        projects_frame = ttk.LabelFrame(self.paned_window, text="项目列表")
        self.paned_window.add(projects_frame, weight=1)
        
        # 项目工具栏
        projects_toolbar = ttk.Frame(projects_frame)
        projects_toolbar.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Button(projects_toolbar, text="刷新", command=self.load_projects).pack(side=tk.LEFT, padx=2)
        ttk.Button(projects_toolbar, text="新建项目", command=self.create_new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(projects_toolbar, text="查看详情", command=self.view_project_details).pack(side=tk.LEFT, padx=2)
        
        # 项目列表
        projects_list_frame = ttk.Frame(projects_frame)
        projects_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(projects_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建项目列表
        self.projects_listbox = tk.Listbox(projects_list_frame, yscrollcommand=scrollbar.set)
        self.projects_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.projects_listbox.yview)
        
        # 绑定选择事件
        self.projects_listbox.bind('<<ListboxSelect>>', self.on_project_selected)
        
        # 项目数据
        self.projects_data = []
    
    def create_tasks_frame(self):
        """创建任务框架"""
        tasks_frame = ttk.LabelFrame(self.paned_window, text="任务列表")
        self.paned_window.add(tasks_frame, weight=2)
        
        # 任务工具栏
        tasks_toolbar = ttk.Frame(tasks_frame)
        tasks_toolbar.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Button(tasks_toolbar, text="刷新", command=self.load_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="新建任务", command=self.create_new_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="下载资源", command=self.download_assets).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="重启任务", command=self.restart_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="取消任务", command=self.cancel_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="删除任务", command=self.remove_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text="查看详情", command=self.on_task_double_click).pack(side=tk.LEFT, padx=2)
        
        # 任务列表
        tasks_list_frame = ttk.Frame(tasks_frame)
        tasks_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建滚动条
        scrollbar_x = ttk.Scrollbar(tasks_list_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        scrollbar_y = ttk.Scrollbar(tasks_list_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建任务表格
        columns = ("id", "name", "created_at", "status", "processing_time")
        self.tasks_treeview = ttk.Treeview(tasks_list_frame, columns=columns, show="headings",
                                          xscrollcommand=scrollbar_x.set,
                                          yscrollcommand=scrollbar_y.set)
        
        # 设置列标题
        self.tasks_treeview.heading("id", text="ID")
        self.tasks_treeview.heading("name", text="名称")
        self.tasks_treeview.heading("created_at", text="创建时间")
        self.tasks_treeview.heading("status", text="状态")
        self.tasks_treeview.heading("processing_time", text="处理时间")
        
        # 设置列宽
        self.tasks_treeview.column("id", width=50)
        self.tasks_treeview.column("name", width=200)
        self.tasks_treeview.column("created_at", width=150)
        self.tasks_treeview.column("status", width=100)
        self.tasks_treeview.column("processing_time", width=100)
        
        self.tasks_treeview.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_x.config(command=self.tasks_treeview.xview)
        scrollbar_y.config(command=self.tasks_treeview.yview)
        
        # 绑定双击事件
        self.tasks_treeview.bind("<Double-1>", self.on_task_double_click)
        
        # 任务数据
        self.tasks_data = []
        self.current_project_id = None
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def show_server_settings(self):
        """显示服务器设置对话框"""
        server_url = simpledialog.askstring("服务器设置", "请输入WebODM服务器地址:",
                                         initialvalue=self.server_url_var.get())
        if server_url:
            self.server_url_var.set(server_url)
            self.config['server_url'] = server_url
            self.save_config()
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", f"WebODM 客户端{VERSION}\n\n一个基于Python和Tkinter的 WebODM(https://github.com/OpenDroneMap/WebODM) 客户端，用于批量管理WebODM中的项目和图片拼接任务")
    
    def login(self):
        """登录WebODM服务器"""
        server_url = self.server_url_var.set(self.server_url_var.get().rstrip('/'))
        self.api.server_url = self.server_url_var.get()
        
        # 创建登录对话框
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title("登录")
        login_dialog.geometry("300x150")
        login_dialog.resizable(False, False)
        login_dialog.transient(self.root)
        login_dialog.grab_set()
        
        ttk.Label(login_dialog, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        username_var = tk.StringVar()
        ttk.Entry(login_dialog, textvariable=username_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(login_dialog, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(login_dialog, textvariable=password_var, width=20, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        def do_login():
            username = username_var.get()
            password = password_var.get()
            
            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空")
                return
            
            self.status_var.set("正在登录...")
            login_dialog.config(cursor="wait")
            self.root.config(cursor="wait")
            
            def login_thread():
                success = self.api.authenticate(username, password)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.after_login(success, login_dialog))
            
            threading.Thread(target=login_thread).start()
        
        ttk.Button(login_dialog, text="登录", command=do_login).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 设置回车键登录
        login_dialog.bind("<Return>", lambda event: do_login())
        
        # 聚焦用户名输入框
        login_dialog.after(100, lambda: username_var.get() or username_var.set(self.config.get('username', '')))
        login_dialog.after(100, lambda: password_entry.focus())
    
    def after_login(self, success: bool, login_dialog: tk.Toplevel):
        """登录后的处理
        
        Args:
            success: 登录是否成功
            login_dialog: 登录对话框
        """
        self.root.config(cursor="")
        login_dialog.config(cursor="")
        
        if success:
            self.status_var.set("登录成功")
            login_dialog.destroy()
            
            # 保存配置
            self.config['server_url'] = self.api.server_url
            self.config['token'] = self.api.token
            self.save_config()
            
            # 更新登录状态
            self.update_login_status(True)
            
            # 加载项目列表
            self.load_projects()
        else:
            self.status_var.set("登录失败")
            messagebox.showerror("登录失败", "用户名或密码错误，或服务器无法连接")
    
    def logout(self):
        """注销登录"""
        self.api.token = None
        self.api.headers = {}
        
        # 更新配置
        if 'token' in self.config:
            del self.config['token']
        self.save_config()
        
        # 更新登录状态
        self.update_login_status(False)
        
        # 清空项目和任务列表
        self.projects_listbox.delete(0, tk.END)
        self.projects_data = []
        
        self.tasks_treeview.delete(*self.tasks_treeview.get_children())
        self.tasks_data = []
        self.current_project_id = None
        
        self.status_var.set("已注销")
    
    def update_login_status(self, logged_in: bool):
        """更新登录状态
        
        Args:
            logged_in: 是否已登录
        """
        if logged_in:
            self.login_status_var.set("已连接")
            self.login_button.config(state=tk.DISABLED)
            self.logout_button.config(state=tk.NORMAL)
        else:
            self.login_status_var.set("未连接")
            self.login_button.config(state=tk.NORMAL)
            self.logout_button.config(state=tk.DISABLED)
    
    def load_projects(self):
        """加载项目列表"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        self.status_var.set("正在加载项目列表...")
        self.root.config(cursor="wait")
        
        def load_thread():
            projects = self.api.get_projects()
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.update_projects_list(projects))
        
        threading.Thread(target=load_thread).start()
    
    def update_projects_list(self, projects: List[Dict[str, Any]]):
        """更新项目列表
        
        Args:
            projects: 项目列表
        """
        self.root.config(cursor="")
        
        # 清空列表
        self.projects_listbox.delete(0, tk.END)
        self.projects_data = projects
        
        # 添加项目
        for project in projects:
            self.projects_listbox.insert(tk.END, f"{project['name']}")
        
        self.status_var.set(f"已加载 {len(projects)} 个项目")
    
    def on_project_selected(self, event):
        """项目选择事件处理
        
        Args:
            event: 事件对象
        """
        selection = self.projects_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.projects_data):
            project = self.projects_data[index]
            self.current_project_id = project['id']
            
            # 加载任务列表
            self.load_tasks()
    
    def create_new_project(self):
        """创建新项目"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        # 创建项目对话框
        project_dialog = tk.Toplevel(self.root)
        project_dialog.title("新建项目")
        project_dialog.geometry("400x200")
        project_dialog.resizable(False, False)
        project_dialog.transient(self.root)
        project_dialog.grab_set()
        
        ttk.Label(project_dialog, text="项目名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(project_dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(project_dialog, text="项目描述:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        description_var = tk.StringVar()
        ttk.Entry(project_dialog, textvariable=description_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        def do_create():
            name = name_var.get()
            description = description_var.get()
            
            if not name:
                messagebox.showerror("错误", "项目名称不能为空")
                return
            
            self.status_var.set("正在创建项目...")
            project_dialog.config(cursor="wait")
            self.root.config(cursor="wait")
            
            def create_thread():
                project = self.api.create_project(name, description)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.after_create_project(project, project_dialog))
            
            threading.Thread(target=create_thread).start()
        
        ttk.Button(project_dialog, text="创建", command=do_create).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 设置回车键创建
        project_dialog.bind("<Return>", lambda event: do_create())
    
    def after_create_project(self, project: Optional[Dict[str, Any]], project_dialog: tk.Toplevel):
        """创建项目后的处理
        
        Args:
            project: 创建的项目信息
            project_dialog: 项目对话框
        """
        self.root.config(cursor="")
        project_dialog.config(cursor="")
        
        if project:
            self.status_var.set("项目创建成功")
            project_dialog.destroy()
            
            # 重新加载项目列表
            self.load_projects()
        else:
            self.status_var.set("项目创建失败")
            messagebox.showerror("创建失败", "无法创建项目，请检查网络连接或服务器状态")
    
    def view_project_details(self):
        """查看项目详细信息"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        # 获取选中的项目
        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        index = selection[0]
        if index < len(self.projects_data):
            project_id = self.projects_data[index]['id']
            
            # 显示加载状态
            self.status_var.set("正在获取项目详情...")
            self.root.config(cursor="wait")
            
            def load_thread():
                # 获取详细的项目信息
                project = self.api.get_project(project_id)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.show_project_details(project))
            
            threading.Thread(target=load_thread).start()
    
    def show_project_details(self, project: Optional[Dict[str, Any]]):
        """显示项目详细信息
        
        Args:
            project: 项目详细信息
        """
        self.root.config(cursor="")
        self.status_var.set("就绪")
        
        if not project:
            messagebox.showerror("错误", "获取项目详情失败")
            return
        
        # 创建项目详情对话框
        details_dialog = tk.Toplevel(self.root)
        details_dialog.title(f"项目详情: {project['name']}")
        details_dialog.geometry("600x300")
        details_dialog.transient(self.root)
        details_dialog.grab_set()
            
        # 创建滚动区域
        main_frame = ttk.Frame(details_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel_restart_single(event):
            try:
                canvas.yview_scroll(-int(event.delta/120), "units")
            except Exception:
                pass
        canvas.bind("<MouseWheel>", _on_mousewheel_restart_single)
        
        def _on_mousewheel_restart_batch(event):
            try:
                canvas.yview_scroll(-int(event.delta/120), "units")
            except Exception:
                pass
        canvas.bind("<MouseWheel>", _on_mousewheel_restart_batch)
        
        def _on_mousewheel_project(event):
            try:
                canvas.yview_scroll(-int(event.delta/120), "units")
            except Exception:
                pass
        canvas.bind("<MouseWheel>", _on_mousewheel_project)
        
        # 显示项目详情
        row = 0
        
        # 项目ID
        ttk.Label(scrollable_frame, text="项目ID:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=str(project['id'])).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 项目名称
        ttk.Label(scrollable_frame, text="项目名称:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=project['name']).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 项目描述
        ttk.Label(scrollable_frame, text="项目描述:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        description = project.get('description', '无')
        ttk.Label(scrollable_frame, text=description, wraplength=400).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 创建时间
        ttk.Label(scrollable_frame, text="创建时间:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        # 获取创建时间并转换为本地时间
        created_at = project.get('created_at', '未知')
        if created_at != '未知':
            try:
                # 将UTC时间字符串转换为datetime对象
                utc_time = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
                # 转换为本地时间
                local_time = utc_time.astimezone()
                created_at = local_time.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
        ttk.Label(scrollable_frame, text=created_at).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 权限
        ttk.Label(scrollable_frame, text="权限:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        permissions = project.get('permissions', [])
        if permissions:
            permissions_text = ", ".join(permissions)
        else:
            permissions_text = "无权限信息"
        ttk.Label(scrollable_frame, text=permissions_text, wraplength=400).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 关闭按钮
        ttk.Button(details_dialog, text="关闭", command=details_dialog.destroy).pack(pady=10)
    
    def load_tasks(self):
        """加载任务列表"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        self.status_var.set("正在加载任务列表...")
        self.root.config(cursor="wait")
        
        def load_thread():
            tasks = self.api.get_tasks(self.current_project_id)
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.update_tasks_list(tasks))
        
        threading.Thread(target=load_thread).start()
    
    def update_tasks_list(self, tasks: List[Dict[str, Any]]):
        """更新任务列表
        
        Args:
            tasks: 任务列表
        """
        self.root.config(cursor="")
        
        # 清空表格
        self.tasks_treeview.delete(*self.tasks_treeview.get_children())
        self.tasks_data = tasks
        
        # 添加任务
        for task in tasks:
            status = status_map.get(task.get('status', 0), "未知")
            processing_time = "-"
            if task.get('processing_time'):
                total_seconds = int(task.get('processing_time') / 1000)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                processing_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            self.tasks_treeview.insert("", tk.END, values=(
                task.get('id', ""),
                task.get('name', "未命名"),
                task.get('created_at', ""),
                status,
                processing_time
            ))
        
        self.status_var.set(f"已加载 {len(tasks)} 个任务")
    
    def on_task_double_click(self, *args):
        """任务双击事件处理
        
        Args:
            event: 事件对象
        """
        item = self.tasks_treeview.selection()
        if not item:
            return
        
        item = item[0]
        task_id = self.tasks_treeview.item(item, "values")[0]
        
        # 查找任务数据
        task = None
        for t in self.tasks_data:
            if str(t.get('id', "")) == task_id:
                task = t
                break
        
        if task:
            self.show_task_details(task)
    
    def show_task_details(self, task: Dict[str, Any]):
        """显示任务详情
        
        Args:
            task: 任务信息
        """
        # 创建任务详情对话框
        details_dialog = tk.Toplevel(self.root)
        details_dialog.title(f"任务详情 - {task.get('name', '未命名')}")
        details_dialog.geometry("600x400")
        details_dialog.transient(self.root)
        
        # 创建选项卡
        notebook = ttk.Notebook(details_dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 基本信息选项卡
        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="基本信息")
        
        # 显示基本信息
        row = 0
        for label, value in [
            ("ID", task.get('id', "")),
            ("名称", task.get('name', "未命名")),
            ("创建时间", task.get('created_at', "")),
            ("状态", status_map.get(task.get('status', 0), "未知")),
            ("处理时间", f"{int(task.get('processing_time', 0)/1000//3600):02d}:{int((task.get('processing_time', 0)/1000%3600)//60):02d}:{int((task.get('processing_time', 0)/1000)%60):02d}" if task.get('processing_time') else "-"),
            ("可用资源", "\n".join(task.get('available_assets', [])))
        ]:
            ttk.Label(info_frame, text=f"{label}:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            row += 1
        
        # 选项选项卡
        if 'options' in task and task['options']:
            options_frame = ttk.Frame(notebook, padding=10)
            notebook.add(options_frame, text="处理选项")
            
            # 显示选项
            row = 0
            for option in task['options']:
                name = option.get('name', "")
                value = option.get('value', "")
                ttk.Label(options_frame, text=f"{name}:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(options_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                row += 1
        
        # 按钮框架
        button_frame = ttk.Frame(details_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=details_dialog.destroy).pack(side=tk.RIGHT)
        
        # 如果任务已完成，添加下载按钮
        if task.get('status') == 40 and task.get('available_assets'):
            ttk.Button(
                button_frame,
                text="下载资源",
                command=lambda: self.download_assets(task['id'])
            ).pack(side=tk.RIGHT, padx=5)
    
    def create_new_task(self):
        """创建新任务
        
        Args:
            无
        
        Returns:
            无
        """
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 创建任务对话框
        task_dialog = tk.Toplevel(self.root)
        task_dialog.title("新建任务")
        task_dialog.geometry("600x700")
        task_dialog.transient(self.root)
        task_dialog.grab_set()
        
        # 创建框架
        main_frame = ttk.Frame(task_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        try:
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(5, weight=1)
        except Exception:
            pass
        
        # 任务名称
        ttk.Label(main_frame, text="任务名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.task_name_var = tk.StringVar(value="")
        ttk.Entry(main_frame, textvariable=self.task_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 图片选择
        ttk.Label(main_frame, text="选择图片:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        images_frame = ttk.Frame(main_frame)
        images_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(images_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建图片列表
        self.images_listbox = tk.Listbox(images_frame, yscrollcommand=scrollbar.set, height=10)
        self.images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.images_listbox.yview)
        
        # 图片路径列表
        self.image_paths = []
        
        # 按钮框架
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="添加图片", command=self.add_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="移除选中", command=self.remove_selected_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="清空列表", command=self.clear_images).pack(side=tk.LEFT, padx=2)
        
        # 处理选项
        ttk.Label(main_frame, text="处理选项:", font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=10)
        
        options_container = ttk.Frame(main_frame)
        options_container.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        canvas = tk.Canvas(options_container)
        scrollbar = ttk.Scrollbar(options_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel_options(event):
            try:
                canvas.yview_scroll(-int(event.delta/120), "units")
            except Exception:
                pass
        canvas.bind("<MouseWheel>", _on_mousewheel_options)
        
        self.status_var.set("正在获取处理选项...")
        processing_node_options = self.api.get_processing_node_options()
        processing_options = {}
        if processing_node_options:
            for option in processing_node_options:
                option_name = option.get('name')
                if not option_name:
                    continue
                option_type = option.get('type')
                option_value = option.get('value')
                option_domain = option.get('domain')
                option_help = option.get('help', '')
                widget_type = "string"
                default_value = option_value
                options_list = []
                if option_type == "bool":
                    widget_type = "bool"
                    default_value = option_value.lower() == "true" if isinstance(option_value, str) else bool(option_value)
                elif option_type == "int":
                    widget_type = "int"
                    try:
                        default_value = int(option_value) if option_value else 0
                    except (ValueError, TypeError):
                        default_value = 0
                elif option_type == "float" or option_type == "percent":
                    widget_type = "float"
                    try:
                        default_value = float(option_value) if option_value else 0.0
                    except (ValueError, TypeError):
                        default_value = 0.0
                elif option_type == "enum" and isinstance(option_domain, list):
                    widget_type = "select"
                    options_list = option_domain
                    default_value = option_value if option_value in option_domain else (option_domain[0] if option_domain else "")
                processing_options[option_name] = {
                    "label": option_name,
                    "type": widget_type,
                    "default": default_value,
                    "options": options_list,
                    "help": option_help
                }
        else:
            processing_options = {
                "mesh-octree-depth": {"label": "网格八叉树深度", "type": "int", "default": 11},
                "mesh-size": {"label": "网格大小", "type": "int", "default": 200000},
                "min-num-features": {"label": "最小特征数", "type": "int", "default": 8000},
                "orthophoto-resolution": {"label": "正射影像分辨率", "type": "float", "default": 2},
                "pc-quality": {"label": "点云质量", "type": "select", "default": "medium", "options": ["ultra", "high", "medium", "low", "lowest"]},
                "pc-filter": {"label": "点云过滤", "type": "int", "default": 2},
                "dsm": {"label": "生成DSM", "type": "bool", "default": True},
                "dtm": {"label": "生成DTM", "type": "bool", "default": False},
                "cog": {"label": "生成COG格式", "type": "bool", "default": False},
                "dem-resolution": {"label": "DEM分辨率", "type": "float", "default": 2},
                "feature-quality": {"label": "特征质量", "type": "select", "default": "medium", "options": ["ultra", "high", "medium", "low", "lowest"]},
                "use-3dmesh": {"label": "使用3D网格", "type": "bool", "default": False},
            }
        self.status_var.set("就绪")
        
        categories = {
            "基本设置": ["end-with", "rerun-from", "min-num-features", "feature-type", "feature-quality", "matcher-type"],
            "点云设置": ["pc-quality", "pc-filter", "pc-classify", "pc-rectify", "pc-geometric"],
            "网格设置": ["mesh-size", "mesh-octree-depth", "mesh-samples", "mesh-point-weight", "use-3dmesh"],
            "正射影像设置": ["orthophoto-resolution", "orthophoto-no-tiled", "orthophoto-png", "orthophoto-compression", "cog"],
            "DEM设置": ["dem-resolution", "dem-gapfill-steps", "dsm", "dtm", "dem-euclidean-map"],
            "相机设置": ["use-fixed-camera-params", "cameras", "camera-lens", "radiometric-calibration"],
            "其他设置": []
        }
        
        tab_control = ttk.Notebook(scrollable_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, pady=10)
        
        all_options = {}
        for key, option in processing_options.items():
            all_options[key] = option
        
        tabs = {}
        for category, option_keys in categories.items():
            tab = ttk.Frame(tab_control)
            tabs[category] = tab
            tab_control.add(tab, text=category)
        
        for key in all_options.keys():
            found = False
            for category, option_keys in categories.items():
                if key in option_keys:
                    found = True
                    break
            if not found:
                categories["其他设置"].append(key)
        
        option_vars = {}
        for category, option_keys in categories.items():
            tab = tabs[category]
            if not option_keys:
                ttk.Label(tab, text="没有可用的选项").pack(pady=20)
                continue
            for key in option_keys:
                if key not in all_options:
                    continue
                option = all_options[key]
                option_frame = ttk.Frame(tab)
                option_frame.pack(fill=tk.X, pady=5, padx=10)
                label_frame = ttk.Frame(option_frame)
                label_frame.pack(fill=tk.X, side=tk.TOP)
                option_label = option.get("label", key)
                ttk.Label(label_frame, text=f"{option_label}").pack(side=tk.LEFT, anchor="w")
                control_frame = ttk.Frame(option_frame)
                control_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 0))
                if option["type"] == "bool":
                    var = tk.BooleanVar(value=option["default"])
                    ttk.Checkbutton(control_frame, variable=var).pack(side=tk.LEFT)
                elif option["type"] == "select":
                    var = tk.StringVar(value=option["default"])
                    ttk.Combobox(control_frame, textvariable=var, values=option["options"], state="readonly", width=30).pack(side=tk.LEFT)
                else:
                    var = tk.StringVar(value=str(option["default"]))
                    ttk.Entry(control_frame, textvariable=var, width=30).pack(side=tk.LEFT)
                if "help" in option and option["help"]:
                    help_frame = ttk.Frame(option_frame)
                    help_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 5))
                    help_text = option["help"].replace("%(default)s", str(option["default"]))
                    if "options" in option and option["options"]:
                        help_text = help_text.replace("%(choices)s", ", ".join(option["options"]))
                    ttk.Label(help_frame, text=help_text, wraplength=500, foreground="gray").pack(side=tk.LEFT, anchor="w")
                ttk.Separator(option_frame, orient="horizontal").pack(fill=tk.X, pady=(5, 0))
                option_vars[key] = var
        
        # 创建任务按钮
        button_frame = ttk.Frame(task_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def do_create():
            if not self.image_paths:
                messagebox.showerror("错误", "请至少添加一张图片")
                return
            
            options = {}
            for key, var in option_vars.items():
                option_info = processing_options.get(key, {})
                opt_type = option_info.get("type", "string")
                raw_value = var.get()
                try:
                    if opt_type == "bool":
                        options[key] = self._parse_bool_value(raw_value)
                    elif opt_type == "int":
                        value_str = str(raw_value).strip()
                        options[key] = int(value_str)
                    elif opt_type == "float":
                        value_str = str(raw_value).strip()
                        options[key] = float(value_str)
                    else:
                        options[key] = str(raw_value).strip()
                except ValueError:
                    label = option_info.get("label", key)
                    if opt_type == "bool":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的布尔值")
                    else:
                        error_type = "整数" if opt_type == "int" else "浮点数"
                        messagebox.showerror("错误", f"选项 {label} 需要有效的{error_type}")
                    return
            
            options = self._clean_option_values(options)
            
            self.status_var.set("正在创建任务...")
            task_dialog.config(cursor="wait")
            self.root.config(cursor="wait")

            upload_dialog = tk.Toplevel(task_dialog)
            upload_dialog.title("上传进度")
            upload_dialog.geometry("400x200")
            upload_dialog.transient(task_dialog)
            upload_dialog.grab_set()
            upload_dialog.resizable(False, False)
            upload_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
            
            upload_status_var = tk.StringVar(value="正在准备上传...")
            ttk.Label(upload_dialog, textvariable=upload_status_var).pack(pady=(20, 10))
            
            total_images = max(len(self.image_paths), 1)
            upload_progress_var = tk.DoubleVar(value=0)
            upload_progress = ttk.Progressbar(
                upload_dialog,
                orient="horizontal",
                length=320,
                mode="determinate",
                maximum=total_images,
                variable=upload_progress_var
            )
            upload_progress.pack(pady=5, padx=20, fill=tk.X)
            
            upload_count_var = tk.StringVar(value=f"0/{len(self.image_paths)}")
            ttk.Label(upload_dialog, textvariable=upload_count_var).pack(pady=(0, 10))
            
            def update_upload_progress(completed: int, total: int, message: str):
                def _update():
                    if not upload_dialog.winfo_exists():
                        return
                    maximum = max(total, 1)
                    upload_progress.config(maximum=maximum)
                    upload_progress_var.set(min(completed, maximum))
                    if total > 0:
                        upload_count_var.set(f"{min(completed, total)}/{total}")
                    else:
                        upload_count_var.set("")
                    upload_status_var.set(message)
                self.root.after(0, _update)
            
            def create_thread():
                task_name = self.task_name_var.get().strip()
                task = None
                try:
                    task = self.api.create_task(
                        self.current_project_id,
                        self.image_paths,
                        options,
                        name=task_name if task_name else None,
                        progress_callback=update_upload_progress
                    )
                except Exception as exc:
                    print(f"创建任务过程中发生错误: {exc}")
                    task = None
                finally:
                    def finish():
                        if upload_dialog.winfo_exists():
                            try:
                                upload_dialog.grab_release()
                            except Exception:
                                pass
                            upload_dialog.destroy()
                        self.after_create_task(task, task_dialog)
                    self.root.after(0, finish)
            
            threading.Thread(target=create_thread).start()
        
        ttk.Button(button_frame, text="取消", command=task_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="创建任务", command=do_create).pack(side=tk.RIGHT)
    
    def add_images(self):
        """添加图片"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.tif *.tiff"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("TIFF文件", "*.tif *.tiff"),
            ("所有文件", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(title="选择图片", filetypes=filetypes)
        if not filenames:
            return
        
        for filename in filenames:
            if filename not in self.image_paths:
                self.image_paths.append(filename)
                self.images_listbox.insert(tk.END, os.path.basename(filename))
        
        try:
            if hasattr(self, 'task_name_var') and self.task_name_var.get().strip() == "":
                first_file = filenames[0]
                folder_name = os.path.basename(os.path.dirname(first_file))
                if folder_name:
                    self.task_name_var.set(folder_name)
        except Exception:
            pass
    
    def remove_selected_images(self):
        """移除选中的图片"""
        selection = self.images_listbox.curselection()
        if not selection:
            return
        
        # 从后往前删除，避免索引变化
        for index in sorted(selection, reverse=True):
            del self.image_paths[index]
            self.images_listbox.delete(index)
    
    def clear_images(self):
        """清空图片列表"""
        self.image_paths = []
        self.images_listbox.delete(0, tk.END)
    
    def after_create_task(self, task: Optional[Dict[str, Any]], task_dialog: tk.Toplevel):
        """创建任务后的处理
        
        Args:
            task: 创建的任务信息
            task_dialog: 任务对话框
        """
        self.root.config(cursor="")
        task_dialog.config(cursor="")
        
        if task:
            self.status_var.set("任务创建成功")
            task_dialog.destroy()
            
            # 重新加载任务列表
            self.load_tasks()
        else:
            self.status_var.set("任务创建失败")
            messagebox.showerror("创建失败", "无法创建任务，请检查图片文件和网络连接")
    
    def download_assets(self, task_ids: Optional[Union[int, str, List[Union[int, str]]]] = None):
        """下载任务资源，支持单个任务或批量任务"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 统一构建任务ID列表
        if task_ids is None:
            selection = self.tasks_treeview.selection()
            if not selection:
                messagebox.showerror("错误", "请先选择至少一个任务")
                return
            collected_ids = [str(self.tasks_treeview.item(item, "values")[0]) for item in selection]
        else:
            if isinstance(task_ids, (int, str)):
                collected_ids = [str(task_ids)]
            else:
                collected_ids = [str(tid) for tid in task_ids if tid is not None]
        
        # 去重并保持顺序
        normalized_ids: List[str] = []
        seen_ids = set()
        for task_id in collected_ids:
            if task_id not in seen_ids:
                normalized_ids.append(task_id)
                seen_ids.add(task_id)
        
        if not normalized_ids:
            messagebox.showerror("错误", "请先选择至少一个任务")
            return
        
        task_info_cache: Dict[str, Dict[str, Any]] = {}
        single_task_mode = len(normalized_ids) == 1
        
        # 构建资源列表
        if single_task_mode:
            single_task_id = normalized_ids[0]
            task_info = self.api.get_task(self.current_project_id, single_task_id)
            if not task_info:
                messagebox.showerror("错误", f"无法获取任务 {single_task_id} 的信息")
                return
            available_assets = task_info.get('available_assets', [])
            if not available_assets:
                messagebox.showerror("错误", f"任务 {task_info.get('name', f'任务_{single_task_id}')} 没有可用的资源")
                return
            asset_choices = available_assets
            default_selected = set(asset_choices)
            dialog_title = f"选择要下载的资源 - {task_info.get('name', '未命名')}"
            task_info_cache[single_task_id] = task_info
        else:
            asset_choices = [
                "all.zip",
                "orthophoto.tif",
                "dsm.tif",
                "dtm.tif",
                "georeferenced_model.laz",
                "cameras.json",
                "shots.geojson",
                "report.pdf"
            ]
            default_selected = {"orthophoto.tif", "dsm.tif"}
            dialog_title = "选择要下载的资源"
        
        # 选择下载目录
        download_dir = filedialog.askdirectory(title="选择下载目录")
        if not download_dir:
            return
        
        download_dir = download_dir.strip()
        if not download_dir:
            messagebox.showerror("错误", "请选择有效的下载目录")
            return
        base_download_dir = os.path.normpath(download_dir)
        
        # 创建资源选择对话框
        asset_dialog = tk.Toplevel(self.root)
        asset_dialog.title(dialog_title)
        asset_dialog.geometry("300x350")
        asset_dialog.transient(self.root)
        asset_dialog.grab_set()
        
        ttk.Label(asset_dialog, text="选择要下载的资源类型:").pack(pady=(10, 5))
        
        asset_vars: Dict[str, tk.BooleanVar] = {}
        for asset in asset_choices:
            var = tk.BooleanVar(value=asset in default_selected)
            asset_vars[asset] = var
            ttk.Checkbutton(asset_dialog, text=asset, variable=var).pack(anchor=tk.W, padx=20, pady=2)
        
        def do_download():
            selected_assets = [asset for asset, var in asset_vars.items() if var.get()]
            if not selected_assets:
                messagebox.showerror("错误", "请至少选择一种资源类型")
                return
            
            asset_dialog.destroy()
            
            self.status_var.set("正在准备下载...")
            self.root.config(cursor="wait")
            
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("下载进度")
            progress_dialog.geometry("400x300")
            progress_dialog.transient(self.root)
            
            progress_frame = ttk.Frame(progress_dialog, padding=10)
            progress_frame.pack(fill=tk.BOTH, expand=True)
            
            progress_text = tk.Text(progress_frame, height=15, width=50)
            progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(progress_frame, command=progress_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            progress_text.config(yscrollcommand=scrollbar.set)
            
            close_button = ttk.Button(progress_dialog, text="关闭", state=tk.DISABLED)
            close_button.pack(pady=10)
            
            def update_progress(text: str):
                self.root.after(0, lambda: progress_text.insert(tk.END, text))
                self.root.after(0, lambda: progress_text.see(tk.END))
            
            def update_progress_title(completed: int, total: int):
                self.root.after(0, lambda: progress_dialog.title(f"下载进度 ({completed}/{total})"))
            
            def download_thread():
                total_downloads = len(normalized_ids) * len(selected_assets)
                completed_downloads = 0
                failed_downloads = 0
                
                for task_id in normalized_ids:
                    # 复用已获取的任务信息
                    task_info = task_info_cache.get(task_id)
                    if not task_info:
                        task_info = self.api.get_task(self.current_project_id, task_id)
                        if task_info:
                            task_info_cache[task_id] = task_info
                    
                    if not task_info:
                        update_progress(f"无法获取任务 {task_id} 的信息\n")
                        continue
                    
                    task_name = task_info.get('name', f"任务_{task_id}")
                    available_assets = task_info.get('available_assets', [])
                    
                    safe_task_dir = os.path.join(
                        base_download_dir,
                        f"{self._sanitize_filename(task_name)}_{self._sanitize_filename(str(task_id))}"
                    )
                    
                    try:
                        os.makedirs(safe_task_dir, exist_ok=True)
                    except OSError as exc:
                        update_progress(f"无法创建目录 {safe_task_dir}: {exc}\n")
                        failed_downloads += len(selected_assets)
                        completed_downloads += len(selected_assets)
                        update_progress_title(completed_downloads, total_downloads)
                        continue
                    
                    for asset in selected_assets:
                        if asset not in available_assets:
                            update_progress(f"任务 {task_id} ({task_name}) 没有资源: {asset}\n")
                            failed_downloads += 1
                            completed_downloads += 1
                            update_progress_title(completed_downloads, total_downloads)
                            continue
                        
                        update_progress(f"正在下载任务 {task_id} ({task_name}) 的资源: {asset}\n")
                        
                        safe_asset_name = self._sanitize_filename(asset)
                        output_path = os.path.join(safe_task_dir, safe_asset_name)
                        success = self.api.download_asset(self.current_project_id, task_id, asset, output_path)
                        
                        if success:
                            update_progress(f"成功下载: {output_path}\n")
                        else:
                            update_progress(f"下载失败: {asset}\n")
                            failed_downloads += 1
                        
                        completed_downloads += 1
                        update_progress_title(completed_downloads, total_downloads)
                
                update_progress(f"\n下载完成! 总计: {total_downloads}, 成功: {total_downloads - failed_downloads}, 失败: {failed_downloads}\n")
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.status_var.set("下载完成"))
                self.root.after(0, lambda: close_button.config(state=tk.NORMAL, command=progress_dialog.destroy))
            
            threading.Thread(target=download_thread).start()
        
        ttk.Button(asset_dialog, text="下载", command=do_download).pack(pady=10)
    
    def _sanitize_filename(self, name: str) -> str:
        """清理Windows路径非法字符，保证生成的文件名安全"""
        safe = re.sub(r'[<>:"/\\|?*]', '_', str(name))
        safe = safe.strip().strip('.')
        if not safe:
            safe = "task"
        return safe[:150]

    def _parse_bool_value(self, value: Any) -> bool:
        """将多种布尔表示转换为bool类型"""
        if isinstance(value, bool):
            return value
        value_str = str(value).strip().lower()
        if value_str in {"1", "true", "yes", "on"}:
            return True
        if value_str in {"0", "false", "no", "off", ""}:
            return False
        raise ValueError("布尔值格式无效")

    def _clean_option_values(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """移除空字符串和None值，避免发送无效的处理选项"""
        cleaned: Dict[str, Any] = {}
        for key, value in options.items():
            if value is None:
                continue
            if isinstance(value, str):
                trimmed = value.strip()
                if not trimmed:
                    continue
                cleaned[key] = trimmed
            else:
                cleaned[key] = value
        return cleaned
    
    def restart_tasks(self):
        """重启选中的任务"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror("错误", "请先选择至少一个任务")
            return
        
        # 获取任务ID列表
        task_ids = []
        for item in selection:
            task_id = self.tasks_treeview.item(item, "values")[0]
            task_ids.append(task_id)
        
        # 如果只选择了一个任务，使用单个任务的重启方法
        if len(task_ids) == 1:
            self.restart_task(task_ids[0])
            return
        
        # 获取处理节点选项
        self.status_var.set("正在获取处理选项...")
        processing_node_options = self.api.get_processing_node_options()
        if not processing_node_options:
            messagebox.showerror("错误", "无法获取处理选项")
            self.status_var.set("就绪")
            return
            
        # 创建重启选项对话框
        restart_dialog = tk.Toplevel(self.root)
        restart_dialog.title("批量重启任务")
        restart_dialog.geometry("600x700")
        restart_dialog.transient(self.root)
        restart_dialog.grab_set()
        
        # 创建滚动区域
        main_frame = ttk.Frame(restart_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加标题
        ttk.Label(scrollable_frame, text=f"将重启 {len(task_ids)} 个任务，您可以修改以下处理选项:", 
                 font=("TkDefaultFont", 10, "bold")).pack(pady=10)
        
        # 将API返回的选项转换为易于处理的格式
        processing_options = {}
        for option in processing_node_options:
            option_name = option.get('name')
            if not option_name:
                continue
                
            option_type = option.get('type')
            option_value = option.get('value')
            option_domain = option.get('domain')
            option_help = option.get('help', '')
            
            # 确定选项类型和默认值
            widget_type = "string"
            default_value = option_value
            options_list = []
            
            if option_type == "bool":
                widget_type = "bool"
                default_value = option_value.lower() == "true" if isinstance(option_value, str) else bool(option_value)
            elif option_type == "int":
                widget_type = "int"
                try:
                    default_value = int(option_value) if option_value else 0
                except (ValueError, TypeError):
                    default_value = 0
            elif option_type == "float" or option_type == "percent":
                widget_type = "float"
                try:
                    default_value = float(option_value) if option_value else 0.0
                except (ValueError, TypeError):
                    default_value = 0.0
            elif option_type == "enum" and isinstance(option_domain, list):
                widget_type = "select"
                options_list = option_domain
                default_value = option_value if option_value in option_domain else (option_domain[0] if option_domain else "")
            
            # 创建选项字典
            processing_options[option_name] = {
                "label": option_name,
                "type": widget_type,
                "default": default_value,
                "current": None,
                "options": options_list,
                "help": option_help
            }
        
        # 如果API没有返回选项，使用默认选项
        if not processing_options:
            processing_options = {
                "mesh-octree-depth": {"label": "网格八叉树深度", "type": "int", "default": 11, "current": None},
                "mesh-size": {"label": "网格大小", "type": "int", "default": 200000, "current": None},
                "min-num-features": {"label": "最小特征数", "type": "int", "default": 8000, "current": None},
                "orthophoto-resolution": {"label": "正射影像分辨率", "type": "float", "default": 2, "current": None},
                "pc-quality": {"label": "点云质量", "type": "select", "default": "medium", "current": None, 
                              "options": ["ultra", "high", "medium", "low", "lowest"]},
                "pc-filter": {"label": "点云过滤", "type": "int", "default": 2, "current": None},
                "dsm": {"label": "生成DSM", "type": "bool", "default": True, "current": None},
                "dtm": {"label": "生成DTM", "type": "bool", "default": False, "current": None},
                "cog": {"label": "生成COG格式", "type": "bool", "default": False, "current": None},
                "dem-resolution": {"label": "DEM分辨率", "type": "float", "default": 2, "current": None},
                "feature-quality": {"label": "特征质量", "type": "select", "default": "medium", "current": None,
                                   "options": ["ultra", "high", "medium", "low", "lowest"]},
                "use-3dmesh": {"label": "使用3D网格", "type": "bool", "default": False, "current": None},
            }
        
        self.status_var.set("就绪")
        
        # 创建分类标签
        categories = {
            "基本设置": ["end-with", "rerun-from", "min-num-features", "feature-type", "feature-quality", "matcher-type"],
            "点云设置": ["pc-quality", "pc-filter", "pc-classify", "pc-rectify", "pc-geometric"],
            "网格设置": ["mesh-size", "mesh-octree-depth", "mesh-samples", "mesh-point-weight", "use-3dmesh"],
            "正射影像设置": ["orthophoto-resolution", "orthophoto-no-tiled", "orthophoto-png", "orthophoto-compression", "cog"],
            "DEM设置": ["dem-resolution", "dem-gapfill-steps", "dsm", "dtm", "dem-euclidean-map"],
            "相机设置": ["use-fixed-camera-params", "cameras", "camera-lens", "radiometric-calibration"],
            "其他设置": []
        }
        
        # 创建分类选项卡
        tab_control = ttk.Notebook(scrollable_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建所有选项的字典，用于分类
        all_options = {}
        for key, option in processing_options.items():
            all_options[key] = option
        
        # 创建分类选项卡
        tabs = {}
        for category, option_keys in categories.items():
            tab = ttk.Frame(tab_control)
            tabs[category] = tab
            tab_control.add(tab, text=category)
        
        # 添加未分类的选项到"其他设置"选项卡
        for key in all_options.keys():
            found = False
            for category, option_keys in categories.items():
                if key in option_keys:
                    found = True
                    break
            if not found:
                categories["其他设置"].append(key)
        
        # 创建选项控件
        option_vars = {}
        
        # 为每个分类创建选项控件
        for category, option_keys in categories.items():
            tab = tabs[category]
            
            # 如果该分类没有选项，添加提示信息
            if not option_keys:
                ttk.Label(tab, text="没有可用的选项").pack(pady=20)
                continue
            
            # 创建选项控件
            for key in option_keys:
                if key not in all_options:
                    continue
                    
                option = all_options[key]
                
                # 创建选项框架
                option_frame = ttk.Frame(tab)
                option_frame.pack(fill=tk.X, pady=5, padx=10)
                
                # 创建选项标签和控件
                label_frame = ttk.Frame(option_frame)
                label_frame.pack(fill=tk.X, side=tk.TOP)
                
                # 显示选项名称
                option_label = option.get("label", key)
                label_text = f"{option_label}"
                ttk.Label(label_frame, text=label_text).pack(side=tk.LEFT, anchor="w")
                
                # 创建控件框架
                control_frame = ttk.Frame(option_frame)
                control_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 0))
                
                # 根据选项类型创建不同的控件
                if option["type"] == "bool":
                    var = tk.BooleanVar(value=option["default"])
                    ttk.Checkbutton(control_frame, variable=var).pack(side=tk.LEFT)
                elif option["type"] == "select":
                    var = tk.StringVar(value=option["default"])
                    ttk.Combobox(control_frame, textvariable=var, values=option["options"], state="readonly", width=30).pack(side=tk.LEFT)
                else:  # int, float, string
                    var = tk.StringVar(value=str(option["default"]))
                    ttk.Entry(control_frame, textvariable=var, width=30).pack(side=tk.LEFT)
                
                # 添加帮助文本
                if "help" in option and option["help"]:
                    help_frame = ttk.Frame(option_frame)
                    help_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 5))
                    
                    help_text = option["help"]
                    # 替换帮助文本中的占位符
                    help_text = help_text.replace("%(default)s", str(option["default"]))
                    if "options" in option and option["options"]:
                        help_text = help_text.replace("%(choices)s", ", ".join(option["options"]))
                    
                    help_label = ttk.Label(help_frame, text=help_text, wraplength=500, foreground="gray")
                    help_label.pack(side=tk.LEFT, anchor="w")
                
                # 添加分隔线
                ttk.Separator(option_frame, orient="horizontal").pack(fill=tk.X, pady=(5, 0))
                
                option_vars[key] = var
        
        # 按钮区域
        button_frame = ttk.Frame(restart_dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def do_restart():
            # 收集选项
            options = {}
            for key, var in option_vars.items():
                option_info = processing_options.get(key, {})
                opt_type = option_info.get("type", "string")
                raw_value = var.get()
                try:
                    if opt_type == "bool":
                        options[key] = self._parse_bool_value(raw_value)
                    elif opt_type == "int":
                        options[key] = int(str(raw_value).strip())
                    elif opt_type == "float":
                        options[key] = float(str(raw_value).strip())
                    else:
                        options[key] = str(raw_value).strip()
                except ValueError:
                    label = option_info.get("label", key)
                    if opt_type == "bool":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的布尔值")
                    elif opt_type == "int":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的整数")
                    elif opt_type == "float":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的浮点数")
                    else:
                        messagebox.showerror("错误", f"选项 {label} 值无效")
                    return
            
            options = self._clean_option_values(options)
            
            restart_dialog.destroy()
            
            # 开始重启任务
            self.start_restart_tasks(task_ids, options)
        
        ttk.Button(button_frame, text="取消", command=restart_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="重启任务", command=do_restart).pack(side=tk.RIGHT)
    
    def start_restart_tasks(self, task_ids: List[Union[int, str]], options: Optional[Dict[str, Any]]):
        """开始重启任务
        
        Args:
            task_ids: 任务ID列表
            options: 处理选项字典
        """
        self.status_var.set("正在重启任务...")
        self.root.config(cursor="wait")
        
        # 创建进度对话框
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("重启进度")
        progress_dialog.geometry("400x300")
        progress_dialog.transient(self.root)
        
        # 创建进度文本框
        progress_frame = ttk.Frame(progress_dialog, padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        progress_text = tk.Text(progress_frame, height=15, width=50)
        progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(progress_frame, command=progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        progress_text.config(yscrollcommand=scrollbar.set)
        
        # 添加关闭按钮
        close_button = ttk.Button(progress_dialog, text="关闭", state=tk.DISABLED)
        close_button.pack(pady=10)
        
        # 重启线程
        def restart_thread():
            total_tasks = len(task_ids)
            completed_tasks = 0
            failed_tasks = 0
            
            for task_id in task_ids:
                # 获取任务信息
                task_info = self.api.get_task(self.current_project_id, task_id)
                if not task_info:
                    update_progress(f"无法获取任务 {task_id} 的信息\n")
                    failed_tasks += 1
                    completed_tasks += 1
                    update_progress_title(completed_tasks, total_tasks)
                    continue
                
                task_name = task_info.get('name', f"任务_{task_id}")
                
                update_progress(f"正在重启任务 {task_id} ({task_name})...\n")
                
                restart_options = options or {}
                success = self.api.restart_task(self.current_project_id, task_id, restart_options)
                
                if success:
                    update_progress(f"成功重启任务 {task_id} ({task_name})\n")
                else:
                    update_progress(f"重启任务 {task_id} ({task_name}) 失败\n")
                    failed_tasks += 1
                
                completed_tasks += 1
                update_progress_title(completed_tasks, total_tasks)
            
            # 完成重启
            update_progress(f"\n重启完成! 总计: {total_tasks}, 成功: {total_tasks - failed_tasks}, 失败: {failed_tasks}\n")
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set("重启完成"))
            self.root.after(0, lambda: close_button.config(state=tk.NORMAL, command=progress_dialog.destroy))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 更新进度文本
        def update_progress(text):
            self.root.after(0, lambda: progress_text.insert(tk.END, text))
            self.root.after(0, lambda: progress_text.see(tk.END))
        
        # 更新进度对话框标题
        def update_progress_title(completed, total):
            self.root.after(0, lambda: progress_dialog.title(f"重启进度 ({completed}/{total})"))
        
        # 启动重启线程
        threading.Thread(target=restart_thread).start()
    
    def cancel_tasks(self):
        """取消选中的任务"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror("错误", "请先选择至少一个任务")
            return
        
        # 获取任务ID列表和检查是否有已完成的任务
        task_ids = []
        completed_tasks = []
        
        for item in selection:
            values = self.tasks_treeview.item(item, "values")
            task_id = values[0]
            task_status = values[3]  # 状态在第4列
            
            if task_status == "已完成":  # 状态40对应"已完成"
                completed_tasks.append(task_id)
            else:
                task_ids.append(task_id)
        
        # 如果所有选中的任务都已完成，显示错误消息
        if not task_ids and completed_tasks:
            messagebox.showerror("错误", "已完成的任务不可取消")
            return
        
        # 如果有部分任务已完成，提示用户
        if completed_tasks:
            if not messagebox.askyesno("警告", f"选中的任务中有 {len(completed_tasks)} 个已完成的任务不可取消，是否继续取消其他 {len(task_ids)} 个任务?"):
                return
        
        # 如果没有可取消的任务，直接返回
        if not task_ids:
            return
        
        # 确认取消
        if not messagebox.askyesno("确认", f"确定要取消选中的 {len(task_ids)} 个任务吗?"):
            return
        
        self.status_var.set("正在取消任务...")
        self.root.config(cursor="wait")
        
        # 取消任务线程
        def cancel_thread():
            total_tasks = len(task_ids)
            completed_tasks = 0
            failed_tasks = 0
            
            for task_id in task_ids:
                # 获取任务信息
                task_info = self.api.get_task(self.current_project_id, task_id)
                if not task_info:
                    print(f"无法获取任务 {task_id} 的信息")
                    failed_tasks += 1
                    completed_tasks += 1
                    continue
                
                task_name = task_info.get('name', f"任务_{task_id}")
                
                print(f"正在取消任务 {task_id} ({task_name})...")
                
                success = self.api.cancel_task(self.current_project_id, task_id)
                
                if success:
                    print(f"成功取消任务 {task_id} ({task_name})")
                else:
                    print(f"取消任务 {task_id} ({task_name}) 失败")
                    failed_tasks += 1
                
                completed_tasks += 1
            
            # 完成取消
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set(f"取消完成! 总计: {total_tasks}, 成功: {total_tasks - failed_tasks}, 失败: {failed_tasks}"))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 启动取消线程
        threading.Thread(target=cancel_thread).start()
    
    def remove_tasks(self):
        """删除选中的任务"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror("错误", "请先选择至少一个任务")
            return
        
        # 获取任务ID列表
        task_ids = []
        for item in selection:
            task_id = self.tasks_treeview.item(item, "values")[0]
            task_ids.append(task_id)
        
        # 确认删除
        if not messagebox.askyesno("确认", f"确定要删除选中的 {len(task_ids)} 个任务吗? 此操作不可恢复!", icon=messagebox.WARNING):
            return
        
        self.status_var.set("正在删除任务...")
        self.root.config(cursor="wait")
        
        # 删除任务线程
        def remove_thread():
            total_tasks = len(task_ids)
            completed_tasks = 0
            failed_tasks = 0
            
            for task_id in task_ids:
                # 获取任务信息
                task_info = self.api.get_task(self.current_project_id, task_id)
                if not task_info:
                    print(f"无法获取任务 {task_id} 的信息")
                    failed_tasks += 1
                    completed_tasks += 1
                    continue
                
                task_name = task_info.get('name', f"任务_{task_id}")
                
                print(f"正在删除任务 {task_id} ({task_name})...")
                
                success = self.api.remove_task(self.current_project_id, task_id)
                
                if success:
                    print(f"成功删除任务 {task_id} ({task_name})")
                else:
                    print(f"删除任务 {task_id} ({task_name}) 失败")
                    failed_tasks += 1
                
                completed_tasks += 1
            
            # 完成删除
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set(f"删除完成! 总计: {total_tasks}, 成功: {total_tasks - failed_tasks}, 失败: {failed_tasks}"))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 启动删除线程
        threading.Thread(target=remove_thread).start()
    
            
    def restart_task(self, task_id):
        """重启任务并允许修改处理选项"""
        if not self.api.token:
            messagebox.showerror("错误", "请先登录")
            return
            
        if not self.current_project_id:
            messagebox.showerror("错误", "请先选择一个项目")
            return
        
        # 获取任务信息
        task_info = self.api.get_task(self.current_project_id, task_id)
        if not task_info:
            messagebox.showerror("错误", f"无法获取任务 {task_id} 的信息")
            return
        
        task_name = task_info.get('name', f"任务_{task_id}")
        current_options = task_info.get('options', [])
        
        # 获取处理节点选项
        self.status_var.set("正在获取处理选项...")
        processing_node_options = self.api.get_processing_node_options()
        if not processing_node_options:
            messagebox.showerror("错误", "无法获取处理选项")
            self.status_var.set("就绪")
            return
        
        # 创建重启任务对话框
        restart_dialog = tk.Toplevel(self.root)
        restart_dialog.title(f"重启任务 - {task_name} (ID: {task_id})")
        restart_dialog.geometry("600x700")
        restart_dialog.transient(self.root)
        restart_dialog.grab_set()
        
        # 创建滚动区域
        main_frame = ttk.Frame(restart_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加标题
        ttk.Label(scrollable_frame, text="修改处理选项", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # 将API返回的选项转换为易于处理的格式
        processing_options = {}
        for option in processing_node_options:
            option_name = option.get('name')
            if not option_name:
                continue
                
            option_type = option.get('type')
            option_value = option.get('value')
            option_domain = option.get('domain')
            option_help = option.get('help', '')
            
            # 确定选项类型和默认值
            widget_type = "string"
            default_value = option_value
            options_list = []
            
            if option_type == "bool":
                widget_type = "bool"
                default_value = option_value.lower() == "true" if isinstance(option_value, str) else bool(option_value)
            elif option_type == "int":
                widget_type = "int"
                try:
                    default_value = int(option_value) if option_value else 0
                except (ValueError, TypeError):
                    default_value = 0
            elif option_type == "float" or option_type == "percent":
                widget_type = "float"
                try:
                    default_value = float(option_value) if option_value else 0.0
                except (ValueError, TypeError):
                    default_value = 0.0
            elif option_type == "enum" and isinstance(option_domain, list):
                widget_type = "select"
                options_list = option_domain
                default_value = option_value if option_value in option_domain else (option_domain[0] if option_domain else "")
            
            # 创建选项字典
            processing_options[option_name] = {
                "label": option_name,
                "type": widget_type,
                "default": default_value,
                "current": None,
                "options": options_list,
                "help": option_help
            }
        
        # 如果API没有返回选项，使用默认选项
        if not processing_options:
            processing_options = {
                "mesh-octree-depth": {"label": "网格八叉树深度", "type": "int", "default": 11, "current": None},
                "mesh-size": {"label": "网格大小", "type": "int", "default": 200000, "current": None},
                "min-num-features": {"label": "最小特征数", "type": "int", "default": 8000, "current": None},
                "orthophoto-resolution": {"label": "正射影像分辨率", "type": "float", "default": 2, "current": None},
                "pc-quality": {"label": "点云质量", "type": "select", "default": "medium", "current": None, 
                              "options": ["ultra", "high", "medium", "low", "lowest"]},
                "pc-filter": {"label": "点云过滤", "type": "int", "default": 2, "current": None},
                "dsm": {"label": "生成DSM", "type": "bool", "default": True, "current": None},
                "dtm": {"label": "生成DTM", "type": "bool", "default": False, "current": None},
                "cog": {"label": "生成COG格式", "type": "bool", "default": False, "current": None},
                "dem-resolution": {"label": "DEM分辨率", "type": "float", "default": 2, "current": None},
                "feature-quality": {"label": "特征质量", "type": "select", "default": "medium", "current": None,
                                   "options": ["ultra", "high", "medium", "low", "lowest"]},
                "use-3dmesh": {"label": "使用3D网格", "type": "bool", "default": False, "current": None},
            }
        
        # 解析当前选项
        for opt in current_options:
            if isinstance(opt, str) and '=' in opt:
                key, value = opt.split('=', 1)
                if key in processing_options:
                    if processing_options[key]["type"] == "bool":
                        processing_options[key]["current"] = value.lower() == "true"
                    elif processing_options[key]["type"] == "int":
                        try:
                            processing_options[key]["current"] = int(value)
                        except ValueError:
                            pass
                    elif processing_options[key]["type"] == "float":
                        try:
                            processing_options[key]["current"] = float(value)
                        except ValueError:
                            pass
                    else:
                        processing_options[key]["current"] = value
        
        self.status_var.set("就绪")
        
        # 创建选项控件
        option_vars = {}
        
        # 创建分类标签
        categories = {
            "基本设置": ["end-with", "rerun-from", "min-num-features", "feature-type", "feature-quality", "matcher-type"],
            "点云设置": ["pc-quality", "pc-filter", "pc-classify", "pc-rectify", "pc-geometric"],
            "网格设置": ["mesh-size", "mesh-octree-depth", "mesh-samples", "mesh-point-weight", "use-3dmesh"],
            "正射影像设置": ["orthophoto-resolution", "orthophoto-no-tiled", "orthophoto-png", "orthophoto-compression", "cog"],
            "DEM设置": ["dem-resolution", "dem-gapfill-steps", "dsm", "dtm", "dem-euclidean-map"],
            "相机设置": ["use-fixed-camera-params", "cameras", "camera-lens", "radiometric-calibration"],
            "其他设置": []
        }
        
        # 创建分类选项卡
        tab_control = ttk.Notebook(scrollable_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建所有选项的字典，用于分类
        all_options = {}
        for key, option in processing_options.items():
            all_options[key] = option
        
        # 创建分类选项卡
        tabs = {}
        for category, option_keys in categories.items():
            tab = ttk.Frame(tab_control)
            tabs[category] = tab
            tab_control.add(tab, text=category)
        
        # 添加未分类的选项到"其他设置"选项卡
        for key in all_options.keys():
            found = False
            for category, option_keys in categories.items():
                if key in option_keys:
                    found = True
                    break
            if not found:
                categories["其他设置"].append(key)
        
        # 为每个分类创建选项控件
        for category, option_keys in categories.items():
            tab = tabs[category]
            
            # 如果该分类没有选项，添加提示信息
            if not option_keys:
                ttk.Label(tab, text="没有可用的选项").pack(pady=20)
                continue
            
            # 创建选项控件
            for key in option_keys:
                if key not in all_options:
                    continue
                    
                option = all_options[key]
                
                # 创建选项框架
                option_frame = ttk.Frame(tab)
                option_frame.pack(fill=tk.X, pady=5, padx=10)
                
                # 创建选项标签和控件
                label_frame = ttk.Frame(option_frame)
                label_frame.pack(fill=tk.X, side=tk.TOP)
                
                # 显示选项名称
                option_label = option.get("label", key)
                label_text = f"{option_label}"
                ttk.Label(label_frame, text=label_text).pack(side=tk.LEFT, anchor="w")
                
                # 创建控件框架
                control_frame = ttk.Frame(option_frame)
                control_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 0))
                
                # 根据选项类型创建不同的控件
                if option["type"] == "bool":
                    var = tk.BooleanVar(value=option["current"] if option["current"] is not None else option["default"])
                    ttk.Checkbutton(control_frame, variable=var).pack(side=tk.LEFT)
                elif option["type"] == "select":
                    var = tk.StringVar(value=option["current"] if option["current"] is not None else option["default"])
                    ttk.Combobox(control_frame, textvariable=var, values=option["options"], state="readonly", width=30).pack(side=tk.LEFT)
                else:  # int, float, string
                    var = tk.StringVar(value=str(option["current"] if option["current"] is not None else option["default"]))
                    ttk.Entry(control_frame, textvariable=var, width=30).pack(side=tk.LEFT)
                
                # 添加帮助文本
                if "help" in option and option["help"]:
                    help_frame = ttk.Frame(option_frame)
                    help_frame.pack(fill=tk.X, side=tk.TOP, pady=(2, 5))
                    
                    help_text = option["help"]
                    # 替换帮助文本中的占位符
                    help_text = help_text.replace("%(default)s", str(option["default"]))
                    if "options" in option and option["options"]:
                        help_text = help_text.replace("%(choices)s", ", ".join(option["options"]))
                    
                    help_label = ttk.Label(help_frame, text=help_text, wraplength=500, foreground="gray")
                    help_label.pack(side=tk.LEFT, anchor="w")
                
                # 添加分隔线
                ttk.Separator(option_frame, orient="horizontal").pack(fill=tk.X, pady=(5, 0))
                
                option_vars[key] = var
        
        # 按钮区域
        button_frame = ttk.Frame(restart_dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        def do_restart():
            # 收集选项
            options = {}
            for key, var in option_vars.items():
                option_info = processing_options.get(key, {})
                opt_type = option_info.get("type", "string")
                raw_value = var.get()
                try:
                    if opt_type == "bool":
                        options[key] = self._parse_bool_value(raw_value)
                    elif opt_type == "int":
                        options[key] = int(str(raw_value).strip())
                    elif opt_type == "float":
                        options[key] = float(str(raw_value).strip())
                    else:
                        options[key] = str(raw_value).strip()
                except ValueError:
                    label = option_info.get("label", key)
                    if opt_type == "bool":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的布尔值")
                    elif opt_type == "int":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的整数")
                    elif opt_type == "float":
                        messagebox.showerror("错误", f"选项 {label} 需要有效的浮点数")
                    else:
                        messagebox.showerror("错误", f"选项 {label} 值无效")
                    return
            
            options = self._clean_option_values(options)
            
            restart_dialog.destroy()
            
            # 开始重启任务
            self.status_var.set(f"正在重启任务 {task_id}...")
            self.root.config(cursor="wait")
            
            def restart_thread():
                success = self.api.restart_task(self.current_project_id, task_id, options)
                
                if success:
                    self.root.after(0, lambda: self.status_var.set(f"任务 {task_id} 重启成功"))
                    self.root.after(0, lambda: self.load_tasks())
                else:
                    self.root.after(0, lambda: self.status_var.set(f"任务 {task_id} 重启失败"))
                    self.root.after(0, lambda: messagebox.showerror("错误", f"重启任务 {task_id} 失败"))
                
                self.root.after(0, lambda: self.root.config(cursor=""))
            
            # 启动重启线程
            threading.Thread(target=restart_thread).start()
        
        ttk.Button(button_frame, text="重启", command=do_restart).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=restart_dialog.destroy).pack(side=tk.RIGHT, padx=5)
