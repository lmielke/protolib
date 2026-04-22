"""
script_path: src/protolib/__main__.py

Shell entry point. Delegates to app.protopy:main so `python -m protolib`
and the `proto` console script share the same dispatch path.
"""
from protolib.app.protopy import main


if __name__ == "__main__":
    main()
