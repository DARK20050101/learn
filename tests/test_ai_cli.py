from app.cli.ai import _provider_name, configuration_report


def test_provider_name_detects_deepseek() -> None:
    assert _provider_name("https://api.deepseek.com") == "DeepSeek"


def test_configuration_report_never_contains_api_key() -> None:
    report = configuration_report()

    assert "api_key" not in report
    assert "api_key_configured" in report
