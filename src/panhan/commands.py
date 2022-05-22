import os
from getpass import getuser
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable

import frontmatter
import pypandoc
import yaml

from panhan.logger import logdec, logger
from panhan.models import AppConfig, DocumentConfig, PanhanFrontmatter

APP_CONFIG_FILENAME = "panhan.yaml"


@logdec
def print_panhan_yaml_template() -> None:
    yaml_template = f"""\
    #{Path.home()}/.config/{APP_CONFIG_FILENAME}
    presets:
        default:
            output_format: html
            variables:
                author: {getuser()}
            pandoc_args:
                standalone: true

        preset_one:
            output_format: html
            output_file: output.html
            variables:
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
def assure_path(path_arg: str) -> Path | None:
    """Check `path_arg` is valid filepath and return as a `Path` object.

    If `path_arg` is an empty string `None` is returned.

    Args:
        path_arg (str): filepath.

    Raises:
        FileNotFoundError: `path_arg` is defined but does not point to a file.

    Returns:
        Path | None: `Path` if `path_arg` is valid file or `None` if empty string.
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
        Path: path to `panhan.yaml`.
    """
    possible_paths = [
        Path.cwd() / APP_CONFIG_FILENAME,
        Path.home() / APP_CONFIG_FILENAME,
        Path.home() / ".config" / APP_CONFIG_FILENAME,
    ]
    for path in possible_paths:
        if path.is_file():
            return path
    raise FileNotFoundError(possible_paths)


@logdec
def update_app_config(panhan_config: AppConfig) -> None:
    """Update application state with settings in `panhan_config`.

    Args:
        panhan_config (AppConfig): panhan config object.
    """
    # If `pandoc_path` is defined, update environment variable for pypandoc.
    if panhan_config.pandoc_path:
        os.environ.setdefault("PYPANDOC_PANDOC", panhan_config.pandoc_path)


@logdec
def load_panhan_frontmatter(source_path: Path) -> PanhanFrontmatter:
    """Read markdown file at `source_path` and return panhan frontmatter.

    Args:
        source_path (Path): path to markdown source file.

    Returns:
        PanhanFrontmatter: panhan frontmatter object.
    """
    panhan_frontmatter = frontmatter.load(source_path).metadata.get("panhan", {})
    return PanhanFrontmatter(panhan_frontmatter)


@logdec
def load_panhan_config(panhan_path: Path) -> AppConfig:
    """Read panhan config `panhan_path` and return config object.

    Args:
        panhan_path (Path): path to panhan.yaml.

    Returns:
        AppConfig: panhan config object.
    """
    yaml_str = panhan_path.read_text()
    panhan_dict = yaml.safe_load(yaml_str)
    return AppConfig(**panhan_dict)


@logdec
def resolve_config(
    document_config: DocumentConfig, panhan_config: AppConfig
) -> DocumentConfig:
    """Determine correct document config from source file and panhan config.

    Args:
        panhan_frontmatter (DocumentConfig): document config from source file.
        panhan_config (AppConfig): panhan settings from panhan.yaml.

    Returns:
        DocumentConfig: resolved output document config.
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
def convert_file(source_path: Path, **pypandoc_kwargs: dict[str, Any]) -> None:
    pypandoc.convert_file(str(source_path), **pypandoc_kwargs)


@logdec
def process_source(source_path: Path, panhan_config: AppConfig) -> None:
    """Read markdown source at `source_path`, resolve config, write output with pypandoc.

    Args:
        source_path (Path): path to markdown source file.
        panhan_config (AppConfig): panhan config object.
    """
    panhan_frontmatter = load_panhan_frontmatter(source_path=source_path)
    for document_config in panhan_frontmatter.document_config_list:
        document_config = resolve_config(
            document_config=document_config, panhan_config=panhan_config
        )
        pypandoc_kwargs = document_config.to_pypandoc_kwargs(panhan_config)
        output_dest = pypandoc_kwargs.get("outputfile") or "stdout"
        logger.info("Writing document to: %s", output_dest)
        output = convert_file(str(source_path), **pypandoc_kwargs)
        if output:
            logger.info("<PANHAN OUTPUT START>")
            print(output)
            logger.info("<PANHAN OUTPUT END>")


@logdec
def process_source_files(SOURCE: str | Iterable[str], panhan_yaml: str) -> None:
    """Read and interpret source file(s) with panhan config, output with pypandoc.

    Args:
        source (str | Iterable[str]): path(s) to source file(s).
        panhan_yaml (str): path to `panhan.yaml` - will check default locations if empty.
    """
    # Ensure source is iterable.
    if isinstance(SOURCE, str):
        SOURCE = (SOURCE,)

    # Load Panhan YAML.
    panhan_path = assure_path(panhan_yaml) or find_panhan_yaml()
    panhan_config = load_panhan_config(panhan_path)
    logger.info("Loaded panhan config: %s", panhan_path)

    # Update application config.
    update_app_config(panhan_config)

    # Process each source file.
    source_path_gen = (Path(src) for src in SOURCE)
    for source_path in source_path_gen:
        logger.info("Processing source: %s", source_path)
        process_source(source_path=source_path, panhan_config=panhan_config)
    logger.info("Process completed.")
