from opspectre._ui import Console, OutputMode, _exit


class TestStripMarkup:
    def test_no_tags(self):
        c = Console()
        assert c._strip_markup("hello world") == "hello world"

    def test_simple_tag(self):
        c = Console()
        assert c._strip_markup("[red]error[/]") == "error"

    def test_nested_tags(self):
        c = Console()
        assert c._strip_markup("[bold][red]alert[/][/]") == "alert"

    def test_tag_with_space(self):
        c = Console()
        assert c._strip_markup("[dim yellow]warning[/]") == "warning"

    def test_nothing_to_strip(self):
        c = Console()
        assert c._strip_markup("plain text") == "plain text"

    def test_mixed_content(self):
        c = Console()
        result = c._strip_markup("[green]Sandbox started[/]  container-name")
        assert result == "Sandbox started  container-name"


class TestConsolePrint:
    def test_print_strips_tags(self, capsys):
        c = Console()
        c.print("[bold]hello[/]")
        captured = capsys.readouterr()
        assert captured.out == "hello\n"

    def test_print_plain(self, capsys):
        c = Console()
        c.print("plain")
        captured = capsys.readouterr()
        assert captured.out == "plain\n"


class TestOutputMode:
    def test_default_false(self):
        mode = OutputMode()
        assert mode.json_output is False

    def test_set_json(self):
        mode = OutputMode()
        mode.json_output = True
        assert mode.json_output is True


class TestExit:
    def test_exit_calls_sys_exit(self):
        import sys
        from unittest.mock import patch
        with patch.object(sys, "exit") as mock_exit:
            _exit(0)
        mock_exit.assert_called_once_with(0)

    def test_exit_with_code(self):
        import sys
        from unittest.mock import patch
        with patch.object(sys, "exit") as mock_exit:
            _exit(42)
        mock_exit.assert_called_once_with(42)
