def test_import_settings():
    from educlaw.config.settings import load_settings

    s = load_settings()
    assert s.app_name == "educlaw"


def test_import_autocourse_autolecture() -> None:
    import educlaw.autocourse  # noqa: PLC0415
    import educlaw.autolecture  # noqa: PLC0415

    assert educlaw.autocourse.run_autocourse
    assert educlaw.autolecture.generate_lecture


def test_import_tts() -> None:
    import educlaw.tts  # noqa: PLC0415

    assert educlaw.tts.build_backend
    assert educlaw.tts.known_backends


def test_import_viz() -> None:
    from educlaw.viz import scene_class_name, syntax_ok

    assert scene_class_name("class A(Scene):\n  pass") == "A"
    assert syntax_ok("class A(Scene):\n  def construct(self):\n    pass\n")


def test_import_automanim() -> None:
    import educlaw.automanim  # noqa: PLC0415

    assert callable(educlaw.automanim.run_automanim)


def test_strict_local():
    from educlaw.config.strict_local import assert_strict_local

    assert_strict_local("http://127.0.0.1:11434")
