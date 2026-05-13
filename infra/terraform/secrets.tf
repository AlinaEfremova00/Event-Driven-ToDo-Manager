resource "kubernetes_secret" "postgres_secret" {
  metadata {
    name      = "postgres-secret"
    namespace = kubernetes_namespace.todo_app.metadata[0].name
  }

  data = {
    POSTGRES_USER     = "todouser"
    POSTGRES_PASSWORD = "todopass"
    POSTGRES_DB       = "taskdb"
  }

  type = "Opaque"
}

resource "kubernetes_secret" "mongo_secret" {
  metadata {
    name      = "mongo-secret"
    namespace = kubernetes_namespace.todo_app.metadata[0].name
  }

  data = {
    MONGO_INITDB_ROOT_USERNAME = "eventuser"
    MONGO_INITDB_ROOT_PASSWORD = "eventpass"
  }

  type = "Opaque"
}

resource "kubernetes_secret" "redis_secret" {
  metadata {
    name      = "redis-secret"
    namespace = kubernetes_namespace.todo_app.metadata[0].name
  }

  data = {
    REDIS_PASSWORD = "redispass"
  }

  type = "Opaque"
}