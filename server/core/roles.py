"""角色常量与权限辅助"""
ROOT_ROLE = "root"
ADMIN_ROLE = "admin"
ADMIN_PANEL_ROLES = frozenset({ADMIN_ROLE, ROOT_ROLE})


def is_admin_panel_role(role: str) -> bool:
    """是否可访问管理后台（普通管理员或 root）"""
    return role in ADMIN_PANEL_ROLES


def expand_required_roles(*roles: str) -> frozenset:
    """展开角色守卫：root 继承 admin 权限"""
    expanded = set(roles)
    if ADMIN_ROLE in expanded:
        expanded.add(ROOT_ROLE)
    return frozenset(expanded)
