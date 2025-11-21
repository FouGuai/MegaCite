

---

# # 📘 DAO 接口文档（Markdown 版本）

---

# ## 👤 UserDAO（用户数据访问层）

```python
class UserDAO(ABC):

    def create_user(self, username: str, password_hash: str) -> int:
        """
        Description:
            创建用户。
        Params:
            username: 用户名
            password_hash: 加密后的密码
        Return:
            user_id(int): 创建后的用户 ID
        """

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Description:
            根据用户名查询用户。
        Params:
            username: 用户名
        Return:
            User | None
        """

    def update_user(self, user_id: int, dict: dict[str: Any]) -> bool:
        """
        Description:
            更新用户字段（允许部分字段更新）。
        Params:
            user_id: 用户 ID
            dict: 要更新的字段，例如 {"token": "..."}
        Return:
            True / False
        """

    def delete_user(self, user_id: int) -> bool:
        """
        Description:
            删除用户。
        Params:
            user_id: 用户 ID
        Return:
            True / False
        """
```

---

# ## 🔐 AuthDAO（外部认证平台管理）

```python
class AuthDAO(ABC):

    def add_platform_auth(self, user_id: int, platform: str, credential: str) -> None:
        """
        Description:
            添加某平台的 OAuth/认证信息。
        Params:
            user_id: 用户 ID
            platform: 平台名 (csdn / cnblogs / jianshu / wordpress)
            credential: 认证凭证(token/cookie)
        """

    def remove_platform_auth(self, user_id: int, platform: str) -> bool:
        """
        Description:
            删除某平台认证。
        Params:
            user_id: 用户 ID
            platform: 平台名
        Return:
            True / False
        """

    def list_platform_auths(self, user_id: int) -> List[str]:
        """
        Description:
            列出用户已绑定的全部平台。
        Params:
            user_id: 用户 ID
        Return:
            ['csdn', 'cnblogs', ...]
        """

    def get_platform_credential(self, user_id: int, platform: str) -> Optional[str]:
        """
        Description:
            获取某平台的认证凭证。
        Params:
            user_id: 用户 ID
            platform: 平台名
        Return:
            credential 或 None
        """
```

---

# ## 📝 PostDAO（文章数据访问层）
```python
class PostDAO(ABC):

    def create_post(self, owner_id: int, cid: str, date: str=None) -> None:
        """
        Description:
            创建一篇文章（date 必须为 YYYY-MM-DD）。
        Params:
            owner_id: 用户 ID
            cid: 唯一文章编号
            date: YYYY-MM-DD
        """

    def update_field(self, cid: str, field: str, value: str) -> bool:
        """
        Description:
            更新文章字段。
        Params:
            cid: 文章 CID
            field: 要更新的字段
                   context / title / date / description / catagory
            value: 新值（字符串）
        Return:
            True / False
        """

    def get_field(self, cid: str, field: str) -> Optional[Any]:
        """
        Description:
            获取文章的某个字段。
        Params:
            cid: 文章 CID
            field: 字段名（context/title/date/description/catagory）
        Return:
            Any
        """

    def delete_post(self, cid: str) -> bool:
        """
        Description:
            删除文章。
        Params:
            cid: 文章 CID
        Return:
            True / False
        """

    def list_posts(self, offset: int, limit: int, orderby=None) -> List[str]:
        """
        Description:
            列出文章列表。
        Params:
            offset: 起始偏移量
            limit: 返回数量
            orderby: 排序字段（可为 None）
        Return:
            [cid1, cid2, ...]
        """

    def search_posts(self, keyword: str) -> List[str]:
        """
        Description:
            按关键字搜索文章。
            匹配顺序优先：title > description > context
        Params:
            keyword: 搜索关键字
        Return:
            匹配到的 CID 列表
        """
```

---

# ## 🔗 PostReferenceDAO（文章引用管理）

```python
class PostReferenceDAO(ABC):

    def add_reference(self, post_cid: str, ref_cid: str) -> None:
        """
        Description:
            添加引用（post_cid 引用 ref_cid）。
        Params:
            post_cid: 当前文章
            ref_cid: 被引用文章
        """

    def remove_reference(self, post_cid: str, ref_cid: str) -> None:
        """
        Description:
            删除引用关系。
        Params:
            post_cid: 源文章
            ref_cid: 引用目标文章
        """

    def list_references(self, post_cid: str) -> List[str]:
        """
        Description:
            列出这篇文章引用的所有文章 CID。
        Params:
            post_cid: 文章 CID
        Return:
            ['cid1', 'cid2', ...]
        """
```

