"""S3-compatible report storage (AWS S3, Aliyun OSS, MinIO)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from ax_storage.keys import object_key


class S3ReportStorage:
    """Upload report trees to an S3-compatible bucket and issue presigned GET URLs."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
    ) -> None:
        if not bucket:
            raise ValueError("AX_S3_BUCKET is required when AX_REPORT_STORAGE=s3")
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise ImportError("Install boto3 for S3 report storage: pip install boto3") from exc

        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key or None,
            aws_secret_access_key=secret_key or None,
            config=Config(signature_version="s3v4"),
        )

    def upload_tree(self, local_dir: Path, key_prefix: str) -> str:
        src = local_dir.resolve()
        if not src.is_dir():
            raise FileNotFoundError(f"Report directory not found: {local_dir}")

        prefix = key_prefix.rstrip("/")
        for path in src.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(src).as_posix()
            self._client.upload_file(
                str(path),
                self.bucket,
                object_key(prefix, rel),
                ExtraArgs={"ContentType": _content_type(path)},
            )
        return prefix

    def exists(self, key_prefix: str, relative: str) -> bool:
        key = object_key(key_prefix, relative)
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as exc:
            from botocore.exceptions import ClientError

            if isinstance(exc, ClientError):
                code = exc.response.get("Error", {}).get("Code")
                if code in {"404", "NoSuchKey", "NotFound"}:
                    return False
            raise

    def read_text(self, key_prefix: str, relative: str) -> str:
        key = object_key(key_prefix, relative)
        resp = self._client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read().decode("utf-8")

    def presigned_url(self, key_prefix: str, relative: str, *, expires: int) -> str:
        key = object_key(key_prefix, relative)
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires,
        )

    def presigned_url_expires_at(self, expires: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=expires)

    def supports_signed_urls(self) -> bool:
        return True

    def delete_tree(self, key_prefix: str) -> None:
        prefix = key_prefix.rstrip("/") + "/"
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            contents = page.get("Contents") or []
            if not contents:
                continue
            self._client.delete_objects(
                Bucket=self.bucket,
                Delete={"Objects": [{"Key": item["Key"]} for item in contents]},
            )


def _content_type(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "text/markdown; charset=utf-8"
    return "application/octet-stream"
