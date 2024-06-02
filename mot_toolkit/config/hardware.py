import os

cpu_count = os.cpu_count()

print(f"CPU Core Count: {cpu_count}")

io_cpu_count = int(cpu_count * (2 / 3))
print(f"Recommend IO CPU Core Count: {io_cpu_count}")
