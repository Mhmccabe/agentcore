"""
Draw.io ArchiMate 3.2 Diagram Generator
Generates an ArchiMate 3.2 architecture diagram from a plain-English problem
statement and opens it directly in the draw.io editor.

The agent uses the official @drawio/mcp MCP server (run via npx — no install
needed) and generates valid mxGraph XML using the ArchiMate 3 shape library
that ships with draw.io.

Architecture:
    problem statement (CLI arg or default)
         |
         v
    Strands Agent  (Claude Sonnet 4.6)
         |
         | reasons about ArchiMate 3.2 layers and elements
         v
    generates mxGraph XML using shape=mxgraph.archimate3.*
         |
         | stdio (JSON-RPC)
         v
    @drawio/mcp  MCP server  (npx, no install required)
         |
         | open_drawio_xml tool
         v
    draw.io editor opens with rendered ArchiMate diagram

Requires:
    npx   (Node.js / npm — already present if npm is installed)
    AWS credentials with access to eu.anthropic.claude-sonnet-4-6

Usage:
    python archimate_diagram.py
    python archimate_diagram.py "Describe your system here"

Note: draw.io will open in your browser or desktop app when the diagram
is ready. The agent prints the generated XML before opening it.
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

SYSTEM_PROMPT = """You are an expert enterprise architect specialising in ArchiMate 3.2.
Your task: given a problem statement, produce a complete ArchiMate 3.2 architecture
diagram and open it in draw.io using the open_drawio_xml tool.

## ArchiMate 3.2 layers — use these swimlane containers

Represent each layer as a horizontal swimlane group (parent container) with the
correct fill colour. Only include layers relevant to the problem.

| Layer                      | fillColor |
|----------------------------|-----------|
| Motivation                 | #CCCCFF   |
| Strategy                   | #F5DEAA   |
| Business                   | #ffff99   |
| Application                | #99ffff   |
| Technology & Physical      | #AFFFAF   |
| Implementation & Migration | #FFE0E0   |

## ArchiMate 3 shape styles — ALL elements use the same base shape

Every element uses this single base shape:
  shape=mxgraph.archimate3.application

Combined with two parameters:
  appType=<type>      — sets the element-type icon in the top-right corner
  archiType=<variant> — sets the overall box shape:
                          square   = Active Structure (straight-cornered rectangle)
                          rounded  = Behavioural (rounded rectangle)
                          oct      = Motivation (octagonal badge shape)

The full style template for any element is:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=<layer-color>;shape=mxgraph.archimate3.application;appType=<type>;archiType=<variant>;

This produces a labelled rectangle with the correct ArchiMate icon — NOT an icon-only shape.
Width=140, Height=60 for all elements.

### Business layer  (fillColor=#ffff99)

  Actor:              appType=actor;        archiType=square;
  Role:               appType=role;         archiType=square;
  Collaboration:      appType=collab;       archiType=square;
  Interface:          appType=interface;    archiType=square;
  Process:            appType=proc;         archiType=rounded;
  Function:           appType=func;         archiType=rounded;
  Interaction:        appType=interaction;  archiType=rounded;
  Event:              appType=event;        archiType=rounded;
  Service:            appType=serv;         archiType=rounded;
  Business Object:    appType=passive;      archiType=square;
  Contract:           appType=contract;     archiType=square;
  Representation:     appType=representation; archiType=square;
  Product:            appType=product;      archiType=square;

### Application layer  (fillColor=#99ffff)

  Component:          appType=comp;         archiType=square;
  Collaboration:      appType=collab;       archiType=square;
  Interface:          appType=interface;    archiType=square;
  Function:           appType=func;         archiType=rounded;
  Interaction:        appType=interaction;  archiType=rounded;
  Process:            appType=proc;         archiType=rounded;
  Event:              appType=event;        archiType=rounded;
  Service:            appType=serv;         archiType=rounded;
  Data Object:        appType=passive;      archiType=square;

