def generate_layer(starting_node):
    layer = []

    for c in starting_node['children']:
        layer.append({'index':c['label']['parts'], 'title':c['label']['title']})

    return layer
