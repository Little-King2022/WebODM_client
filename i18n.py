"""Internationalization module for WebODM Client UI.

This module provides translations for the UI in multiple languages.
Currently supports Chinese (zh_CN) and English (en).
"""

from typing import Dict

# Chinese translations (default)
ZH_CN: Dict[str, str] = {
    # Window title
    "window_title": "WebODM 客户端",
    
    # Menu items
    "menu_file": "文件",
    "menu_exit": "退出",
    "menu_settings": "设置",
    "menu_server_settings": "服务器设置",
    "menu_help": "帮助",
    "menu_about": "关于",
    "menu_language": "语言",
    
    # Connection frame
    "server_connection": "服务器连接",
    "server_address": "服务器地址:",
    "login": "登录",
    "logout": "注销",
    "status": "状态:",
    "not_connected": "未连接",
    "connected": "已连接",
    "logged_out": "已注销",
    
    # Login dialog
    "login_title": "登录",
    "username": "用户名:",
    "password": "密码:",
    "logging_in": "正在登录...",
    "login_success": "登录成功",
    "login_failed": "登录失败",
    "login_failed_msg": "用户名或密码错误，或服务器无法连接",
    "error_empty_credentials": "用户名和密码不能为空",
    
    # Projects frame
    "project_list": "项目列表",
    "refresh": "刷新",
    "new_project": "新建项目",
    "view_details": "查看详情",
    "projects_loaded": "已加载 {count} 个项目",
    
    # New project dialog
    "new_project_title": "新建项目",
    "project_name": "项目名称:",
    "project_description": "项目描述:",
    "create": "创建",
    "creating_project": "正在创建项目...",
    "project_created": "项目创建成功",
    "project_create_failed": "项目创建失败",
    "project_create_failed_msg": "无法创建项目，请检查网络连接或服务器状态",
    "error_empty_project_name": "项目名称不能为空",
    
    # Project details dialog
    "project_details": "项目详情",
    "project_id": "项目ID:",
    "created_at": "创建时间:",
    "permissions": "权限:",
    "no_permissions": "无权限信息",
    "unknown": "未知",
    "none": "无",
    "close": "关闭",
    "getting_project_details": "正在获取项目详情...",
    "get_project_details_failed": "获取项目详情失败",
    
    # Tasks frame
    "task_list": "任务列表",
    "new_task": "新建任务",
    "download_assets": "下载资源",
    "restart_tasks": "重启任务",
    "cancel_tasks": "取消任务",
    "delete_tasks": "删除任务",
    "tasks_loaded": "已加载 {count} 个任务",
    "loading_tasks": "正在加载任务列表...",
    "loading_projects": "正在加载项目列表...",
    
    # Task table columns
    "col_id": "ID",
    "col_name": "名称",
    "col_created_at": "创建时间",
    "col_status": "状态",
    "col_processing_time": "处理时间",
    
    # Task status
    "status_queued": "队列中",
    "status_running": "运行中",
    "status_failed": "失败",
    "status_completed": "已完成",
    "status_canceled": "已取消",
    "status_unknown": "未知",
    
    # Task details dialog
    "task_details": "任务详情",
    "unnamed": "未命名",
    "basic_info": "基本信息",
    "processing_options": "处理选项",
    "available_assets": "可用资源",
    
    # New task dialog
    "new_task_title": "新建任务",
    "task_name": "任务名称:",
    "select_images": "选择图片:",
    "add_images": "添加图片",
    "remove_selected": "移除选中",
    "clear_list": "清空列表",
    "select_preset": "选择预设:",
    "preset": "预设:",
    "preset_options_readonly": "预设选项 (只读)",
    "upload_progress": "上传进度",
    "waiting_to_start": "等待开始...",
    "cancel": "取消",
    "create_task": "创建任务",
    "minimize": "最小化",
    "creating_task": "正在创建任务...",
    "task_created": "任务创建成功",
    "task_create_failed": "任务创建失败",
    "task_create_failed_msg": "无法创建任务，请检查图片文件和网络连接",
    "error_no_images": "请至少添加一张图片",
    "error_invalid_preset": "请选择有效的预设",
    "preparing_upload": "正在准备上传...",
    "uploading": "正在上传 {filename}...",
    "uploaded": "已上传 {filename}",
    "upload_complete_submitting": "上传完成，已提交任务",
    "select_images_title": "选择图片",
    
    # File types
    "filetype_images": "图片文件",
    "filetype_jpeg": "JPEG文件",
    "filetype_png": "PNG文件",
    "filetype_tiff": "TIFF文件",
    "filetype_all": "所有文件",
    
    # Download assets dialog
    "select_assets_to_download": "选择要下载的资源",
    "select_asset_types": "选择要下载的资源类型:",
    "download": "下载",
    "select_download_dir": "选择下载目录",
    "download_progress": "下载进度",
    "preparing_download": "正在准备下载...",
    "downloading_asset": "正在下载任务 {task_id} ({task_name}) 的资源: {asset}",
    "download_success": "成功下载: {path}",
    "download_failed": "下载失败: {asset}",
    "download_complete": "下载完成! 总计: {total}, 成功: {success}, 失败: {failed}",
    "download_complete_status": "下载完成",
    "error_no_task_info": "无法获取任务 {task_id} 的信息",
    "error_no_assets": "任务 {task_name} 没有可用的资源",
    "task_no_asset": "任务 {task_id} ({task_name}) 没有资源: {asset}",
    "error_create_dir": "无法创建目录 {dir}: {error}",
    "error_invalid_download_dir": "请选择有效的下载目录",
    
    # Restart tasks dialog
    "restart_task_title": "重启任务",
    "batch_restart_title": "批量重启任务",
    "will_restart_tasks": "将重启 {count} 个任务，请选择预设:",
    "restart": "重启",
    "restart_progress": "重启进度",
    "restarting_task": "正在重启任务 {task_id} ({task_name})...",
    "restart_success": "成功重启任务 {task_id} ({task_name})",
    "restart_failed": "重启任务 {task_id} ({task_name}) 失败",
    "restart_complete": "重启完成! 总计: {total}, 成功: {success}, 失败: {failed}",
    "restart_complete_status": "重启完成",
    "restarting_tasks": "正在重启任务...",
    "getting_presets": "正在获取预设...",
    "get_presets_failed": "无法获取预设配置",
    
    # Cancel tasks
    "confirm_cancel": "确定要取消选中的 {count} 个任务吗?",
    "warning_completed_tasks": "选中的任务中有 {completed} 个已完成的任务不可取消，是否继续取消其他 {remaining} 个任务?",
    "error_completed_tasks": "已完成的任务不可取消",
    "canceling_tasks": "正在取消任务...",
    "cancel_complete": "取消完成! 总计: {total}, 成功: {success}, 失败: {failed}",
    
    # Delete tasks
    "confirm_delete": "确定要删除选中的 {count} 个任务吗? 此操作不可恢复!",
    "deleting_tasks": "正在删除任务...",
    "delete_complete": "删除完成! 总计: {total}, 成功: {success}, 失败: {failed}",
    
    # Common
    "error": "错误",
    "warning": "警告",
    "confirm": "确认",
    "ready": "就绪",
    "error_not_logged_in": "请先登录",
    "error_no_project_selected": "请先选择一个项目",
    "error_no_task_selected": "请先选择至少一个任务",
    
    # Server settings dialog
    "server_settings_title": "服务器设置",
    "server_settings_prompt": "请输入WebODM服务器地址:",
    
    # About dialog
    "about_title": "关于",
    "about_text": "WebODM 客户端 {version}\n\nhttps://github.com/Little-King2022/WebODM_client\n\n基于Python和Tkinter的 WebODM(https://github.com/OpenDroneMap/WebODM) 客户端，用于批量管理WebODM中的项目和图片拼接任务",
    
    # Language names
    "lang_zh_cn": "中文",
    "lang_en": "English",
}

