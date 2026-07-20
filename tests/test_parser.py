from bid_screenshot_assistant.services.parser import parse_query_names


def test_parse_query_names_removes_prefixes_and_duplicates():
    result = parse_query_names("1. 项目A\n2、项目B\n项目A\n；\n（三）项目C")
    assert result.names == ["项目A", "项目B", "项目C"]
    assert result.duplicates == ["项目A"]
