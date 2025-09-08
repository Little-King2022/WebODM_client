import requests
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union

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
    
    def create_task(self, project_id: int, images: List[str], options: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """创建新任务
        
        Args:
            project_id: 项目ID
            images: 图片文件路径列表
            options: 处理选项（可选）
            
        Returns:
            Optional[Dict[str, Any]]: 创建的任务信息
        """
        if not self.token:
            raise Exception("未认证，请先调用authenticate方法")
            
        try:
            # 准备图片文件
            files = []
            for image_path in images:
                if os.path.exists(image_path):
                    filename = os.path.basename(image_path)
                    files.append(('images', (filename, open(image_path, 'rb'), 'image/jpeg')))
                else:
                    print(f"图片不存在: {image_path}")
            
            if not files:
                print("没有有效的图片文件")
                return None
            
            # 准备处理选项
            data = {}
            if options:
                data['options'] = json.dumps([{'name': k, 'value': v} for k, v in options.items()])
            
            response = requests.post(
                f"{self.server_url}/api/projects/{project_id}/tasks/",
                headers=self.headers,
                files=files,
                data=data
            )
            
            # 关闭所有打开的文件
            for _, (_, f, _) in files:
                f.close()
            
            if response.status_code == 201 or response.status_code == 200:
                return response.json()
            else:
                print(f"创建任务失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"创建任务错误: {str(e)}")
            return None
    
    def restart_task(self, project_id: int, task_id: Union[int, str], options: Dict[str, Any] = None) -> bool:
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
                data['options'] = json.dumps([{'name': k, 'value': v} for k, v in options.items()])
            
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
            response = requests.delete(
                f"{self.server_url}/api/projects/{project_id}/tasks/{task_id}/",
                headers=self.headers
            )
            
            return response.status_code == 204
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