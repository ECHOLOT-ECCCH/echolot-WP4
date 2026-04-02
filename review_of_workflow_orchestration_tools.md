# Rational
ECHOLOT needs a solution for executing long running, complex pipelines that take data from somewhere (mainly the ECHOLOT wiki), does something with the data and saves it to another system (ECHOLOT wiki, wikidata, ECCCH etc.). This document is an evaluation of existing solutions with regards to ECHOLOTs demands.

## Evaluation Criteria

| Criteria | Description |
|----------|-------------|
| **License** | Open source license type (permissive vs copyleft) |
| **Programming Languages** | Which languages can be used to define workflows/tasks |
| **Deployment** | Self-hosted, cloud-only, or both; complexity of deployment |
| **Standards** | Adherence to industry standards (OpenAPI, CloudEvents, etc.) |
| **Adoption** | Community size, enterprise usage, GitHub stars |
| **Human in the Loop** | Ability to pause workflows for manual intervention/approval |
| **Development Activity** | Release frequency, maintainability, documentation quality |
| **API Accessibility** | REST API availability for programmatic access |
| **State Management** | How workflow state is persisted and recovered |
| **Observability** | Built-in monitoring, logging, alerting capabilities |

## Tools Under Review

### 1. Prefect.io

🔗 https://www.prefect.io/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 (open source core) |
| **Programming Languages** | Python-first (primary), can trigger any task via subprocess |
| **Deployment** | Self-hosted (open source) or Prefect Cloud (managed); Docker/Kubernetes capable |
| **Standards** | Uses Pydantic for validation; OpenAPI/Swagger for API |
| **Adoption** | 22k+ GitHub stars; used by Cash App, NASA, Cisco, Meta, 1Password |
| **Human in the Loop** | Yes - supports manual approval tasks, task runners can be paused |
| **Development Activity** | Very active; frequent releases; strong documentation |
| **API Accessibility** | Full REST API via Prefect Cloud; open source API server available |
| **State Management** | PostgreSQL backend; automatic checkpointing |
| **Observability** | Excellent - real-time UI, logs, retry handling, dataflow tracking |

**Strengths:**
- Python-native with elegant decorator-based API
- Excellent observability and debugging tools
- Strong cloud offering with autoscaling workers
- Good for ML/AI workflows
- Active community and regular releases

**Weaknesses:**
- Cloud lock-in risk with Prefect Cloud
- Heavy reliance on Prefect's ecosystem for best experience
- Larger deployment footprint than some alternatives

---

### 2. Apache Airflow

🔗 https://airflow.apache.org/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Python (primary); operators can trigger any language via subprocess/BashOperator |
| **Deployment** | Self-hosted; CeleryExecutor or KubernetesExecutor for scale; Astronomer for managed |
| **Standards** | Large ecosystem of "providers" for integrations; follows PEP8; Jinja templating |
| **Adoption** | Largest adoption in data orchestration; 33k+ GitHub stars; massive enterprise use |
| **Human in the Loop** | Limited - relies on ExternalTaskSensor or custom sensors; no native approval flow |
| **Development Activity** | Very mature; Apache project; regular releases; extensive documentation |
| **API Accessibility** | REST API available via Airflow 2.0+; CLI comprehensive |
| **State Management** | Metadata database (PostgreSQL/MySQL); Scheduler/Executor pattern |
| **Observability** | Strong UI; logging integrated; connection to monitoring tools |

**Strengths:**
- Largest community and ecosystem
- Mature, production-tested at massive scale
- Huge library of pre-built operators
- Good for batch processing pipelines

**Weaknesses:**
- Python-only workflows
- Complex deployment and configuration
- Limited native human-in-the-loop support
- UI can be slow with many DAGs
- No native support for streaming/bulk operations

---

### 3. Luigi

🔗 https://github.com/spotify/luigi

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Python only |
| **Deployment** | Self-hosted; simple architecture (central scheduler + workers) |
| **Standards** | Minimal; Python-based configuration |
| **Adoption** | 18.7k GitHub stars; used by Spotify, Foursquare, Stripe, Groupon, etc. |
| **Human in the Loop** | Possible via custom implementation but not native |
| **Development Activity** | Low activity; maintained but not heavily developed; limited releases |
| **API Accessibility** | Limited REST API; primarily CLI-driven |
| **State Management** | File-based (HDFS or local); task results stored as files |
| **Observability** | Basic web UI for visualization; limited metrics |