### Technology & Physical layer  (fillColor=#AFFFAF)

  Node:               appType=node;         archiType=square;
  Device:             appType=device;       archiType=square;
  System Software:    appType=sysSw;        archiType=square;
  Collaboration:      appType=collab;       archiType=square;
  Interface:          appType=interface;    archiType=square;
  Path:               appType=path;         archiType=square;
  Network:            appType=netw;         archiType=square;
  Function:           appType=func;         archiType=rounded;
  Process:            appType=proc;         archiType=rounded;
  Interaction:        appType=interaction;  archiType=rounded;
  Event:              appType=event;        archiType=rounded;
  Service:            appType=serv;         archiType=rounded;
  Artifact:           appType=artifact;     archiType=square;
  Equipment:          appType=equipment;    archiType=square;
  Facility:           appType=facility;     archiType=square;
  Material:           appType=material;     archiType=square;

### Motivation layer  (fillColor=#CCCCFF)

  Stakeholder:        appType=role;         archiType=oct;
  Driver:             appType=driver;       archiType=oct;
  Assessment:         appType=assess;       archiType=oct;
  Goal:               appType=goal;         archiType=oct;
  Outcome:            appType=outcome;      archiType=oct;
  Principle:          appType=principle;    archiType=oct;
  Requirement:        appType=requirement;  archiType=oct;
  Constraint:         appType=constraint;   archiType=oct;
  Meaning:            appType=meaning;      archiType=oct;
  Value:              appType=amValue;      archiType=oct;

### Strategy layer  (fillColor=#F5DEAA)

  Resource:           appType=resource;     archiType=square;
  Capability:         appType=capability;   archiType=rounded;
  Value Stream:       appType=valueStream;  archiType=rounded;
  Course of Action:   appType=course;       archiType=rounded;

### Implementation & Migration layer  (fillColor=#FFE0E0)

  Work Package:       appType=workPackage;  archiType=rounded;
  Deliverable:        appType=deliverable;  archiType=square;
  Implementation Event: appType=event;      archiType=rounded;
  Plateau:            appType=plateau;      archiType=square;
  Gap:                appType=gap;          archiType=square;

### Example element styles (copy these patterns exactly)

Business Process:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#ffff99;shape=mxgraph.archimate3.application;appType=proc;archiType=rounded;

Application Component:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#99ffff;shape=mxgraph.archimate3.application;appType=comp;archiType=square;

Technology Network:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#AFFFAF;shape=mxgraph.archimate3.application;appType=netw;archiType=square;

Technology Node:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#AFFFAF;shape=mxgraph.archimate3.application;appType=node;archiType=square;

Application Service:
  html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#99ffff;shape=mxgraph.archimate3.application;appType=serv;archiType=rounded;

## ArchiMate 3.2 relationship styles

Use these exact edge styles for the seven core relationship types:

  Serving (solid arrow, open head):
    style=endArrow=open;endFill=0;edgeStyle=orthogonalEdgeStyle;html=1;

  Realization (dashed arrow, open head):
    style=endArrow=open;endFill=0;dashed=1;edgeStyle=orthogonalEdgeStyle;html=1;

  Composition (solid line, filled diamond at source):
    style=endArrow=none;startArrow=ERmandOne;startFill=1;edgeStyle=orthogonalEdgeStyle;html=1;

  Aggregation (solid line, open diamond at source):
    style=endArrow=none;startArrow=ERmanyToOne;startFill=0;edgeStyle=orthogonalEdgeStyle;html=1;

  Assignment (solid line, filled circle at source):
    style=endArrow=open;endFill=0;startArrow=ERone;startFill=1;edgeStyle=orthogonalEdgeStyle;html=1;

  Triggering (solid arrow, filled head):
    style=endArrow=block;endFill=1;edgeStyle=orthogonalEdgeStyle;html=1;

  Flow (dashed arrow, filled head):
    style=endArrow=block;endFill=1;dashed=1;edgeStyle=orthogonalEdgeStyle;html=1;

  Association (plain line, no arrowhead):
    style=endArrow=none;edgeStyle=orthogonalEdgeStyle;html=1;

  Influence (dashed line, open head):
    style=endArrow=open;endFill=0;dashed=1;edgeStyle=orthogonalEdgeStyle;html=1;

