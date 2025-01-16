output = Path("output")  # We can use pathlib.Path without importing it


@rule(output / "hello.txt", depends=output)  # hello now depends on output directory
def hello(target, *args):
    # output_dir is not used
    with open(target, "w") as f:
        f.write("Hello, world!")


@rule(output)
def makedir(target):
    os.makedirs(target)
