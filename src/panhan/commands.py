import os
import tempfile
from getpass import getuser
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable

import frontmatter  # type: ignore
import pypandoc  # type: ignore
import yaml

from panhan.logger import logdec, logger
from panhan.config import BaseConfig, DocumentConfig, PanhanFrontmatter

BASE_CONFIG_FILENAME = "panhan.yaml"
USER_CONFIG_LOCATION = Path.home() / ".config/panhan/" / BASE_CONFIG_FILENAME


@logdec
def print_panhan_yaml_template() -> None:
    yaml_template = f"""\
    #{USER_CONFIG_LOCATION}
    presets:
        default:
            output_format: html
            metadata:
                author: {getuser()}
            pandoc_args:
                standalone: true

        preset_one:
            output_format: html
            output_file: output.html
            metadata:
                arg1: value
                arg2: value
            pandoc_args:
                arg1: value
                arg2: value
            filters:
                - filter1
                - filter2

        preset_two:
            use_preset: preset_one
            filters:
                - filter3

    pandoc_path: null
    """
    print(dedent(yaml_template))


@logdec
def assure_path(path_arg: str | None) -> Path | None:
    """Check `path_arg` is valid filepath and return as a `Path` object.

    If `path_arg` is an empty string `None` is returned.

    Args:
        path_arg: filepath.

    Raises:
        FileNotFoundError: `path_arg` is defined but does not point to a file.

    Returns:
        `Path` if `path_arg` is valid file or `None` if empty string.
    """
    if path_arg:
        path_obj = Path(path_arg)
        if path_obj.is_file():
            return path_obj
        raise FileNotFoundError(path_arg)
    return None


@logdec
def find_panhan_yaml() -> Path:
    """Look for `panhan.yaml` in default locations and return path.

    Returns instance - see code for order of precedence.

    Raises:
        FileNotFoundError: `panhan.yaml` was not found.

    Returns:
        path to `panhan.yaml`.
    """
    possible_paths = [
        Path.cwd() / BASE_CONFIG_FILENAME,
        USER_CONFIG_LOCATION,
        Path.home() / BASE_CONFIG_FILENAME,
    ]
    for path in possible_paths:
        if path.is_file():
            return path
    raise FileNotFoundError(possible_paths)


@logdec
def update_environment(panhan_config: BaseConfig) -> None:
    """Update the environment with `panhan_config` values.

    Args:
        panhan_config: panhan config object.
    """
    # If `pandoc_path` is defined, update environment variable for pypandoc.
    if panhan_config.pandoc_path:
        os.environ.setdefault("PYPANDOC_PANDOC", panhan_config.pandoc_path)


@logdec
def load_panhan_frontmatter(source_path: Path) -> PanhanFrontmatter:
    """Read markdown file at `source_path` and return panhan frontmatter.

    Args:
        source_path: path to markdown source file.

    Returns:
        panhan frontmatter object.
    """
    panhan_frontmatter: list[dict[str, Any]] = frontmatter.load(
        source_path
    ).metadata.get("panhan", {})
    return PanhanFrontmatter(panhan_frontmatter)


@logdec
def load_base_config(panhan_path: Path) -> BaseConfig:
    """Read panhan config `panhan_path` and return config object.

    Args:
        panhan_path: path to panhan.yaml.

    Returns:
        panhan config object.
    """
    yaml_str = panhan_path.read_text()
    panhan_dict = yaml.safe_load(yaml_str)
    return BaseConfig(**panhan_dict)


@logdec
def resolve_config(
    document_config: DocumentConfig, panhan_config: BaseConfig
) -> DocumentConfig:
    """Determine correct document config from source file and panhan config.

    Args:
        panhan_frontmatter: document config from source file.
        panhan_config: panhan settings from panhan.yaml.

    Returns:
        resolved output document config.
    """

    # Get config from named preset if specified.
    preset_name = document_config.use_preset
    if preset_name:
        preset_config = panhan_config.get_preset(preset_name)
    else:
        preset_config = DocumentConfig()

    # Get default config values if specified.
    default_config = panhan_config.get_default_preset()

    # Combine config values in order of precedence.
    final_config = document_config.combine(preset_config).combine(default_config)

    return final_config


@logdec
def convert_file(source_path: Path | str, **pypandoc_kwargs: dict[str, Any]) -> str | None:
    return pypandoc.convert_file(str(source_path), **pypandoc_kwargs)


@logdec
def process_source(source_path: Path, panhan_config: BaseConfig, preset_name: str | None, output_file: str | None) -> None:
    """Read markdown source at `source_path`, resolve config, write output with pypandoc.

    Args:
        source_path: path to markdown source file.
        panhan_config: panhan config object.
        preset_name: name of preset to use.
        output_file: name of output file.
    """
    document = frontmatter.loads(source_path.read_text())

    if preset_name:
        document.metadata["panhan"] = [{"use_preset": preset_name, "output_file": output_file}]

    panhan_frontmatter = PanhanFrontmatter(document.metadata.get("panhan", {}))

    for document_config in panhan_frontmatter.document_config_list:
        document_config = resolve_config(
            document_config=document_config, panhan_config=panhan_config
        )
        document.metadata = {**document_config.metadata, **document.metadata}
        pypandoc_kwargs = document_config.get_pypandoc_kwargs()
        output_dest = pypandoc_kwargs.get("outputfile") or "stdout"
        logger.info("Writing to: %s", output_dest)
        with tempfile.NamedTemporaryFile(suffix=source_path.suffix) as temp_file:
            frontmatter.dump(document, temp_file)
            output = convert_file(temp_file.name, **pypandoc_kwargs)
        if output:
            logger.info("<PANHAN OUTPUT START>")
            print(output)
            logger.info("<PANHAN OUTPUT END>")


@logdec
def process_source_files(SOURCE: str | Iterable[str], preset: str | None, output: str | None, config: str | None) -> None:
    """Read and interpret source file(s) with panhan config, output with pypandoc.

    Args:
        source: path(s) to source file(s).
        panhan_yaml: path to `panhan.yaml` - will check default locations if empty.
    """
    # Ensure source is iterable.
    if isinstance(SOURCE, str):
        SOURCE = (SOURCE,)

    # Load Panhan YAML.
    base_config_path = assure_path(config) or find_panhan_yaml()
    logger.info("Loading base config: %s", base_config_path)
    panhan_config = load_base_config(base_config_path)

    # Update environment according to config.
    update_environment(panhan_config)

    # Process each source file.
    source_path_gen = (Path(src) for src in SOURCE)
    for source_path in source_path_gen:
        logger.info("Processing source: %s", source_path)
        process_source(source_path=source_path, panhan_config=panhan_config, preset_name=preset, output_file=output)
    logger.info("Process completed.")
