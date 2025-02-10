# Development notes

My personal development notes.

## Steps used

1. Init this repo:

```bash
# Create development directory
mkdir -p ~/AlfredWorkflows/audible-workflow
cd ~/AlfredWorkflows/audible-workflow
git init
```

2. Create Alfred workflow with imagined schema.

3. Get workflow path by right-clicking workflow in Alfred and selecting "Reveal in Finder". Then right click to `copy [...] as Pathname`. Run the following for ease in next commands:

```bash
export WORKFLOW_PATH="<pasted path>"
```

4. Copy workflow contents to development directory:

```bash
cp -r $WORKFLOW_PATH/* .
```

5. Remove contents of workflow in Alfred:

```bash
rm -rf $WORKFLOW_PATH/*
```

6. Create symbolic link to workflow directory:

```bash
ln -s "$(pwd)"/* $WORKFLOW_PATH
```