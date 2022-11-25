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
    metadata: dict[str, Any] = dc.field(default_factory=dict)
    pandoc_args: dict[str, Any] = dc.field(default_factory=dict)
    filters: dict[str, bool] = dc.field(default_factory=dict)

    @logdec
    def combine(self, other: "DocumentConfig") -> "DocumentConfig":
        """Combine config values of `self` with `other`.

        If config keys are present in both objects, `self` will take precedence.

        Args:
            other: another document config object.

        Returns:
            combined document config.
        """
        use_preset = self.use_preset or other.use_preset
        output_format = self.output_format or other.output_format
        output_file = self.output_file or other.output_file
        metadata = {**other.metadata, **self.metadata}
        pandoc_args = {**other.pandoc_args, **self.pandoc_args}
        filters = {**other.filters, **self.filters}

        return DocumentConfig(
            use_preset=use_preset,
            output_format=output_format,
            output_file=output_file,
            metadata=metadata,
            pandoc_args=pandoc_args,
            filters=filters,
        )

    @classmethod
    @logdec
    def from_dict(cls, dict_: dict[str, Any]) -> "DocumentConfig":
        """Create config from dictionary.

        Args:
            dict_: input dictionary.

        Returns:
            document config.
        """
        valid_keys = [
            key
            for key in inspect.signature(cls.__init__).parameters.keys()
            if key != "self"
        ]
        invalid_keys = sorted(set(dict_.keys()).difference(valid_keys))
        if invalid_keys:
            msg = f"Unexpected key(s) in config: {invalid_keys}. Valid keys are: {valid_keys}."
            raise KeyError(msg)
        return DocumentConfig(**dict_)

    @logdec
    def get_pypandoc_kwargs(self) -> dict[str, Any]:
        """Get dictionary of kwargs for pypandoc.

        Returns:
            kwarg dict.
        """
        extra_args = [
            arg
            for arg in pandoc_args_dict_to_list(self.pandoc_args)
            if arg
        ]

        filters = pandoc_filter_dict_to_list(self.filters)

        pypandoc_kwargs = {
            "to": self.output_format,
            "outputfile": self.output_file,
            "extra_args": extra_args,
            "filters": filters,
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
class BaseConfig:
    """Base config data."""

    presets: dict[str, Any]
    pandoc_path: str | None

    @logdec
    def get_preset(
        self, preset_name: str, default: None | DocumentConfig = None
    ) -> DocumentConfig:
        """Get settings for `preset_name` from user presets.

        If `preset_name` is not found and default is not provided, the application will error and close.

        Args:
            preset_name: name of preset stored in panhan.yaml.
            default: returned if `preset_name` not found. Defaults to None.

        Returns:
            document settings for `preset_name` or `default` if not found.
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
            f"Preset value not found: '{preset_name}'. Available presets: {available_presets}"
        )
        raise KeyError(msg)

    @logdec
    def get_default_preset(self) -> DocumentConfig:
        """Get default preset config if defined.

        Returns empty config if `default` is not defined.

        Returns:
            document config object.
        """
        return self.get_preset("default", DocumentConfig())


DocumentConfigDict = dict[str, DocumentConfig]

ARG_DELIMITER = "<delimiter>"


def format_flag(flag: str) -> str:
    """Prepend correct number of dashes to CLI option `flag`.

    Single letter flags have one '-', all others have '--'.

    Args:
        flag: command line flag.

    Returns:
        modified flag.
    """
    flag = flag.replace("_", "-")
    return f"--{flag}" if len(flag) > 1 else f"-{flag}"


def format_value(value: Any) -> Any:
    """Add quotes around value if it contains spaces.

    Args:
        value: command line value.

    Returns:
        modified value.
    """
    if isinstance(value, str):
        value = value.strip()
        return f'"{value}"' if " " in value else value
    return value


@logdec
def pandoc_args_dict_to_list(pandoc_args_dict: dict[str, Any]) -> list[str]:
    """Transform dict of CLI args to list for pypandoc.

    `pandoc_args_dict` should take format `{"arg": <value>}`.

    If <value> is `True` the arg will be returned with no corresponding value.
    If <value> is `False` the arg will be suppressed.
    All other values will be cast to string.

    Args:
        pandoc_args_dict: dictionary of CLI args and values.

    Returns:
        CLI args as list of strings.
    """
    pandoc_args_filtered = {
        key: value for key, value in pandoc_args_dict.items() if value is not False
    }
    delimiter = ARG_DELIMITER
    pandoc_args_list = delimiter.join(
        f"{format_flag(flag)}{delimiter}{format_value(value)}"
        if not isinstance(value, bool)
        else f"{format_flag(flag)}"
        for flag, value in pandoc_args_filtered.items()
        if value is not False
    ).split(delimiter)
    return pandoc_args_list


@logdec
def pandoc_filter_dict_to_list(pandoc_filters_dict: dict[str, bool]) -> list[str]:
    """Transform dict of filters to list for pypandoc.

    `pandoc_filters_dict` should take format `{"filter": <bool>}`.

    If <bool> is `True` the filter will be returned.
    If <bool> is `False` the filter will be suppressed.

    Args:
        pandoc_filters_dict: dictionary of filter names and booleans.

    Returns:
        filters as list of strings.
    """
    return [key for key, value in pandoc_filters_dict.items() if value]
