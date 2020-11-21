# railGetter

railGetter is a Python script for retrieving & displaying upcoming train times for a specified station in the United Kingdom using National Rail's OpenLDBWS API.

## Dependencies

- [Python](https://www.python.org/downloads/) 3.6+
- [Zeep](https://docs.python-zeep.org/en/master/)

## Usage

To use railGetter simply call it:

```bash
$ python3 railGetter.py [OPTIONS]...
```

See also `python3 railGetter.py --help`.

### Options

Required:

`-s` or `--station`: Station code to fetch train times from.

`-t` or `--token`: OpenLDBWS Token to use for connection to the API.

Optional:

`-n` or `--next`: Max number of next train times to fetch. (Min=1, Max=10, Default=5)

### Example

Get the next 10 trains from London Paddington:

```bash
$ python3 railGetter.py -s PAD -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -n 10
```

Get the next 5 trains from Bristol Temple Meads:

```bash
$ python3 railGetter.py -s BRI -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
```
or
```bash
$ python3 railGetter.py -s BRI -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -n 5
```

## Compatibility
These files were only written as a personal test project, and designed to work on my MacOS machine (MacOS 10.14.6) for the Bash shell. I haven't tested its functionality for anything else, I imagine it should also work on Linux as well as other shells with some minor issues, but not Windows, unless ran through WSL.
