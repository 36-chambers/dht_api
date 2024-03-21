from datetime import datetime, timezone
from typing import Generic, Type, TypeVar

import aioboto3
import structlog
from botocore.exceptions import ClientError
from pydantic import BaseModel

log = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class S3Object(Generic[T], BaseModel):
    last_modified: datetime
    item: T


class S3Manager:
    def __init__(self, bucket_name: str):
        self.session = aioboto3.Session()
        self.bucket_name = bucket_name

    async def write(self, info_hash: str, model: BaseModel) -> bool:
        """
        Write a BaseModel instance to S3 as a JSON blob.
        """
        try:
            async with self.session.resource("s3") as s3:
                bucket = await s3.Bucket(self.bucket_name)
                await bucket.put_object(
                    Bucket=self.bucket_name, Key=info_hash, Body=model.model_dump_json()
                )
            return True
        except ClientError as e:
            log.error("Failed to write object to S3", exc_info=e)
            return False

    async def read(self, info_hash: str, model_class: Type[BaseModel]) -> S3Object | None:
        """
        Read a JSON blob from S3 and convert it into a BaseModel instance.
        """
        try:
            async with self.session.client("s3") as s3:
                response = await s3.get_object(Bucket=self.bucket_name, Key=info_hash)
                if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                    log.info("Object not found", info_hash=info_hash)
                    return None
                body = await response["Body"].read()
                modified = datetime.strptime(
                    (
                        response.get("ResponseMetadata", {})
                        .get("HTTPHeaders", None)
                        .get("last-modified", None)
                    ),
                    r"%a, %d %b %Y %H:%M:%S %Z",
                ).replace(tzinfo=timezone.utc)
                return S3Object(
                    last_modified=modified,
                    item=model_class.model_validate_json(body),
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                log.debug("Object not cached", info_hash=info_hash)
                return None
            log.error("Failed to read object from S3", exc_info=e)
            return None
