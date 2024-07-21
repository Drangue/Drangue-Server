terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "> 3.38.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "> 3.1.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"
}
