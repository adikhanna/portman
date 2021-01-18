#### Assumptions:

System `python3` is located at `/usr/local/bin/python3`

#### Building the project:

Run `make venv` to create a `python3` virtual environment and install all project
dependencies

#### Running the app:

Run `make ui` from the `vsf` base directory only

#### Updating the source code:

1. All source code lives within the `src/` directory
2. Any changes should be introduced via pull requests:
   - `git checkout -b <branch_name>`
   - `git add src/*`
   - `git commit -m "<commit_message>"`
   - `git push -u origin <branch_name>`
   - Create a PR from the `git` repo webpage
3. Remember to run `make format && make typecheck` when updating the source code
and/or before pushing to `git`