**Strengths:**
- Simple, lightweight architecture
- Easy to extend with custom Tasks
- Good for Hadoop/batch processing
- Python-only is simple for Python teams

**Weaknesses:**
- No native human-in-the-loop
- Limited scalability (no distributed execution without extra tools)
- Development has slowed significantly
- Minimal external integrations out of the box
- No streaming support

---

### 4. Dagster

🔗 https://dagster.io/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 (open source) |
| **Programming Languages** | Python-first; can invoke any language via subprocess |
| **Deployment** | Self-hosted or Dagster Cloud (managed); Docker/Kubernetes |
| **Standards** | Asset-based model; OpenTelemetry for observability; Good ISO CQL |
| **Adoption** | Growing rapidly; 9k+ GitHub stars; Bayer, Weights & Biases, Airbus use it |
| **Human in the Loop** | Yes - asset materialization can be triggered manually; sensor-based approvals |
| **Development Activity** | Very active; backed by Elementl (company); frequent releases |
| **API Accessibility** | GraphQL API; REST API; Dagster Cloud API |
| **State Management** | PostgreSQL backend; dagster-daemon for orchestration |
| **Observability** | Excellent - asset lineage, data quality checks, integrated UI |

**Strengths:**
- Asset-based approach excellent for data engineering
- Strong data quality and cataloging features
- Modern, developer-friendly API
- Good CI/CD integration
- Built-in data lineage

**Weaknesses:**
- Python-only for definitions
- More opinionated about data engineering patterns
- Cloud offering relatively new
- Steeper learning curve for non-data engineers

---

### 5. Kestra

🔗 https://kestra.io/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 (fully open source) |
| **Programming Languages** | Language-agnostic - YAML definitions; Python, Bash, Node.js, Go, Java, Ruby via plugins |
| **Deployment** | Self-hosted (Docker/Kubernetes) or Kestra Cloud; runs anywhere |
| **Standards** | 1200+ plugins; OpenAPI support; event-driven via webhooks/schedules |
| **Adoption** | 9k+ GitHub stars; growing rapidly; JPMorgan Chase, Toyota, Xiaomi users |
| **Human in the Loop** | Yes - native approval tasks, manual triggers, backfills |
| **Development Activity** | Very active; regular releases; strong community growth |
| **API Accessibility** | Full REST API; GraphQL; CLI |
| **State Management** | PostgreSQL backend; persistent execution state |
| **Observability** | Excellent - real-time UI, logs, metrics, audit logs |

**Strengths:**
- Truly language-agnostic via plugins
- Event-driven (triggers: schedule, webhook, event)
- Declarative YAML syntax is approachable
- Massive plugin ecosystem
- Excellent for hybrid infrastructure automation

**Weaknesses:**
- YAML-based workflows can become verbose
- Less mature than Airflow/ Prefect
- Smaller community than established tools
- Newer to market

---

### 6. Temporal

🔗 https://temporal.io/

| Aspect | Details |
|--------|---------|
| **License** | MIT (open source core) |
| **Programming Languages** | Go, Python, TypeScript, Java, Ruby, PHP, C# |
| **Deployment** | Self-hosted (Temporal Cluster) or Temporal Cloud (managed) |
| **Standards** | Durable execution model; event sourcing; OpenTelemetry support |
| **Adoption** | 19k+ GitHub stars; used by Netflix, Snap, Stripe, Uber, DoorDash |
| **Human in the Loop** | Excellent - signals allow external input; workflow can wait for human approval |
| **Development Activity** | Very active; backed by Temporal Technologies (VC funded) |
| **API Accessibility** | gRPC and REST; client SDKs in multiple languages |
| **State Management** | Built-in durable execution; state persisted to database; automatic recovery |
| **Observability** | Strong - Workflow history, tracing, metrics; UI dashboard |

**Strengths:**
- Fault-tolerant by design (durable execution)
- Excellent for long-running workflows (days/weeks)
- Built-in retry logic and compensation (saga pattern)
- Strong human-in-the-loop via signals
- Multiple language SDKs

**Weaknesses:**
- Requires Temporal server infrastructure
- Complex local development setup
- Workflow code must be deterministic (limitation on some patterns)
- Event sourcing model can be unfamiliar
- Debugging can be challenging

---

### 7. Nextflow