## Layout rules

1. Place layer swimlane containers stacked vertically (Business on top, Technology at bottom).
2. Elements within a layer are arranged left to right.
3. Use the rigid grid: col x = col_index * 180 + 60, row y = row_index * 100 + 40 inside each layer.
4. Layer swimlane containers: x=0, y=stacked, width=1000 (or wider), height=200 per layer.
5. Elements are children of their layer container (set parent to the layer cell id).
6. Do not compute waypoints — draw.io routes edges automatically.

## XML structure

```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- Layer swimlane -->
    <mxCell id="layer_app" value="Application Layer" style="swimlane;startSize=30;fillColor=#99ffff;strokeColor=#000000;fontStyle=1;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="0" y="250" width="1000" height="200" as="geometry"/>
    </mxCell>

    <!-- Element inside layer — note: appType+archiType drive the icon, fillColor must match the layer -->
    <mxCell id="e1" value="Order Service" style="html=1;outlineConnect=0;whiteSpace=wrap;fillColor=#99ffff;shape=mxgraph.archimate3.application;appType=serv;archiType=rounded;" vertex="1" parent="layer_app">
      <mxGeometry x="60" y="80" width="140" height="60" as="geometry"/>
    </mxCell>

    <!-- Relationship -->
    <mxCell id="r1" value="serves" style="endArrow=open;endFill=0;edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="e1" target="e2" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

## Process

1. Analyse the problem statement — identify actors, systems, services, data, and technology.
2. Map each element to an ArchiMate layer and element type.
3. Identify relationships between elements using ArchiMate relationship semantics.
4. Generate complete, well-formed mxGraph XML with all elements and relationships.
5. Call open_drawio_xml with the XML to open the diagram.

Generate a complete, meaningful diagram — not a minimal skeleton. Include all significant
elements implied by the problem statement.
"""

DEFAULT_PROBLEM = """
An online retail company wants to sell products through a web storefront and mobile app.
Customers browse a product catalogue, add items to a cart, and place orders.
Orders are processed by a payment service (Stripe) and fulfilled by a warehouse management
system. Inventory is tracked in a central database. An event-driven notification service
emails customers with order status updates. The platform runs on AWS: containerised
microservices on ECS, an Aurora PostgreSQL database, S3 for product images, and
CloudFront as the CDN.
"""

model = BedrockModel(
    model_id="eu.anthropic.claude-sonnet-4-6",
    region_name="eu-west-1",
)

server_params = StdioServerParameters(
    command="npx",
    args=["@drawio/mcp"],
)

mcp_client = MCPClient(lambda: stdio_client(server_params))

with mcp_client:
    tools = mcp_client.list_tools_sync()
    print(f"Connected to draw.io MCP server — {len(tools)} tools available:")
    for t in tools:
        print(f"  - {t.tool_name}")
    print()

    agent = TrackedAgent(Agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    ))

    parser = argparse.ArgumentParser(description="Generate an ArchiMate 3.2 diagram from a problem statement.")
    parser.add_argument("--problem", metavar="URI", help="Path to a file containing the problem statement")
    parser.add_argument("words", nargs="*", help="Inline problem statement (alternative to --problem)")
    args = parser.parse_args()

    if args.problem:
        path = os.path.expanduser(args.problem)
        if not os.path.exists(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path) as f:
            problem = f.read()
        print(f"Problem statement loaded from: {path}\n")
    elif args.words:
        problem = " ".join(args.words)
    else:
        problem = DEFAULT_PROBLEM

    print(f"Problem statement:\n{problem.strip()}\n")
    print("Generating ArchiMate 3.2 diagram — draw.io will open when ready...\n")

    agent(f"""Generate an ArchiMate 3.2 architecture diagram for the following problem statement.
Use the ArchiMate 3 shape library in draw.io (shape=mxgraph.archimate3.*).
Include all relevant layers, elements, and relationships. Open the diagram when done.

Problem statement:
{problem.strip()}""")

    agent.print_session_total()
