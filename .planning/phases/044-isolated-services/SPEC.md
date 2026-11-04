# Isolated local service verification

Run the optional PostgreSQL, Redis and LocalStack service checks in a dedicated Compose project with dynamically allocated loopback ports. Verify actual operations against the owned containers, record commands, exit codes and outputs, and remove only resources created by this run. Existing containers and campaign state must remain untouched. No model requests are authorized by this phase.
