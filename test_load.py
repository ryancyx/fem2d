from model.load import Load

load = Load(
    id=1,
    node_id=2,
    fx=1000.0,
    fy=0.0
)

print(load)
print(load.to_dict())