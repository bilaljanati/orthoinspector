import json

with open("tree.json", "r") as f:
    tree = json.load(f)


root = None
children = {}
size = {}

for sp in tree:
    parent = sp["parent"]
    taxid = sp["id"]
    size[taxid] = sp["value"]
    if parent == "":
        root = taxid
        continue
    if parent not in children:
        children[parent] = []
    children[parent].append(taxid)

min_size = 8
max_size = 16
solutions = []


def bfs(children, size):
    queue = [root]

    while len(queue) > 0:
        node = queue.pop(0)

        if node not in children:
            continue
        for c in children[node]:
            queue.append(c)
        if len(queue) >= min_size and len(queue) <= max_size:
            solutions.append(queue.copy())


bfs(children, size)
print(solutions)
