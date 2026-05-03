"""
DevOpsDojo Kubernetes Operator using Kopf

Lifecycle: Database -> Migration -> Backend -> Frontend
"""

import kopf
import kubernetes
import logging
import yaml
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kubernetes API clients
kubernetes.config.load_incluster_config()
apps_api = kubernetes.client.AppsV1Api()
core_api = kubernetes.client.CoreV1Api()
batch_api = kubernetes.client.BatchV1Api()
networking_api = kubernetes.client.NetworkingV1Api()
custom_api = kubernetes.client.CustomObjectsApi()

# Constants
GROUP = "apps.devopsdojo.io"
VERSION = "v1"
PLURAL = "devopsdojos"

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def load_template(name: str) -> dict:
    """Load a YAML template file."""
    template_path = TEMPLATES_DIR / f"{name}.yaml"
    with open(template_path) as f:
        return yaml.safe_load(f)


def update_status(name: str, namespace: str, status: dict):
    """Update the CR status."""
    status["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
    try:
        custom_api.patch_namespaced_custom_object_status(
            group=GROUP,
            version=VERSION,
            namespace=namespace,
            plural=PLURAL,
            name=name,
            body={"status": status}
        )
    except Exception as e:
        logger.error(f"Failed to update status: {e}")


def get_owner_reference(body: dict) -> list:
    """Create owner reference for child resources."""
    return [{
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "DevOpsDojo",
        "name": body["metadata"]["name"],
        "uid": body["metadata"]["uid"],
        "controller": True,
        "blockOwnerDeletion": True
    }]


# ============================================================================
# CREATE HANDLER
# ============================================================================

@kopf.on.create(GROUP, VERSION, PLURAL)
def on_create(body, spec, name, namespace, logger, **kwargs):
    """Handle DevOpsDojo CR creation."""
    logger.info(f"Creating DevOpsDojo: {name} in namespace {namespace}")

    # Initialize status
    update_status(name, namespace, {
        "phase": "Pending",
        "databaseReady": False,
        "migrationCompleted": False,
        "backendReady": False,
        "frontendReady": False,
        "message": "Starting deployment..."
    })

    # Create namespace resources
    create_secrets(body, spec, name, namespace)
    create_configmap(body, spec, name, namespace)

    # Start with database
    update_status(name, namespace, {
        "phase": "CreatingDatabase",
        "message": "Creating PostgreSQL StatefulSet..."
    })
    create_database(body, spec, name, namespace)

    return {"message": f"DevOpsDojo {name} creation initiated"}


# ============================================================================
# RESOURCE CREATION FUNCTIONS
# ============================================================================

def create_secrets(body, spec, name, namespace):
    """Create secrets for the application."""
    secrets_ref = spec.get("secretsRef")

    # If no external secret reference, create internal one
    if not secrets_ref:
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{name}-secrets",
                "namespace": namespace,
                "ownerReferences": get_owner_reference(body)
            },
            "type": "Opaque",
            "stringData": {
                "DB_USERNAME": "postgres",
                "DB_PASSWORD": "postgres",  # Should be overridden
                "SECRET_KEY": "dev-secret-key",
                "DB_HOST": f"{name}-postgres",
                "DB_PORT": "5432",
                "DB_NAME": "devopsdojo"
            }
        }
        try:
            core_api.create_namespaced_secret(namespace, secret)
            logger.info(f"Created secret: {name}-secrets")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status != 409:  # Ignore already exists
                raise


def create_configmap(body, spec, name, namespace):
    """Create ConfigMap for the application."""
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"{name}-config",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "data": {
            "DB_HOST": f"{name}-postgres",
            "DB_PORT": "5432",
            "DB_NAME": "devopsdojo",
            "FLASK_DEBUG": "0",
            "BACKEND_URL": f"http://{name}-backend:8000"
        }
    }
    try:
        core_api.create_namespaced_config_map(namespace, configmap)
        logger.info(f"Created configmap: {name}-config")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise


def create_database(body, spec, name, namespace):
    """Create PostgreSQL StatefulSet and Service."""
    db_spec = spec.get("database", {})
    storage = db_spec.get("storage", "10Gi")
    storage_class = db_spec.get("storageClass", "")
    resources = db_spec.get("resources", {})

    # PostgreSQL Service (headless for StatefulSet)
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-postgres",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "clusterIP": "None",
            "ports": [{"port": 5432, "targetPort": 5432, "name": "postgres"}],
            "selector": {"app": f"{name}-postgres"}
        }
    }

    # PostgreSQL StatefulSet
    statefulset = {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {
            "name": f"{name}-postgres",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "serviceName": f"{name}-postgres",
            "replicas": 1,
            "selector": {
                "matchLabels": {"app": f"{name}-postgres"}
            },
            "template": {
                "metadata": {
                    "labels": {"app": f"{name}-postgres"}
                },
                "spec": {
                    "containers": [{
                        "name": "postgres",
                        "image": "postgres:14",
                        "ports": [{"containerPort": 5432}],
                        "env": [
                            {"name": "POSTGRES_DB", "value": "devopsdojo"},
                            {
                                "name": "POSTGRES_USER",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": spec.get("secretsRef", f"{name}-secrets"),
                                        "key": "DB_USERNAME"
                                    }
                                }
                            },
                            {
                                "name": "POSTGRES_PASSWORD",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": spec.get("secretsRef", f"{name}-secrets"),
                                        "key": "DB_PASSWORD"
                                    }
                                }
                            }
                        ],
                        "volumeMounts": [{
                            "name": "postgres-data",
                            "mountPath": "/var/lib/postgresql/data"
                        }],
                        "readinessProbe": {
                            "exec": {
                                "command": ["pg_isready", "-U", "postgres"]
                            },
                            "initialDelaySeconds": 5,
                            "periodSeconds": 5
                        },
                        "livenessProbe": {
                            "exec": {
                                "command": ["pg_isready", "-U", "postgres"]
                            },
                            "initialDelaySeconds": 30,
                            "periodSeconds": 10
                        },
                        "resources": {
                            "requests": resources.get("requests", {"memory": "256Mi", "cpu": "100m"}),
                            "limits": resources.get("limits", {"memory": "512Mi", "cpu": "500m"})
                        }
                    }]
                }
            },
            "volumeClaimTemplates": [{
                "metadata": {"name": "postgres-data"},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "storageClassName": storage_class if storage_class else None,
                    "resources": {"requests": {"storage": storage}}
                }
            }]
        }
    }

    # Remove None storageClassName
    if not storage_class:
        del statefulset["spec"]["volumeClaimTemplates"][0]["spec"]["storageClassName"]

    try:
        core_api.create_namespaced_service(namespace, service)
        logger.info(f"Created service: {name}-postgres")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    try:
        apps_api.create_namespaced_stateful_set(namespace, statefulset)
        logger.info(f"Created statefulset: {name}-postgres")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise


def create_migration_job(body, spec, name, namespace):
    """Create database migration Job."""
    backend_spec = spec.get("backend", {})
    image = backend_spec.get("image", "livingdevopswithakhilesh/devopsdozo:backend-latest-1")

    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": f"{name}-migration",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "ttlSecondsAfterFinished": 300,
            "backoffLimit": 3,
            "activeDeadlineSeconds": 300,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "initContainers": [{
                        "name": "wait-for-db",
                        "image": "busybox:1.28",
                        "command": ["sh", "-c", f"until nc -z {name}-postgres 5432; do echo 'Waiting for database...'; sleep 2; done; echo 'Database is ready!'"]
                    }],
                    "containers": [{
                        "name": "migrate",
                        "image": image,
                        "command": ["/bin/sh", "-c", "flask db upgrade && echo 'Migration completed!'"],
                        "env": [
                            {"name": "FLASK_APP", "value": "run.py"},
                            {
                                "name": "DATABASE_URL",
                                "value": f"postgresql://$(DB_USERNAME):$(DB_PASSWORD)@{name}-postgres:5432/devopsdojo"
                            }
                        ],
                        "envFrom": [
                            {"secretRef": {"name": spec.get("secretsRef", f"{name}-secrets")}},
                            {"configMapRef": {"name": f"{name}-config"}}
                        ]
                    }]
                }
            }
        }
    }

    try:
        batch_api.create_namespaced_job(namespace, job)
        logger.info(f"Created migration job: {name}-migration")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise


