# Kubernetes Service Discovery Concepts

This folder contains comprehensive documentation about Kubernetes service discovery mechanisms, with practical examples from our DevOps Dojo application.

## 📚 Documentation Structure

### Core Concepts
- **[Service Discovery Overview](./01-service-discovery-overview.md)** - What is service discovery and why it matters
- **[Environment Variables Method](./02-environment-variables.md)** - How Kubernetes automatically injects service environment variables
- **[DNS-Based Discovery](./03-dns-service-discovery.md)** - Using DNS for service discovery with examples
- **[Practical Examples](./04-practical-examples.md)** - Real-world examples from our application

### Advanced Topics  
- **[Service Types and Discovery](./05-service-types.md)** - Different service types and their discovery patterns
- **[Troubleshooting Guide](./06-troubleshooting.md)** - Common issues and debugging techniques

## 🎯 Learning Path

1. Start with **Service Discovery Overview** to understand the basics
2. Learn about **Environment Variables Method** - the automatic injection mechanism
3. Explore **DNS-Based Discovery** for more flexible service communication
4. Review **Practical Examples** to see real implementation
5. Dive into **Advanced Topics** for production considerations

## 🚀 Quick Example

In our DevOps Dojo application:

```bash
# Frontend automatically detects it's in Kubernetes
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    # Uses DNS-based discovery
    BACKEND_URL="http://backend.3-tier-app-eks.svc.cluster.local:8000"
fi
```

This demonstrates both environment variable detection and DNS-based service discovery!

## 🔗 Related Files

- `/k8s/` - Our Kubernetes manifests
- `/frontend/docker-entrypoint.sh` - Service discovery implementation
- `/docker-compose.yml` - Comparison with Docker Compose networking

---

Each document includes theory, practical examples, and hands-on exercises to master Kubernetes service discovery! 🎓