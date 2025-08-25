import os
import uuid
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageOps, ImageDraw, ImageFont
import hashlib
import json
from datetime import datetime

class FileHandler:
    """文件处理工具类"""
    
    def __init__(self, upload_dir: str = "static/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件类型
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        self.video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv'}
        self.audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'}
        
        # 所有支持的扩展名
        self.allowed_extensions = (
            self.image_extensions | 
            self.video_extensions | 
            self.audio_extensions | 
            self.document_extensions
        )
        
        # 文件大小限制 (MB)
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '50')) * 1024 * 1024
        
        # 缩略图配置
        self.thumbnail_size = tuple(map(int, os.getenv('THUMBNAIL_SIZE', '300,300').split(',')))
        self.image_quality = int(os.getenv('IMAGE_QUALITY', '85'))

    def is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        return Path(filename).suffix.lower() in self.allowed_extensions

    def get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        if ext in self.image_extensions:
            return 'photo'
        elif ext in self.video_extensions:
            return 'video'
        elif ext in self.audio_extensions:
            return 'audio'
        elif ext in self.document_extensions:
            return 'document'
        else:
            return 'other'

    def generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4().hex)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{unique_id}{ext}"

    def get_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def save_file(self, file_content: bytes, filename: str) -> Tuple[str, dict]:
        """保存文件并返回文件路径和元数据"""
        if not self.is_allowed_file(filename):
            raise ValueError(f"不支持的文件类型: {Path(filename).suffix}")
        
        if len(file_content) > self.max_file_size:
            raise ValueError(f"文件大小超过限制: {self.max_file_size / 1024 / 1024}MB")
        
        # 生成新文件名
        new_filename = self.generate_filename(filename)
        file_path = self.upload_dir / new_filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 获取文件信息
        file_info = {
            'filename': filename,
            'file_path': str(file_path),
            'file_size': len(file_content),
            'mime_type': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
            'file_hash': self.get_file_hash(str(file_path)),
            'work_type': self.get_file_type(filename)
        }
        
        # 如果是图片，处理图片信息和缩略图
        if file_info['work_type'] == 'photo':
            image_info = self.process_image(file_path)
            file_info.update(image_info)
        
        return str(file_path), file_info

    def process_image(self, image_path: Path) -> dict:
        """处理图片，生成缩略图和获取尺寸信息"""
        try:
            with Image.open(image_path) as img:
                # 获取原始尺寸
                width, height = img.size
                
                # 修正图片方向
                img = ImageOps.exif_transpose(img)
                
                # 生成缩略图
                thumbnail_path = self.generate_thumbnail(img, image_path)
                
                # 如果需要，添加水印
                if os.getenv('WATERMARK_ENABLED', 'false').lower() == 'true':
                    watermark_path = self.add_watermark(img, image_path)
                else:
                    watermark_path = None
                
                return {
                    'width': width,
                    'height': height,
                    'thumbnail_path': str(thumbnail_path) if thumbnail_path else None,
                    'watermark_path': str(watermark_path) if watermark_path else None
                }
                
        except Exception as e:
            print(f"图片处理失败: {e}")
            return {'width': None, 'height': None, 'thumbnail_path': None}

    def generate_thumbnail(self, img: Image.Image, original_path: Path) -> Optional[Path]:
        """生成缩略图"""
        try:
            # 创建缩略图副本
            thumbnail = img.copy()
            thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # 生成缩略图文件名
            thumb_filename = f"thumb_{original_path.name}"
            thumb_path = self.upload_dir / thumb_filename
            
            # 保存缩略图
            if thumbnail.mode == 'RGBA':
                # 处理透明图片
                background = Image.new('RGB', thumbnail.size, (255, 255, 255))
                background.paste(thumbnail, mask=thumbnail.split()[-1])
                thumbnail = background
            
            thumbnail.save(thumb_path, optimize=True, quality=self.image_quality)
            return thumb_path
            
        except Exception as e:
            print(f"缩略图生成失败: {e}")
            return None

    def add_watermark(self, img: Image.Image, original_path: Path) -> Optional[Path]:
        """添加水印"""
        try:
            watermark_text = os.getenv('WATERMARK_TEXT', '© Your Name')
            
            # 创建水印副本
            watermarked = img.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # 计算字体大小
            font_size = min(watermarked.size) // 20
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # 获取文本尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 计算水印位置 (右下角)
            margin = 20
            x = watermarked.width - text_width - margin
            y = watermarked.height - text_height - margin
            
            # 添加半透明背景
            overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                [(x-10, y-5), (x+text_width+10, y+text_height+5)],
                fill=(0, 0, 0, 128)
            )
            
            # 合并背景
            watermarked = Image.alpha_composite(watermarked.convert('RGBA'), overlay)
            
            # 添加文字
            draw = ImageDraw.Draw(watermarked)
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 200))
            
            # 保存水印版本
            watermark_filename = f"watermark_{original_path.name}"
            watermark_path = self.upload_dir / watermark_filename
            
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
            
            watermarked.save(watermark_path, optimize=True, quality=self.image_quality)
            return watermark_path
            
        except Exception as e:
            print(f"水印添加失败: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """删除文件及其相关文件"""
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                
                # 删除相关的缩略图和水印文件
                thumb_path = file_path.parent / f"thumb_{file_path.name}"
                if thumb_path.exists():
                    thumb_path.unlink()
                    
                watermark_path = file_path.parent / f"watermark_{file_path.name}"
                if watermark_path.exists():
                    watermark_path.unlink()
                
                return True
        except Exception as e:
            print(f"文件删除失败: {e}")
        return False

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """获取文件详细信息"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                'filename': path.name,
                'file_path': str(path),
                'file_size': stat.st_size,
                'mime_type': mimetypes.guess_type(str(path))[0],
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'work_type': self.get_file_type(path.name)
            }
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return None

class BackupManager:
    """备份管理工具类"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, source_dir: str, backup_name: str = None) -> str:
        """创建备份"""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        import tarfile
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, restore_dir: str) -> bool:
        """恢复备份"""
        try:
            import tarfile
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(restore_dir)
            return True
        except Exception as e:
            print(f"备份恢复失败: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """清理旧备份"""
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                print(f"已删除过期备份: {backup_file}")

def slugify(text: str) -> str:
    """将文本转换为URL友好的slug"""
    import re
    import unicodedata
    
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_image(file_content: bytes) -> bool:
    """验证图片文件是否有效"""
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()
        return True
    except Exception:
        return False

def get_image_dimensions(file_path: str) -> Tuple[Optional[int], Optional[int]]:
    """获取图片尺寸"""
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        return None, None

def create_color_palette(image_path: str, num_colors: int = 5) -> List[str]:
    """从图片中提取主要颜色"""
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((150, 150))
            
            # 获取颜色
            colors = img.getcolors(maxcolors=256*256*256)
            if not colors:
                return []
            
            # 按使用频率排序
            colors.sort(key=lambda x: x[0], reverse=True)
            
            # 转换为十六进制
            hex_colors = []
            for count, color in colors[:num_colors]:
                hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                hex_colors.append(hex_color)
            
            return hex_colors
    except Exception:
        return []