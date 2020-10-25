# railGetter

railGetter is a Python script for retrieving upcoming train times for a specified station using National Rail's OpenLDBWS API.

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

`-n`: Max number of next train times to fetch. (Min=1, Max=20, Default=5)

### Example

Get the next 10 trains from London Paddington:

```bash
$ python3 railGetter.py -s PAD -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -n 10
```