# English translations
EN: Dict[str, str] = {
    # Window title
    "window_title": "WebODM Client",
    
    # Menu items
    "menu_file": "File",
    "menu_exit": "Exit",
    "menu_settings": "Settings",
    "menu_server_settings": "Server Settings",
    "menu_help": "Help",
    "menu_about": "About",
    "menu_language": "Language",
    
    # Connection frame
    "server_connection": "Server Connection",
    "server_address": "Server Address:",
    "login": "Login",
    "logout": "Logout",
    "status": "Status:",
    "not_connected": "Not Connected",
    "connected": "Connected",
    "logged_out": "Logged Out",
    
    # Login dialog
    "login_title": "Login",
    "username": "Username:",
    "password": "Password:",
    "logging_in": "Logging in...",
    "login_success": "Login successful",
    "login_failed": "Login failed",
    "login_failed_msg": "Invalid username or password, or server unreachable",
    "error_empty_credentials": "Username and password cannot be empty",
    
    # Projects frame
    "project_list": "Project List",
    "refresh": "Refresh",
    "new_project": "New Project",
    "view_details": "View Details",
    "projects_loaded": "Loaded {count} projects",
    
    # New project dialog
    "new_project_title": "New Project",
    "project_name": "Project Name:",
    "project_description": "Description:",
    "create": "Create",
    "creating_project": "Creating project...",
    "project_created": "Project created successfully",
    "project_create_failed": "Project creation failed",
    "project_create_failed_msg": "Unable to create project, please check network connection or server status",
    "error_empty_project_name": "Project name cannot be empty",
    
    # Project details dialog
    "project_details": "Project Details",
    "project_id": "Project ID:",
    "created_at": "Created At:",
    "permissions": "Permissions:",
    "no_permissions": "No permission information",
    "unknown": "Unknown",
    "none": "None",
    "close": "Close",
    "getting_project_details": "Getting project details...",
    "get_project_details_failed": "Failed to get project details",
    
    # Tasks frame
    "task_list": "Task List",
    "new_task": "New Task",
    "download_assets": "Download Assets",
    "restart_tasks": "Restart Tasks",
    "cancel_tasks": "Cancel Tasks",
    "delete_tasks": "Delete Tasks",
    "tasks_loaded": "Loaded {count} tasks",
    "loading_tasks": "Loading tasks...",
    "loading_projects": "Loading projects...",
    
    # Task table columns
    "col_id": "ID",
    "col_name": "Name",
    "col_created_at": "Created At",
    "col_status": "Status",
    "col_processing_time": "Processing Time",
    
    # Task status
    "status_queued": "Queued",
    "status_running": "Running",
    "status_failed": "Failed",
    "status_completed": "Completed",
    "status_canceled": "Canceled",
    "status_unknown": "Unknown",
    
    # Task details dialog
    "task_details": "Task Details",
    "unnamed": "Unnamed",
    "basic_info": "Basic Info",
    "processing_options": "Processing Options",
    "available_assets": "Available Assets",
    
    # New task dialog
    "new_task_title": "New Task",
    "task_name": "Task Name:",
    "select_images": "Select Images:",
    "add_images": "Add Images",
    "remove_selected": "Remove Selected",
    "clear_list": "Clear List",
    "select_preset": "Select Preset:",
    "preset": "Preset:",
    "preset_options_readonly": "Preset Options (Read-only)",
    "upload_progress": "Upload Progress",
    "waiting_to_start": "Waiting to start...",
    "cancel": "Cancel",
    "create_task": "Create Task",
    "minimize": "Minimize",
    "creating_task": "Creating task...",
    "task_created": "Task created successfully",
    "task_create_failed": "Task creation failed",
    "task_create_failed_msg": "Unable to create task, please check image files and network connection",
    "error_no_images": "Please add at least one image",
    "error_invalid_preset": "Please select a valid preset",
    "preparing_upload": "Preparing upload...",
    "uploading": "Uploading {filename}...",
    "uploaded": "Uploaded {filename}",
    "upload_complete_submitting": "Upload complete, task submitted",
    "select_images_title": "Select Images",
    
    # File types
    "filetype_images": "Image Files",
    "filetype_jpeg": "JPEG Files",
    "filetype_png": "PNG Files",
    "filetype_tiff": "TIFF Files",
    "filetype_all": "All Files",
    
    # Download assets dialog
    "select_assets_to_download": "Select Assets to Download",
    "select_asset_types": "Select asset types to download:",
    "download": "Download",
    "select_download_dir": "Select Download Directory",
    "download_progress": "Download Progress",
    "preparing_download": "Preparing download...",
    "downloading_asset": "Downloading asset {asset} for task {task_id} ({task_name})",
    "download_success": "Downloaded: {path}",
    "download_failed": "Download failed: {asset}",
    "download_complete": "Download complete! Total: {total}, Success: {success}, Failed: {failed}",
    "download_complete_status": "Download complete",
    "error_no_task_info": "Unable to get task {task_id} information",
    "error_no_assets": "Task {task_name} has no available assets",
    "task_no_asset": "Task {task_id} ({task_name}) does not have asset: {asset}",
    "error_create_dir": "Unable to create directory {dir}: {error}",
    "error_invalid_download_dir": "Please select a valid download directory",
    
    # Restart tasks dialog
    "restart_task_title": "Restart Task",
    "batch_restart_title": "Batch Restart Tasks",
    "will_restart_tasks": "Will restart {count} tasks, please select a preset:",
    "restart": "Restart",
    "restart_progress": "Restart Progress",
    "restarting_task": "Restarting task {task_id} ({task_name})...",
    "restart_success": "Successfully restarted task {task_id} ({task_name})",
    "restart_failed": "Failed to restart task {task_id} ({task_name})",
    "restart_complete": "Restart complete! Total: {total}, Success: {success}, Failed: {failed}",
    "restart_complete_status": "Restart complete",
    "restarting_tasks": "Restarting tasks...",
    "getting_presets": "Getting presets...",
    "get_presets_failed": "Unable to get preset configurations",
    
    # Cancel tasks
    "confirm_cancel": "Are you sure you want to cancel the selected {count} task(s)?",
    "warning_completed_tasks": "{completed} completed task(s) cannot be canceled. Continue canceling the other {remaining} task(s)?",
    "error_completed_tasks": "Completed tasks cannot be canceled",
    "canceling_tasks": "Canceling tasks...",
    "cancel_complete": "Cancel complete! Total: {total}, Success: {success}, Failed: {failed}",
    
    # Delete tasks
    "confirm_delete": "Are you sure you want to delete the selected {count} task(s)? This action cannot be undone!",
    "deleting_tasks": "Deleting tasks...",
    "delete_complete": "Delete complete! Total: {total}, Success: {success}, Failed: {failed}",
    
    # Common
    "error": "Error",
    "warning": "Warning",
    "confirm": "Confirm",
    "ready": "Ready",
    "error_not_logged_in": "Please login first",
    "error_no_project_selected": "Please select a project first",
    "error_no_task_selected": "Please select at least one task first",
    
    # Server settings dialog
    "server_settings_title": "Server Settings",
    "server_settings_prompt": "Enter WebODM server address:",
    
    # About dialog
    "about_title": "About",
    "about_text": "WebODM Client {version}\n\nhttps://github.com/Little-King2022/WebODM_client\n\nA Python and Tkinter-based WebODM (https://github.com/OpenDroneMap/WebODM) client for batch management of projects and image stitching tasks",
    
    # Language names
    "lang_zh_cn": "中文",
    "lang_en": "English",
}

