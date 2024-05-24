def convert_to_weighted_edgelist(input_file, output_file, with_weights=True):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # Separate edge data from weight attribute
            node1, node2, _, weight = line.split()
            if with_weights:
                weight = weight.split('}')[0]
                outfile.write(f"{node1} {node2} {weight}\n")
            else:
                outfile.write(f"{node1} {node2}\n")


convert_to_weighted_edgelist('congress.edgelist', 'congress_edges_weighted.dat', with_weights=True)
convert_to_weighted_edgelist('congress.edgelist', 'congress_edges.dat', with_weights=False)
