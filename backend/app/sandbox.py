import docker
import tarfile
import io
import time
import os
import logging
import yaml
from datetime import datetime
from typing import Optional, Dict, List, Any, AsyncGenerator
from .sandbox_utils import SandboxManifest, detect_project_type, generate_dynamic_dockerfile

logger = logging.getLogger(__name__)

class Sandbox:
    def __init__(self, project_path: str = ".", image: str = "bug-exorcist-sandbox:latest") -> None:
        self.project_path = project_path
        self.use_mock = False
        self.sidecar_containers = []
        self.network = None
        self.session_id = f"exorcist-{int(time.time())}"
        
        # Load manifest
        manifest_path = os.path.join(project_path, ".exorcist.yaml")
        self.manifest = SandboxManifest.from_yaml(manifest_path)

        try:
            self.client = docker.from_env()
            self.image = image
            # Create a dedicated network for this session
            self._create_network()
        except Exception:
            logger.warning("Docker not found or unreachable. Falling back to Mock Sandbox.")
            self.use_mock = True

    def _create_network(self):
        """Creates a dedicated bridge network for this sandbox session."""
        if self.use_mock: return
        try:
            network_name = f"net-{self.session_id}"
            self.network = self.client.networks.create(network_name, driver="bridge")
            logger.info(f"Created dedicated network: {network_name}")
        except Exception as e:
            logger.error(f"Failed to create network: {e}")

    async def _wait_for_service_health(self, container, timeout=30):
        """Waits for a container to become healthy if a healthcheck is defined."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            health = container.attrs.get('State', {}).get('Health', {}).get('Status')
            if health == 'healthy':
                return True
            if health == 'unhealthy':
                return False
            # If no healthcheck is defined, we just wait a bit and assume it's okay
            if health is None:
                await asyncio.sleep(2)
                return True
            await asyncio.sleep(1)
        return False

    async def get_diagnostics(self) -> Dict[str, Any]:
        """
        Runs a suite of diagnostic checks in the sandbox environment.
        Useful for the agent to verify sidecar reachability and env setup.
        """
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "env": {},
            "disk_usage": ""
        }
        
        # Check sidecars
        for sidecar in self.sidecar_containers:
            name = sidecar.name.split('-')[1]
            sidecar.reload()
            diagnostics["services"][name] = {
                "status": sidecar.status,
                "health": sidecar.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown')
            }
            
        # Run basic env checks in a temp container
        check_code = """
