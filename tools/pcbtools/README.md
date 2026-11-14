# PCB tooling

[Freerouting](https://github.com/freerouting/freerouting) 2.5.0 is an optional autorouter for the SCM-1 board (`SCM_ROUTER=freerouting pcb/build_scm.sh`). It is GPL-3.0 and is not committed. Fetch the build for your platform and verify it against the upstream checksums in `freerouting-cli-2.5.0-checksums.txt`:

```bash
scripts/fetch_assets.sh freerouting
```

The EC2 build host uses the Freerouting 2.1.0 JAR instead (`tools/ec2_build/bootstrap.sh`, `FREEROUTING_JAR`).
