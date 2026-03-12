import os
import logging
from typing import Optional

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_REGION")
        addressing = os.getenv("S3_ADDRESSING_STYLE", "virtual")

        boto_config = Config(s3={'addressing_style': addressing})

        # Create client using explicit credentials (env vars expected)
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name=region,
            config=boto_config,
        )

    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        force_binary: bool = False,
    ) -> dict:
        """Upload raw bytes to S3.

        If `force_binary` is True the object will be uploaded with
        Content-Type `application/octet-stream` which prevents S3/console
        from treating it as a PDF and previewing it.
        """
        extra_args = {}

        if force_binary:
            extra_args["ContentType"] = "application/octet-stream"
        elif content_type:
            extra_args["ContentType"] = content_type

        logger.info("Uploading object to s3 bucket=%s key=%s (force_binary=%s)", bucket, key, force_binary)
        resp = self.client.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
        return resp


s3_service = S3Service()
