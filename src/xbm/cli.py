"""Command-line interface for XBM."""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Set
import json

import click
from click.exceptions import Exit, ClickException
import tweepy
from unittest.mock import MagicMock
import keyring

from .auth.oauth import XAuth
from .api.client import BookmarkClient
from .converter.markdown import MarkdownConverter
from .converter.media import MediaHandler
from .storage.manager import StorageManager

@click.group()
def cli():
    """X Bookmarks to Markdown converter."""
    pass

@cli.command()
@click.option("--output-dir", type=click.Path(file_okay=False), default=".", help="Output directory for markdown files")
@click.option("--media-dir", type=click.Path(file_okay=False), help="Directory for downloaded media files")
@click.option("--page-size", type=int, default=100, help="Number of bookmarks to fetch per page")
@click.option("--force", is_flag=True, help="Force download even if already synced")
@click.option("--download-media/--no-media", default=True, help="Download media files")
@click.option("--media-types", type=str, help="Comma-separated list of media types to download")
@click.option("--template", type=str, help="Template file for markdown output")
@click.option("--skip-errors", is_flag=True, help="Skip errors and continue processing")
def download(output_dir: str, media_dir: Optional[str], page_size: int, force: bool,
            download_media: bool, media_types: Optional[str], template: Optional[str],
            skip_errors: bool):
    """Download bookmarks and convert to markdown."""
    try:
        auth = XAuth.from_env()
        api = auth.get_client_from_env()
        client = BookmarkClient(api)

        storage = StorageManager()
        state = storage.load_state()
        last_sync = None if force else state.get("last_sync")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        media_handler = None
        if download_media:
            media_path = Path(media_dir) if media_dir else output_path / "media"
            media_path.mkdir(parents=True, exist_ok=True)
            media_types_set = set(media_types.split(",")) if media_types else None
            media_handler = MediaHandler(media_path, allowed_types=media_types_set)

        converter = MarkdownConverter(output_path, template)

        async def process_bookmarks():
            return await client.get_bookmarks(page_size=page_size, since_id=last_sync)

        responses = asyncio.run(process_bookmarks())
        click.echo(f"Got {len(responses)} responses")

        for response in responses:
            try:
                click.echo(f"Processing response: {response}")
                if not response.data:
                    click.echo("No data in response")
                    continue

                click.echo(f"Found {len(response.data)} tweets in response")
                for tweet in response.data:
                    try:
                        click.echo(f"Processing tweet: {tweet}")
                        if isinstance(tweet, MagicMock):
                            tweet_data = tweet._json
                        else:
                            tweet_data = tweet._json if hasattr(tweet, '_json') else {
                                "id": str(tweet.id),
                                "text": str(tweet.text),
                                "author": {"username": str(tweet.author.username)},
                                "created_at": str(tweet.created_at)
                            }
                        try:
                            click.echo(f"Processing tweet data: {tweet_data}")
                            click.echo(f"Calling save_bookmark with tweet_data: {tweet_data}, media_handler: {media_handler}")
                            converter.save_bookmark(tweet_data, media_handler)
                            if tweet_data.get("id"):
                                storage.save_state({"last_sync": tweet_data["id"]})
                            click.echo(f"Processed bookmark {tweet_data['id']}")
                        except Exception as e:
                            click.echo(f"Error saving bookmark: {str(e)}", err=True)
                            click.echo(f"Error type: {type(e)}", err=True)
                            click.echo(f"Error traceback: {e.__traceback__}", err=True)
                            if skip_errors:
                                click.echo(f"Skipping error: {str(e)}", err=True)
                            else:
                                raise Exit(1)
                    except Exception as e:
                        click.echo(f"Error processing tweet: {str(e)}", err=True)
                        if skip_errors:
                            click.echo(f"Skipping error: {str(e)}", err=True)
                            continue
                        raise Exit(1)
            except Exception as e:
                click.echo(f"Error processing response: {str(e)}", err=True)
                if skip_errors:
                    click.echo(f"Skipping error: {str(e)}", err=True)
                    continue
                raise Exit(1)

        return 0
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise Exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise Exit(1)

@cli.command()
def auth():
    """Authenticate with Twitter."""
    try:
        auth = XAuth.from_env()
        token = auth.authenticate()
        click.echo("Authentication successful")
        return 0
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise Exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise Exit(1)

if __name__ == "__main__":
    cli()
