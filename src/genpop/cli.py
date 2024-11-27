import click
from . import generate


@click.group(context_settings=dict(help_option_names=[u"-h", u"--help"]))
def cli():
    pass


@cli.command("create_persons")
@click.option(
    "-n",
    "--num-persons",
    type=click.INT,
    help="The number of persons to create",
    required=True
)
@click.option(
    "-p",
    "--places_file",
    type=click.Path(),
    help="Path to the places file containing the places to assign to persons",
    required=True
)
@click.option(
    "-s",
    "--schedules-file",
    type=click.Path(),
    help="Path to the schedules file containing the activity schedule to assign to persons",
    required=True
)
@click.option(
    "-o",
    "--output_file",
    type=click.Path(),
    help="Path to create the created persons to",
    required=True
)
@click.option(
    "--ppc",
    type=click.INT,
    help="Number of persons to assign to each cell",
    required=True
)
def create_persons(num_persons: int, ppc: int, places_file, schedules_file, output_file):
    generate.generate_persons(num_persons, ppc, places_file, schedules_file, output_file)


@cli.command("create_schedules")
@click.option(
    "-n",
    "--num-schedules",
    type=click.INT,
    help="The number of schedules to create",
    required=True
)
@click.option(
    "-o",
    "--output_file",
    type=click.Path(),
    help="Path to create the created persons to",
    required=True
)
def create_schedules(num_schedules: int, output_file):
    generate.generate_schedules(num_schedules, output_file)