def create_backend(body, spec, name, namespace):
    """Create Backend Deployment and Service."""
    backend_spec = spec.get("backend", {})
    replicas = backend_spec.get("replicas", 2)
    image = backend_spec.get("image", "livingdevopswithakhilesh/devopsdozo:backend-latest-1")
    resources = backend_spec.get("resources", {})

    # Backend Service
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-backend",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 8000, "targetPort": 8000, "name": "http"}],
            "selector": {"app": f"{name}-backend"}
        }
    }

    # Backend Deployment
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-backend",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {"app": f"{name}-backend"}
            },
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0}
            },
            "template": {
                "metadata": {
                    "labels": {"app": f"{name}-backend"}
                },
                "spec": {
                    "containers": [{
                        "name": "backend",
                        "image": image,
                        "ports": [{"containerPort": 8000}],
                        "env": [
                            {
                                "name": "DATABASE_URL",
                                "value": f"postgresql://$(DB_USERNAME):$(DB_PASSWORD)@{name}-postgres:5432/devopsdojo"
                            },
                            {
                                "name": "ALLOWED_ORIGINS",
                                "value": f"http://{name}-frontend"
                            }
                        ],
                        "envFrom": [
                            {"secretRef": {"name": spec.get("secretsRef", f"{name}-secrets")}},
                            {"configMapRef": {"name": f"{name}-config"}}
                        ],
                        "readinessProbe": {
                            "httpGet": {"path": "/health", "port": 8000},
                            "initialDelaySeconds": 10,
                            "periodSeconds": 5
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 8000},
                            "initialDelaySeconds": 15,
                            "periodSeconds": 10
                        },
                        "resources": {
                            "requests": resources.get("requests", {"memory": "256Mi", "cpu": "100m"}),
                            "limits": resources.get("limits", {"memory": "512Mi", "cpu": "500m"})
                        }
                    }]
                }
            }
        }
    }

    try:
        core_api.create_namespaced_service(namespace, service)
        logger.info(f"Created service: {name}-backend")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    try:
        apps_api.create_namespaced_deployment(namespace, deployment)
        logger.info(f"Created deployment: {name}-backend")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise


def create_frontend(body, spec, name, namespace):
    """Create Frontend Deployment and Service."""
    frontend_spec = spec.get("frontend", {})
    replicas = frontend_spec.get("replicas", 2)
    image = frontend_spec.get("image", "livingdevopswithakhilesh/devopsdozo:frontend-latest-1")
    resources = frontend_spec.get("resources", {})

    # Frontend Service
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-frontend",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 80, "targetPort": 80, "name": "http"}],
            "selector": {"app": f"{name}-frontend"}
        }
    }

    # Frontend Deployment
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-frontend",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body)
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {"app": f"{name}-frontend"}
            },
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0}
            },
            "template": {
                "metadata": {
                    "labels": {"app": f"{name}-frontend"}
                },
                "spec": {
                    "containers": [{
                        "name": "frontend",
                        "image": image,
                        "ports": [{"containerPort": 80}],
                        "env": [
                            {"name": "BACKEND_URL", "value": f"http://{name}-backend:8000"},
                            {"name": "PORT", "value": "80"}
                        ],
                        "readinessProbe": {
                            "httpGet": {"path": "/health", "port": 80},
                            "initialDelaySeconds": 10,
                            "periodSeconds": 5
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 80},
                            "initialDelaySeconds": 15,
                            "periodSeconds": 20
                        },
                        "resources": {
                            "requests": resources.get("requests", {"memory": "128Mi", "cpu": "100m"}),
                            "limits": resources.get("limits", {"memory": "256Mi", "cpu": "300m"})
                        }
                    }]
                }
            }
        }
    }

    try:
        core_api.create_namespaced_service(namespace, service)
        logger.info(f"Created service: {name}-frontend")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    try:
        apps_api.create_namespaced_deployment(namespace, deployment)
        logger.info(f"Created deployment: {name}-frontend")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise

    # Create Ingress if enabled
    ingress_spec = spec.get("ingress", {})
    if ingress_spec.get("enabled", False):
        create_ingress(body, spec, name, namespace)