# Available languages
LANGUAGES = {
    "zh_CN": ZH_CN,
    "en": EN,
}

# Default language
DEFAULT_LANGUAGE = "zh_CN"


class I18n:
    """Internationalization class for managing translations."""
    
    def __init__(self, language: str = DEFAULT_LANGUAGE):
        """Initialize with a specific language.
        
        Args:
            language: Language code (e.g., 'zh_CN', 'en')
        """
        self._language = language if language in LANGUAGES else DEFAULT_LANGUAGE
        self._translations = LANGUAGES[self._language]
    
    @property
    def language(self) -> str:
        """Get current language code."""
        return self._language
    
    @language.setter
    def language(self, value: str):
        """Set current language.
        
        Args:
            value: Language code
        """
        if value in LANGUAGES:
            self._language = value
            self._translations = LANGUAGES[value]
    
    def get(self, key: str, **kwargs) -> str:
        """Get translated text for a key.
        
        Args:
            key: Translation key
            **kwargs: Format arguments for the translation string
            
        Returns:
            Translated string, or the key itself if not found
        """
        text = self._translations.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text
    
    def __call__(self, key: str, **kwargs) -> str:
        """Shorthand for get().
        
        Args:
            key: Translation key
            **kwargs: Format arguments
            
        Returns:
            Translated string
        """
        return self.get(key, **kwargs)
    
    @staticmethod
    def get_available_languages() -> Dict[str, str]:
        """Get available languages with their display names.
        
        Returns:
            Dict mapping language codes to display names
        """
        return {
            "zh_CN": "中文",
            "en": "English",
        }


# Global i18n instance
_i18n = I18n()


def get_i18n() -> I18n:
    """Get the global i18n instance."""
    return _i18n


def set_language(language: str):
    """Set the global language.
    
    Args:
        language: Language code
    """
    _i18n.language = language


def t(key: str, **kwargs) -> str:
    """Translate a key using the global i18n instance.
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated string
    """
    return _i18n.get(key, **kwargs)
