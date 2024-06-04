import sys
import io


class SuppressPrint:
    """
    A class that suppresses the standard output. It can be used
    in a with statement to temporarily suppress print statements.
    """

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._original_stdout


if __name__ == "__main__":
    # Usage:
    with SuppressPrint():
        print("This will not be printed")
        # Call the function from the library here

    print("This will be printed")
