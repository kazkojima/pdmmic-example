import os.path
__dir__ = os.path.split(os.path.abspath(os.path.realpath(__file__)))[0]
data_location = os.path.join(__dir__, "verilog")

def data_file(f):
    """Get absolute path for file inside pdmmic."""
    fn = os.path.join(data_location, f)
    fn = os.path.abspath(fn)
    if not os.path.exists(fn):
        raise IOError("File {f} doesn't exist in pdmmic".format(f))
    return fn

from .pdmmic import PDMmic

__all__ = [PDMmic]
