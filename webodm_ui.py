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
from i18n import get_i18n, set_language, t, I18n


def get_status_map() -> Dict[int, str]:
    """Get status map with translated values."""
    return {
        10: t("status_queued"),
        20: t("status_running"),
        30: t("status_failed"),
        40: t("status_completed"),
        50: t("status_canceled")
    }

def _read_project_version() -> str:
    """读取项目版本号
    
    功能:
        从与本文件同目录的 `pyproject.toml` 中解析并返回 `project.version` 字段，
        如果解析失败则返回空字符串。
    传入参数:
        无
    返回值:
        str: 成功解析则返回版本号字符串（例如 "1.3.5"），否则返回空字符串
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        toml_path = os.path.join(base_dir, "pyproject.toml")
        if not os.path.exists(toml_path):
            return ""
        # Python 3.11+ 自带 tomllib，旧版用 tomli
        try:
            import tomllib
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
        except ImportError:
            import tomli
            with open(toml_path, "rb") as f:
                data = tomli.load(f)
        return str(data.get("project", {}).get("version", ""))
    except Exception:
        return ""

VERSION = _read_project_version() or "1.3.1"

class WebODMClientUI:
    """WebODM客户端UI类，使用Tkinter实现用户界面"""
    
    def __init__(self, root: tk.Tk):
        """初始化UI界面
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 创建API客户端
        self.api = WebODMAPI()
        
        # 创建配置文件夹
        self.config_dir = os.path.join(os.path.expanduser("~"), ".webodm_client")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
        
        # 设置语言
        self.i18n = get_i18n()
        if 'language' in self.config:
            set_language(self.config['language'])
        
        # 设置窗口标题
        self.root.title(f"{t('window_title')} {VERSION}")
        
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
        file_menu.add_command(label=t("menu_exit"), command=self.root.quit)
        self.menu_bar.add_cascade(label=t("menu_file"), menu=file_menu)
        
        # 设置菜单
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label=t("menu_server_settings"), command=self.show_server_settings)
        
        # 语言子菜单
        language_menu = tk.Menu(settings_menu, tearoff=0)
        language_menu.add_command(label=t("lang_zh_cn"), command=lambda: self.change_language("zh_CN"))
        language_menu.add_command(label=t("lang_en"), command=lambda: self.change_language("en"))
        settings_menu.add_cascade(label=t("menu_language"), menu=language_menu)
        
        self.menu_bar.add_cascade(label=t("menu_settings"), menu=settings_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label=t("menu_about"), command=self.show_about)
        self.menu_bar.add_cascade(label=t("menu_help"), menu=help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def change_language(self, language: str):
        """切换界面语言
        
        Args:
            language: 语言代码 (zh_CN 或 en)
        """
        set_language(language)
        self.config['language'] = language
        self.save_config()
        
        # 提示用户需要重启
        messagebox.showinfo(
            t("menu_language"),
            "Language changed. Please restart the application for changes to take effect.\n\n语言已更改，请重启应用程序以使更改生效。"
        )
    
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
        connection_frame = ttk.LabelFrame(self.main_frame, text=t("server_connection"), padding="10")
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 服务器地址
        server_frame = ttk.Frame(connection_frame)
        server_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(server_frame, text=t("server_address")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.server_url_var = tk.StringVar(value="http://localhost:8000")
        server_entry = ttk.Entry(server_frame, textvariable=self.server_url_var, width=40)
        server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 登录按钮
        self.login_button = ttk.Button(server_frame, text=t("login"), command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        self.logout_button = ttk.Button(server_frame, text=t("logout"), command=self.logout, state=tk.DISABLED)
        self.logout_button.pack(side=tk.LEFT)
        
        # 登录状态
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text=t("status")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.login_status_var = tk.StringVar(value=t("not_connected"))
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
        projects_frame = ttk.LabelFrame(self.paned_window, text=t("project_list"))
        self.paned_window.add(projects_frame, weight=1)
        
        # 项目工具栏
        projects_toolbar = ttk.Frame(projects_frame)
        projects_toolbar.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Button(projects_toolbar, text=t("refresh"), command=self.load_projects).pack(side=tk.LEFT, padx=2)
        ttk.Button(projects_toolbar, text=t("new_project"), command=self.create_new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(projects_toolbar, text=t("view_details"), command=self.view_project_details).pack(side=tk.LEFT, padx=2)
        
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
        tasks_frame = ttk.LabelFrame(self.paned_window, text=t("task_list"))
        self.paned_window.add(tasks_frame, weight=2)
        
        # 任务工具栏
        tasks_toolbar = ttk.Frame(tasks_frame)
        tasks_toolbar.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Button(tasks_toolbar, text=t("refresh"), command=self.load_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("new_task"), command=self.create_new_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("download_assets"), command=self.download_assets).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("restart_tasks"), command=self.restart_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("cancel_tasks"), command=self.cancel_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("delete_tasks"), command=self.remove_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(tasks_toolbar, text=t("view_details"), command=self.on_task_double_click).pack(side=tk.LEFT, padx=2)
        
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
        self.tasks_treeview.heading("id", text=t("col_id"), command=lambda: self.sort_tasks_by("id"))
        self.tasks_treeview.heading("name", text=t("col_name"), command=lambda: self.sort_tasks_by("name"))
        self.tasks_treeview.heading("created_at", text=t("col_created_at"), command=lambda: self.sort_tasks_by("created_at"))
        self.tasks_treeview.heading("status", text=t("col_status"), command=lambda: self.sort_tasks_by("status"))
        self.tasks_treeview.heading("processing_time", text=t("col_processing_time"), command=lambda: self.sort_tasks_by("processing_time"))
        
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
        self.tasks_sort_state = {"id": True, "name": True, "created_at": True, "status": True, "processing_time": True}
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set(t("ready"))
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def show_server_settings(self):
        """显示服务器设置对话框"""
        server_url = simpledialog.askstring(t("server_settings_title"), t("server_settings_prompt"),
                                         initialvalue=self.server_url_var.get())
        if server_url:
            self.server_url_var.set(server_url)
            self.config['server_url'] = server_url
            self.save_config()
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(t("about_title"), t("about_text", version=VERSION))
    
    def login(self):
        """登录WebODM服务器"""
        server_url = self.server_url_var.set(self.server_url_var.get().rstrip('/'))
        self.api.server_url = self.server_url_var.get()
        
        # 创建登录对话框
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title(t("login_title"))
        login_dialog.geometry("300x150")
        login_dialog.resizable(False, False)
        login_dialog.transient(self.root)
        login_dialog.grab_set()
        # 将对话框居中显示
        login_dialog.update_idletasks()
        x = (login_dialog.winfo_screenwidth() - login_dialog.winfo_width()) // 2
        y = (login_dialog.winfo_screenheight() - login_dialog.winfo_height()) // 2
        login_dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(login_dialog, text=t("username")).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        username_var = tk.StringVar()
        ttk.Entry(login_dialog, textvariable=username_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(login_dialog, text=t("password")).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(login_dialog, textvariable=password_var, width=20, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        def do_login():
            username = username_var.get()
            password = password_var.get()
            
            if not username or not password:
                messagebox.showerror(t("error"), t("error_empty_credentials"))
                return
            
            self.status_var.set(t("logging_in"))
            login_dialog.config(cursor="wait")
            self.root.config(cursor="wait")
            
            def login_thread():
                success = self.api.authenticate(username, password)
                if success:
                    try:
                        self.config['username'] = username
                        self.config['password'] = password
                        self.save_config()
                    except Exception:
                        pass
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.after_login(success, login_dialog))
            
            threading.Thread(target=login_thread).start()
        
        ttk.Button(login_dialog, text=t("login"), command=do_login).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 设置回车键登录
        login_dialog.bind("<Return>", lambda event: do_login())
        
        # 预填用户名和密码，并聚焦密码输入框
        login_dialog.after(100, lambda: username_var.set(self.config.get('username', '')))
        login_dialog.after(100, lambda: password_var.set(self.config.get('password', '')))
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
            self.status_var.set(t("login_success"))
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
            self.status_var.set(t("login_failed"))
            messagebox.showerror(t("login_failed"), t("login_failed_msg"))
    
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
        
        self.status_var.set(t("logged_out"))
    
    def update_login_status(self, logged_in: bool):
        """更新登录状态
        
        Args:
            logged_in: 是否已登录
        """
        if logged_in:
            self.login_status_var.set(t("connected"))
            self.login_button.config(state=tk.DISABLED)
            self.logout_button.config(state=tk.NORMAL)
        else:
            self.login_status_var.set(t("not_connected"))
            self.login_button.config(state=tk.NORMAL)
            self.logout_button.config(state=tk.DISABLED)
    
    def load_projects(self):
        """加载项目列表"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        self.status_var.set(t("loading_projects"))
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
        
        self.status_var.set(t("projects_loaded", count=len(projects)))
    
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
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        # 创建项目对话框
        project_dialog = tk.Toplevel(self.root)
        project_dialog.title(t("new_project_title"))
        project_dialog.geometry("400x200")
        project_dialog.resizable(False, False)
        project_dialog.transient(self.root)
        project_dialog.grab_set()
        
        ttk.Label(project_dialog, text=t("project_name")).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(project_dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(project_dialog, text=t("project_description")).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        description_var = tk.StringVar()
        ttk.Entry(project_dialog, textvariable=description_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        def do_create():
            name = name_var.get()
            description = description_var.get()
            
            if not name:
                messagebox.showerror(t("error"), t("error_empty_project_name"))
                return
            
            self.status_var.set(t("creating_project"))
            project_dialog.config(cursor="wait")
            self.root.config(cursor="wait")
            
            def create_thread():
                project = self.api.create_project(name, description)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.after_create_project(project, project_dialog))
            
            threading.Thread(target=create_thread).start()
        
        ttk.Button(project_dialog, text=t("create"), command=do_create).grid(row=2, column=0, columnspan=2, pady=10)
        
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
            self.status_var.set(t("project_created"))
            project_dialog.destroy()
            
            # 重新加载项目列表
            self.load_projects()
        else:
            self.status_var.set(t("project_create_failed"))
            messagebox.showerror(t("project_create_failed"), t("project_create_failed_msg"))
    
    def view_project_details(self):
        """查看项目详细信息"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        # 获取选中的项目
        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        index = selection[0]
        if index < len(self.projects_data):
            project_id = self.projects_data[index]['id']
            
            # 显示加载状态
            self.status_var.set(t("getting_project_details"))
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
        self.status_var.set(t("ready"))
        
        if not project:
            messagebox.showerror(t("error"), t("get_project_details_failed"))
            return
        
        # 创建项目详情对话框
        details_dialog = tk.Toplevel(self.root)
        details_dialog.title(f"{t('project_details')}: {project['name']}")
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
        ttk.Label(scrollable_frame, text=t("project_id"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=str(project['id'])).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 项目名称
        ttk.Label(scrollable_frame, text=t("project_name"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(scrollable_frame, text=project['name']).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 项目描述
        ttk.Label(scrollable_frame, text=t("project_description"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        description = project.get('description', t("none"))
        ttk.Label(scrollable_frame, text=description, wraplength=400).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 创建时间
        ttk.Label(scrollable_frame, text=t("created_at"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        # 获取创建时间并转换为本地时间
        created_at = project.get('created_at', t("unknown"))
        if created_at != t("unknown"):
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
        ttk.Label(scrollable_frame, text=t("permissions"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        permissions = project.get('permissions', [])
        if permissions:
            permissions_text = ", ".join(permissions)
        else:
            permissions_text = t("no_permissions")
        ttk.Label(scrollable_frame, text=permissions_text, wraplength=400).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # 关闭按钮
        ttk.Button(details_dialog, text=t("close"), command=details_dialog.destroy).pack(pady=10)
    
    def load_tasks(self):
        """加载任务列表"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        self.status_var.set(t("loading_tasks"))
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
        
        status_map = get_status_map()
        
        # 添加任务
        for task in tasks:
            status = status_map.get(task.get('status', 0), t("status_unknown"))
            processing_time = "-"
            if task.get('processing_time'):
                total_seconds = int(task.get('processing_time') / 1000)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                processing_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            created_local = self._format_to_local_time(task.get('created_at', ""))
            
            self.tasks_treeview.insert("", tk.END, values=(
                task.get('id', ""),
                task.get('name', t("unnamed")),
                created_local,
                status,
                processing_time
            ))
        
        self.status_var.set(t("tasks_loaded", count=len(tasks)))

    def sort_tasks_by(self, column: str):
        """按指定列排序任务列表，支持升/降序切换
        
        Args:
            column: 列名，可为 'id'、'name'、'created_at'、'status'、'processing_time'
        Returns:
            无
        """
        ascending = self.tasks_sort_state.get(column, True)
        status_map = get_status_map()
        def key_func(task: Dict[str, Any]):
            if column == "id":
                return str(task.get('id', 0))
            if column == "name":
                return str(task.get('name', "")).lower()
            if column == "created_at":
                dt = self._parse_utc_to_local_dt(task.get('created_at', ""))
                return dt.timestamp() if dt else 0.0
            if column == "status":
                return str(status_map.get(task.get('status', 0), "")).lower()
            if column == "processing_time":
                try:
                    return int(task.get('processing_time', 0))
                except Exception:
                    return 0
            return str(task.get(column, ""))
        sorted_tasks = sorted(self.tasks_data, key=key_func, reverse=not ascending)
        self.tasks_sort_state[column] = not ascending
        self.update_tasks_list(sorted_tasks)

    def _parse_utc_to_local_dt(self, utc_str: str) -> Optional[datetime]:
        """将UTC时间字符串解析并转换为本地时区的datetime
        
        Args:
            utc_str: UTC时间字符串，如 '2025-10-17T05:12:51.583409Z' 或 '2025-10-17T05:12:51Z'
        Returns:
            datetime: 本地时区的datetime；若解析失败返回None
        """
        if not utc_str:
            return None
        try:
            dt = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception:
            try:
                dt = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%SZ')
            except Exception:
                return None
        dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone()

    def _format_to_local_time(self, utc_str: str) -> str:
        """将UTC时间字符串格式化为本地时间字符串 'YYYY-MM-DD HH:MM:SS'
        
        Args:
            utc_str: UTC时间字符串
        Returns:
            str: 本地时间格式化字符串；解析失败返回原字符串或空串
        """
        dt = self._parse_utc_to_local_dt(utc_str)
        if not dt:
            return str(utc_str or "")
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
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
        status_map = get_status_map()
        
        # 创建任务详情对话框
        details_dialog = tk.Toplevel(self.root)
        details_dialog.title(f"{t('task_details')} - {task.get('name', t('unnamed'))}")
        details_dialog.geometry("600x400")
        details_dialog.transient(self.root)
        
        # 创建选项卡
        notebook = ttk.Notebook(details_dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 基本信息选项卡
        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text=t("basic_info"))
        
        # 显示基本信息
        row = 0
        for label, value in [
            (t("col_id"), task.get('id', "")),
            (t("col_name"), task.get('name', t("unnamed"))),
            (t("col_created_at"), self._format_to_local_time(task.get('created_at', ""))),
            (t("col_status"), status_map.get(task.get('status', 0), t("status_unknown"))),
            (t("col_processing_time"), f"{int(task.get('processing_time', 0)/1000//3600):02d}:{int((task.get('processing_time', 0)/1000%3600)//60):02d}:{int((task.get('processing_time', 0)/1000)%60):02d}" if task.get('processing_time') else "-"),
            (t("available_assets"), "\n".join(task.get('available_assets', [])))
        ]:
            ttk.Label(info_frame, text=f"{label}:", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            row += 1
        
        # 选项选项卡
        if 'options' in task and task['options']:
            options_frame = ttk.Frame(notebook, padding=10)
            notebook.add(options_frame, text=t("processing_options"))
            
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
        
        ttk.Button(button_frame, text=t("close"), command=details_dialog.destroy).pack(side=tk.RIGHT)
        
        # 如果任务已完成，添加下载按钮
        if task.get('status') == 40 and task.get('available_assets'):
            ttk.Button(
                button_frame,
                text=t("download_assets"),
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
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 创建任务对话框
        task_dialog = tk.Toplevel(self.root)
        task_dialog.title(t("new_task_title"))
        task_dialog.geometry("600x750")
        task_dialog.transient(self.root)
        
        
        # 创建框架
        main_frame = ttk.Frame(task_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        try:
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(5, weight=1)
        except Exception:
            pass
        
        ttk.Label(main_frame, text=t("task_name")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        task_name_var = tk.StringVar(value="")
        ttk.Entry(main_frame, textvariable=task_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 图片选择
        ttk.Label(main_frame, text=t("select_images")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        images_frame = ttk.Frame(main_frame)
        images_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(images_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建图片列表
        images_listbox = tk.Listbox(images_frame, yscrollcommand=scrollbar.set, height=10)
        images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=images_listbox.yview)
        
        image_paths: List[str] = []
        
        # 按钮框架
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        def add_images():
            filetypes = [
                (t("filetype_images"), "*.jpg *.jpeg *.png *.tif *.tiff"),
                (t("filetype_jpeg"), "*.jpg *.jpeg"),
                (t("filetype_png"), "*.png"),
                (t("filetype_tiff"), "*.tif *.tiff"),
                (t("filetype_all"), "*.*")
            ]
            filenames = filedialog.askopenfilenames(title=t("select_images_title"), filetypes=filetypes)
            if not filenames:
                return
            for filename in filenames:
                if filename not in image_paths:
                    image_paths.append(filename)
                    images_listbox.insert(tk.END, os.path.basename(filename))
            try:
                if task_name_var.get().strip() == "":
                    first_file = filenames[0]
                    folder_name = os.path.basename(os.path.dirname(first_file))
                    if folder_name:
                        task_name_var.set(folder_name)
            except Exception:
                pass
        def remove_selected_images():
            selection = images_listbox.curselection()
            if not selection:
                return
            for index in sorted(selection, reverse=True):
                del image_paths[index]
                images_listbox.delete(index)
        def clear_images():
            image_paths.clear()
            images_listbox.delete(0, tk.END)
        ttk.Button(buttons_frame, text=t("add_images"), command=add_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text=t("remove_selected"), command=remove_selected_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text=t("clear_list"), command=clear_images).pack(side=tk.LEFT, padx=2)
        
        # 预设选择
        ttk.Label(main_frame, text=t("select_preset"), font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=10)

        preset_frame = ttk.Frame(main_frame)
        preset_frame.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)

        presets = self.api.get_presets()
        preset_name_map = {p.get('name', f"preset_{p.get('id')}"): p for p in presets} if presets else {}
        preset_names = list(preset_name_map.keys())
        default_preset_name = next((name for name in preset_names if name.lower() == 'default'), preset_names[0] if preset_names else '')

        selected_preset_var = tk.StringVar(value=default_preset_name)
        ttk.Label(preset_frame, text=t("preset")).pack(side=tk.LEFT, padx=(0, 5))
        preset_select = ttk.Combobox(preset_frame, textvariable=selected_preset_var, values=preset_names, state="readonly", width=30)
        preset_select.pack(side=tk.LEFT)

        # 预设详情显示
        details_container = ttk.LabelFrame(main_frame, text=t("preset_options_readonly"))
        details_container.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        details_text = tk.Text(details_container, height=10, width=60)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def render_preset_details():
            details_text.config(state="normal")
            details_text.delete("1.0", tk.END)
            name = selected_preset_var.get()
            preset = preset_name_map.get(name)
            if preset and isinstance(preset.get('options'), list):
                for opt in preset['options']:
                    oname = str(opt.get('name'))
                    oval = opt.get('value')
                    details_text.insert(tk.END, f"{oname} = {oval}\n")
            details_text.config(state="disabled")

        preset_select.bind("<<ComboboxSelected>>", lambda e: render_preset_details())
        render_preset_details()
        
        progress_group = ttk.LabelFrame(main_frame, text=t("upload_progress"))
        progress_group.grid(row=7, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        upload_status_var = tk.StringVar(value=t("waiting_to_start"))
        ttk.Label(progress_group, textvariable=upload_status_var).pack(pady=(8, 6), padx=10, anchor=tk.W)
        upload_progress_var = tk.DoubleVar(value=0)
        upload_progress = ttk.Progressbar(progress_group, orient="horizontal", length=320, mode="determinate", maximum=1, variable=upload_progress_var)
        upload_progress.pack(pady=4, padx=10, fill=tk.X)
        upload_count_var = tk.StringVar(value="")
        ttk.Label(progress_group, textvariable=upload_count_var).pack(pady=(0, 8), padx=10, anchor=tk.W)

        button_frame = ttk.Frame(task_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def do_create():
            if not image_paths:
                messagebox.showerror(t("error"), t("error_no_images"))
                return
            
            selected_name = selected_preset_var.get()
            preset = preset_name_map.get(selected_name)
            if not preset:
                messagebox.showerror(t("error"), t("error_invalid_preset"))
                return
            options = {}
            for opt in preset.get('options', []):
                oname = opt.get('name')
                if not oname:
                    continue
                options[oname] = opt.get('value')
            
            self.status_var.set(t("creating_task"))
            total_images = max(len(image_paths), 1)
            upload_progress.config(maximum=total_images)
            upload_progress_var.set(0)
            upload_count_var.set(f"0/{len(image_paths)}")
            upload_status_var.set(t("preparing_upload"))
            
            def update_upload_progress(completed: int, total: int, message: str):
                def _update():
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
                task_name = task_name_var.get().strip()
                task = None
                try:
                    task = self.api.create_task(
                        self.current_project_id,
                        image_paths,
                        options,
                        name=task_name if task_name else None,
                        progress_callback=update_upload_progress
                    )
                except Exception as exc:
                    print(f"Error creating task: {exc}")
                    task = None
                finally:
                    def finish():
                        if task:
                            self.status_var.set(t("task_created"))
                            self.load_tasks()
                            upload_status_var.set(t("upload_complete_submitting"))
                        else:
                            self.status_var.set(t("task_create_failed"))
                            messagebox.showerror(t("task_create_failed"), t("task_create_failed_msg"))
                    self.root.after(0, finish)
            
            threading.Thread(target=create_thread).start()
        
        ttk.Button(button_frame, text=t("cancel"), command=task_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text=t("create_task"), command=do_create).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text=t("minimize"), command=task_dialog.iconify).pack(side=tk.LEFT)
    
    def add_images(self):
        """添加图片"""
        filetypes = [
            (t("filetype_images"), "*.jpg *.jpeg *.png *.tif *.tiff"),
            (t("filetype_jpeg"), "*.jpg *.jpeg"),
            (t("filetype_png"), "*.png"),
            (t("filetype_tiff"), "*.tif *.tiff"),
            (t("filetype_all"), "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(title=t("select_images_title"), filetypes=filetypes)
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
            self.status_var.set(t("task_created"))
            task_dialog.destroy()
            
            # 重新加载任务列表
            self.load_tasks()
        else:
            self.status_var.set(t("task_create_failed"))
            messagebox.showerror(t("task_create_failed"), t("task_create_failed_msg"))
    
    def download_assets(self, task_ids: Optional[Union[int, str, List[Union[int, str]]]] = None):
        """下载任务资源，支持单个任务或批量任务"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 统一构建任务ID列表
        if task_ids is None:
            selection = self.tasks_treeview.selection()
            if not selection:
                messagebox.showerror(t("error"), t("error_no_task_selected"))
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
            messagebox.showerror(t("error"), t("error_no_task_selected"))
            return
        
        task_info_cache: Dict[str, Dict[str, Any]] = {}
        single_task_mode = len(normalized_ids) == 1
        
        # 构建资源列表
        if single_task_mode:
            single_task_id = normalized_ids[0]
            task_info = self.api.get_task(self.current_project_id, single_task_id)
            if not task_info:
                messagebox.showerror(t("error"), t("error_no_task_info", task_id=single_task_id))
                return
            available_assets = task_info.get('available_assets', [])
            if not available_assets:
                task_name = task_info.get('name', f'task_{single_task_id}')
                messagebox.showerror(t("error"), t("error_no_assets", task_name=task_name))
                return
            asset_choices = available_assets
            default_selected = set(asset_choices)
            dialog_title = f"{t('select_assets_to_download')} - {task_info.get('name', t('unnamed'))}"
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
            dialog_title = t("select_assets_to_download")
        
        # 选择下载目录
        download_dir = filedialog.askdirectory(title=t("select_download_dir"))
        if not download_dir:
            return
        
        download_dir = download_dir.strip()
        if not download_dir:
            messagebox.showerror(t("error"), t("error_invalid_download_dir"))
            return
        base_download_dir = os.path.normpath(download_dir)
        
        # 创建资源选择对话框
        asset_dialog = tk.Toplevel(self.root)
        asset_dialog.title(dialog_title)
        asset_dialog.geometry("300x350")
        asset_dialog.transient(self.root)
        asset_dialog.grab_set()
        
        ttk.Label(asset_dialog, text=t("select_asset_types")).pack(pady=(10, 5))
        
        asset_vars: Dict[str, tk.BooleanVar] = {}
        for asset in asset_choices:
            var = tk.BooleanVar(value=asset in default_selected)
            asset_vars[asset] = var
            ttk.Checkbutton(asset_dialog, text=asset, variable=var).pack(anchor=tk.W, padx=20, pady=2)
        
        def do_download():
            selected_assets = [asset for asset, var in asset_vars.items() if var.get()]
            if not selected_assets:
                messagebox.showerror(t("error"), t("error_no_task_selected"))
                return
            
            asset_dialog.destroy()
            
            self.status_var.set(t("preparing_download"))
            self.root.config(cursor="wait")
            
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title(t("download_progress"))
            progress_dialog.geometry("400x300")
            progress_dialog.transient(self.root)
            
            progress_frame = ttk.Frame(progress_dialog, padding=10)
            progress_frame.pack(fill=tk.BOTH, expand=True)
            
            progress_text = tk.Text(progress_frame, height=15, width=50)
            progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(progress_frame, command=progress_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            progress_text.config(yscrollcommand=scrollbar.set)
            
            close_button = ttk.Button(progress_dialog, text=t("close"), state=tk.DISABLED)
            close_button.pack(pady=10)
            
            def update_progress(text: str):
                self.root.after(0, lambda: progress_text.insert(tk.END, text))
                self.root.after(0, lambda: progress_text.see(tk.END))
            
            def update_progress_title(completed: int, total: int):
                self.root.after(0, lambda: progress_dialog.title(f"{t('download_progress')} ({completed}/{total})"))
            
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
                        update_progress(f"{t('error_no_task_info', task_id=task_id)}\n")
                        continue
                    
                    task_name = task_info.get('name', f"task_{task_id}")
                    available_assets = task_info.get('available_assets', [])
                    
                    safe_task_dir = os.path.join(
                        base_download_dir,
                        f"{self._sanitize_filename(task_name)}_{self._sanitize_filename(str(task_id))}"
                    )
                    
                    try:
                        os.makedirs(safe_task_dir, exist_ok=True)
                    except OSError as exc:
                        update_progress(f"{t('error_create_dir', dir=safe_task_dir, error=str(exc))}\n")
                        failed_downloads += len(selected_assets)
                        completed_downloads += len(selected_assets)
                        update_progress_title(completed_downloads, total_downloads)
                        continue
                    
                    for asset in selected_assets:
                        if asset not in available_assets:
                            update_progress(f"{t('task_no_asset', task_id=task_id, task_name=task_name, asset=asset)}\n")
                            failed_downloads += 1
                            completed_downloads += 1
                            update_progress_title(completed_downloads, total_downloads)
                            continue
                        
                        update_progress(f"{t('downloading_asset', task_id=task_id, task_name=task_name, asset=asset)}\n")
                        
                        safe_asset_name = self._sanitize_filename(asset)
                        output_path = os.path.join(safe_task_dir, safe_asset_name)
                        success = self.api.download_asset(self.current_project_id, task_id, asset, output_path)
                        
                        if success:
                            update_progress(f"{t('download_success', path=output_path)}\n")
                        else:
                            update_progress(f"{t('download_failed', asset=asset)}\n")
                            failed_downloads += 1
                        
                        completed_downloads += 1
                        update_progress_title(completed_downloads, total_downloads)
                
                update_progress(f"\n{t('download_complete', total=total_downloads, success=total_downloads - failed_downloads, failed=failed_downloads)}\n")
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.status_var.set(t("download_complete_status")))
                self.root.after(0, lambda: close_button.config(state=tk.NORMAL, command=progress_dialog.destroy))
            
            threading.Thread(target=download_thread).start()
        
        ttk.Button(asset_dialog, text=t("download"), command=do_download).pack(pady=10)
    
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
        raise ValueError("Invalid boolean format")

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
                if trimmed.lower() in {"none", "null"}:
                    continue
                cleaned[key] = trimmed
            else:
                cleaned[key] = value
        return cleaned
    
    def restart_tasks(self):
        """重启选中的任务"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror(t("error"), t("error_no_task_selected"))
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
        
        # 获取预设
        self.status_var.set(t("getting_presets"))
        presets = self.api.get_presets()
        if not presets:
            messagebox.showerror(t("error"), t("get_presets_failed"))
            self.status_var.set(t("ready"))
            return

        # 创建重启选项对话框（预设选择）
        restart_dialog = tk.Toplevel(self.root)
        restart_dialog.title(t("batch_restart_title"))
        restart_dialog.geometry("500x400")
        restart_dialog.transient(self.root)
        restart_dialog.grab_set()

        main_frame = ttk.Frame(restart_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text=t("will_restart_tasks", count=len(task_ids)), font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 10), anchor=tk.W)

        preset_name_map = {p.get('name', f"preset_{p.get('id')}"): p for p in presets}
        preset_names = list(preset_name_map.keys())
        default_preset_name = next((name for name in preset_names if name.lower() == 'default'), preset_names[0])

        selected_preset_var = tk.StringVar(value=default_preset_name)
        selector_frame = ttk.Frame(main_frame)
        selector_frame.pack(fill=tk.X, pady=5)
        ttk.Label(selector_frame, text=t("preset")).pack(side=tk.LEFT, padx=(0, 5))
        preset_select = ttk.Combobox(selector_frame, textvariable=selected_preset_var, values=preset_names, state="readonly", width=30)
        preset_select.pack(side=tk.LEFT)

        details_group = ttk.LabelFrame(main_frame, text=t("preset_options_readonly"))
        details_group.pack(fill=tk.BOTH, expand=True, pady=10)
        details_text = tk.Text(details_group, height=10, width=60)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def render_details():
            details_text.config(state="normal")
            details_text.delete("1.0", tk.END)
            preset = preset_name_map.get(selected_preset_var.get())
            if preset and isinstance(preset.get('options'), list):
                for opt in preset['options']:
                    details_text.insert(tk.END, f"{opt.get('name')} = {opt.get('value')}\n")
            details_text.config(state="disabled")

        preset_select.bind("<<ComboboxSelected>>", lambda e: render_details())
        render_details()

        button_frame = ttk.Frame(restart_dialog)
        button_frame.pack(fill=tk.X, pady=10)

        def do_restart():
            preset = preset_name_map.get(selected_preset_var.get())
            if not preset:
                messagebox.showerror(t("error"), t("error_invalid_preset"))
                return
            options = {}
            for opt in preset.get('options', []):
                name = opt.get('name')
                if not name:
                    continue
                options[name] = opt.get('value')
            restart_dialog.destroy()
            self.start_restart_tasks(task_ids, options)

        ttk.Button(button_frame, text=t("cancel"), command=restart_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text=t("restart_tasks"), command=do_restart).pack(side=tk.RIGHT)
    
    def start_restart_tasks(self, task_ids: List[Union[int, str]], options: Optional[Dict[str, Any]]):
        """开始重启任务
        
        Args:
            task_ids: 任务ID列表
            options: 处理选项字典
        """
        self.status_var.set(t("restarting_tasks"))
        self.root.config(cursor="wait")
        
        # 创建进度对话框
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title(t("restart_progress"))
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
        close_button = ttk.Button(progress_dialog, text=t("close"), state=tk.DISABLED)
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
                    update_progress(f"{t('error_no_task_info', task_id=task_id)}\n")
                    failed_tasks += 1
                    completed_tasks += 1
                    update_progress_title(completed_tasks, total_tasks)
                    continue
                
                task_name = task_info.get('name', f"task_{task_id}")
                
                update_progress(f"{t('restarting_task', task_id=task_id, task_name=task_name)}\n")
                
                restart_options = options or {}
                success = self.api.restart_task(self.current_project_id, task_id, restart_options)
                
                if success:
                    update_progress(f"{t('restart_success', task_id=task_id, task_name=task_name)}\n")
                else:
                    update_progress(f"{t('restart_failed', task_id=task_id, task_name=task_name)}\n")
                    failed_tasks += 1
                
                completed_tasks += 1
                update_progress_title(completed_tasks, total_tasks)
            
            # 完成重启
            update_progress(f"\n{t('restart_complete', total=total_tasks, success=total_tasks - failed_tasks, failed=failed_tasks)}\n")
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set(t("restart_complete_status")))
            self.root.after(0, lambda: close_button.config(state=tk.NORMAL, command=progress_dialog.destroy))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 更新进度文本
        def update_progress(text):
            self.root.after(0, lambda: progress_text.insert(tk.END, text))
            self.root.after(0, lambda: progress_text.see(tk.END))
        
        # 更新进度对话框标题
        def update_progress_title(completed, total):
            self.root.after(0, lambda: progress_dialog.title(f"{t('restart_progress')} ({completed}/{total})"))
        
        # 启动重启线程
        threading.Thread(target=restart_thread).start()
    
    def cancel_tasks(self):
        """取消选中的任务"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror(t("error"), t("error_no_task_selected"))
            return
        
        # 获取任务ID列表和检查是否有已完成的任务
        task_ids = []
        completed_tasks = []
        status_completed = t("status_completed")
        
        for item in selection:
            values = self.tasks_treeview.item(item, "values")
            task_id = values[0]
            task_status = values[3]  # 状态在第4列
            
            if task_status == status_completed:  # 状态40对应"已完成"
                completed_tasks.append(task_id)
            else:
                task_ids.append(task_id)
        
        # 如果所有选中的任务都已完成，显示错误消息
        if not task_ids and completed_tasks:
            messagebox.showerror(t("error"), t("error_completed_tasks"))
            return
        
        # 如果有部分任务已完成，提示用户
        if completed_tasks:
            if not messagebox.askyesno(t("warning"), t("warning_completed_tasks", completed=len(completed_tasks), remaining=len(task_ids))):
                return
        
        # 如果没有可取消的任务，直接返回
        if not task_ids:
            return
        
        # 确认取消
        if not messagebox.askyesno(t("confirm"), t("confirm_cancel", count=len(task_ids))):
            return
        
        self.status_var.set(t("canceling_tasks"))
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
                    print(f"Unable to get task {task_id} info")
                    failed_tasks += 1
                    completed_tasks += 1
                    continue
                
                task_name = task_info.get('name', f"task_{task_id}")
                
                print(f"Canceling task {task_id} ({task_name})...")
                
                success = self.api.cancel_task(self.current_project_id, task_id)
                
                if success:
                    print(f"Successfully canceled task {task_id} ({task_name})")
                else:
                    print(f"Failed to cancel task {task_id} ({task_name})")
                    failed_tasks += 1
                
                completed_tasks += 1
            
            # 完成取消
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set(t("cancel_complete", total=total_tasks, success=total_tasks - failed_tasks, failed=failed_tasks)))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 启动取消线程
        threading.Thread(target=cancel_thread).start()
    
    def remove_tasks(self):
        """删除选中的任务"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
        
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 获取选中的任务
        selection = self.tasks_treeview.selection()
        if not selection:
            messagebox.showerror(t("error"), t("error_no_task_selected"))
            return
        
        # 获取任务ID列表
        task_ids = []
        for item in selection:
            task_id = self.tasks_treeview.item(item, "values")[0]
            task_ids.append(task_id)
        
        # 确认删除
        if not messagebox.askyesno(t("confirm"), t("confirm_delete", count=len(task_ids)), icon=messagebox.WARNING):
            return
        
        self.status_var.set(t("deleting_tasks"))
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
                    print(f"Unable to get task {task_id} info")
                    failed_tasks += 1
                    completed_tasks += 1
                    continue
                
                task_name = task_info.get('name', f"task_{task_id}")
                
                print(f"Deleting task {task_id} ({task_name})...")
                
                success = self.api.remove_task(self.current_project_id, task_id)
                
                if success:
                    print(f"Successfully deleted task {task_id} ({task_name})")
                else:
                    print(f"Failed to delete task {task_id} ({task_name})")
                    failed_tasks += 1
                
                completed_tasks += 1
            
            # 完成删除
            self.root.after(0, lambda: self.root.config(cursor=""))
            self.root.after(0, lambda: self.status_var.set(t("delete_complete", total=total_tasks, success=total_tasks - failed_tasks, failed=failed_tasks)))
            
            # 重新加载任务列表
            self.root.after(1000, self.load_tasks)
        
        # 启动删除线程
        threading.Thread(target=remove_thread).start()
    
            
    def restart_task(self, task_id):
        """重启任务并允许修改处理选项"""
        if not self.api.token:
            messagebox.showerror(t("error"), t("error_not_logged_in"))
            return
            
        if not self.current_project_id:
            messagebox.showerror(t("error"), t("error_no_project_selected"))
            return
        
        # 获取任务信息
        task_info = self.api.get_task(self.current_project_id, task_id)
        if not task_info:
            messagebox.showerror(t("error"), t("error_no_task_info", task_id=task_id))
            return
        
        task_name = task_info.get('name', f"task_{task_id}")
        current_options = task_info.get('options', [])
        
        # 获取预设
        self.status_var.set(t("getting_presets"))
        presets = self.api.get_presets()
        if not presets:
            messagebox.showerror(t("error"), t("get_presets_failed"))
            self.status_var.set(t("ready"))
            return

        # 创建重启任务对话框（预设选择）
        restart_dialog = tk.Toplevel(self.root)
        restart_dialog.title(f"{t('restart_task_title')} - {task_name} (ID: {task_id})")
        restart_dialog.geometry("500x400")
        restart_dialog.transient(self.root)
        restart_dialog.grab_set()

        main_frame = ttk.Frame(restart_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text=t("select_preset"), font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 10), anchor=tk.W)

        preset_name_map = {p.get('name', f"preset_{p.get('id')}"): p for p in presets}
        preset_names = list(preset_name_map.keys())
        default_preset_name = next((name for name in preset_names if name.lower() == 'default'), preset_names[0])

        selected_preset_var = tk.StringVar(value=default_preset_name)
        selector_frame = ttk.Frame(main_frame)
        selector_frame.pack(fill=tk.X, pady=5)
        ttk.Label(selector_frame, text=t("preset")).pack(side=tk.LEFT, padx=(0, 5))
        preset_select = ttk.Combobox(selector_frame, textvariable=selected_preset_var, values=preset_names, state="readonly", width=30)
        preset_select.pack(side=tk.LEFT)

        details_group = ttk.LabelFrame(main_frame, text=t("preset_options_readonly"))
        details_group.pack(fill=tk.BOTH, expand=True, pady=10)
        details_text = tk.Text(details_group, height=10, width=60)
        details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def render_details():
            details_text.config(state="normal")
            details_text.delete("1.0", tk.END)
            preset = preset_name_map.get(selected_preset_var.get())
            if preset and isinstance(preset.get('options'), list):
                for opt in preset['options']:
                    details_text.insert(tk.END, f"{opt.get('name')} = {opt.get('value')}\n")
            details_text.config(state="disabled")

        preset_select.bind("<<ComboboxSelected>>", lambda e: render_details())
        render_details()

        button_frame = ttk.Frame(restart_dialog)
        button_frame.pack(fill=tk.X, pady=10)

        def do_restart():
            preset = preset_name_map.get(selected_preset_var.get())
            if not preset:
                messagebox.showerror(t("error"), t("error_invalid_preset"))
                return
            options = {}
            for opt in preset.get('options', []):
                name = opt.get('name')
                if not name:
                    continue
                options[name] = opt.get('value')
            restart_dialog.destroy()

            self.status_var.set(t("restarting_task", task_id=task_id, task_name=task_name))
            self.root.config(cursor="wait")

            def restart_thread():
                success = self.api.restart_task(self.current_project_id, task_id, options)
                if success:
                    self.root.after(0, lambda: self.status_var.set(t("restart_success", task_id=task_id, task_name=task_name)))
                    self.root.after(0, lambda: self.load_tasks())
                else:
                    self.root.after(0, lambda: self.status_var.set(t("restart_failed", task_id=task_id, task_name=task_name)))
                    self.root.after(0, lambda: messagebox.showerror(t("error"), t("restart_failed", task_id=task_id, task_name=task_name)))
                self.root.after(0, lambda: self.root.config(cursor=""))

            threading.Thread(target=restart_thread).start()

        ttk.Button(button_frame, text=t("restart"), command=do_restart).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text=t("cancel"), command=restart_dialog.destroy).pack(side=tk.RIGHT, padx=5)
