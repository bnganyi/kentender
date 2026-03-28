### KenTender (core app)

Frappe app **`kentender`** — platform foundation (Wave 0 ticket name: **kentender_core**). Shared master data, security primitives, and cross-cutting services live here.

### KenTender architecture (STORY-CORE-002)

**Role:** Foundation app; no other KenTender app may sit below this in the dependency graph.  
**Allowed upstream KenTender deps:** none.  
**Do not** import any `kentender_*` package or depend on downstream business apps.  
Full DAG, `required_apps`, naming, and service rules: [App dependencies and boundaries](../docs/architecture/app-dependencies-and-boundaries.md).

### Monorepo / installation

This directory is part of the [KenTender monorepo](../README.md). Use the root README and [`scripts/link_apps_on_bench.sh`](../scripts/link_apps_on_bench.sh) for bench layout.

### License

mit
