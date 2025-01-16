@rule("hello.txt")
def hello(target):
    with open(target, "w") as f:
        f.write("Hello, world!")
