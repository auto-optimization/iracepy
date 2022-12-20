[![Python Test](https://github.com/auto-optimization/iracepy/actions/workflows/test.yml/badge.svg)](https://github.com/auto-optimization/iracepy/actions/workflows/test.yml)
[![codecov Badge](https://codecov.io/gh/auto-optimization/iracepy/branch/main/graph/badge.svg)](https://codecov.io/gh/auto-optimization/iracepy)


# Example of using irace from Python. #

## HELP WANTED

Unfortunately, I do not have enough time to extend and maintain iracepy on my own. If you are interested in Python and automatic algorithm configuration and would like to take ownership of this project, please feel free to contact me!

## Installation

  1. Install R: https://github.com/MLopez-Ibanez/irace#installing-r
  1. Install python packages:
      ```bash
      pip install git+https://github.com/auto-optimization/iracepy@main
      ```
  1. Install R packages with 
      ```bash
      Rscript -e "install.packages('irace', repos='https://cloud.r-project.org')"
      ```
      For more detailed instruction, please see [irace README](https://github.com/mlopez-Ibanez/irace#readme)

## Usage

 * See the examples in `examples/`
 
 * Any help/requests/suggestions are welcome.

Since this package is still under development, API **will** change and features might even be removed. We suggest you wait until it's more or less finalized. If you really want to use it now, we recommend you fork this repository and maintain it yourself so you don't rugpulled when we make updates.
 
## TODO

 - [ ] Implement all functionality available in irace
 - [ ] ACOTSP example
 - [ ] Add more examples.
 - [ ] Integrate capping methods: https://github.com/souzamarcelo/capopt



