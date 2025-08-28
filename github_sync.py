"""
GitHub同步模块 - 实现JSON数据与GitHub仓库的双向同步
"""

import json
import base64
import os
import logging
from typing import Optional, Dict, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class GitHubSyncError(Exception):
    """GitHub同步相关异常"""
    pass

class GitHubSync:
    """GitHub数据同步类"""
    
    def __init__(self, 
                 token: Optional[str] = None,
                 repo: Optional[str] = None,
                 file_path: str = "games_data.json",
                 branch: str = "main"):
        """
        初始化GitHub同步
        
        Args:
            token: GitHub Personal Access Token
            repo: 仓库名称，格式：username/repo-name
            file_path: 要同步的文件路径
            branch: 分支名称
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO", "DengXiaoLong0611/Gametracker")
        self.file_path = file_path
        self.branch = branch
        
        if not self.token:
            logger.warning("GitHub Token未配置，GitHub同步功能将被禁用")
            self.enabled = False
        else:
            self.enabled = True
            
        self.api_url = f"https://api.github.com/repos/{self.repo}/contents/{self.file_path}"
        
    def is_enabled(self) -> bool:
        """检查GitHub同步是否启用"""
        return self.enabled and bool(self.token)
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送GitHub API请求"""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GameTracker-GitHubSync/1.0"
        }
        
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise GitHubSyncError(f"GitHub API请求失败: {e}")
    
    def get_file_info(self) -> Optional[Dict[str, Any]]:
        """获取GitHub上文件的信息"""
        if not self.is_enabled():
            return None
            
        try:
            response = self._make_request("GET", f"{self.api_url}?ref={self.branch}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.info(f"文件 {self.file_path} 在GitHub上不存在")
                return None
            else:
                logger.error(f"获取文件信息失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取GitHub文件信息失败: {e}")
            return None
    
    def download_from_github(self) -> Optional[Dict[str, Any]]:
        """从GitHub下载数据"""
        if not self.is_enabled():
            return None
            
        try:
            file_info = self.get_file_info()
            if not file_info:
                return None
                
            # 解码base64内容
            content = base64.b64decode(file_info["content"]).decode('utf-8')
            data = json.loads(content)
            
            logger.info(f"成功从GitHub下载数据，文件大小: {len(content)} bytes")
            return data
            
        except Exception as e:
            logger.error(f"从GitHub下载数据失败: {e}")
            return None
    
    def upload_to_github(self, data: Dict[str, Any], commit_message: Optional[str] = None) -> bool:
        """上传数据到GitHub"""
        if not self.is_enabled():
            logger.warning("GitHub同步未启用，跳过上传")
            return False
            
        try:
            # 获取当前文件的SHA（如果存在）
            file_info = self.get_file_info()
            sha = file_info.get("sha") if file_info else None
            
            # 准备数据
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('ascii')
            
            # 准备提交信息
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"🎮 自动同步游戏数据 - {timestamp}"
            
            # 准备请求载荷
            payload = {
                "message": commit_message,
                "content": encoded_content,
                "branch": self.branch
            }
            
            if sha:
                payload["sha"] = sha
            
            # 发送请求
            response = self._make_request("PUT", self.api_url, json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"成功上传数据到GitHub: {response.json().get('commit', {}).get('html_url', '')}")
                return True
            else:
                logger.error(f"上传到GitHub失败: HTTP {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"上传数据到GitHub失败: {e}")
            return False
    
    def sync_from_github(self, local_file_path: str) -> bool:
        """从GitHub同步数据到本地文件"""
        if not self.is_enabled():
            return False
            
        try:
            data = self.download_from_github()
            if data is None:
                logger.warning("无法从GitHub获取数据")
                return False
                
            # 写入本地文件
            with open(local_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"成功从GitHub同步数据到本地: {local_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"从GitHub同步到本地失败: {e}")
            return False
    
    def sync_to_github(self, local_file_path: str, commit_message: Optional[str] = None) -> bool:
        """同步本地文件到GitHub"""
        if not self.is_enabled():
            return False
            
        try:
            # 读取本地文件
            with open(local_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 上传到GitHub
            return self.upload_to_github(data, commit_message)
            
        except Exception as e:
            logger.error(f"同步本地文件到GitHub失败: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态信息"""
        status = {
            "enabled": self.is_enabled(),
            "repo": self.repo,
            "file_path": self.file_path,
            "branch": self.branch,
            "github_file_exists": False,
            "last_github_update": None
        }
        
        if self.is_enabled():
            file_info = self.get_file_info()
            if file_info:
                status["github_file_exists"] = True
                status["last_github_update"] = file_info.get("commit", {}).get("committer", {}).get("date")
                
        return status

# 创建全局GitHub同步实例
github_sync = GitHubSync()