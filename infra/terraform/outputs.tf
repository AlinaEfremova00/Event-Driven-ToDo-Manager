output "namespaces" {
  value = [
    kubernetes_namespace.todo_app.metadata[0].name,
    kubernetes_namespace.kafka.metadata[0].name,
    kubernetes_namespace.argocd.metadata[0].name,
    kubernetes_namespace.monitoring.metadata[0].name
  ]
}