# Bug Laws

> Candidate engineering laws recovered from `github.com/pallets/click`.
> Every law is evidence-linked and requires human review before becoming project policy.

## Scan summary

- Commits seen: `807`
- Fix candidates inspected: `80`
- Candidate laws: `28`
- Repeated laws: `2`
- Fixes without test changes: `5`

## LAW-001 — Fish multiline help complete

- Confidence: `80%` — candidate law, human review required
- Recurrence: `3` fix commit(s)
- Test protection: `3` protected / `0` unprotected
- Affected files: `src/click/shell_completion.py`

### Evidence

- `19fd4d6e18` (2026-04-30): Fix: Ensure fish completion handles multiline help strings correctly (#3126)
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `guard:if test $metadata[3] != "_";`, `test:test_fish_multiline_help_complete`, `guard:assert result.exit_code == 0`, `guard:if lines[i] == "plain" and lines[i + 1] in ("--at", "--attachment-type"):`
- `b7e5fd4cc7` (2026-05-23): Fix broken fish completion and multiline help string
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `guard:if item.help:`
- `c3535905c7` (2026-05-23): Fix broken fish completion and multiline help string
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `guard:if item.help:`

## LAW-002 — Flag value optional behavior

- Confidence: `93%` — candidate law, human review required
- Recurrence: `2` fix commit(s)
- Test protection: `2` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `4fd2fea0db` (2025-05-20): Fix condition for setting flag value when type is provided
  - Source: `src/click/core.py`
  - Tests: `tests/test_options.py`
  - Signals: `guard:if is_flag and flag_value is None:`, `test:test_flag_value_is_correctly_set`, `guard:assert result.output == f"{expected}\n"`, `test:test_non_flag_with_non_negatable_default`
- `91de59c6c8` (2025-10-07): Fix #3084: Correct flag optional value behavior and add comprehensive tests
  - Source: `src/click/core.py`
  - Tests: `tests/test_options.py`
  - Signals: `test:test_flag_value_optional_behavior`, `guard:assert result.exit_code == 0`, `guard:assert result.output == "Hello, Flag!\n"`, `test:test_flag_value_with_type_conversion`

## LAW-003 — Full prompt passed to readline

- Confidence: `95%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/termui.py`

### Evidence

- `2468b70997` (2026-04-29): Fix readline backspace/line-wrapping on linux (#2969)
  - Source: `src/click/termui.py`
  - Tests: `tests/test_utils.py`
  - Signals: `guard:if WIN:`, `guard:if err:`, `guard:assert out == "\ninterrupted\n"`, `test:test_full_prompt_passed_to_readline`

## LAW-004 — Zsh full complete with colons

- Confidence: `95%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/shell_completion.py`

### Evidence

- `a1235aacb1` (2025-07-21): Fix Zsh completions with colons (#2846)
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `test:test_zsh_full_complete_with_colons`, `guard:assert result.output == expect`

## LAW-005 — Version option resolves import name to distribution

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/decorators.py`

### Evidence

- `bec59289d8` (2026-06-11): Fix `package_name` resolution when top-level module differs from distribution name
  - Source: `src/click/decorators.py`
  - Tests: `tests/test_basic.py`
  - Signals: `guard:if len(distributions) == 1:`, `guard:elif len(distributions) > 1:`, `guard:raise RuntimeError(`, `guard:raise RuntimeError(`

## LAW-006 — Choice argument optional metavar

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `762c97eef7` (2026-06-10): Fix double-bracketing of choices in synopsis
  - Source: `src/click/core.py`
  - Tests: `tests/test_basic.py`
  - Signals: `guard:if not self.required and not already_bracketed:`, `test:test_choice_argument_optional_metavar`, `guard:assert "Usage: cli-variadic [OPTIONS] [foo|bar|baz]...\n" in variadic`, `guard:assert "[[foo|bar|baz]]" not in variadic`

## LAW-007 — Echo via pager yields before exception

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/_compat.py`

### Evidence

- `7eb57cff7c` (2026-05-22): Fix pager test race by raising before yield
  - Source: `src/click/_compat.py`
  - Tests: `tests/test_stream_lifecycle.py`, `tests/test_utils.py`
  - Signals: `guard:raise RuntimeError("This is a test.")`, `test:test_echo_via_pager_yields_before_exception`, `guard:assert "".join(writes) == "test", (`, `test:test_stress_echo_via_pager_exception_cleanup`

## LAW-008 — Deprecated empty help no leading space

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `82f377c547` (2026-05-23): Fix deprecated label formatting
  - Source: `src/click/core.py`
  - Tests: `tests/test_commands.py`, `tests/test_options.py`
  - Signals: `test:test_deprecated_empty_help_no_leading_space`, `guard:assert "\n  (DEPRECATED" in out`, `guard:assert "\n   (DEPRECATED" not in out`, `test:test_deprecated_empty_help_no_leading_space`

## LAW-009 — Parameter source during paramtype convert

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `7d05a59b9d` (2026-05-19): Fix get_parameter_source() during type conversion and eager callbacks
  - Source: `src/click/core.py`
  - Tests: `tests/test_defaults.py`, `tests/test_options.py`
  - Signals: `guard:elif existing_source is not None:`, `test:test_parameter_source_during_paramtype_convert`, `guard:assert not result.exception`, `guard:assert "default: {'value': '/tmp/file', 'source': " in result.output`

## LAW-010 — Help formatter write usage

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/formatting.py`

### Evidence

- `0551bf5358` (2026-05-16): Fix `HelpFormatter.write_usage` producing spurious characters
  - Source: `src/click/formatting.py`
  - Tests: `tests/test_formatting.py`
  - Signals: `guard:if not args:`, `test:test_help_formatter_write_usage`, `guard:if prefix is None:`, `guard:assert f.getvalue() == expected`

## LAW-011 — Bool flag group competition

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `0f71fe771c` (2026-05-15): Fix dual-option arbitration to respect explicit defaults
  - Source: `src/click/core.py`
  - Tests: `tests/test_options.py`
  - Signals: `guard:if is_winner:`, `guard:if self.expose_value:`, `guard:elif existing_source is None:`, `test:test_bool_flag_group_competition`

## LAW-012 — Hide input error message

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/termui.py`

### Evidence

- `a09c1c655e` (2026-03-11): fix: show custom error message in prompt with hide_input=True
  - Source: `src/click/termui.py`
  - Tests: `tests/test_termui.py`
  - Signals: `guard:if repr_val in e.message:`, `guard:elif value in e.message:`, `guard:if len(value) < 4:`, `guard:if value == "bad":`

## LAW-013 — Show default with empty string

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `d340b0c120` (2026-04-01): Fix speculative speculative empty string check
  - Source: `src/click/core.py`
  - Tests: `tests/test_options.py`
  - Signals: `guard:elif isinstance(default_value, str) and default_value == "":`, `guard:if isinstance(other, str):`, `guard:raise ValueError("cannot compare to string")`, `test:test_show_default_with_empty_string`

## LAW-014 — Default map with callable flag value

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `546f2851f4` (2026-02-21): Fix callable ``flag_value`` being instantiated when used as a default
  - Source: `src/click/core.py`
  - Tests: `tests/test_defaults.py`, `tests/test_options.py`
  - Signals: `guard:if value is True and self.is_flag:`, `guard:elif call and callable(value):`, `test:test_default_map_with_callable_flag_value`, `guard:if default_map is not None:`

## LAW-015 — Shared param prefers first default

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `1c20dc6e72` (2025-09-22): Fix default handling to defer UNSET normalization
  - Source: `src/click/core.py`
  - Tests: `tests/test_defaults.py`
  - Signals: `guard:if value is UNSET:`, `test:test_shared_param_prefers_first_default`, `guard:assert "green" in result.output`, `guard:assert "red" in result.output`

## LAW-016 — Choice default rendering

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`, `src/click/exceptions.py`, `src/click/shell_completion.py`, `src/click/testing.py`

### Evidence

- `e252437313` (2025-07-22): Revert "Revert "Merge Stable into master""
  - Source: `src/click/core.py`, `src/click/exceptions.py`, `src/click/shell_completion.py`, `src/click/testing.py`
  - Tests: `tests/test_options.py`, `tests/test_shell_completion.py`, `tests/test_testing.py`
  - Signals: `guard:elif isinstance(default_value, enum.Enum):`, `guard:if sys.version_info < (3, 11):`, `guard:assert (`, `test:test_choice_default_rendering`

## LAW-017 — Nested group

- Confidence: `90%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/shell_completion.py`

### Evidence

- `ac6a2acfdb` (2025-05-12): Fix shell completion for nested groups
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `test:test_nested_group`, `guard:assert _get_words(cli, [], "") == ["get"]`, `guard:assert _get_words(cli, ["get"], "") == ["full"]`, `guard:assert _get_words(cli, ["get", "full"], "") == ["data"]`

## LAW-018 — Required behavior: completions for quoted/escaped parameters in Fish

- Confidence: `78%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/shell_completion.py`

### Evidence

- `701b313160` (2025-08-09): Fix completions for quoted/escaped parameters in Fish (#3013)
  - Source: `src/click/shell_completion.py`
  - Tests: `tests/test_shell_completion.py`
  - Signals: `guard:if incomplete:`

## LAW-019 — Required behavior: rendering when `prompt_suffix` is empty

- Confidence: `73%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/termui.py`

### Evidence

- `812b8000f7` (2025-07-28): Fix rendering when `prompt_suffix` is empty
  - Source: `src/click/termui.py`
  - Tests: `tests/test_utils.py`
  - Signals: `guard:assert out == "Prompt to stdin with no suffix"`, `guard:assert err == ""`, `guard:assert out == "x"`, `guard:assert err == "Prompt to stderr with no suffi"`

## LAW-020 — Required behavior: merge Stable into master

- Confidence: `73%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`, `src/click/exceptions.py`, `src/click/shell_completion.py`, `src/click/testing.py`

### Evidence

- `8bc9127107` (2025-07-22): Revert "Merge Stable into master"
  - Source: `src/click/core.py`, `src/click/exceptions.py`, `src/click/shell_completion.py`, `src/click/testing.py`
  - Tests: `tests/test_options.py`, `tests/test_shell_completion.py`, `tests/test_testing.py`
  - Signals: `guard:return f"{item.type}\n{item.value}\n{item.help if item.help else '_'}"`, `guard:assert f"[{'|'.join([str(i) for i in choices])}]" in result.output`, `guard:assert err.getvalue() == b"\\udce2"`, `guard:assert err.getvalue() == b"\\udce2"`

## LAW-021 — Required behavior: reconciliation of envvar with default, flag_value and type parameters for flag options

- Confidence: `73%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/core.py`, `src/click/types.py`

### Evidence

- `9caedb9206` (2025-05-28): Fix reconciliation of envvar with default, flag_value and type parameters for flag options
  - Source: `src/click/core.py`, `src/click/types.py`
  - Tests: `tests/test_arguments.py`, `tests/test_basic.py`, `tests/test_imports.py`, `tests/test_options.py`
  - Signals: `guard:elif self.secondary_opts:`, `guard:if is_flag:`, `guard:if self.default is None and not self.required and not self.prompt:`, `guard:if multiple:`

## LAW-022 — Required behavior: testing/CliRunner: Fix regression related to EOF introduced in 262bdf0

- Confidence: `73%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/testing.py`

### Evidence

- `93c6966eb3` (2025-05-22): testing/CliRunner: Fix regression related to EOF introduced in 262bdf0
  - Source: `src/click/testing.py`
  - Tests: `tests/test_chain.py`
  - Signals: `guard:except StopIteration as e:`, `guard:raise EOFError() from e`, `guard:except StopIteration as e:`, `guard:raise EOFError() from e`

## LAW-023 — Required behavior: skip flaky pager test on macOS with free-threaded Python 3.14t

- Confidence: `63%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `1` protected / `0` unprotected
- Affected files: `src/click/_compat.py`

### Evidence

- `d15f3c23a1` (2026-05-18): fix: Skip flaky pager test on macOS with free-threaded Python 3.14t
  - Source: `src/click/_compat.py`
  - Tests: `tests/test_utils.py`

## LAW-024 — Required behavior: sentinel typing and its uses in parser

- Confidence: `60%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `0` protected / `1` unprotected
- Affected files: `src/click/_utils.py`, `src/click/core.py`, `src/click/parser.py`

### Evidence

- `73e1550065` (2026-05-04): Fix sentinel typing and its uses in parser (#3396)
  - Source: `src/click/_utils.py`, `src/click/core.py`, `src/click/parser.py`
  - Tests: **missing in this fix**
  - Signals: `guard:if spos is None:`

## LAW-025 — Required behavior: `_termui_impl.open_url()` — 'start' on Windows is a cmd built-in, not an executable

- Confidence: `60%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `0` protected / `1` unprotected
- Affected files: `src/click/_termui_impl.py`

### Evidence

- `c5cced7b30` (2026-04-30): fix: `_termui_impl.open_url()` — 'start' on Windows is a cmd built-in, not an executable (#3186)
  - Source: `src/click/_termui_impl.py`
  - Tests: **missing in this fix**
  - Signals: `guard:except OSError:`, `guard:except OSError:`

## LAW-026 — Required behavior: ruff E501 line-too-long in PowerShell template

- Confidence: `55%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `0` protected / `1` unprotected
- Affected files: `src/click/shell_completion.py`

### Evidence

- `1ac08db953` (2026-06-26): Fix ruff E501 line-too-long in PowerShell template
  - Source: `src/click/shell_completion.py`
  - Tests: **missing in this fix**
  - Signals: `guard:if ($_.PSIsContainer) { $kind = 'ProviderContainer' }`

## LAW-027 — Required behavior: generic typed dict `TypeError` on Python 3.10

- Confidence: `55%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `0` protected / `1` unprotected
- Affected files: `src/click/types.py`

### Evidence

- `9a2d169fcf` (2026-05-18): fix generic typed dict `TypeError` on Python 3.10
  - Source: `src/click/types.py`
  - Tests: **missing in this fix**
  - Signals: `guard:if t.TYPE_CHECKING:`, `guard:if t.TYPE_CHECKING:`, `guard:if t.TYPE_CHECKING:`

## LAW-028 — Required behavior: use `default=True` as a sentinel for non-boolean flags

- Confidence: `55%` — candidate law, human review required
- Recurrence: `1` fix commit(s)
- Test protection: `0` protected / `1` unprotected
- Affected files: `src/click/core.py`

### Evidence

- `bb7be1f6a9` (2026-03-02): Revert "Use `default=True` as a sentinel for non-boolean flags"
  - Source: `src/click/core.py`
  - Tests: **missing in this fix**
  - Signals: `guard:if value is True and self.is_flag:`
