# -------------------------------
# 用户注册与登录接口
# -------------------------------

def register(username: str, password: str, email: str = None) -> bool:
    """
    注册新用户
    :param username: 用户名
    :param password: 密码
    :param email: 可选邮箱
    :return: 注册是否成功
    """

def login(username: str, password: str) -> str:
    """
    用户登录
    :param username: 用户名
    :param password: 密码
    :return: 登录成功返回token，失败返回空字符串或异常
    """

def logout(token: str) -> bool:
    """
    用户登出
    :param token: 用户登录凭证
    :return: 是否成功登出
    """

# -------------------------------
# 用户信息管理接口
# -------------------------------

def get_user_info(token: str) -> dict:
    """
    获取用户信息
    :param token: 登录凭证
    :return: 用户信息字典
    """

def update_user_info(token: str, **kwargs) -> bool:
    """
    更新用户信息
    :param token: 登录凭证
    :param kwargs: 可更新字段，例如 email, nickname, avatar_url
    :return: 是否更新成功
    """

def change_password(token: str, old_password: str, new_password: str) -> bool:
    """
    修改用户密码
    :param token: 登录凭证
    :param old_password: 旧密码
    :param new_password: 新密码
    :return: 是否修改成功
    """

# -------------------------------
# 密码与安全相关接口
# -------------------------------

# def reset_password_request(email: str) -> bool:
#     """
#     请求重置密码（发送邮件或短信验证码）
#     :param email: 用户绑定的邮箱
#     :return: 是否成功发送重置请求
#     """

# def reset_password(token: str, new_password: str) -> bool:
#     """
#     使用重置凭证修改密码
#     :param token: 重置密码的临时token
#     :param new_password: 新密码
#     :return: 是否重置成功
#     """

# def verify_email(token: str) -> bool:
#     """
#     验证用户邮箱
#     :param token: 邮箱验证token
#     :return: 是否验证成功
#     """

# def send_verification_code(contact: str) -> bool:
#     """
#     发送验证码到邮箱或手机号
#     :param contact: 邮箱或手机号
#     :return: 是否发送成功
#     """

# def verify_code(contact: str, code: str) -> bool:
#     """
#     验证收到的验证码
#     :param contact: 邮箱或手机号
#     :param code: 验证码
#     :return: 是否验证成功
#     """


def verify_login(token: str) -> bool:
    """
    验证用户登录状态
    :param token: 用户登录凭证（token）
    :return: 如果 token 有效且用户在线返回 True，否则返回 False
    所有请求都要经过这个函数验证
    """