🔗 https://www.nextflow.io/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Nextflow DSL (Groovy-based); any language via process/ executor |
| **Deployment** | Self-hosted; HPC, AWS, GCP, Azure, Kubernetes; cloud-native |
| **Standards** | nf-core ecosystem; container support (Docker, Singularity); CWL/WDL support via plugins |
| **Adoption** | 3.3k GitHub stars; heavy adoption in bioinformatics (nf-core: 100+ pipelines) |
| **Human in the Loop** | Limited - primarily batch-oriented; manual resume possible |
| **Development Activity** | Active; backed by Seqera; regular releases |
| **API Accessibility** | Limited API; primarily file-based/CLI |
| **State Management** | Checkpointing to file system; resume from last successful step |
| **Observability** | Good - real-time monitoring; nf-core sharing standards |

**Strengths:**
- Excellent for scientific workflows
- Strong containerization and reproducibility
- nf-core ecosystem for bioinformatics
- Native support for HPC schedulers
- Dataflow programming model simplifies parallelism

**Weaknesses:**
- Domain-specific (bioinformatics focus)
- Groovy DSL adds learning curve
- Limited enterprise features
- No native human-in-the-loop
- Less suitable for general-purpose pipelines

---

### 8. StackStorm

🔗 https://stackstorm.com/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Python; any language via shell commands |
| **Deployment** | Self-hosted; Docker, Kubernetes; Linux-focused |
| **Standards** | Exchange (plugin library); Webhooks; ChatOps |
| **Adoption** | 6k+ GitHub stars; used by Netflix (Winston), Target, Pearson |
| **Human in the Loop** | Excellent - rules engine with manual approvals; ChatOps integration |
| **Development Activity** | Moderate; Linux Foundation project; slower release cycle |
| **API Accessibility** | REST API; CLI; ChatOps |
| **State Management** | MongoDB backend; action execution state |
| **Observability** | Good - logging, audit trails, ChatOps integration |

**Strengths:**
- Event-driven automation
- Excellent for DevOps/IT automation
- Strong ChatOps integration
- Rule-based with excellent flexibility
- Good for incident response

**Weaknesses:**
- Complex setup and configuration
- UI less modern than alternatives
- YAML/rule-based, not code-first
- Primarily IT/DevOps focused, not data pipelines
- Performance at scale can be an issue

---

### 9. n8n

🔗 https://n8n.io/

| Aspect | Details |
|--------|---------|
| **License** | Sustainable Source License (custom) + Apache 2.0 for some components |
| **Programming Languages** | Node.js/JavaScript; Python via code nodes; 500+ integrations |
| **Deployment** | Self-hosted (Docker/Kubernetes) or n8n Cloud |
| **Standards** | 500+ pre-built integrations; webhooks; OpenAPI |
| **Adoption** | 181k GitHub stars; massive growth; used by thousands of teams |
| **Human in the Loop** | Yes - approval nodes, manual triggers, human-in-the-loop AI workflows |
| **Development Activity** | Very active; commercial company backing |
| **API Accessibility** | REST API; webhook triggers; CLI |
| **State Management** | PostgreSQL (self-hosted); cloud version managed |
| **Observability** | Good - workflow execution history, error handling, logs |

**Strengths:**
- Visual workflow builder (low-code)
- Massive integration library
- Easy to get started
- Good for AI/LLM integrations
- Strong community

**Weaknesses:**
- Custom license (Sustainable Source) restricts some use cases
- Code execution limited to JavaScript/Python nodes
- Visual workflows can become complex to maintain
- Less control than code-first approaches
- Scale concerns for very large workflows

---

## Additional Tools to Consider

### Flyte (Lyft)

🔗 https://flyte.org/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Python, Java, C++; Flytekit for Python |
| **Deployment** | Self-hosted (Kubernetes) or Flyte Cloud (managed) |
| **Standards** | Container-based; structured datasets; LaunchPlans |
| **Adoption** | 9.6k GitHub stars; Lyft, Spotify, Amazon, Union.ai backing |
| **Human in the Loop** | Yes - notifications, approval workflows via FlyteConsole |
| **Development Activity** | Active; Union AI commercial backing |
| **API Accessibility** | REST API; FlyteCTL CLI |
| **State Management** | Kubernetes-native; etcd for coordination |
| **Observability** | FlyteConsole for visualization; Kubernetes-native metrics |

### Apache Beam

