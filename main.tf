provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "my_public_bucket" {
  bucket = "my-public-bucket-unique-name"

  acl    = "public-read"

  tags = {
    Name        = "My public S3 bucket"
    Environment = "Production"
  }
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = aws_s3_bucket.my_public_bucket.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.my_public_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.my_public_bucket.arn}/*"
      }
    ]
  })
}