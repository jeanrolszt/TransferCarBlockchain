import subprocess

subprocess.run(["docker", "build", "-t", "transfercarblockchain", "."]) 
subprocess.run(["docker","run","-ti", "transfercarblockchain"]) 
