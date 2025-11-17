import requests
import json
import os
import time
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class WebODMAPI:
    """WebODM API客户端类，用于与WebODM服务器进行交互"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """初始化WebODM API客户端
        
        Args:
            server_url: WebODM服务器URL，默认为http://localhost:8000
        """
        self.server_url = server_url.rstrip('/')
        self.token = None
        self.headers = {}
    
    def authenticate(self, username: str, password: str) -> bool:
        """用户认证，获取JWT令牌
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 认证是否成功
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/token-auth/",
                data={
                    'username': username,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                if self.token:
                    self.headers = {'Authorization': f'JWT {self.token}'}
                    return True
            return False
        except Exception as e:
            print(f"认证错误: {str(e)}")
            return False
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """获取所有项目列表
        
        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/projects/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                # 处理API返回的不同格式
                if isinstance(result, list):
                    return result  # 直接返回列表
                elif isinstance(result, dict) and 'results' in result:
                    return result['results']  # 返回results字段
                else:
                    return []  # 未知格式，返回空列表
            else:
                print(f"获取项目失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取项目错误: {str(e)}")
            return []
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取指定项目的详细信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict[str, Any]]: 项目详细信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/projects/{project_id}/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取项目详情失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取项目详情错误: {str(e)}")
            return None
    
    def create_project(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """创建新项目
        
        Args:
            name: 项目名称
            description: 项目描述（可选）
            
        Returns:
            Optional[Dict[str, Any]]: 创建的项目信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            data = {'name': name}
            if description:
                data['description'] = description
                
            response = requests.post(
                f"{self.server_url}/api/projects/",
                headers=self.headers,
                data=data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"创建项目失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"创建项目错误: {str(e)}")
            return None
    
    def get_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """获取指定项目的所有任务
        
        Args:
            project_id: 项目ID
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/projects/{project_id}/tasks/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                # 处理API返回的不同格式
                if isinstance(result, list):
                    return result  # 直接返回列表
                elif isinstance(result, dict) and 'results' in result:
                    return result['results']  # 返回results字段
                else:
                    return []  # 未知格式，返回空列表
            else:
                print(f"获取任务列表失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取任务列表错误: {str(e)}")
            return []
    
    def get_task(self, project_id: int, task_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """获取指定任务的详细信息
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务详细信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取任务详情失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取任务详情错误: {str(e)}")
            return None
    
    def create_task(
        self,
        project_id: int,
        images: List[str],
        options: Dict[str, Any] = None,
        name: Optional[str] = None,
        processing_node: Optional[Union[int, str]] = None,
        auto_processing_node: bool = True,
        partial: bool = True,
        align_to: str = "auto",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Optional[Dict[str, Any]]:
        """创建新任务
        
        Args:
            project_id: 项目ID
            images: 图片文件路径列表
            options: 处理选项（可选）
            name: 任务名称（可选）
            processing_node: 处理节点ID（可选）
            auto_processing_node: 是否自动分配处理节点
            partial: 是否以分段上传方式创建任务
            align_to: 任务对齐方式
            progress_callback: 上传进度回调函数，参数为(已完成数量, 总数, 状态信息)
            
        Returns:
            Optional[Dict[str, Any]]: 创建的任务信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            valid_images = []
            for image_path in images:
                if os.path.exists(image_path):
                    valid_images.append(image_path)
                else:
                    print(f"图片不存在: {image_path}")
            
            if not valid_images:
                print("没有有效的图片文件")
                return None
            
            total_images = len(valid_images)
            if progress_callback:
                progress_callback(0, total_images, "正在创建任务...")
            
            payload: Dict[str, Any] = {
                "name": name or "",
                "options": self._build_options_list(options),
                "auto_processing_node": auto_processing_node,
                "partial": partial,
                "align_to": align_to
            }
            if processing_node is not None:
                payload["processing_node"] = processing_node

            print(options)
            print("\n\n")
            print(payload["options"])
            
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code not in (200, 201):
                print(f"创建任务失败: {response.status_code} {response.text}")
                return None
            
            task_info = response.json()
            task_id = task_info.get('id')
            if not task_id:
                print("创建任务失败: 返回数据中缺少任务ID")
                return None
            
            uploaded = 0
            for image_path in valid_images:
                filename = os.path.basename(image_path)
                if progress_callback:
                    progress_callback(uploaded, total_images, f"正在上传 {filename}...")
                
                success = self.upload_task_image(project_id, task_id, image_path)
                if not success:
                    print(f"上传图片失败: {filename}")
                    return None
                
                uploaded += 1
                if progress_callback:
                    progress_callback(uploaded, total_images, f"已上传 {filename}")
            
            if progress_callback:
                progress_callback(total_images, total_images, "正在提交任务...")
            
            commit_result = self.commit_task(project_id, task_id)
            if not commit_result:
                print("提交任务失败")
                return None
            
            return commit_result
        except Exception as e:
            print(f"创建任务错误: {str(e)}")
            return None
    
    def restart_task(
        self,
        project_id: int,
        task_id: Union[int, str],
        options: Dict[str, Any] = None,
        processing_node: Optional[Union[int, str]] = None,
        auto_processing_node: bool = True
    ) -> bool:
        """重启任务
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            options: 新的处理选项（可选）
            
        Returns:
            bool: 重启是否成功
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            data = {}
            if options:
                serialized = self._serialize_options(options)
                if serialized:
                    data['options'] = serialized
            if processing_node is not None:
                data['processing_node'] = processing_node
            data['auto_processing_node'] = 'true' if auto_processing_node else 'false'
            
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/restart/",
                headers=self.headers,
                data=data
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"重启任务错误: {str(e)}")
            return False
    
    def cancel_task(self, project_id: int, task_id: Union[int, str]) -> bool:
        """取消任务
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            
        Returns:
            bool: 取消是否成功
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/cancel/",
                headers=self.headers
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"取消任务错误: {str(e)}")
            return False
    
    def remove_task(self, project_id: int, task_id: Union[int, str]) -> bool:
        """删除任务
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/remove/",
                headers=self.headers
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"删除任务错误: {str(e)}")
            return False
    
    def download_asset(self, project_id: int, task_id: Union[int, str], asset: str, output_path: str) -> bool:
        """下载任务资源
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            asset: 资源名称，如'orthophoto.tif'
            output_path: 输出文件路径
            
        Returns:
            bool: 下载是否成功
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/download/{asset}",
                headers=self.headers,
                stream=True
            )
            
            if response.status_code == 200:
                # 确保输出目录存在
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # 写入文件
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"下载资源失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"下载资源错误: {str(e)}")
            return False
    
    def get_available_assets(self, project_id: int, task_id: int) -> List[str]:
        """获取任务可用的资源列表
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            
        Returns:
            List[str]: 可用资源列表
        """
        task_info = self.get_task(project_id, task_id)
        if task_info and 'available_assets' in task_info:
            return task_info['available_assets']
        return []
        
    def get_processing_node_options(self) -> List[Dict[str, Any]]:
        """获取处理节点支持的选项
        
        Returns:
            List[Dict[str, Any]]: 处理选项列表
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            response = requests.get(
                f"{self.server_url}/api/processingnodes/options/",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取处理选项失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取处理选项错误: {str(e)}")
            return []
    
    def upload_task_image(self, project_id: int, task_id: Union[int, str], image_path: str) -> bool:
        """上传单张图片到任务"""
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
        
        if not os.path.exists(image_path):
            print(f"图片不存在: {image_path}")
            return False
        
        try:
            filename = os.path.basename(image_path)
            mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
            with open(image_path, 'rb') as f:
                files = {'images': (filename, f, mime_type)}
                response = requests.post(
                    f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/upload/",
                    headers=self.headers,
                    files=files
                )
            if response.status_code == 200:
                return True
            print(f"上传图片失败: {response.status_code} {response.text}")
            return False
        except Exception as e:
            print(f"上传图片错误: {str(e)}")
            return False
    
    def commit_task(self, project_id: int, task_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """提交已上传图片的任务"""
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
        
        try:
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/commit/",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            print(f"提交任务失败: {response.status_code} {response.text}")
            return None
        except Exception as e:
            print(f"提交任务错误: {str(e)}")
            return None
    
    def _build_options_list(self, options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将处理选项转换为API需要的列表"""
        if not options:
            return []
        serialized = []
        for key, value in options.items():
            if key is None:
                continue
            formatted = self._format_option_value(value)
            if formatted is None:
                continue
            serialized.append({'name': key, 'value': formatted})
        return serialized
    
    def _serialize_options(self, options: Dict[str, Any]) -> str:
        """将处理选项转换为API需要的JSON字符串"""
        serialized = []
        for key, value in options.items():
            if key is None:
                continue
            formatted = self._format_option_value(value)
            if formatted is None:
                continue
            serialized.append({'name': key, 'value': formatted})
        return json.dumps(serialized)

    def _format_option_value(self, value: Any) -> Optional[str]:
        """将选项的值统一转换为字符串表示"""
        if value is None:
            return None
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        value_str = str(value).strip()
        if value_str == "":
            return None
        return value_str
    
    def wait_for_task_completion(self, project_id: int, task_id: int, check_interval: int = 3) -> Dict[str, Any]:
        """等待任务完成
        
        Args:
            project_id: 项目ID
            task_id: 任务ID
            check_interval: 检查间隔（秒）
            
        Returns:
            Dict[str, Any]: 任务完成后的详细信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
        
        while True:
            task_info = self.get_task(project_id, task_id)
            if not task_info:
                raise Exception(f"无法获取任务信息: {task_id}")
            
            status = task_info.get('status')
            if status == 30:  # COMPLETED
                return task_info
            elif status == 40:  # FAILED
                raise Exception(f"任务失败: {task_info}")
            elif status == 50:  # CANCELED
                raise Exception(f"任务已取消: {task_info}")
            
            print(f"任务处理中，状态: {status}")
            time.sleep(check_interval)