def create_ingress(body, spec, name, namespace):
    """Create Ingress for the application."""
    ingress_spec = spec.get("ingress", {})

    ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": f"{name}-ingress",
            "namespace": namespace,
            "ownerReferences": get_owner_reference(body),
            "annotations": ingress_spec.get("annotations", {
                "kubernetes.io/ingress.class": ingress_spec.get("className", "alb"),
                "alb.ingress.kubernetes.io/scheme": "internet-facing",
                "alb.ingress.kubernetes.io/target-type": "ip",
                "alb.ingress.kubernetes.io/healthcheck-path": "/health"
            })
        },
        "spec": {
            "ingressClassName": ingress_spec.get("className", "alb"),
            "rules": [{
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": f"{name}-frontend",
                                "port": {"number": 80}
                            }
                        }
                    }]
                }
            }]
        }
    }

    # Add host if specified
    if ingress_spec.get("host"):
        ingress["spec"]["rules"][0]["host"] = ingress_spec["host"]

    try:
        networking_api.create_namespaced_ingress(namespace, ingress)
        logger.info(f"Created ingress: {name}-ingress")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 409:
            raise


# ============================================================================
# TIMER HANDLER - Lifecycle State Machine
# ============================================================================

@kopf.timer(GROUP, VERSION, PLURAL, interval=10.0)
def check_status(body, spec, name, namespace, status, logger, **kwargs):
    """
    Periodically check status and progress through lifecycle:
    Database -> Migration -> Backend -> Frontend
    """
    current_status = status or {}
    phase = current_status.get("phase", "Pending")

    logger.info(f"Checking status for {name}, phase: {phase}")

    # State machine
    if phase in ["Pending", "CreatingDatabase"]:
        # Check if database is ready
        if is_database_ready(name, namespace):
            logger.info(f"Database is ready for {name}")
            update_status(name, namespace, {
                **current_status,
                "phase": "RunningMigration",
                "databaseReady": True,
                "message": "Database ready, running migrations..."
            })
            create_migration_job(body, spec, name, namespace)

    elif phase == "WaitingForDatabase":
        if is_database_ready(name, namespace):
            update_status(name, namespace, {
                **current_status,
                "phase": "RunningMigration",
                "databaseReady": True,
                "message": "Database ready, running migrations..."
            })
            create_migration_job(body, spec, name, namespace)

    elif phase == "RunningMigration":
        update_status(name, namespace, {
            **current_status,
            "phase": "WaitingForMigration",
            "message": "Waiting for migration to complete..."
        })

    elif phase == "WaitingForMigration":
        migration_status = get_migration_status(name, namespace)
        if migration_status == "succeeded":
            logger.info(f"Migration completed for {name}")
            update_status(name, namespace, {
                **current_status,
                "phase": "DeployingBackend",
                "migrationCompleted": True,
                "message": "Migration completed, deploying backend..."
            })
            create_backend(body, spec, name, namespace)
        elif migration_status == "failed":
            update_status(name, namespace, {
                **current_status,
                "phase": "Failed",
                "message": "Migration failed! Check job logs."
            })

    elif phase == "DeployingBackend":
        if is_deployment_ready(f"{name}-backend", namespace):
            logger.info(f"Backend is ready for {name}")
            update_status(name, namespace, {
                **current_status,
                "phase": "DeployingFrontend",
                "backendReady": True,
                "message": "Backend ready, deploying frontend..."
            })
            create_frontend(body, spec, name, namespace)
        else:
            update_status(name, namespace, {
                **current_status,
                "message": "Waiting for backend pods to be ready..."
            })

    elif phase == "DeployingFrontend":
        if is_deployment_ready(f"{name}-frontend", namespace):
            logger.info(f"Frontend is ready for {name}")
            update_status(name, namespace, {
                **current_status,
                "phase": "Ready",
                "frontendReady": True,
                "message": "Application is fully deployed and ready!"
            })
        else:
            update_status(name, namespace, {
                **current_status,
                "message": "Waiting for frontend pods to be ready..."
            })

    elif phase == "Ready":
        # Verify all components still healthy
        all_healthy = (
            is_database_ready(name, namespace) and
            is_deployment_ready(f"{name}-backend", namespace) and
            is_deployment_ready(f"{name}-frontend", namespace)
        )
        if not all_healthy:
            update_status(name, namespace, {
                **current_status,
                "message": "Some components unhealthy, checking..."
            })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_database_ready(name: str, namespace: str) -> bool:
    """Check if PostgreSQL StatefulSet is ready."""
    try:
        sts = apps_api.read_namespaced_stateful_set(f"{name}-postgres", namespace)
        return sts.status.ready_replicas == sts.spec.replicas
    except:
        return False


