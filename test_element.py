from model.element import Element

element = Element(id=1, node_ids=[1, 2, 3], material_id=1)

print(element)
print(element.to_dict())
