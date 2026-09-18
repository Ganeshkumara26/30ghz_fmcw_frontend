import os

handover_path = r"C:\Users\hvnth\.gemini\antigravity-ide\brain\0e800da0-0ffc-49c4-994b-28d3b800bb54\HANDOVER.md"

with open("append.md", "r") as f:
    content = f.read()

with open(handover_path, "a") as f:
    f.write(content)