import os, sys, shutil
print(f"PYTHON_VER:{sys.version.split()[0]}")
print(f"CWD:{os.getcwd()}")
usage = shutil.disk_usage("/")
print(f"DISK_FREE:{usage.free // (2**20)}MB")
"""
        res = await self.run_code(check_code, "python")
        for line in res.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                diagnostics["env"][k] = v
                
        return diagnostics
        """
        Dynamically builds a Docker image based on project dependencies and manifest.
        Uses hashing for intelligent caching of built images.
        """
        if self.use_mock:
            return self.image

        # Generate Dockerfile content
        dockerfile_content = generate_dynamic_dockerfile(self.project_path, self.manifest, self.image)
        
        # Compute a hash for caching
        import hashlib
        cache_hash = hashlib.sha256(dockerfile_content.encode()).hexdigest()[:12]
        project_id = os.path.basename(os.path.abspath(self.project_path))
        custom_image_tag = f"bug-exorcist-{project_id}:{cache_hash}"
        
        # Check if image already exists in cache
        try:
            self.client.images.get(custom_image_tag)
            logger.info(f"Using cached image: {custom_image_tag}")
            if log_callback:
                await log_callback(f"♻️ Using cached environment: {custom_image_tag}")
            self.image = custom_image_tag
            return custom_image_tag
        except docker.errors.ImageNotFound:
            pass
        
        # Prepare build context
        f = io.BytesIO(dockerfile_content.encode('utf-8'))
        
        try:
            logger.info(f"Building dynamic sandbox image: {custom_image_tag}")
            if log_callback:
                await log_callback(f"🏗️ Building fresh environment: {custom_image_tag}")
                
            build_logs = self.client.api.build(
                fileobj=f,
                tag=custom_image_tag,
                rm=True,
                decode=True
            )
            
            for chunk in build_logs:
                if 'stream' in chunk:
                    log_line = chunk['stream'].strip()
                    if log_line:
                        logger.info(f"Build Log: {log_line}")
                        if log_callback:
                            if hasattr(log_callback, 'send'): # Synchronous callback
                                log_callback.send(log_line)
                            else: # Asynchronous callback
                                await log_callback(log_line)
                elif 'error' in chunk:
                    error_msg = chunk['error']
                    logger.error(f"Build Error: {error_msg}")
                    raise Exception(f"Docker build failed: {error_msg}")

            self.image = custom_image_tag
            return custom_image_tag
        except Exception as e:
            logger.error(f"Failed to build image: {e}")
            return self.image # Fallback to default image

    async def start_sidecars(self):
        """
        Start sidecar containers (e.g., Redis, Postgres) defined in the manifest.
        """
        if self.use_mock or not self.manifest.services:
            return []

        for service in self.manifest.services:
            name = service.get('name')
            image = service.get('image')
            env = service.get('env', {})
            healthcheck = service.get('healthcheck')
            
            if not name or not image:
                continue
                
            try:
                logger.info(f"Starting sidecar service: {name} ({image})")
                container = self.client.containers.run(
                    image,
                    name=f"sidecar-{name}-{self.session_id}",
                    environment=env,
                    detach=True,
                    network=self.network.name if self.network else "bridge",
                    healthcheck=healthcheck
                )
                self.sidecar_containers.append(container)
                
                # Wait for service to be ready
                is_ready = await self._wait_for_service_health(container)
                if not is_ready:
                    logger.warning(f"Service {name} failed health check or timed out.")
                else:
                    logger.info(f"Service {name} is ready.")
                    
            except Exception as e:
                logger.error(f"Failed to start sidecar {name}: {e}")

    def cleanup_sidecars(self):
        """
        Stop and remove all sidecar containers and the session network.
        """
        for container in self.sidecar_containers:
            try:
                container.stop(timeout=1)
                container.remove(force=True)
            except Exception:
                pass
        self.sidecar_containers = []
        
        if self.network:
            try:
                self.network.remove()
                logger.info(f"Removed dedicated network: {self.network.name}")
            except Exception:
                pass
            self.network = None

    async def run_code(self, code: str, language: str = "python") -> str:
        """
        Executes code in a secure Docker sandbox.
        """
        if self.use_mock:
            return "Mock execution successful (Docker not available)."

        container = None
        try:
            # Start sidecars first
            await self.start_sidecars()
            
            # Configure resource limits from manifest or defaults
            mem_limit = self.manifest.resources.get('memory', "512m")
            cpu_limit = self.manifest.resources.get('cpu', 0.5)
            nano_cpus = int(cpu_limit * 1_000_000_000)
            
            # Map language to execution command
            commands = {
                "python": ["/bin/sh", "-c", "python3 -c \"import sys; exec(sys.stdin.read())\""],
                "javascript": ["/bin/sh", "-c", "node -e \"$(cat)\""],
                "nodejs": ["/bin/sh", "-c", "node -e \"$(cat)\""],
                "go": ["/bin/sh", "-c", "cat > main.go && go run main.go"],
                "go-test": ["/bin/sh", "-c", "cat > main_test.go && go test -v"],
                "rust": ["/bin/sh", "-c", "cat > main.rs && rustc main.rs -o main && ./main"],
                "cargo-test": ["/bin/sh", "-c", "cargo test"],
                "npm-test": ["/bin/sh", "-c", "cat > test.js && npm test -- --test-file=test.js"],
                "bash": ["/bin/bash", "-c", "$(cat)"]
            }
            
            command = commands.get(language.lower(), commands["python"])

            # Set up environment variables
            env_vars = self.manifest.env.copy()
            
            # Volume configuration
            volumes = {}
            for host_path, container_path in self.manifest.volumes.items():
                # Ensure paths are absolute for Docker
                abs_host_path = os.path.abspath(os.path.join(self.project_path, host_path))
                volumes[abs_host_path] = {'bind': container_path, 'mode': 'rw'}

            # Create the container with restrictions
            container = self.client.containers.run(
                self.image,
                command=command,
                stdin_open=True,
                detach=True,
                environment=env_vars,
                volumes=volumes,
                # Security restrictions
                network=self.network.name if self.network else "none",
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                cap_drop=["ALL"] 
            )

            sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
            sock.send(code.encode('utf-8'))
            sock.close() 

            try:
                result = container.wait(timeout=30)
                exit_code = result['StatusCode']
            except Exception:
                container.kill()
                return "Error: Execution timed out (30s limit)."

            # Get logs
            logs = container.logs().decode('utf-8')
            
            if exit_code != 0:
                return f"Error (Exit Code {exit_code}):\n{logs}"
            
            return logs

        except Exception as e:
            return f"System Error: {str(e)}"
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            self.cleanup_sidecars()
