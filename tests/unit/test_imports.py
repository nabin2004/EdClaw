def test_import_settings():
    from educlaw.config.settings import load_settings

    s = load_settings()
    assert s.app_name == "educlaw"


def test_import_autocourse_autolecture() -> None:
    import educlaw.autocourse  # noqa: PLC0415
    import educlaw.autolecture  # noqa: PLC0415

    assert educlaw.autocourse.run_autocourse
    assert educlaw.autolecture.generate_lecture


def test_strict_local():
    from educlaw.config.strict_local import assert_strict_local

    assert_strict_local("http://127.0.0.1:11434")
