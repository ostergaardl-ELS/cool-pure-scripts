# cool-pure-scripts

## api.py
Small script to download content from Pure to a spreadsheet. Default usage is research output with UUIDs, titles and secondary sources, but any content family can be downloaded if desired.

Usage: 

1. Install Python 3 and pip.
2. Clone this repository to your local file system.
3. Install requirements in working folder: `pip install -r requirements.txt`.
4. Run `python3 api.py --help` for instructions.
5. Output file will be saved in working folder with a .xlsx extension supplied in the `--outputfile` option.

Examples:
`python3 api.py https://test.pure.elsevier.com not-real-api-key --resume --apiversion 521`.

This example downloads the data, but also checks if data was previously downloaded and will resume from that point on. This helps avoid having to reharvest everything if an incremental upate is needed. The `apiversion` parameter can be used to override the Pure API version being called.

`python3 api.py https://test.pure.elsevier.com not-real-api-key --family persons --fields 'uuid,externalId,name.*,orcid,info.additionalExternalIds.*,info.previousUuids'`

The second example downloads all persons but limits the fields to include with the `fields` parameter.
