terraform {
  required_providers {
    aws = {
      source  = "registry.opentofu.org/hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "bot" {
  source = "./modules/bot"

  aws_region          = var.aws_region
  image_uri           = var.image_uri
  schedule_expression = var.schedule_expression
}
