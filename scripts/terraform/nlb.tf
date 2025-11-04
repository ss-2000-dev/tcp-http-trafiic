data "aws_vpc" "default" {
  # TODO: いったん直書き
  id = "vpc-08c9172c3ec4e81e5"
}

resource "aws_lb" "gateway_tcp" {
  name               = "gateway-tcp-nlb"
  internal           = false
  load_balancer_type = "network"
  # TODO: とりあえず直書き
  subnets = ["subnet-0a01ab2fa32f7ea5e", "subnet-035bf28d06e6f63d4"]

  tags = {
    project = "tcp-http-traffic-test"
  }
}

resource "aws_lb_target_group" "gateway_tcp" {
  name        = "gateway-tcp-nlb-tg"
  port        = 80
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"
}

resource "aws_lb_listener" "gateway-tcp" {
  load_balancer_arn = aws_lb.gateway_tcp.arn
  port              = 3129
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway_tcp.arn
  }
}

# aws_lb_target_group_attachmentは必要なさそう...