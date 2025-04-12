provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "private_bucket" {
  bucket = "my-private-bucket-123456"

  acl    = "private"

  tags = {
    Name        = "My Private Bucket"
    Environment = "Production"
  }
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.private_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.private_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = aws_s3_bucket.private_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "logging" {
  bucket = aws_s3_bucket.private_bucket.id

  target_bucket = "my-logs-bucket"
  target_prefix = "logs/"
}