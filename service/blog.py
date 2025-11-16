from typing import List, Optional, Dict

# 博客管理模块接口

def create_post(user_id: int, title: str, content: str, markdown_content: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict:
    """
    发布博客
    Args:
        user_id: 作者用户ID
        title: 博客标题
        content: 博客内容（HTML/文本）
        markdown_content: 博客Markdown内容（可选）
        tags: 标签列表（可选）
    Returns:
        dict: 新建博客的基本信息，如id、title、user_id、created_at等
    """
    pass

def get_post(post_id: int) -> Dict:
    """
    获取单个博客
    Args:
        post_id: 博客ID
    Returns:
        dict: 博客详细信息，包括id、title、content、markdown_content、tags、created_at、updated_at等
    """
    pass

def update_post(post_id: int, user_id: int, title: Optional[str] = None, content: Optional[str] = None,
                markdown_content: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
    """
    编辑博客
    Args:
        post_id: 博客ID
        user_id: 当前用户ID（用于权限验证）
        title: 新标题（可选）
        content: 新内容（可选）
        markdown_content: 新Markdown内容（可选）
        tags: 新标签列表（可选）
    Returns:
        bool: True表示更新成功，False表示失败或无权限
    """
    pass

def delete_post(post_id: int, user_id: int) -> bool:
    """
    删除博客
    Args:
        post_id: 博客ID
        user_id: 当前用户ID（用于权限验证）
    Returns:
        bool: True表示删除成功，False表示失败或无权限
    """
    pass

def list_posts(user_id: Optional[int] = None, tag: Optional[str] = None, page: int = 1, page_size: int = 10) -> List[Dict]:
    """
    获取博客列表
    Args:
        user_id: 仅获取某个用户的博客（可选）
        tag: 根据标签筛选博客（可选）
        page: 页码
        page_size: 每页数量
    Returns:
        List[Dict]: 博客列表，每个博客包含id、title、user_id、tags、created_at等信息
    """
    pass

# 需要再实现
# def search_poists()
