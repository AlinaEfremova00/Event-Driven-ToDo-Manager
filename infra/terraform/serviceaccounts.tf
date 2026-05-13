resource "kubernetes_service_account" "todo_sa" {
  metadata {
    name      = "todo-service-account"
    namespace = kubernetes_namespace.todo_app.metadata[0].name
  }
}

resource "kubernetes_service_account" "kafka_sa" {
  metadata {
    name      = "kafka-service-account"
    namespace = kubernetes_namespace.kafka.metadata[0].name
  }
}

resource "kubernetes_service_account" "argocd_sa" {
  metadata {
    name      = "argocd-manager"
    namespace = kubernetes_namespace.argocd.metadata[0].name
  }
}