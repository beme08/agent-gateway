from app.rag.retrieve import accessible_tags


def test_viewer_only_public():
    assert accessible_tags("viewer") == ["public"]


def test_employee_includes_hr_policy():
    tags = accessible_tags("employee")
    assert "public" in tags
    assert "hr_policy" in tags
    assert "executive" not in tags


def test_manager_includes_manager_only():
    tags = accessible_tags("manager")
    assert "manager_only" in tags
    assert "executive" not in tags


def test_admin_has_all_tags():
    tags = accessible_tags("admin")
    assert set(tags) == {"public", "hr_policy", "support_kb", "manager_only", "executive"}


def test_support_kb_visible_to_employee_and_above():
    assert "support_kb" not in accessible_tags("viewer")
    assert "support_kb" in accessible_tags("employee")
    assert "support_kb" in accessible_tags("manager")


def test_unknown_role_defaults_to_public():
    assert accessible_tags("ghost") == ["public"]