def get_migration_status(name: str, namespace: str) -> str:
    """Get migration job status: pending, running, succeeded, failed."""
    try:
        job = batch_api.read_namespaced_job(f"{name}-migration", namespace)
        if job.status.succeeded and job.status.succeeded > 0:
            return "succeeded"
        elif job.status.failed and job.status.failed > 0:
            return "failed"
        elif job.status.active and job.status.active > 0:
            return "running"
        return "pending"
    except:
        return "pending"


def is_deployment_ready(name: str, namespace: str) -> bool:
    """Check if Deployment is ready."""
    try:
        deployment = apps_api.read_namespaced_deployment(name, namespace)
        return (
            deployment.status.ready_replicas is not None and
            deployment.status.ready_replicas == deployment.spec.replicas
        )
    except:
        return False


# ============================================================================
# DELETE HANDLER
# ============================================================================

@kopf.on.delete(GROUP, VERSION, PLURAL)
def on_delete(body, name, namespace, logger, **kwargs):
    """Handle DevOpsDojo CR deletion."""
    logger.info(f"Deleting DevOpsDojo: {name}")
    # Owner references will handle cascade deletion
    return {"message": f"DevOpsDojo {name} deletion initiated"}


# ============================================================================
# UPDATE HANDLER
# ============================================================================

@kopf.on.update(GROUP, VERSION, PLURAL)
def on_update(body, spec, name, namespace, status, logger, **kwargs):
    """Handle DevOpsDojo CR updates."""
    logger.info(f"Updating DevOpsDojo: {name}")

    current_status = status or {}

    # Update deployments if spec changed
    if current_status.get("phase") == "Ready":
        try:
            # Update backend
            backend_spec = spec.get("backend", {})
            backend = apps_api.read_namespaced_deployment(f"{name}-backend", namespace)
            backend.spec.replicas = backend_spec.get("replicas", 2)
            backend.spec.template.spec.containers[0].image = backend_spec.get(
                "image", "livingdevopswithakhilesh/devopsdozo:backend-latest-1"
            )
            apps_api.patch_namespaced_deployment(f"{name}-backend", namespace, backend)

            # Update frontend
            frontend_spec = spec.get("frontend", {})
            frontend = apps_api.read_namespaced_deployment(f"{name}-frontend", namespace)
            frontend.spec.replicas = frontend_spec.get("replicas", 2)
            frontend.spec.template.spec.containers[0].image = frontend_spec.get(
                "image", "livingdevopswithakhilesh/devopsdozo:frontend-latest-1"
            )
            apps_api.patch_namespaced_deployment(f"{name}-frontend", namespace, frontend)

            logger.info(f"Updated deployments for {name}")
        except Exception as e:
            logger.error(f"Failed to update deployments: {e}")

    return {"message": f"DevOpsDojo {name} update processed"}
