import subprocess

# criar nós aleatórios


# rodar docker build
subprocess.run(["docker", "build", "-t", "transfercarimage", "."]) 
subprocess.run(["docker-compose", "up"]) 