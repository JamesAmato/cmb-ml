# ml_cmb_pysm_sims - Directory Structure Branch

Rough development repository for PySM simulations for ML project

This branch is just for checking out a directory structure. Compare to the jim_lab.yaml.

## File System Considerations

I suggest using the following directory structure.

```
CMB_Project/
│
├── pysm3/                             # PySM3
├── ml_cmb_pysm_sims/                  # This repository for ML-driven CMB simulations with PySM
     ├── Data
          ├── Assets
               ├── Planck
               ├── WMAP
          ├── Cache
          ├── Datasets
```

Clearly systems vary. Configuration files may be changed to describe your local structure. I suggest creating your own configuration file by copying one included in `cfg/local_system/` (after getting the repo).

If you're regularly pulling from the repo, add `export CMB_SIMS_LOCAL_SYSTEM=your_system` to the end of your `.bashrc` file and then either `source ~/.bashrc` or restart your terminal. If using a Mac, use `.zshrc` instead of `.bashrc` (or whatever... Jim is moving on but one day these will be good general instructions).

If you won't be actively pulling from the repo (how I long for that day), simply change the top-level configuration (config.yaml) to `defaults: - local_system: your_system` where `your_system` is the filename of your configuration.

## Setup

Go to another branch for this information

## Needed files

Descriptions of how to obtain needed files are in the `/Data/Assets` varied README.md files. Note that you only need one set of WMAP chain files.

# To do

- [ ] Does this file structure look ok?
- [ ] Does the .gitignore work correctly for you?
