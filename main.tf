module "s3_bucket" {
  source            = "./modules/s3"
  bucket_name       = "desired-bucket-name"
  bucket_acl        = "private"
  versioning_enabled = true
  tags = {
    Environment = "production"
    Project     = "example-project"
  }
}

provider "aws" {
  region = "us-west-2"
}