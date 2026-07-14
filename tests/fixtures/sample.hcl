resource "null_resource" "example" {
  triggers = {
    message = "Hello"
  }
}
