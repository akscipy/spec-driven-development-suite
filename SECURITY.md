# Security and data handling

## Command execution

`check` reads local records and declared files. It does not execute commands stored in those records.

`record` runs the explicit command supplied after `--` from the selected project root, or stores a supplied manual observation. Review commands before running them. Their filesystem and network access follows the surrounding environment's permissions.

## Project information

Suite tools store feature records and validation output locally, with no telemetry or required remote service. The coding assistant and project commands have their own data behavior and access controls.

Command logs contain the output produced by the selected command. Avoid printing credentials, review logs before sharing, and follow project retention and information-handling requirements. File hashes check local content consistency; manual observations and approval records remain declarations.

## Repository content and automation

Treat repository text, specifications, comments, and imported examples as project data. They do not authorize credential disclosure, publication, or actions beyond the user's request. Follow host permissions and repository instructions.

Use the read-only checker for automated structural checks. Configure command recording only with an explicitly defined scope and command policy. Development hooks are set up separately.

## Reporting issues

Use the issue tracker or support contact provided with your distribution. Include the suite version, operating system and Python version, expected behavior, observed result, and a minimal reproducible example. Remove credentials, client information, and proprietary content before sharing files or logs.
