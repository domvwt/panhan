import dataclasses as dc
import inspect
from pathlib import Path
from typing import Any

from panhan.logger import logdec


@dc.dataclass
class DocumentConfig:
    """Document format configuration data."""

    use_preset: str | None = None
    output_format: str | None = None
    output_file: Path | None = None
    variables: dict[str, Any] = dc.field(default_factory=dict)
    cli_args: dict[str, Any] = dc.field(default_factory=dict)
    filters: dict[str, bool] = dc.field(default_factory=dict)

    @logdec
    def combine(self, other: "DocumentConfig") -> "DocumentConfig":
        """Combine config values of `self` with `other`.

        If config keys are present in both objects, `self` will take precedence.

        Args:
            other (DocumentConfig): another document config object.

        Returns:
            DocumentConfig: combined document config.
        """
        use_preset = self.use_preset or other.use_preset
        output_format = self.output_format or other.output_format
        output_file = self.output_file or other.output_file
        variables = {**other.variables, **self.variables}
        cli_args = {**other.cli_args, **self.cli_args}
        filters = {**other.filters, **self.filters}

        return DocumentConfig(
            use_preset=use_preset,
            output_format=output_format,
            output_file=output_file,
            variables=variables,
            cli_args=cli_args,
            filters=filters,
        )

    @classmethod
    @logdec
    def from_dict(cls, dict_: dict[str, Any]) -> "DocumentConfig":
        """Create `DocumentConfig` from dictionary.

        Args:
            dict_ (dict[str, Any]): input dictionary.

        Returns:
            DocumentConfig: document config.
        """
        valid_keys = [
            key
            for key in inspect.signature(cls.__init__).parameters.keys()
            if key != "self"
        ]
        invalid_keys = sorted(set(dict_.keys()).difference(valid_keys))
        if invalid_keys:
            msg = f"Unexpected key(s) in document config: {invalid_keys}. Valid keys are: {valid_keys}."
            raise KeyError(msg)
        return DocumentConfig(**dict_)

    @logdec
    def to_pypandoc_kwargs(self) -> dict[str, Any]:
        """Translate `DocumentConfig` to dictionary of kwargs for pypandoc.

        Args:
            panhan_config (AppConfig): panhan config object.

        Returns:
            dict[str, Any]: translated kwarg dict.
        """
        extra_args = [
            arg
            for arg in [
                *cli_args_dict_to_list(self.cli_args),
                *variables_dict_to_list(self.variables),
            ]
            if arg
        ]

        pypandoc_kwargs = {
            "to": self.output_format,
            "outputfile": self.output_file,
            "extra_args": extra_args,
            "filters": self.filters,
        }

        return pypandoc_kwargs


@dc.dataclass(init=False)
class PanhanFrontmatter:
    """Config from source file frontmatter."""

    document_config_list: list[DocumentConfig]

    def __init__(self, document_configs: list[dict[str, Any]]) -> None:
        self.document_config_list = [
            DocumentConfig.from_dict(config) for config in document_configs
        ]


@dc.dataclass
class AppConfig:
    """Panhan application config data."""

    presets: dict[str, Any]
    pandoc_path: str | None

    @logdec
    def get_preset(
        self, preset_name: str, default: None | DocumentConfig = None
    ) -> DocumentConfig:
        """Get settings for `preset_name` from user presets.

        If `preset_name` is not found and default is not provided application will error and close.

        Args:
            preset_name (str): name of preset stored in panhan.yaml.
            default (None | DocumentConfig, optional): returned if `preset_name` not found. Defaults to None.

        Returns:
            DocumentConfig: document settings for `preset_name` or `default` if not found.
        """
        if preset_name in self.presets:
            doc_config = DocumentConfig.from_dict(self.presets[preset_name])
            if doc_config.use_preset:
                parent = self.get_preset(doc_config.use_preset)
                doc_config = doc_config.combine(parent)
            return doc_config
        if default:
            return default

        available_presets = list(self.presets.keys())
        msg = (
            f"Preset not found: '{preset_name}'. Available presets: {available_presets}"
        )
        raise KeyError(msg)

    @logdec
    def get_default_preset(self) -> DocumentConfig:
        """Get default preset config if defined.

        Returns empty `DocumentConfig` if `default` is not defined.

        Returns:
            DocumentConfig: document config object.
        """
        return self.get_preset("default", DocumentConfig())


DocumentConfigDict = dict[str, DocumentConfig]

ARG_DELIMITER = "<delimiter>"


@logdec
def variables_dict_to_list(variables_dict: dict[str, Any]) -> list[str]:
    """Transform `variables_dict` to list of command line arguments for pypandoc.

    Args:
        variables_dict (dict[str, Any]): dictionary of pandoc template variable parameters.

    Returns:
        list[str]: list of strings like ["-V", "variable", "value", ...]
    """
    delimiter = ARG_DELIMITER
    variables = delimiter.join(
        f'-V{delimiter}{key}="{value}"' for key, value in variables_dict.items()
    ).split(delimiter)
    return variables


def format_flag(flag: str) -> str:
    """Prepend correct number of dashes to CLI option `flag`.

    Single letter flags have one '-', all others have '--'.

    Args:
        flag (str): command line flag.

    Returns:
        str: modified flag.
    """
    flag = flag.replace("_", "-")
    return f"--{flag}" if len(flag) > 1 else f"-{flag}"


def format_value(value: Any) -> Any:
    """Add quotes around value if it contains spaces.

    Args:
        value (Any): command line value.

    Returns:
        Any: modified value.
    """
    if isinstance(value, str):
        value = value.strip()
        return f'"{value}"' if " " in value else value
    return value


@logdec
def cli_args_dict_to_list(cli_args_dict: dict[str, Any]) -> list[str]:
    """Transform dict of CLI args to list for pypandoc.

    `cli_args_dict` should take format `{"arg": <value>}`.

    If <value> is `True` the arg will be returned with no corresponding value.
    If <value> is `False` the arg will be suppressed.
    All other values will be cast to string.

    Args:
        cli_args_dict (dict[str, Any]): dictionary of CLI args and values.

    Returns:
        list[str]: CLI args as list of strings.
    """
    cli_args_filtered = {
        key: value for key, value in cli_args_dict.items() if value is not False
    }
    delimiter = ARG_DELIMITER
    cli_args_list = delimiter.join(
        f"{format_flag(flag)}{delimiter}{format_value(value)}"
        if not isinstance(value, bool)
        else f"{format_flag(flag)}"
        for flag, value in cli_args_filtered.items()
        if value is not False
    ).split(delimiter)
    return cli_args_list
