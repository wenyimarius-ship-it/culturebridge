from cb_config import configuration_issue

URL = "https://crgfsrfxnwyjcjgmvpjr.supabase.co"


def test_rejects_markdown_urls_wrong_projects_and_browser_keys():
    for url in [URL + "`", URL + "/rest/v1", "https://other.supabase.co", " " + URL]:
        assert configuration_issue(url, "sb_secret_example") == "invalid_url"
    for key in ["sb_publishable_example", "replace-me", "sb_secret_example "]:
        assert configuration_issue(URL, key) == "invalid_server_key"
    assert configuration_issue(URL, "sb_secret_example") is None
