import sys
from unittest.mock import patch

from opspectre._ui import Console, _exit


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

    def test_mixed_content(self):
        c = Console()
        result = c._strip_markup("[green]Sandbox started[/]  container-name")
        assert result == "Sandbox started  container-name"

    def test_unclosed_tag(self):
        c = Console()
        assert c._strip_markup("[bold]still visible") == "still visible"

    def test_multiple_tags(self):
        c = Console()
        assert c._strip_markup("[red]a[/] [green]b[/] [blue]c[/]") == "a b c"

    def test_brackets_not_tags(self):
        c = Console()
        assert c._strip_markup("[not a tag") == "[not a tag"

    def test_empty_string(self):
        c = Console()
        assert c._strip_markup("") == ""


class TestConsoleOutput:
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

    def test_success_strips_tags(self, capsys):
        c = Console()
        c.success("[green]done[/]")
        captured = capsys.readouterr()
        assert captured.out == "done\n"

    def test_error_strips_tags(self, capsys):
        c = Console()
        c.error("[red]fail[/]")
        captured = capsys.readouterr()
        assert captured.out == "fail\n"

    def test_warning_strips_tags(self, capsys):
        c = Console()
        c.warning("[yellow]caution[/]")
        captured = capsys.readouterr()
        assert captured.out == "caution\n"

    def test_info_strips_tags(self, capsys):
        c = Console()
        c.info("[blue]note[/]")
        captured = capsys.readouterr()
        assert captured.out == "note\n"

    def test_dim_strips_tags(self, capsys):
        c = Console()
        c.dim("[dim]quiet[/]")
        captured = capsys.readouterr()
        assert captured.out == "quiet\n"

    def test_print_custom_end(self, capsys):
        c = Console()
        c.print("no newline", end="")
        captured = capsys.readouterr()
        assert captured.out == "no newline"


class TestExit:
    def test_exit_calls_sys_exit_with_code(self):
        with patch.object(sys, "exit") as mock_exit:
            _exit(0)
        mock_exit.assert_called_once_with(0)

    def test_exit_default_code_is_1(self):
        with patch.object(sys, "exit") as mock_exit:
            _exit()
        mock_exit.assert_called_once_with(1)
