"""
Command-line interface for station-related tools

"""

import logging
from pathlib import Path
from typing import Any

import click
from click_aliases import ClickAliasedGroup
from rich import print

from ab import (
    configuration,
    dates,
)
from ab.cli import _options
from ab.bsw import campaign as _campaign
from ab.station import sta

log = logging.getLogger(__name__)


@click.group(cls=ClickAliasedGroup)
def station() -> None:
    """
    Stand-alone tools for station data.

    """


@station.command
@_options.campaign
@click.option(
    "-f",
    "--config",
    required=False,
    default=None,
    type=Path,
    help="Path to an input YAML file with valid `station`.",
)
@click.option(
    "-i",
    "sitelogs",
    multiple=True,
    type=Path,
    help="One or more paths to site-log files to build the STA-file from.",
)
@click.option(
    "-k",
    "individually_calibrated",
    multiple=True,
    type=str,
    help="Four-letter ID for each station that is individually calibrated.",
)
@click.option(
    "-o",
    "output_filename",
    required=False,
    default=Path(".").resolve() / "sitelogs.STA",
    type=Path,
    help="Path to optional output path and filename for the STA file.",
)
@click.option(
    "-l",
    "preferred_station_id_length",
    required=False,
    type=click.Choice(["four", "nine"]),
    help="Preferred station-ID length. Choose between values `four` and `nine`. Default is to use available length in each given file.",
)
# define skip period for TYPE003 entries
@click.option(
    "-s",
    "skip_period",
    required=False,
    default=None,
    type=click.Choice(["day", "week"]),
    help="Choose time period to skip on station events in TYPE003 entries. Default is None. Can be set to 'day' or 'week'.",
)
def sitelogs2sta(
    name: str,
    config: Path,
    sitelogs: tuple[Path],
    individually_calibrated: tuple[str],
    output_filename: Path,
    preferred_station_id_length: str | None = None,
    skip_period: str | None = None,
) -> None:
    """
    Create a STA file from sitelogs and optional station information.

    Choose one of the following ways to run it:

    1.  No arguments: Use input provided in common user configuration
        (`autobernese.yaml`).

    2.  Use the flag `-c` to supply a name for a campaign whose configuration
        (`campaign.yaml`) contains to create a STA file from standard settings
        in campaign-specific configuration.

    2.  Use the flag `-f` to supply a path to a custom path to a YAML file with
        arguments.

    4.  Use flags `-i`, `-k`, `-o`, `-l`, and `-s` to supply needed and optional
        arguments on the command line.

    The following arguments are possible:

    \b
    *   Site-log filenames are required.
    *   Station IDs for individually-calibrated stations are optional.
    *   The path to the output STA file is optional. (Default: `sitelogs.STA`)

    These arguments can be provided in a configuration file which has the
    following structure:

    \b
    ```yaml
    station:
      sitelogs: [sta1.log, sta2.log]
      individually_calibrated: [sta1]
      output_sta_file: /path/to/output.STA
    ```

    Provided configuration files are loaded with the current Bernese
    environment, so advanced paths are possible, e.g.

    \b
    ```yaml
    sitelogs: !Path [*D, sitelogs, '*.log']
    ```

    which will give a sequence of all the files ending with `log` in the given
    directory.

    \b
    ```yaml
    sitelogs:
    - !Path [*D, sitelogs, 'sta1*.log']
    - !Path [*D, sitelogs, 'sta2*.log']
    - !Path [*D, sitelogs, 'sta3*.log']
    ```

    which will let you create the sequence of filenames yourself when you want
    to specifiy specific stations. The wildcard `*` lets you avoid having to
    look up the date, when the file was last updated.

    For the output STA file, you can also write the following:

    \b
    ```yaml
    output_sta_file: `!Path [*D, station, sitelogs.STA]`
    ```

    """
    arguments: dict[str, Any] | None = None
    # get arguments from configuration files
    if config is not None:
        ifname = config.absolute()
        msg = f"Create STA file with arguments in file {ifname} ..."
        log.info(msg)
        print(msg)
        arguments = configuration.load(ifname).get("station")
    elif name is not None:
        msg = f"Create STA file from arguments in configuration for campaign {name} ..."
        log.info(msg)
        print(msg)
        arguments = _campaign.load(name).get("station")
    elif sitelogs:
        msg = f"Create STA file from command-line-supplied sitelogs..."
        log.info(msg)
        print(msg)
        arguments["sitelogs"] = list(sitelogs)
    elif configuration.load().get("station") is not None:
        msg = f"Create STA file from arguments in the common user configuration `autobernese.yaml` ..."
        log.info(msg)
        print(msg)
        arguments = configuration.load().get("station")

    # overwrite or complement with arguments from the command line
    if individually_calibrated:
        msg = f"Using command-line-supplied value for parameter individually_calibrated = {individually_calibrated}..."
        log.info(msg)
        print(msg)
        arguments["individually_calibrated"] = individually_calibrated
    if output_filename:
        msg = f"Using command-line-supplied parameter output_sta_file = {output_filename}..."
        log.info(msg)
        print(msg)
        arguments["output_sta_file"] = output_filename
    if skip_period:
        msg = f"Using command-line-supplied value for parameter skip_period = {skip_period}..."
        log.info(msg)
        print(msg)
        arguments["skip_period"] = skip_period

    if arguments is None:
        msg = f"No arguments found ..."
        print(msg)
        log.info(msg)
        return

    sta.create_sta_file_from_sitelogs(**arguments)
