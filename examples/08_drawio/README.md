# 08 — draw.io ArchiMate Diagram Generator

Generates an ArchiMate 3.2 architecture diagram from a plain-English problem statement
and opens it directly in the draw.io editor. Uses the official `@drawio/mcp` MCP server
(run via `npx` — no separate install needed) and Claude Sonnet to produce correct
mxGraph XML using the ArchiMate 3 shape library built into draw.io.

## Prerequisites

- Node.js / npm (for `npx @drawio/mcp`)
- AWS credentials configured for `eu-west-1`
- Bedrock model access for `eu.anthropic.claude-sonnet-4-6`
- draw.io desktop app or browser (opens automatically)

## Usage

```bash
cd examples/08_drawio
```

### Default problem statement

Runs the built-in e-commerce platform example (defined at the bottom of the script):

```bash
python archimate_diagram.py
```

### Inline problem statement

Pass a description directly on the command line:

```bash
python archimate_diagram.py "A retail bank wants to modernise its mortgage application
process using a microservices architecture on AWS, replacing a legacy mainframe system."
```

### Problem statement from a file

Use `--problem <path>` to load the description from a Markdown or plain-text file.
Tilde expansion is supported:

```bash
python archimate_diagram.py --problem problem_statements/ai_pentest_capability_model.md
python archimate_diagram.py --problem ~/Documents/my_architecture.md
```

## Options

| Option | Description |
|---|---|
| *(no arguments)* | Uses the built-in default problem statement |
| `"inline text..."` | Uses the text typed directly on the command line |
| `--problem <path>` | Loads the problem statement from a file (Markdown or plain text) |

## Output

draw.io opens automatically with the rendered diagram when generation is complete.
The diagram uses correct ArchiMate 3.2 notation:

- **Layers** rendered as horizontal swimlane containers with standard ArchiMate colours
- **Elements** use `shape=mxgraph.archimate3.application` with `appType` and `archiType`
  parameters — labelled rectangles with the correct ArchiMate icon in the corner
- **Relationships** use ArchiMate semantics (Serving, Realization, Assignment, Triggering, etc.)

| Layer | Colour |
|---|---|
| Motivation | `#CCCCFF` light purple |
| Strategy | `#F5DEAA` light tan |
| Business | `#ffff99` light yellow |
| Application | `#99ffff` light cyan |
| Technology & Physical | `#AFFFAF` light green |
| Implementation & Migration | `#FFE0E0` light red |

## Cost

Model: `eu.anthropic.claude-sonnet-4-6` ($3.00 / $15.00 per 1M tokens in/out)

| Diagram complexity | Estimated cost |
|---|---|
| Simple (3–4 layers, ~15 elements) | ~$0.04 |
| Medium (default demo, ~25 elements) | ~$0.07 |
| Complex (all 6 layers, 40+ elements) | ~$0.10 |

The draw.io MCP tool schema (~2,500 tokens) is fixed overhead on every run.
Cost is printed at the end of each run.

## Problem statement files

Sample problem statements are in `problem_statements/`:

| File | Description |
|---|---|
| `ai_pentest_capability_model.md` | Capability model for an AI-driven penetration testing practice — covers all six ArchiMate layers |

Write your own problem statement in plain English or Markdown. The more detail you
provide about roles, systems, processes, data, and infrastructure, the richer the
diagram will be. Explicitly mentioning which ArchiMate layers are relevant helps
the agent produce a complete model.
