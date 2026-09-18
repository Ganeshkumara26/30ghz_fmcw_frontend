import sys
for f in ["sweep_lna.py", "sweep_pa.py", "sweep_vco.py"]:
    with open(f, "r") as file:
        data = file.read()
    data = data.replace("delimiter=',', comments='E'", "comments='E'")
    with open(f, "w") as file:
        file.write(data)
