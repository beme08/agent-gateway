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
    assert set(tags) == {"public", "hr_policy", "manager_only", "executive"}


def test_unknown_role_defaults_to_public():
    assert accessible_tags("ghost") == ["public"]
