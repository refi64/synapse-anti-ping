## Contributing notes

- [Poetry](https://python-poetry.org/) is used to manage dependencies. The `requirements.txt` you
  see in the repo was exported using:

  ```
  poetry export -f requirements.txt --without-hashes > requirements.txt
  ```

  It's highly recommended to set `virtualenvs.in-project` to `true` if using VSCode, as the editor
  will then pick up on the `.venv` directory.

  Note that it is critically important that the dependencies in `requirements.txt` don't conflict
  with those installed in the official, Alpine-based Synapse container images.
- The code is expected to pass type checking using *both* [mypy](http://mypy-lang.org/) *and*
  [Pyright](https://github.com/microsoft/pyright/). (Mypy is the easier of two; it's already listed
  as a development dependency in the Poetry project.) You should run them as below:
  ```
  poetry run mypy .
  poetry run pyright --lib
  ```
  If you're using Pyright as part of VSCode, make sure you enable
  `"pyright.useLibraryCodeForTypes": true`  in your user or workspace settings.
- The (very few) tests are run using `poetry run pytest`.
