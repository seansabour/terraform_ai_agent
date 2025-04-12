provider "aws" {
  region = "us-west-2"
}

module "s3_bucket" {
  source            = "./modules/s3"
  bucket_name       = "my-private-bucket"
  bucket_acl        = "private"
  versioning_enabled = true
  tags = {
    Environment = "production"
    Project     = "terraform-s3"
  }
}