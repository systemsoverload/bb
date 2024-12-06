from bb.core.config import BBConfig


def test_config_update_does_not_clobber():
    # Updating config values should leave adjacent keys untouched
    conf = BBConfig()

    conf.update("auth.username", "tj_kells")
    conf.update("auth.app_password", "1234")

    conf.update("arbitrary.setting", "456")

    assert conf._conf["auth"]["app_password"] == "1234"
    assert conf._conf["auth"]["username"] == "tj_kells"
    assert conf._conf["arbitrary"]["setting"] == "456"


def test_config_update_new_keys():
    conf = BBConfig()
    conf.update("foo", "bar")
    conf.update("foo", "baz")

    assert conf._conf["foo"] == "baz"


def test_config_get():
    conf = BBConfig()

    conf.update("auth.username", "tj_kells")
    conf.update("auth.app_password", "1234")
    conf.update("foo", "bar")

    assert conf.get("foo") == "bar"
    assert conf.get("auth.username") == "tj_kells"
    assert conf.get("auth.app_password") == "1234"


def test_config_delete():
    conf = BBConfig()

    conf.update("auth.username", "tj_kells")
    conf.update("auth.app_password", "1234")

    assert conf._conf["auth"]["username"] == "tj_kells"

    conf.delete("auth.username")

    assert conf._conf["auth"]["app_password"] == "1234"

    conf.delete("auth")

    assert conf._conf.get("auth", None) is None
