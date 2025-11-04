terraform {
  backend "s3" {
    bucket = "tfstate-tcp-http-traffic-test"
    key    = "tcp-http-traffic.tfstate"
    region = "ap-northeast-1"
  }
}