# cool-pure-scripts

## api.py
This is a utility script to download content from Pure to a spreadsheet. The output is saved in 50 record CSV batches and a combined Excel spreadsheet.

By default the script will download select fields for research output. The `--family` and `--fields` options allow you to override the content family and fields included, respectively. 

### Usage

1. Install Python 3 and pip.
2. Clone this repository to your local file system.
3. Install requirements in working folder: `pip install -r requirements.txt`.
4. Run `python3 api.py --help` for instructions.
5. Output will be saved in a subfolder named by the Pure URL.

#### Options
Hint: Use `--help` to show these options.
| Name | Description | Default |
| - | - | - |
| **`url`** | Pure base URL (exclude /ws). | |
| **`apikey`** | Pure API key. | |
| `--apiversion` | The API version to use. | `522` |
| `--family` | The family to download. | `research-outputs` |
| `--fields` | The fields to retrieve. | `uuid,title.value,info.*` |
| `--resume` | Resume harvesting from last time. | `True` |
| `--flatten_data` | Flattens nested data into separate columns. | `True` |
| `--help` | Display help. | |

#### Dependencies
```
click==7.1.2
numpy==1.21.2
flatten_json==0.1.13
requests==2.26.0
pandas==1.3.2
```
### Examples

This section describes examples of usage.

Note: Since the output Excel is always indexed by `uuid`, you must make sure to include this field when overriding `--fields`.

#### Version and Resumption

The following example download research output and will resume from the last batch number downloaded in the output folder. This helps avoid having to reharvest everything if an incremental upate is needed. The `--apiversion` parameter can be used to override the Pure API version being called.

`python3 api.py https://test.pure.elsevier.com not-real-api-key --resume --apiversion 521`

#### Research Output

Downloads all research output, including UUID, title, created date and source.

`python3 api.py https://test.pure.elsevier.com not-real-api-key --fields uuid,title.value,info.createdDate,externalIdSource`

#### Persons

Download all persons and limit the fields to include with the `--fields` option.

`python3 api.py https://test.pure.elsevier.com not-real-api-key --family persons --fields 'uuid,externalId,name.*,orcid,info.additionalExternalIds.*,info.previousUuids'`

#### Projects

Download projects, including title, source, creation date, period and status.

`python3 api.py https://test.pure.elsevier.com not-real-api-key --fields 'uuid,externalId,title.text.value,externalIdSource,info.createdDate,period.*,status.key' --family projects`


## Future Work
- Option to remove unflattened columns from output.
- Smarter resumption - label output by family.
- Select most recent API version by default.
- Add list of families to `--help`.
- Override page size from `50`.
- Support search query `--query`.
- Add `--clean` argument to clear output folder.
- Support new Pure API (write).
