terraform {
  backend "s3" {
    bucket = "billionaire-matchmaker-tofu-state"
    key    = "tofu.tfstate"
    region = "us-east-1"

    # S3-native locking (no DynamoDB required)
    use_lockfile = true
  }
}
