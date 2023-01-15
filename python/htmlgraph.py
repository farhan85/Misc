#!/usr/bin/env python

"""
Creates a directional graph which can be viewed in the browser.
This can be used as an imported package, or invoked from the cli.

This script is just for quickly visualising a graph. It is not
a full-featured graph visualisation program. For that, check out
the Cytoscape library https://js.cytoscape.org/

Usage examples:

As an imported package:
    from htmlgraph import CytoscapeGraph
    graph = CytoscapeGraph()
    graph.edd_edge('node 1', 'node 2')
    graph.edd_edge('node 1', 'node 3')
    print(graph.to_html())

From the CLI:
> python ./htmlgraph.py node1,node2 node1,node3 > output.html
"""

import jinja2
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import defaultdict


TEMPLATE = jinja2.Template("""
<html>
  <head>
    <meta content="text/html;charset=utf-8" http-equiv="Content-Type">
    <meta content="utf-8" http-equiv="encoding">
    <style>
      #cy {
        width: 95%;
        height: 95%;
        display: block;
      }
    </style>
    <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
    <script>
      document.addEventListener("DOMContentLoaded", function() {
        var cy = cytoscape({
          container: document.getElementById('cy'),
          elements: {
            nodes: [
{%- for n_name, n_id in nodes %}
              { data: { id: '{{n_id}}', name: '{{n_name}}' } },
{%- endfor %}
            ],
            edges: [
{%- for e_id, e_source, e_dest in edges %}
              { data: { id: '{{e_id}}', source: '{{e_source}}', target: '{{e_dest}}' } },
{%- endfor %}
            ]
          },
          style: [
            {
              selector: 'node',
              style: {
                'background-color': '#666',
                'label': 'data(name)'
              }
            },
            {
              selector: 'edge',
              style: {
                'width': 3,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier'
              }
            }
          ],
          layout: {
            name: 'breadthfirst',
            directed: true
          }
        })
      });
    </script>
  </head>

  <body>
    <div id="cy"></div>
  </body>
</html>
""".strip())


class CytoscapeGraph:
    def __init__(self):
        self.node_name_to_id = defaultdict(lambda: 'n{}'.format(len(self.node_name_to_id) + 1))
        self.edges = set()

    def add_edge(self, node_name_1, node_name_2):
        self.edges.add((self.node_name_to_id[node_name_1], self.node_name_to_id[node_name_2]))

    def to_html(self):
        edges = ((f'e{idx}', n_id_1, n_id_2) for idx, (n_id_1, n_id_2) in enumerate(self.edges))
        return TEMPLATE.render(nodes=self.node_name_to_id.items(), edges=edges)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument('edges', help='List of connected node pairs', nargs='*')
    args = parser.parse_args()
    graph = CytoscapeGraph()
    for edge in args.edges:
        src, dst = edge.split(',')
        graph.add_edge(src, dst)
    print(graph.to_html())
