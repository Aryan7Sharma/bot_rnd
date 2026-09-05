"""CLI entrypoint: `kriyon-bd <command>`."""

from __future__ import annotations

from uuid import UUID

import click

from kriyon_bd import db
from kriyon_bd.digest.markdown_digest import write_digest
from kriyon_bd.gdpr.purge import purge_contact, purge_organisation
from kriyon_bd.ingest.pipeline import run_ted_ingest
from kriyon_bd.logging_conf import configure_logging, get_logger
from kriyon_bd.scoring.classifier import SignalClassifier
from kriyon_bd.scoring.pipeline import run_scoring
from kriyon_bd.settings import load_settings

logger = get_logger(__name__)


@click.group()
def cli() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)


@cli.command("ingest-ted")
@click.option(
    "--since",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Only fetch notices published on/after this date (default: config lookback window).",
)
def ingest_ted(since) -> None:
    settings = load_settings()
    with db.connect(settings) as conn:
        counts = run_ted_ingest(
            conn, base_url=settings.ted_api_base_url, since=since.date() if since else None
        )
    click.echo(counts)


@cli.command("score")
@click.option("--limit", type=int, default=None, help="Max number of unscored signals to score.")
def score(limit) -> None:
    settings = load_settings()
    classifier = SignalClassifier(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    with db.connect(settings) as conn:
        counts = run_scoring(conn, classifier, limit=limit)
    click.echo(counts)


@cli.command("run-digest")
def run_digest_cmd() -> None:
    settings = load_settings()
    with db.connect(settings) as conn:
        path = write_digest(conn, settings.digest_output_dir)
    click.echo(f"Digest written to {path}")


@cli.command("purge")
@click.option("--contact-id", type=str, default=None)
@click.option("--contact-email", type=str, default=None)
@click.option("--organisation-id", type=str, default=None)
@click.option("--reason", type=str, default="", help="Free-text reason recorded in deletion_log.")
def purge(contact_id, contact_email, organisation_id, reason) -> None:
    if not any([contact_id, contact_email, organisation_id]):
        raise click.UsageError("Specify one of --contact-id, --contact-email, --organisation-id")
    settings = load_settings()
    with db.connect(settings) as conn:
        if organisation_id:
            counts = purge_organisation(conn, UUID(organisation_id), reason=reason)
        else:
            counts = purge_contact(
                conn,
                contact_id=UUID(contact_id) if contact_id else None,
                email=contact_email,
                reason=reason,
            )
    click.echo(counts)


if __name__ == "__main__":
    cli()
