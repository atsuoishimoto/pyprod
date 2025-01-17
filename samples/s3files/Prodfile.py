# ruff: NOQA
# type: ignore

pip("boto3", "-q")  # install boto3

import boto3, botocore
from urllib.parse import urlparse

s3 = boto3.client("s3")
BUCKET = params.BUCKET or "TESTBUCKET"  # Run pyprod with BUCKET=bucket-name
TARGET = f"s3://{BUCKET}/S3TEST.txt"


def parse_s3url(s3url):
    """Parses an S3 URL and returns the bucket name and the key."""
    parsed = urlparse(s3url)
    return parsed.netloc, parsed.path.lstrip("/")


@rule(targets=TARGET, pattern="*/%.txt", depends="%.txt")
def copyfile(target, src):
    """Copies a file to an S3 bucket."""
    bucket, key = parse_s3url(target)
    s3.upload_file(Filename=str(src), Bucket=bucket, Key=key)


@check("s3://*")
def check_s3file(s3url):
    """Checks if an S3 file exists. Returns timestamp if it does."""
    bucket, key = parse_s3url(s3url)
    try:
        return s3.head_object(Bucket=bucket, Key=key)["LastModified"]
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return
        raise


@task
def clean():
    """Deletes an S3 file."""
    bucket, key = parse_s3url(TARGET)
    s3.delete_object(Bucket=bucket, Key=key)


@task
def ls():
    """Lists the contents of an S3 bucket."""
    bucket, key = parse_s3url(TARGET)
    run("aws s3 ls", bucket)


@task
def rebuild():
    build(clean, TARGET)