🔗 https://beam.apache.org/

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Programming Languages** | Java, Python, Go, SQL, Scala |
| **Deployment** | Portable (runners: Flink, Spark, Dataflow, etc.) |
| **Standards** | Unified programming model; Cross-language support |
| **Adoption** | 5k GitHub stars; Google, data-intensive processing |
| **Human in the Loop** | Limited - streaming/batch focused |
| **Development Activity** | Moderate; Apache project |
| **API Accessibility** | SDK-based; multiple runners |
| **State Management** | Runner-dependent |
| **Observability** | Runner-dependent |

---

## Summary Comparison Table

| Tool | License | Languages | Deployment | Human in Loop | Adoption (Stars) | Activity | Best For |
|------|---------|-----------|------------|---------------|------------------|----------|----------|
| **Prefect** | Apache 2.0 | Python | Self-hosted/Cloud | Yes | 22k | Very High | Python-centric ML/AI pipelines |
| **Airflow** | Apache 2.0 | Python | Self-hosted | Limited | 33k | Very High | Enterprise data pipelines |
| **Luigi** | Apache 2.0 | Python | Self-hosted | Limited | 18.7k | Low | Hadoop/batch jobs |
| **Dagster** | Apache 2.0 | Python | Self-hosted/Cloud | Yes | 9k | Very High | Data assets & quality |
| **Kestra** | Apache 2.0 | Any (YAML) | Self-hosted/Cloud | Yes | 9k | Very High | Language-agnostic, event-driven |
| **Temporal** | MIT | Go, Python, TS, Java... | Self-hosted/Cloud | Excellent | 19k | Very High | Long-running, fault-tolerant |
| **Nextflow** | Apache 2.0 | DSL (Groovy) | Self-hosted | Limited | 3.3k | High | Scientific workflows |
| **StackStorm** | Apache 2.0 | Python | Self-hosted | Excellent | 6k | Moderate | DevOps/IT automation |
| **n8n** | Custom | JS, Python | Self-hosted/Cloud | Yes | 181k | Very High | Low-code, AI integrations |
| **Flyte** | Apache 2.0 | Python, Java, C++ | Self-hosted/Cloud | Yes | 9.6k | High | ML/data pipelines on K8s |
| **Apache Beam** | Apache 2.0 | Java, Python, Go, SQL | Portable | Limited | 5k | Moderate | Portable batch/streaming |

---

## Recommendations for ECHOLOT

Based on ECHOLOT's requirements (workflow orchestration for automatic enrichment, integration with Wikibase/Wikidata, human-in-the-loop support):

### Top Recommendations

1. **Kestra** - Best for ECHOLOT's use case:
   - Language-agnostic (can integrate with any existing code)
   - Event-driven (can react to wiki changes)
   - Native human-in-the-loop approval workflows
   - 1200+ plugins including many useful for data processing
   - Fully open source (Apache 2.0) with no lock-in
   - Strong API for integration with external systems
   - Excellent for hybrid workloads (data, AI, infrastructure)

2. **Temporal** - Strong alternative for complex workflows:
   - Excellent fault tolerance and state recovery
   - Perfect for long-running enrichment tasks
   - Strong human-in-the-loop via signals
   - Multiple language support for diverse teams
   - MIT license (most permissive)

3. **Prefect** - Best if team is Python-centric:
   - Python-native elegance
   - Excellent observability
   - Strong AI/ML integration
   - Good human-in-the-loop support
   - Note: Cloud has licensing considerations

### Considerations

- **Airflow** has the largest ecosystem but Python-only and limited human-in-the-loop
- **Dagster** excellent for data assets but more opinionated toward data engineering
- **StackStorm** good for IT automation but less suited for data pipelines
- **n8n** great for low-code but custom license may be a concern

### Deployment Considerations

For ECHOLOT, self-hosted deployment is likely preferred to:
- Maintain control over data (especially if processing Wikidata)
- Avoid vendor lock-in
- Support potential air-gapped environments

All major tools except n8n (custom license) support full self-hosted deployment with Apache 2.0 or MIT licenses.

---

## Additional Criteria to Consider

When making a final decision, also evaluate:

1. **Integration with Wikibase** - Does the tool have existing plugins or easy HTTP integration for Wikibase APIs?
2. **Scalability** - Can it handle expected pipeline volume?
3. **Monitoring** - Alerting on failures, SLA tracking
4. **Team Skills** - Learning curve vs. productivity gain
5. **Future-proofing** - Project vitality, commercial backing
6. **Cost** - Infrastructure costs for self-hosted vs. managed services
