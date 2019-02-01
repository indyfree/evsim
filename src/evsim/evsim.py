import click
from datetime import datetime
import logging
import os

from evsim.simulation import Simulation
from evsim.data import loader


@click.group(name="evsim")
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    click.echo("Debug is %s." % (ctx.obj["DEBUG"] and "on" or "off"))

    os.makedirs("./logs", exist_ok=True)
    fh = logging.FileHandler(
        "./logs/%s.log" % str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    )
    fh.setFormatter(logging.Formatter("%(name)-10s: %(levelname)-7s %(message)s"))
    fh.setLevel(logging.DEBUG)
    ctx.obj["FH"] = fh

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    if not debug:
        sh.setLevel(logging.ERROR)

    logging.basicConfig(
        level=logging.DEBUG, datefmt="%d.%m. %H:%M:%S", handlers=[sh, fh]
    )


@cli.command(help="Start the EV Simulation.")
@click.pass_context
@click.option(
    "-n",
    "--name",
    default=str(datetime.now().strftime("%Y%m%d-%H%M%S")),
    help="Name of the Simulation.",
)
@click.option(
    "-s",
    "--charging-speed",
    default=3.6,
    help="Charging power of charging stations in kW.",
)
@click.option(
    "-c", "--ev-capacity", default=17.6, help="Battery capacity of EV in kWh."
)
def simulate(ctx, name, charging_speed, ev_capacity):
    click.echo("Charging speed is set to %skW." % charging_speed)
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    sim = Simulation(name, charging_speed, ev_capacity)
    sim.start()


@cli.group(invoke_without_command=True, help="(Re)build all data sources.")
@click.option(
    "-s",
    "--charging-speed",
    default=3.6,
    help="Charging power of charging stations in kW.",
)
@click.option(
    "-c", "--ev-capacity", default=17.6, help="Battery capacity of EV in kWh."
)
@click.option("-r", "--ev-range", default=160, help="Maximal Range of EV in km.")
@click.pass_context
def build(ctx, charging_speed, ev_capacity, ev_range):
    ctx.ensure_object(dict)
    ctx.obj["CHARGING_SPEED"] = charging_speed
    ctx.obj["EV_CAPACITY"] = ev_capacity
    ctx.obj["EV_RANGE"] = ev_range

    if ctx.invoked_subcommand is None:
        click.echo("Building all data sources.")
        loader.rebuild(charging_speed)


@build.command(help="(Re)build car2go trip data.")
@click.pass_context
def trips(ctx):
    ev_range = ctx.obj["EV_RANGE"]
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("Building car2go trip data...")
    loader.load_car2go_trips(ev_range, rebuild=True)


@build.command(help="(Re)build mobility demand data.")
@click.pass_context
def mobility_demand(ctx):
    cs = ctx.obj["CHARGING_SPEED"]
    ev_capacity = ctx.obj["EV_CAPACITY"]
    ev_range = ctx.obj["EV_RANGE"]
    click.echo("Charging speed is set to %skW." % cs)
    click.echo("EV battery capacity is set to %skWh." % ev_capacity)
    click.echo("Maximal EV range is set to %skm." % ev_range)
    click.echo("Building mobility demand data...")
    loader.load_car2go_capacity(cs, ev_capacity, ev_range, rebuild=True)


@build.command(help="(Re)build intraday price data.")
@click.pass_context
def intraday_prices(ctx):
    click.echo("Rebuilding intraday price data...")
    loader.load_intraday_prices(rebuild=True)


@build.command(help="(Re)build balancing price data.")
@click.pass_context
def balancing_prices(ctx):
    click.echo("Rebuilding balanacing price data...")
    loader.load_balancing_data(rebuild=True)
