# MDStudio_cli

Command line interface to interact with [MDStudio](https://github.com/MD-Studio/MDStudio)
microservices.

## Installation

Clone or download the `mdstudio_cli` repository from Github and install using Python pip (PyPI) as:

> ```pip install mdstudio_cli```

## Usage

1) Get basic usage information and configuration options for the command line as:

   ```mdstudio-cli -h```

2) Get configuration for a MDStudio WAMP endpoint using the endpoints URI and -i/--info:
    
   ```mdstudio-cli -i -u mdgroup.lie_structures.endpoint.convert```

3) Calling an endpoint using the configuration options obtained in step 2:

   ```mdstudio-cli -u mdgroup.lie_structures.endpoint.convert --mol mol.pdb --output_format mol2```
   
   Takes the content of PDB file "mol.pdb", sends it to the `convert` endpoint of the
   lie_structures endpoint and convert it to a mol2 format.
   The output is stored as "mol.mol2" on disk again, all none file-like output if any is
   printed to standard out (stdout).
   
   The raw JSON output from a microservice endpoint can be stored to disk as JSON file using
   the -j/--store_json option.