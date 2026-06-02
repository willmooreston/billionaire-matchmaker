terraform {
  backend "s3" {
    bucket = "billionaire-matchmaker-tofu-state"
    key    = "tofu.tfstate"
    region = "us-west-2"

    # S3-native locking (no DynamoDB required)
    use_lockfile = true
  }
}
